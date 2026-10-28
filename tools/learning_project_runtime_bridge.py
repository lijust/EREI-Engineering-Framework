"""Opt-in project runtime knowledge-read hook gated by EXISTING capability activation.

This is a live-project-capable, read-only integration API; CI uses synthetic
projects only. Opening an observation session does not authorize an AI model
to execute anything or prove it consumed knowledge. Existing Task Learning
capture remains a separate owner-controlled operation.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from tools import capability_activation as activation
from tools import learning_trace_reference_producer as reference
from tools import task_learning

ALLOWED_CAPABILITIES = frozenset({
    "learning_pattern_analysis", "framework_effectiveness_measurement",
})
MAX_SESSION_CLOCK_SKEW = timedelta(minutes=5)
MAX_CLOCK_ROLLBACK = timedelta(seconds=5)


def _runtime_utc_now() -> datetime:
    # Local runtime clock is not a remotely authenticated time source.
    return datetime.now(timezone.utc)


class ProjectReadDenied(RuntimeError):
    pass


def _sha(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def _activation_snapshot(root: Path, capability: str, now: datetime) -> dict:
    """Re-use the existing policy resolver, clean-checkout and project records."""
    try:
        activation.assert_clean_framework_checkout()
        sources = {
            "manifest": root / activation.MANIFEST_PATH,
            "registry": activation.REGISTRY_PATH,
            "adoption": root / activation.ADOPTION_PATH,
        }
        before = {name: _sha(path) for name, path in sources.items()}
        manifest = activation._read_json(sources["manifest"], "project framework manifest")
        registry = activation._read_json(sources["registry"], "Framework capability registry")
        adoption = (activation._read_json(sources["adoption"], "candidate capability adoption")
                    if sources["adoption"].exists() else None)
        framework = activation._validate_manifest(manifest)
        loaded = activation.detect_loaded_framework_ref()
        resolved = (activation.resolve_project_tag_ref(framework["ref"])
                    if framework["ref_type"] == "tag" else None)
        status = activation.resolve_activation(
            manifest, registry, capability, adoption_document=adoption,
            loaded_framework_ref=loaded, resolved_project_ref=resolved, now=now,
        )
        if status["status"] not in activation.ACTIVE_STATUSES:
            raise ProjectReadDenied("CAPABILITY_NOT_ACTIVE")
        if (before != {name: _sha(path) for name, path in sources.items()}
                or activation.detect_loaded_framework_ref() != loaded):
            raise ProjectReadDenied("ACTIVATION_SOURCE_CHANGED")
        activation.assert_clean_framework_checkout()
        return {
            "capability": capability, "status": status["status"],
            "framework_sha": loaded, "manifest_sha256": before["manifest"],
            "registry_sha256": before["registry"],
            "adoption_sha256": before["adoption"],
        }
    except ProjectReadDenied:
        raise
    except (activation.ActivationError, OSError, ValueError, KeyError,
            TypeError, AttributeError, UnicodeError, OverflowError) as exc:
        raise ProjectReadDenied("ACTIVATION_SOURCE_UNVERIFIED") from exc


class ProjectKnowledgeReadSession:
    """Revalidate active project capability before read and after ledger capture.

    An actual caller must pass the content returned by read() into its own
    task executor. This class CANNOT know whether the consumer used it.
    """

    def __init__(
        self, project_root: Path | str, occurrence_id: str,
        intervention_id: str, implementation_ref: str, *,
        capability: str, now: datetime,
    ):
        if (type(capability) is not str or capability not in ALLOWED_CAPABILITIES
                or type(now) is not datetime or now.tzinfo is None
                or now.utcoffset() is None):
            raise ProjectReadDenied("SESSION_POLICY_INPUT_INVALID")
        try:
            root = Path(project_root).resolve(strict=True)
            if not root.is_dir():
                raise ProjectReadDenied("PROJECT_ROOT_INVALID")
        except (TypeError, OSError, ValueError, AttributeError) as exc:
            raise ProjectReadDenied("PROJECT_ROOT_INVALID") from exc
        try:
            clock = _runtime_utc_now()
            if (clock.tzinfo is None or clock.utcoffset() is None or
                    abs((now.astimezone(timezone.utc) - clock).total_seconds()) >
                    MAX_SESSION_CLOCK_SKEW.total_seconds()):
                raise ProjectReadDenied("SESSION_CLOCK_OUT_OF_SYNC")
        except (TypeError, ValueError, OverflowError) as exc:
            raise ProjectReadDenied("SESSION_CLOCK_UNVERIFIED") from exc
        self.root = root
        self.capability = capability
        self.now = now
        self._last_runtime_clock = clock
        self.bound = _activation_snapshot(root, capability, clock)
        # An existing completed occurrence must never gain retrospective
        # "exposure" merely because knowledge was read after task completion.
        self._started_occurrence = occurrence_id
        self._assert_no_terminal_occurrence()
        try:
            self.observer = reference.KnowledgeReadObserver(
                root, occurrence_id, intervention_id, implementation_ref,
            )
        except (reference.ObservationDenied, ValueError, TypeError) as exc:
            raise ProjectReadDenied("SESSION_IDENTITY_INVALID") from exc
        self.observed_read = False

    def _assert_no_terminal_occurrence(self) -> None:
        try:
            snapshot = task_learning.authoritative_snapshot(self.root)
            if any(
                task_learning._occurrence(event) == self._started_occurrence
                for event in snapshot["events"]
            ):
                raise ProjectReadDenied("TASK_ALREADY_TERMINAL_BEFORE_READ")
        except ProjectReadDenied:
            raise
        except (task_learning.LearningError, OSError, ValueError) as exc:
            raise ProjectReadDenied("TASK_SOURCE_UNVERIFIED") from exc

    def _recheck(self) -> None:
        # Recheck at the actual time of use: a fixed caller-supplied clock
        # could otherwise keep a now-expired candidate active indefinitely.
        clock = _runtime_utc_now()
        if clock.tzinfo is None or clock.utcoffset() is None:
            raise ProjectReadDenied("SESSION_CLOCK_UNVERIFIED")
        if clock < self._last_runtime_clock - MAX_CLOCK_ROLLBACK:
            raise ProjectReadDenied("SESSION_CLOCK_ROLLBACK")
        self._last_runtime_clock = max(clock, self._last_runtime_clock)
        new = _activation_snapshot(self.root, self.capability, clock)
        if new != self.bound:
            raise ProjectReadDenied("ACTIVATION_CHANGED_DURING_SESSION")

    def read(self, relative_path: str, expected_sha256: str) -> bytes:
        self._recheck()
        self._assert_no_terminal_occurrence()
        try:
            data = self.observer.read(relative_path, expected_sha256)
        except reference.ObservationDenied as exc:
            raise ProjectReadDenied(str(exc)) from exc
        self._assert_no_terminal_occurrence()
        self._recheck()
        self.observed_read = True
        return data

    def finalize_after_capture(
        self, intervention: Any, selection: Any, trace_ref: str,
    ) -> dict:
        """Require existing captured terminal event and complete cohort.

        This does NOT capture the event or change the intervention record.
        The project remains responsible for recording terminal outcomes,
        including failed/canceled tasks, through existing Task Learning.
        """
        if not self.observed_read:
            raise ProjectReadDenied("NO_PROJECT_READ_OBSERVED")
        if type(trace_ref) is not str or trace_ref != self.bound["framework_sha"]:
            raise ProjectReadDenied("TRACE_FRAMEWORK_REVISION_MISMATCH")
        self._recheck()
        try:
            snapshot = task_learning.authoritative_snapshot(self.root)
            matching = [
                event for event in snapshot["events"]
                if task_learning._occurrence(event) == self.observer.occurrence_id
            ]
            if len(matching) != 1:
                raise ProjectReadDenied("TERMINAL_TASK_NOT_RECORDED")
            event = matching[0]
            if event["framework_ref"] != self.bound["framework_sha"]:
                raise ProjectReadDenied("TASK_FRAMEWORK_REVISION_MISMATCH")
            if event["project"]["repository"] != intervention["cohort"]["repository"]:
                raise ProjectReadDenied("TASK_REPOSITORY_MISMATCH")
            output = self.observer.finish(intervention, selection, trace_ref)
            self._recheck()
        except ProjectReadDenied:
            raise
        except (reference.ObservationDenied, task_learning.LearningError,
                OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            raise ProjectReadDenied("PROJECT_TRACE_RECONCILIATION_DENIED") from exc
        return {
            **output,
            "status": "PROJECT_LOCAL_ACTIVE_KNOWLEDGE_READ_RECONCILED",
            "source_activation": dict(self.bound),
            "observed_read_delivered_to_caller": True,
            "consumer_use_verified": False,
            "trace_runtime_independently_attested": False,
            "learning_exposure_independently_verified": False,
            "effectiveness": "NOT_ESTABLISHED",
            "causation": "NOT_ESTABLISHED",
            "stable_ready": False,
        }
