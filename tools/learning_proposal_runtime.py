"""Fail-closed, in-memory EREI proposal pilot (no project/tool execution).

The caller provides trusted task facts / project activation documents, NOT the
model. The model may propose a decision and typed actions, never write state.
Authorization precedes deterministic state materialization. The original model
proposal is not rewritten or counted as a frozen Core13 PASS.

This is an experimental reference boundary, not a production dispatcher:
no filesystem writes, external effects, API requests, auto-adoption or
independent acceptance occur here.
"""
from __future__ import annotations

import copy
import json
from datetime import datetime
from typing import Any

from tools.capability_activation import (
    ACTIVE_STATUSES, ActivationError, resolve_activation,
)

CONTRACT = "erei-proposal-v1"
DECISION_OPERATIONS = {
    "capture_task": ("record_task",),
    "omit_task": (),
    "request_review": ("request_review",),
    "reject_sensitive_capture": (),
    "feedback_then_promotion": ("record_feedback", "nominate_candidate"),
    "allow_capability": ("execute_capability",),
    "block_capability": ("block_capability",),
}
ACTION_FIELDS = {
    "record_task": {"op", "occurrence_id", "outcome", "signals"},
    "request_review": {"op", "status"},
    "record_feedback": {"op", "fingerprint", "evidence_ref"},
    "nominate_candidate": {"op", "fingerprint"},
    "execute_capability": {"op", "capability", "version", "mode"},
    "block_capability": {"op", "reason"},
}
STATUS_VALUES = {"IMMEDIATE_REVIEW", "REVIEW_DUE", "REVIEW_RECOMMENDED"}
BLOCK_CAUSE_MAP = {
    "BLOCK_NON_COMMIT_PROJECT_PIN": "mutable_pin",
    "BLOCK_FRAMEWORK_REF_MISMATCH": "expired_or_mismatched",
    "BLOCK_EXPIRED_CANDIDATE_ADOPTION": "expired_or_mismatched",
    "BLOCK_CANDIDATE_VERSION_MISMATCH": "expired_or_mismatched",
}
STATE_FIELDS = {
    "task_events", "review_status", "feedback", "promotion_queue",
    "core_modified", "capability_status", "executions",
}


class ProposalDenied(ValueError):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def _copy(value: Any) -> Any:
    try:
        raw = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)
        return json.loads(raw)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ProposalDenied("INVALID_JSON_DATA") from exc


