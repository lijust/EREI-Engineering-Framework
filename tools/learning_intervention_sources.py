"""Fail-closed, read-only binding for existing Learning Intervention V1 evidence.

This module does NOT authenticate adoption, attest intervention exposure, prove
recurrence, or infer causation. It joins declarations to an existing validated
Task Learning ledger and recalculates *cohort membership and observed task
outcomes* only. It never runs a capability, closes reviews or writes artifacts.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from tools import capability_activation, learning_effectiveness, task_learning

SELECTION_RULE = "all_material_workflow_risk_time_v1"


def _deny(reason: str, *, membership: dict | None = None) -> dict:
    value = {
        "kind": "EREI_INTERVENTION_LEDGER_BINDING_V1",
        "status": "DENIED", "reason_code": reason,
        "project_files_written": False, "model_original_score_changed": False,
        "source_identity_attested": False, "cohort_selection_pre_registered": False,
        "adoption_authenticity_verified": False, "exposure_verified": False,
        "root_cause_recurrence_verified": False, "effectiveness": "NOT_ESTABLISHED",
        "causation": "NOT_ESTABLISHED", "stable_ready": False,
    }
    if membership is not None:
        value["membership_diagnostic"] = membership
    return value


def _validate_selection(selection: Any, cohort: dict) -> tuple[Any, Any]:
    """Strict, explicit selector: no free-text rule interpretation."""
    if type(selection) is not dict or set(selection) != {
        "schema_version", "rule_id", "selection_ref", "workflow", "risk",
        "from_inclusive", "to_exclusive", "material_only",
    }:
        raise ValueError("SELECTION_CONTRACT_INVALID")
    if (type(selection["schema_version"]) is not int or
            selection["schema_version"] != 1 or
            selection["rule_id"] != SELECTION_RULE or
            type(selection["workflow"]) is not str or
            not selection["workflow"].strip() or
            selection["workflow"] != selection["workflow"].strip() or
            (selection["risk"] is not None and
             (type(selection["risk"]) is not str or not selection["risk"].strip()
              or selection["risk"] != selection["risk"].strip())) or
            selection["material_only"] is not True):
        raise ValueError("SELECTION_CONTRACT_INVALID")
    if (type(selection["selection_ref"]) is not str or
            selection["selection_ref"] != cohort["selection_ref"] or
            cohort["eligibility_rule"] != SELECTION_RULE):
        raise ValueError("SELECTION_REFERENCE_MISMATCH")
    try:
        begin = capability_activation._time(
            selection["from_inclusive"], "from_inclusive"
        )
        end = capability_activation._time(selection["to_exclusive"], "to_exclusive")
    except (capability_activation.ActivationError, TypeError, ValueError, OverflowError):
        raise ValueError("SELECTION_WINDOW_INVALID") from None
    if begin >= end:
        raise ValueError("SELECTION_WINDOW_INVALID")
    return begin, end


def _events_in_epoch(snapshot: dict, epoch: str) -> list[dict] | None:
    if epoch == snapshot["state"]["epoch_id"]:
        reviewed, _ = task_learning._reviewed_occurrences(
            snapshot["events"], snapshot["reviews"]
        )
        return [
            event for event in snapshot["events"]
            if task_learning._occurrence(event) not in reviewed
        ]
    matching = [
        review for review in snapshot["reviews"] if review["epoch_id"] == epoch
    ]
    if len(matching) != 1:
        return None
    review = matching[0]
    if review["schema_version"] != 2:
        # Legacy positional cutoffs are not independently attributable here.
        return None
    identities = set(review["reviewed_occurrence_ids"])
    return [
        event for event in snapshot["events"]
        if task_learning._occurrence(event) in identities
    ]


def _source_qualities(events: list[dict]) -> dict:
    # These are only descriptive observations from validated local records.
    # Do not reinterpret missing measured assessments as successful zeros.
    escape_measured = [
        event for event in events
        if task_learning._is_measured(event, "verification_escape")
    ]
    failure_measured = [
        event for event in events
        if task_learning._is_measured(event, "verification_failures")
    ]
    return {
        "material_tasks": len(events),
        "verified_successes": sum(
            event["outcome_class"] == "verified_success" for event in events
        ),
        "failed_tasks": sum(event["outcome_class"] == "failed" for event in events),
        "blocked_tasks": sum(event["outcome_class"] == "blocked" for event in events),
        "verification_escape_assessed": len(escape_measured),
        "verification_escapes": sum(
            event["verification_escape"] is True for event in escape_measured
        ),
        "verification_failure_assessed": len(failure_measured),
        "tasks_with_verification_failures": sum(
            event["verification_failures"] > 0 for event in failure_measured
        ),
    }


def assess_intervention_against_ledger(
    project_root: Path | str, intervention: Any, selection: Any,
) -> dict:
    """Compare declared cohort IDs to ALL locally eligible project occurrences.

    The explicit source selector computes eligibility from validated task
    facts. Source binding cannot prove selection was pre-registered, Git
    ancestry, code exposure, root-cause recurrence or treatment effect.
    """
    if not isinstance(project_root, (str, Path)) or not str(project_root).strip():
        return _deny("PROJECT_PATH_INVALID")
    try:
        accounting = learning_effectiveness.assess_intervention(intervention)
        cohort = intervention["cohort"]
    except (learning_effectiveness.EffectivenessError, TypeError, ValueError,
            KeyError, AttributeError):
        return _deny("INTERVENTION_CONTRACT_INVALID")

    try:
        begin, end = _validate_selection(selection, cohort)
    except ValueError as exc:
        return _deny(str(exc))
    try:
        target = Path(project_root).resolve(strict=True)
        snapshot = task_learning.authoritative_snapshot(target)
        paths = task_learning._paths(target)
        events_path = paths["events"]
        # The legacy intervention schema names a ledger_sha256: bind it to
        # the exact bytes of the Task Learning event projection, NOT the
        # multi-file ledger-generation digest.
        ledger_bytes = events_path.read_bytes()
        ledger_digest = hashlib.sha256(ledger_bytes).hexdigest()
        if ledger_digest != cohort["ledger_sha256"]:
            return _deny("EVENT_LEDGER_SHA256_MISMATCH")
        # A project should not silently combine different repositories.
        if any(event["project"]["repository"] != cohort["repository"]
               for event in snapshot["events"]):
            return _deny("PROJECT_REPOSITORY_MISMATCH")
        epoch_events = _events_in_epoch(snapshot, cohort["epoch_id"])
        if epoch_events is None:
            return _deny("EPOCH_NOT_SUPPORTED_OR_NOT_FOUND")

        eligible = []
        for event in epoch_events:
            event_time = capability_activation._time(
                event["recorded_at"], "task.recorded_at"
            )
            if (event["material"] is True and
                    event["workflow"] == selection["workflow"] and
                    (selection["risk"] is None or event["risk"] == selection["risk"]) and
                    begin <= event_time < end):
                eligible.append(event)
        by_id = {
            task_learning._occurrence(event): event for event in eligible
        }
        declared_rows = cohort["tasks"]
        declared_ids = {row["occurrence_id"] for row in declared_rows}
        eligible_ids = set(by_id)
        missing = eligible_ids - declared_ids
        extra = declared_ids - eligible_ids
        diagnostic = {
            "eligible_local_source": len(eligible_ids),
            "declared": len(declared_ids),
            "missing_count": len(missing),
            "unexpected_count": len(extra),
        }
        if missing or extra:
            return _deny("COHORT_SELECTION_MISMATCH", membership=diagnostic)
        # Never silently promote a historical V1 event to prospective:
        # even validated V2 records still require independent provenance
        # of prospective registration before exposure can be asserted.
        if any(
            row["identity_basis"] == "prospective" and
            by_id[row["occurrence_id"]]["schema_version"] != 2
            for row in declared_rows
        ):
            return _deny("PROSPECTIVE_IDENTITY_NOT_ESTABLISHED")

        if (hashlib.sha256(events_path.read_bytes()).hexdigest() != ledger_digest
                or task_learning._ledger_generation(paths) != snapshot["generation"]):
            return _deny("LEDGER_CHANGED_DURING_ASSESSMENT")

        return {
            "kind": "EREI_INTERVENTION_LEDGER_BINDING_V1",
            "status": "LOCAL_COHORT_MEMBERSHIP_MATCHED",
            "membership": diagnostic,
            "source_binding": {
                "event_ledger_sha256": ledger_digest,
                "ledger_generation_sha256": snapshot["generation"],
                "epoch_id": cohort["epoch_id"],
                "declared_project_commit": cohort["ref"],
                "declared_selection_commit": cohort["selection_ref"],
                "source_authority": "LOCAL_LEDGER_ONLY",
            },
            "source_outcomes": _source_qualities(eligible),
            "intervention_accounting": accounting,
            "project_files_written": False,
            "model_original_score_changed": False,
            "source_identity_attested": False,
            "cohort_selection_pre_registered": False,
            "adoption_authenticity_verified": False,
            "exposure_verified": False,
            "root_cause_recurrence_verified": False,
            "effectiveness": "NOT_ESTABLISHED",
            "causation": "NOT_ESTABLISHED",
            "stable_ready": False,
        }
    except (task_learning.LearningError, capability_activation.ActivationError,
            OSError, ValueError, OverflowError, KeyError, TypeError, AttributeError,
            UnicodeError):
        return _deny("LEDGER_EVIDENCE_INVALID")
