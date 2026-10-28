"""Read-only Project Task Learning → Core13 proposal pilot binding.

This is an OFFLINE PREVIEW adapter: it derives the review trigger from the
existing authoritative V2 project ledger, rather than accepting a model- or
caller-written `trusted_context`. It never executes a capability, closes a
review, captures an event, mutates a file, or establishes independent trust.
The caller still chooses which local project directory to inspect.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from tools import learning_proposal_runtime as pilot
from tools import task_learning


def _denied(reason: str) -> dict:
    return {
        "kind": "EREI_LEDGER_REVIEW_PREVIEW_V1",
        "status": "DENIED",
        "reason_code": reason,
        "executed": False,
        "independently_verified": False,
        "model_original_score_changed": False,
        "stable_ready": False,
        "source_authority": "LOCAL_LEDGER_ONLY_NOT_INDEPENDENTLY_ATTESTED",
    }


def evaluate_review_from_ledger(proposal: Any, project_root: Path | str) -> dict:
    """Preview an AI review request against actual, validated project ledger facts.

    No caller-supplied initial_state, review level, or trusted_context is
    accepted here. The existing task-learning implementation validates
    occurrence fingerprints, review digests, epoch membership and trigger
    rules. The returned digest pins the read-only local observation; it is
    not proof of Git commit identity or independent evidence authenticity.
    """
    if not isinstance(project_root, (Path, str)) or not str(project_root).strip():
        return _denied("PROJECT_PATH_INVALID")
    try:
        target = Path(project_root).resolve(strict=True)
        snapshot = task_learning.authoritative_snapshot(target)
        state = snapshot["state"]
        trigger = state["trigger"]
        level = trigger["level"]
        if type(level) is not str or type(trigger["reasons"]) is not list:
            return _denied("LEDGER_TRIGGER_INVALID")

        source = {
            "ledger_generation_sha256": snapshot["generation"],
            "epoch_id": state["epoch_id"],
            "trigger_level": level,
            "trigger_reasons": list(trigger["reasons"]),
            "total_events": state["total_events"],
            "total_reviews": len(snapshot["reviews"]),
        }
        if level not in pilot.STATUS_VALUES:
            result = _denied("NO_ACTIONABLE_REVIEW_TRIGGER")
        else:
            # The original trigger is the authoritative *starting* status.
            # Only the already-derived policy result is supplied to the pilot.
            result = pilot.evaluate_proposal(
                proposal,
                {"review_status": level},
                {"domain": "learning_review", "authorized_review_status": level},
            )
            result = {
                **result,
                "kind": "EREI_LEDGER_REVIEW_PREVIEW_V1",
                "source_authority": "LOCAL_LEDGER_ONLY_NOT_INDEPENDENTLY_ATTESTED",
            }

        # Catch straightforward changes during materialization; no write is
        # performed. This is NOT an atomic filesystem snapshot or a lock for
        # future execution.
        if task_learning._ledger_generation(task_learning._paths(target)) != snapshot["generation"]:
            return _denied("LEDGER_CHANGED_DURING_PREVIEW")
        return {**result, "source_binding": source}
    except (task_learning.LearningError, OSError, ValueError, TypeError, KeyError,
            UnicodeError):
        # Do not expose potentially sensitive file contents or raw paths.
        return _denied("LEDGER_EVIDENCE_INVALID")
