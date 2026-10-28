"""Reference runtime observation of an actual knowledge-file read, not proof of effectiveness.

A call to KnowledgeReadObserver.read() actually reads pinned bytes, and finish()
joins that observation to an already-recorded Task Learning occurrence.
It does NOT attest production execution, intervention adoption, knowledge use
by an AI model, or intervention causation. No provider calls.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools import learning_exposure_traces, learning_intervention_sources, task_learning

SHA40 = re.compile(r"^[a-f0-9]{40}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
MAX_KNOWLEDGE_BYTES = 128 * 1024
REFERENCE_TIMESTAMP = datetime(2026, 10, 28, 3, 0, tzinfo=timezone.utc)
REFERENCE_OCCURRENCE = "EOCC-20261028T030000Z-A1B2C3D4"
REFERENCE_TASK = "ETASK-20261028T030000Z-A1B2C3D4"
REFERENCE_KNOWLEDGE = b"synthetic reference knowledge: verify the task outcome independently\n"


class ObservationDenied(RuntimeError):
    pass


class KnowledgeReadObserver:
    """A narrow read hook; caller-owned invocation is not independently trusted."""

    def __init__(self, project_root: Path | str, occurrence_id: str,
                 intervention_id: str, implementation_ref: str):
        if (type(occurrence_id) is not str or
                task_learning.OCCURRENCE_ID_RE.fullmatch(occurrence_id) is None or
                type(intervention_id) is not str or not intervention_id.strip() or
                type(implementation_ref) is not str or
                SHA40.fullmatch(implementation_ref) is None):
            raise ObservationDenied("OBSERVER_IDENTITY_INVALID")
        self.root = Path(project_root).resolve(strict=True)
        self.occurrence_id = occurrence_id
        self.intervention_id = intervention_id
        self.implementation_ref = implementation_ref
        self._observed = False

    def read(self, relative_path: str, expected_sha256: str) -> bytes:
        """Read bytes beneath a fixed project knowledge directory and pin digest."""
        if self._observed:
            raise ObservationDenied("ALREADY_OBSERVED")
        if (type(relative_path) is not str or not relative_path or
                Path(relative_path).is_absolute() or
                any(p in ("..", ".") for p in Path(relative_path).parts) or
                type(expected_sha256) is not str or
                SHA256.fullmatch(expected_sha256) is None):
            raise ObservationDenied("KNOWLEDGE_LOCATION_INVALID")
        try:
            base = (self.root / ".erei" / "knowledge").resolve(strict=True)
            candidate = (base / relative_path).resolve(strict=True)
            if not candidate.is_relative_to(base) or not candidate.is_file():
                raise ObservationDenied("KNOWLEDGE_LOCATION_INVALID")
            if candidate.stat().st_size > MAX_KNOWLEDGE_BYTES:
                raise ObservationDenied("KNOWLEDGE_FILE_TOO_LARGE")
            with candidate.open("rb") as stream:
                data = stream.read(MAX_KNOWLEDGE_BYTES + 1)
            if not data or len(data) > MAX_KNOWLEDGE_BYTES:
                raise ObservationDenied("KNOWLEDGE_FILE_INVALID")
            if hashlib.sha256(data).hexdigest() != expected_sha256:
                raise ObservationDenied("KNOWLEDGE_DIGEST_MISMATCH")
            self._observed = True
            return data
        except (OSError, ValueError, OverflowError) as exc:
            raise ObservationDenied("KNOWLEDGE_READ_INVALID") from exc

    def finish(self, intervention: Any, selection: Any, trace_ref: str) -> dict:
        """Bind the observed read to existing local occurrence; no new task writes."""
        if not self._observed:
            raise ObservationDenied("NO_KNOWLEDGE_READ_OBSERVED")
        if type(trace_ref) is not str or SHA40.fullmatch(trace_ref) is None:
            raise ObservationDenied("TRACE_REF_INVALID")
        if (type(intervention) is not dict or
                intervention.get("intervention_id") != self.intervention_id or
                type(intervention.get("implementation")) is not dict or
                intervention["implementation"].get("ref") != self.implementation_ref):
            raise ObservationDenied("INTERVENTION_IDENTITY_MISMATCH")
        baseline = learning_intervention_sources.assess_intervention_against_ledger(
            self.root, intervention, selection,
        )
        if baseline["status"] != "LOCAL_COHORT_MEMBERSHIP_MATCHED":
            raise ObservationDenied("SOURCE_COHORT_NOT_ESTABLISHED")
        snapshot = task_learning.authoritative_snapshot(self.root)
        if snapshot["generation"] != baseline["source_binding"]["ledger_generation_sha256"]:
            raise ObservationDenied("LEDGER_CHANGED_DURING_OBSERVATION")
        by_id = {task_learning._occurrence(e): e for e in snapshot["events"]}
        rows = intervention["cohort"]["tasks"]
        if (self.occurrence_id not in {r["occurrence_id"] for r in rows} or
                any(row["exposed"] is not None for row in rows)):
            raise ObservationDenied("COHORT_EXPOSURE_ALREADY_DECLARED")
        updated = copy.deepcopy(intervention)
        receipts = []
        for row in updated["cohort"]["tasks"]:
            identity = row["occurrence_id"]
            event = by_id[identity]
            match = identity == self.occurrence_id
            if match:
                row["exposed"] = True
            receipts.append({
                "occurrence_id": identity,
                "task_fingerprint": event["fingerprint"],
                "framework_ref": event["framework_ref"],
                "trace_ref": trace_ref,
                "capture_complete": match,
                "steps": [{
                    "op": "learning_reuse",
                    "intervention_id": self.intervention_id,
                    "implementation_ref": self.implementation_ref,
                }] if match else [],
            })
        bundle = {
            "schema_version": 1,
            "intervention_id": self.intervention_id,
            "epoch_id": intervention["cohort"]["epoch_id"],
            "ledger_generation_sha256": snapshot["generation"],
            "traces": receipts,
        }
        join = learning_exposure_traces.reconcile_learning_trace_claims(
            self.root, updated, selection, bundle,
        )
        if join["status"] != "UNVERIFIED_TRACE_CLAIMS_RECONCILED":
            raise ObservationDenied("TRACE_RECONCILIATION_DENIED")
        return {
            "status": "LOCAL_KNOWLEDGE_READ_OBSERVED",
            "bundle": bundle, "intervention_accounting_input": updated,
            "knowledge_file_read_observed": True,
            "knowledge_used_in_real_project_verified": False,
            "independent_trace_attestation": False,
            "effectiveness": "NOT_ESTABLISHED",
            "causation": "NOT_ESTABLISHED",
            "stable_ready": False,
        }


def produce_reference_fixture(framework_sha: str) -> dict:
    """Execute a synthetic read + Task Learning capture in a temp project."""
    if type(framework_sha) is not str or SHA40.fullmatch(framework_sha) is None:
        raise ObservationDenied("FRAMEWORK_SHA_INVALID")
    with tempfile.TemporaryDirectory(prefix="erei-reference-trace-") as temp:
        root = Path(temp)
        (root / ".erei" / "knowledge").mkdir(parents=True)
        (root / ".erei" / "framework.json").write_text("{}", encoding="utf-8")
        knowledge = root / ".erei" / "knowledge" / "reference.txt"
        knowledge.write_bytes(REFERENCE_KNOWLEDGE)
        observer = KnowledgeReadObserver(
            root, REFERENCE_OCCURRENCE, "synthetic-reference-learning", "a" * 40
        )
        content = observer.read(
            "reference.txt", hashlib.sha256(REFERENCE_KNOWLEDGE).hexdigest()
        )
        if content != REFERENCE_KNOWLEDGE:
            raise ObservationDenied("REFERENCE_READ_MISMATCH")
        args = argparse.Namespace(
            task_id=REFERENCE_TASK, occurrence_id=REFERENCE_OCCURRENCE,
            project_repository="example/reference-only-project",
            project_name="Synthetic only", framework_ref=framework_sha,
            workflow="bug-fix", risk="L2", terminal_state="COMPLETE_VERIFIED",
            outcome_class="verified_success", material=True,
            rework_cycles=0, verification_failures=0,
            verification_escape=False, framework_feedback_created=False,
            manual_workaround=False, context_gap=False,
            unexpected_scope_growth=False, security_or_data_critical_event=False,
            duration_class="short", failure_stage="none", failure_subject=None,
            feedback_id=[], feedback_fingerprint=[], tag=[], task_group=None,
        )
        event = task_learning.build_event(args, now=REFERENCE_TIMESTAMP)
        task_learning.capture(root, event)
        snapshot = task_learning.authoritative_snapshot(root)
        ledger_path = task_learning._paths(root)["events"]
        intervention = {
            "schema_version": 1, "intervention_id": "synthetic-reference-learning",
            "finding_refs": ["synthetic:reference"], "root_cause": "synthetic-only",
            "development_output_ref": "synthetic:LDO",
            "implementation": {"repository": "example/framework", "ref": "a" * 40},
            "adoption": {"repository": "example/reference-only-project",
                         "ref": "b" * 40, "implementation_ref": "a" * 40,
                         "evidence": ["synthetic:adoption"]},
            "cohort": {
                "repository": "example/reference-only-project",
                "ref": "c" * 40,
                "ledger_sha256": hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
                "epoch_id": snapshot["state"]["epoch_id"],
                "eligibility_rule": learning_intervention_sources.SELECTION_RULE,
                "selection_ref": "d" * 40,
                "tasks": [{"occurrence_id": REFERENCE_OCCURRENCE,
                           "identity_basis": "prospective",
                           "exposed": None, "recurred": None,
                           "evidence": ["synthetic:reference-record"]}],
            },
        }
        selection = {
            "schema_version": 1,
            "rule_id": learning_intervention_sources.SELECTION_RULE,
            "selection_ref": "d" * 40, "workflow": "bug-fix",
            "risk": "L2", "material_only": True,
            "from_inclusive": "2026-10-28T03:00:00Z",
            "to_exclusive": "2026-10-28T03:01:00Z",
        }
        result = observer.finish(intervention, selection, framework_sha)
        return result["bundle"]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic-only reference trace producer")
    parser.add_argument("--reference-fixture", action="store_true", required=True)
    parser.add_argument("--framework-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    bundle = produce_reference_fixture(args.framework_sha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(bundle, sort_keys=True, ensure_ascii=False,
                   allow_nan=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print("REFERENCE_ONLY_SYNTHETIC_TRACE_PRODUCED; NO_REAL_PROJECT_EXPOSURE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
