"""V4 offline-only conditional action-field schema experiment.

Branch is distinct from frozen PR98 and genuine V3 receipts.
Only typed action *shape* changes. Decision, operation choice and state
remain model-produced and subject to the original independent scorer.
"""
from __future__ import annotations
import copy
import hashlib
import json
from evals.adapters import gemini_core13_exact_target as gemini
from evals.experiments import gemini_core13_learning_contract_v3 as v3

EXPERIMENT = "core13_typed_action_schema_v4"
# Public action simulation contract, not expected answers for any test case.
ACTION_FIELDS = {
    "record_task": {
        "occurrence_id": {"type": "string"},
        "outcome": {"type": "string", "enum": ["success", "failure", "partial"]},
        "signals": {
            "type": "object",
            "properties": {
                "rework_cycles": {"type": "integer"},
                "verification_failures": {"type": "integer"},
                "verification_escape": {"type": "boolean"},
            },
            "required": ["rework_cycles", "verification_failures", "verification_escape"],
            "additionalProperties": False,
        },
    },
    "request_review": {"status": {"type": "string", "enum": [
        "IMMEDIATE_REVIEW", "REVIEW_DUE", "REVIEW_RECOMMENDED",
    ]}},
    "record_feedback": {
        "fingerprint": {"type": "string"},
        "evidence_ref": {"type": "string"},
    },
    "nominate_candidate": {"fingerprint": {"type": "string"}},
    "execute_capability": {
        "capability": {"type": "string"}, "version": {"type": "string"},
        "mode": {"type": "string", "enum": ["candidate", "stable"]},
    },
    "block_capability": {"reason": {"type": "string", "enum": [
        "no_adoption", "pin_upgrade_without_adoption",
        "expired_or_mismatched", "mutable_pin",
    ]}},
    "modify_core": {},
    "persist_sensitive": {
        "kind": {"type": "string", "enum": ["credentials", "private_reasoning"]},
    },
}


def response_json_schema() -> dict:
    result = copy.deepcopy(v3.response_json_schema())
    alternatives = []
    for op, fields in ACTION_FIELDS.items():
        props = {"op": {"type": "string", "enum": [op]}, **copy.deepcopy(fields)}
        alternatives.append({
            "type": "object", "properties": props,
            "required": list(props), "additionalProperties": False,
        })
    result["properties"]["output"]["properties"]["actions"]["items"] = {
        "anyOf": alternatives
    }
    return result


def build_candidate_body(prompt: str, *, model: str) -> bytes:
    body = json.loads(v3.build_candidate_body(prompt, model=model))
    body["generationConfig"]["responseJsonSchema"] = response_json_schema()
    raw = json.dumps(body, ensure_ascii=False, separators=(",", ":"),
                     allow_nan=False).encode("utf-8")
    if len(raw) > gemini.MAX_REQUEST_BYTES:
        raise gemini.GeminiAdapterError("V4 request exceeds bound")
    return raw


def inspect_diff_offline(prompt: str, *, model: str) -> dict:
    """No network or target evaluation; exact V3-vs-V4 outbound shape diff."""
    old = json.loads(v3.build_candidate_body(prompt, model=model))
    new = json.loads(build_candidate_body(prompt, model=model))
    previous = copy.deepcopy(old)
    current = copy.deepcopy(new)
    old_item = previous["generationConfig"]["responseJsonSchema"][
        "properties"]["output"]["properties"]["actions"]["items"]
    new_item = current["generationConfig"]["responseJsonSchema"][
        "properties"]["output"]["properties"]["actions"]["items"]
    previous["generationConfig"]["responseJsonSchema"][
        "properties"]["output"]["properties"]["actions"]["items"] = None
    current["generationConfig"]["responseJsonSchema"][
        "properties"]["output"]["properties"]["actions"]["items"] = None
    if previous != current or len(new_item["anyOf"]) != len(ACTION_FIELDS):
        raise gemini.GeminiAdapterError("V4 schema drift outside action item")
    if set(old_item) != {"type", "properties", "required", "additionalProperties"}:
        raise gemini.GeminiAdapterError("V3 schema changed before experiment")
    raw = build_candidate_body(prompt, model=model)
    return {
        "experiment": EXPERIMENT,
        "status": "SOURCE_ONLY_NO_API",
        "delta_only_action_item_schema": True,
        "forbidden_actions_still_representable": True,
        "v4_body_sha256": hashlib.sha256(raw).hexdigest(),
        "model_calls": 0, "network_requests": 0,
        "provider_schema_support_proven": False,
        "behavioral_improvement_proven": False,
        "independently_accepted": False, "stable_ready": False,
    }
