"""Offline reconciliation of per-task learning-reuse trace markers with Task Learning.

This is a read-only *claim consistency* check. A marker is not independent
proof of execution or exposure; an absent marker is never proof of absence
without a complete-trace declaration (which is itself unauthenticated).
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from tools import learning_intervention_sources, task_learning


class TraceContractError(ValueError):
    pass


SHA_RE = re.compile(r"^[a-f0-9]{40}$")


def _deny(code: str) -> dict:
    return {
        "kind": "EREI_LEARNING_TRACE_JOIN_V1", "status": "DENIED",
        "reason_code": code, "executed": False, "files_written": False,
        "trace_identity_attested": False, "trace_capture_authenticated": False,
        "learning_exposure_independently_verified": False,
        "root_cause_recurrence_verified": False,
        "effectiveness": "NOT_ESTABLISHED", "causation": "NOT_ESTABLISHED",
        "stable_ready": False,
    }


def _exact(obj: Any, keys: set[str]) -> dict:
    if type(obj) is not dict or set(obj) != keys:
        raise TraceContractError("TRACE_CONTRACT_INVALID")
    return obj


def _text(value: Any) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise TraceContractError("TRACE_CONTRACT_INVALID")
    return value


def _sha(value: Any) -> str:
    if not SHA_RE.fullmatch(_text(value)):
        raise TraceContractError("TRACE_CONTRACT_INVALID")
    return value


def _task_stats(events: list[dict]) -> dict:
    escape_assessed = [
        e for e in events
        if task_learning._is_measured(e, "verification_escape")
    ]
    failure_assessed = [
        e for e in events
        if task_learning._is_measured(e, "verification_failures")
    ]
    return {
        "tasks": len(events),
        "verified_successes": sum(e["outcome_class"] == "verified_success" for e in events),
        "failed_tasks": sum(e["outcome_class"] == "failed" for e in events),
        "blocked_tasks": sum(e["outcome_class"] == "blocked" for e in events),
        "verification_escape_assessed": len(escape_assessed),
        "verification_escapes": sum(e["verification_escape"] is True for e in escape_assessed),
        "verification_failure_assessed": len(failure_assessed),
        "tasks_with_verification_failures": sum(
            e["verification_failures"] > 0 for e in failure_assessed
        ),
    }


def reconcile_learning_trace_claims(
    project_root: Path | str, intervention: Any, selection: Any, bundle: Any,
) -> dict:
    """Reconcile *claimed* reuse steps against all locally eligible occurrences.

    Source membership comes from PR119, which checks the original event ledger
    and full cohort denominator. Trace receipts are caller-supplied, not
    authenticated. No effect or intervention exposure is independently proven.
    """
    baseline = learning_intervention_sources.assess_intervention_against_ledger(
        project_root, intervention, selection,
    )
    if baseline["status"] != "LOCAL_COHORT_MEMBERSHIP_MATCHED":
        return _deny("SOURCE_COHORT_NOT_ESTABLISHED")
    try:
        _exact(bundle, {
            "schema_version", "intervention_id", "epoch_id",
            "ledger_generation_sha256", "traces",
        })
        if (type(bundle["schema_version"]) is not int or bundle["schema_version"] != 1
                or _text(bundle["intervention_id"]) != intervention["intervention_id"]
                or _text(bundle["epoch_id"]) != intervention["cohort"]["epoch_id"]
                or _text(bundle["ledger_generation_sha256"]) !=
                baseline["source_binding"]["ledger_generation_sha256"]):
            raise TraceContractError("TRACE_SOURCE_BINDING_MISMATCH")
        entries = bundle["traces"]
        if type(entries) is not list:
            raise TraceContractError("TRACE_CONTRACT_INVALID")
        target = Path(project_root).resolve(strict=True)
        snapshot = task_learning.authoritative_snapshot(target)
        if snapshot["generation"] != bundle["ledger_generation_sha256"]:
            raise TraceContractError("LEDGER_CHANGED_DURING_TRACE_JOIN")
        by_id = {
            task_learning._occurrence(event): event for event in snapshot["events"]
        }
        declared = {
            row["occurrence_id"]: row for row in intervention["cohort"]["tasks"]
        }
        seen: set[str] = set()
        groups: dict[str, list[dict]] = {
            "reuse_marker_reported": [],
            "no_marker_complete_trace_claim": [],
            "trace_incomplete_no_marker": [],
        }
        for entry in entries:
            _exact(entry, {
                "occurrence_id", "task_fingerprint", "framework_ref",
                "trace_ref", "capture_complete", "steps",
            })
            identity = _text(entry["occurrence_id"])
            if identity in seen:
                raise TraceContractError("DUPLICATE_TRACE_OCCURRENCE")
            seen.add(identity)
            if identity not in declared or identity not in by_id:
                raise TraceContractError("TRACE_COHORT_MEMBERSHIP_MISMATCH")
            event = by_id[identity]
            if (_text(entry["task_fingerprint"]) != event["fingerprint"]
                    or _sha(entry["framework_ref"]) != event["framework_ref"]):
                raise TraceContractError("TRACE_TASK_SOURCE_MISMATCH")
            _sha(entry["trace_ref"])
            if type(entry["capture_complete"]) is not bool or type(entry["steps"]) is not list:
                raise TraceContractError("TRACE_CONTRACT_INVALID")
            found = False
            for step in entry["steps"]:
                if type(step) is not dict:
                    raise TraceContractError("TRACE_CONTRACT_INVALID")
                op = step.get("op")
                if op == "other_operation":
                    _exact(step, {"op"})
                elif op == "learning_reuse":
                    _exact(step, {"op", "intervention_id", "implementation_ref"})
                    if (_text(step["intervention_id"]) != intervention["intervention_id"]
                            or _sha(step["implementation_ref"]) !=
                            intervention["implementation"]["ref"]):
                        raise TraceContractError("REUSE_MARKER_IDENTITY_MISMATCH")
                    found = True
                else:
                    raise TraceContractError("TRACE_CONTRACT_INVALID")
            expected = True if found else False if entry["capture_complete"] else None
            if declared[identity]["exposed"] is not expected:
                raise TraceContractError("EXPOSURE_DECLARATION_CONFLICT")
            if found and intervention["adoption"] is None:
                raise TraceContractError("REUSE_MARKER_WITHOUT_ADOPTION")
            group = (
                "reuse_marker_reported" if found else
                "no_marker_complete_trace_claim" if entry["capture_complete"] else
                "trace_incomplete_no_marker"
            )
            # Do not silently upgrade historical observations into prospective.
            if declared[identity]["identity_basis"] == "prospective":
                groups[group].append(event)
        if seen != set(declared):
            raise TraceContractError("TRACE_COHORT_MEMBERSHIP_MISMATCH")
        paths = task_learning._paths(target)
        if task_learning._ledger_generation(paths) != bundle["ledger_generation_sha256"]:
            raise TraceContractError("LEDGER_CHANGED_DURING_TRACE_JOIN")
        digest = hashlib.sha256(
            json.dumps(bundle, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest()
        return {
            "kind": "EREI_LEARNING_TRACE_JOIN_V1",
            "status": "UNVERIFIED_TRACE_CLAIMS_RECONCILED",
            "trace_bundle_sha256": digest,
            "source_binding": baseline["source_binding"],
            "prospective_groups": {
                name: _task_stats(events) for name, events in groups.items()
            },
            "prospective_eligible": sum(len(events) for events in groups.values()),
            "all_declared_receipts_joined": len(seen),
            "executed": False, "files_written": False,
            "trace_identity_attested": False, "trace_capture_authenticated": False,
            "learning_exposure_independently_verified": False,
            "root_cause_recurrence_verified": False,
            "effectiveness": "NOT_ESTABLISHED", "causation": "NOT_ESTABLISHED",
            "stable_ready": False,
        }
    except (TraceContractError, TypeError, ValueError, KeyError, AttributeError,
            OSError, OverflowError, task_learning.LearningError) as exc:
        return _deny(exc.args[0] if isinstance(exc, TraceContractError)
                     else "TRACE_EVIDENCE_INVALID")