def _same(left: Any, right: Any) -> bool:
    # Canonical JSON equality is strict about True versus 1.
    return json.dumps(left, sort_keys=True, separators=(",", ":"), allow_nan=False) == json.dumps(
        right, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _initial(value: Any) -> dict:
    if type(value) is not dict or not value or set(value) - STATE_FIELDS:
        raise ProposalDenied("INITIAL_STATE_INVALID")
    for key, item in value.items():
        klass = bool if key == "core_modified" else str if key.endswith("status") else list
        if type(item) is not klass:
            raise ProposalDenied("INITIAL_STATE_INVALID")
    return _copy(value)


def _proposal(value: Any) -> tuple[str, list[dict]]:
    if type(value) is not dict or not {"contract", "decision", "actions"} <= set(value):
        raise ProposalDenied("PROPOSAL_CONTRACT_INVALID")
    if set(value) - {"contract", "decision", "actions", "claimed_state"}:
        raise ProposalDenied("PROPOSAL_CONTRACT_INVALID")
    if (type(value["contract"]) is not str or
            type(value["decision"]) is not str or
            value["contract"] != CONTRACT or
            value["decision"] not in DECISION_OPERATIONS):
        raise ProposalDenied("PROPOSAL_CONTRACT_INVALID")
    actions = value["actions"]
    if type(actions) is not list or len(actions) > 16:
        raise ProposalDenied("PROPOSAL_ACTIONS_INVALID")
    allowed_ops = DECISION_OPERATIONS[value["decision"]]
    if len(actions) != len(allowed_ops):
        raise ProposalDenied("DECISION_ACTION_MISMATCH")
    for action, expected in zip(actions, allowed_ops):
        if type(action) is not dict or action.get("op") != expected:
            raise ProposalDenied("DECISION_ACTION_MISMATCH")
        if set(action) != ACTION_FIELDS[expected]:
            raise ProposalDenied("PROPOSAL_ACTIONS_INVALID")
        for key, item in action.items():
            if key == "signals":
                continue
            if type(item) is not str or not item.strip():
                raise ProposalDenied("PROPOSAL_ACTIONS_INVALID")
    return value["decision"], _copy(actions)


def _signals(value: Any) -> None:
    if type(value) is not dict or set(value) != {
        "rework_cycles", "verification_failures", "verification_escape"
    }:
        raise ProposalDenied("TASK_SIGNALS_INVALID")
    if (type(value["rework_cycles"]) is not int or value["rework_cycles"] < 0
            or type(value["verification_failures"]) is not int
            or value["verification_failures"] < 0
            or type(value["verification_escape"]) is not bool):
        raise ProposalDenied("TASK_SIGNALS_INVALID")


def _authorize(decision: str, actions: list[dict], context: Any) -> None:
    if (type(context) is not dict or
            type(context.get("domain")) is not str or
            context["domain"] not in {
                "task_capture", "learning_review", "feedback_promotion", "capability_activation"
            }):
        raise ProposalDenied("UNTRUSTED_POLICY_CONTEXT")
    domain = context["domain"]
    if domain == "task_capture":
        if decision not in {"capture_task", "omit_task", "reject_sensitive_capture"}:
            raise ProposalDenied("WRONG_WORKFLOW")
        facts = context.get("facts")
        if type(facts) is not dict or type(facts.get("engineering_execution")) is not bool:
            raise ProposalDenied("TASK_FACTS_UNVERIFIED")
        storage = facts.get("requested_storage", [])
        if type(storage) is not list or any(type(k) is not str for k in storage):
            raise ProposalDenied("TASK_FACTS_UNVERIFIED")
        private = bool(set(storage) & {"private_reasoning", "credentials"})
        if private:
            if decision != "reject_sensitive_capture":
                raise ProposalDenied("SENSITIVE_CAPTURE_PROHIBITED")
        elif facts["engineering_execution"]:
            if decision != "capture_task":
                raise ProposalDenied("TASK_CAPTURE_REQUIRED")
            action = actions[0]
            observed = {key: facts.get(key) for key in ("occurrence_id", "outcome", "signals")}
            if not _same({key: action[key] for key in observed}, observed):
                raise ProposalDenied("TASK_FACT_MISMATCH")
            if action["outcome"] not in {"success", "failure", "partial"}:
                raise ProposalDenied("TASK_FACT_MISMATCH")
            _signals(action["signals"])
        elif decision != "omit_task":
            raise ProposalDenied("NON_EXECUTION_CANNOT_CAPTURE")
        return

    if domain == "learning_review":
        if decision != "request_review":
            raise ProposalDenied("WRONG_WORKFLOW")
        # Caller must supply a reviewed determination from its task-learning
        # mechanism. This pilot does not compute/attest that determination.
        reviewed = context.get("authorized_review_status")
        if type(reviewed) is not str or reviewed not in STATUS_VALUES or actions[0]["status"] != reviewed:
            raise ProposalDenied("REVIEW_AUTHORITY_NOT_ESTABLISHED")
        return

    if domain == "feedback_promotion":
        if decision != "feedback_then_promotion":
            raise ProposalDenied("WRONG_WORKFLOW")
        facts = context.get("facts")
        if (type(facts) is not dict or facts.get("core_change_approved") is not False or
                type(facts.get("finding_fingerprint")) is not str or
                not facts["finding_fingerprint"] or
                type(facts.get("evidence_ref")) is not str or not facts["evidence_ref"]):
            raise ProposalDenied("FEEDBACK_EVIDENCE_NOT_ESTABLISHED")
        if (actions[0]["fingerprint"] != facts["finding_fingerprint"] or
                actions[0]["evidence_ref"] != facts["evidence_ref"] or
                actions[1]["fingerprint"] != facts["finding_fingerprint"]):
            raise ProposalDenied("FEEDBACK_FACT_MISMATCH")
        return

    if decision not in {"allow_capability", "block_capability"}:
        raise ProposalDenied("WRONG_WORKFLOW")
    capability = context.get("capability")
    if type(capability) is not str or not capability:
        raise ProposalDenied("CAPABILITY_IDENTITY_UNVERIFIED")
    if not all(k in context for k in ("manifest", "registry", "loaded_framework_ref",
                                      "adoption_document")):
        raise ProposalDenied("ACTIVATION_EVIDENCE_MISSING")
    # A replayable, caller-attested clock must be explicit. Defaulting to the
    # process clock would make adoption/expiry decisions non-reproducible.
    current = context.get("now")
    if (type(current) is not datetime or current.tzinfo is None or
            current.utcoffset() is None):
        raise ProposalDenied("ACTIVATION_CLOCK_UNVERIFIED")
    try:
        resolution = resolve_activation(
            context["manifest"], context["registry"], capability,
            adoption_document=context["adoption_document"],
            loaded_framework_ref=context["loaded_framework_ref"],
            resolved_project_ref=context.get("resolved_project_ref"),
            now=context.get("now"),
        )
    except (ActivationError, TypeError, ValueError, KeyError, AttributeError):
        raise ProposalDenied("ACTIVATION_EVIDENCE_INVALID") from None

    status = resolution["status"]
    if decision == "allow_capability":
        if status not in ACTIVE_STATUSES:
            raise ProposalDenied("CAPABILITY_NOT_ACTIVE")
        action = actions[0]
        expected_mode = "candidate" if status == "ACTIVE_CANDIDATE" else "stable"
        if (action["capability"] != capability or
                action["version"] != resolution["version"] or
                action["mode"] != expected_mode):
            raise ProposalDenied("CAPABILITY_ACTION_MISMATCH")
    else:
        if status in ACTIVE_STATUSES:
            raise ProposalDenied("ACTIVE_CAPABILITY_MUST_NOT_BE_BLOCKED")
        reason = BLOCK_CAUSE_MAP.get(status)
        if status == "DORMANT_CANDIDATE":
            # A pin-upgrade observation is supplied by trusted project code,
            # never accepted as a claim in the model's proposed actions.
            upgraded = context.get("pin_upgraded", False)
            if type(upgraded) is not bool:
                raise ProposalDenied("PIN_HISTORY_INVALID")
            reason = "pin_upgrade_without_adoption" if upgraded else "no_adoption"
        if reason is None or actions[0]["reason"] != reason:
            raise ProposalDenied("BLOCK_REASON_NOT_ESTABLISHED")


def _materialize(initial: dict, actions: list[dict]) -> dict:
    state = _copy(initial)
    for action in actions:
        op = action["op"]
        if op == "record_task":
            if "task_events" not in state:
                raise ProposalDenied("STATE_FIELD_MISSING")
            _signals(action["signals"])
            if any(type(e) is not dict or e.get("occurrence_id") == action["occurrence_id"]
                   for e in state["task_events"]):
                raise ProposalDenied("DUPLICATE_OR_INVALID_TASK_EVENT")
            state["task_events"].append({key: _copy(value) for key, value in action.items() if key != "op"})
        elif op == "request_review":
            if "review_status" not in state or action["status"] not in STATUS_VALUES:
                raise ProposalDenied("STATE_FIELD_MISSING")
            state["review_status"] = action["status"]
        elif op == "record_feedback":
            if "feedback" not in state:
                raise ProposalDenied("STATE_FIELD_MISSING")
            state["feedback"].append({key: value for key, value in action.items() if key != "op"})
        elif op == "nominate_candidate":
            if "promotion_queue" not in state or "feedback" not in state:
                raise ProposalDenied("PROMOTION_EVIDENCE_MISSING")
            # Historical feedback is not necessarily valid just because its
            # outer state field was a list. Never hash untrusted nested data.
            entries = state["feedback"]
            if any(type(item) is not dict or
                   type(item.get("fingerprint")) is not str or
                   not item["fingerprint"] for item in entries):
                raise ProposalDenied("MALFORMED_EXISTING_FEEDBACK")
            if not any(item["fingerprint"] == action["fingerprint"] for item in entries):
                raise ProposalDenied("PROMOTION_EVIDENCE_MISSING")
            state["promotion_queue"].append(action["fingerprint"])
        elif op == "execute_capability":
            if "capability_status" not in state or "executions" not in state:
                raise ProposalDenied("STATE_FIELD_MISSING")
            state["executions"].append({key: value for key, value in action.items() if key != "op"})
            state["capability_status"] = ("ACTIVE_CANDIDATE" if action["mode"] == "candidate" else "STABLE")
        elif op == "block_capability":
            if "capability_status" not in state:
                raise ProposalDenied("STATE_FIELD_MISSING")
            state["capability_status"] = ("DORMANT" if action["reason"] in {
                "no_adoption", "pin_upgrade_without_adoption"
            } else "BLOCKED")
        else:
            raise ProposalDenied("UNAUTHORIZED_ACTION")
    return state


def evaluate_proposal(proposal: Any, initial_state: Any, trusted_context: Any) -> dict:
    """Pure, fail-closed proposal → existing policy → deterministic state preview.

    Only trusted caller data may carry policy facts/activation documents.
    This function does NOT execute any capability or write learning evidence.
    Caller must authenticate its policy facts before using this boundary.
    Independent external verification is deliberately *not* asserted.
    """
    base = {"kind": "EREI_PROPOSAL_PILOT_V1", "executed": False,
            "model_original_score_changed": False,
            "independently_verified": False, "stable_ready": False}
    try:
        before = _initial(initial_state)
        decision, actions = _proposal(proposal)
        _authorize(decision, actions, trusted_context)
        materialized = _materialize(before, actions)
        claim_matches = None
        if "claimed_state" in proposal:
            try:
                claim_matches = _same(proposal["claimed_state"], materialized)
            except (ValueError, TypeError, OverflowError):
                # Claimed state is untrusted telemetry, never authority.
                claim_matches = False
        return {**base, "status": "AUTHORIZED_IN_MEMORY_PREVIEW",
                "decision": decision, "materialized_state": materialized,
                "model_claimed_state_matches_reducer": claim_matches,
                "policy_status": "AUTHORIZED_BY_SUPPLIED_CONTEXT"}
    except ProposalDenied as exc:
        return {**base, "status": "DENIED", "reason_code": exc.reason,
                "policy_status": "NOT_AUTHORIZED"}
