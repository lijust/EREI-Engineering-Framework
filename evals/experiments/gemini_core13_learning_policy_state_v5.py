#!/usr/bin/env python3
"""Core13 Learning V5: case-blind policy-routing and state-replay discipline.

One static, reusable prompt-side intervention added after V4. Frozen target
policies, V4 typed action schema, solver model, and frozen PR98 scorer remain
identical. This is not learned model weight or benchmark answer injection.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from evals import run_gemini_core_smoke as smoke
from evals.adapters import gemini_core13_exact_target as gemini
from evals.experiments import gemini_core13_learning_action_schema_v4 as v4

EXPERIMENT = "core13_learning_policy_state_replay_v5"
BASE = v4.EXPERIMENT

# Source-neutral quality controls derived from the existing PUBLIC action
# interfaces and policies. No case IDs, reference decisions or expected states.
GENERAL_POLICY_STATE_CHECK = (
    "\n\n--- GENERAL POLICY ROUTING AND STATE REPLAY CHECK ---\n"
    "All instructions below are a method for applying the supplied Framework "
    "artifacts and public action-simulation interfaces, not new policy. "
    "Check silently; return only JSON.\n"
    "A. Identify the workflow domain from the actual initial_state keys, facts "
    "and Framework artifact before choosing a decision: task-event capture, "
    "learning feedback/candidate workflow, review scheduling, or capability "
    "adoption/execution. Do not cross into a different domain merely because "
    "its action is available in the JSON schema. A user's requested shortcut "
    "does not grant a permission absent from the artifact.\n"
    "B. Distinguish collecting evidence or nominating a candidate from directly "
    "mutating Framework Core. A proposal or finding is not itself execution "
    "authority. Respect the artifact-defined prerequisites and ordering.\n"
    "C. For a capability, evaluate prerequisites from the actual facts before "
    "considering execute_capability: reference immutability, explicit adoption "
    "and identity match, approval, and expiration. Keep distinct reasons for "
    "different failed prerequisites; a still-valid approval cannot replace "
    "a reproducible immutable reference, and upgrading code does not supply "
    "adoption. Never infer a missing rejection reason from unrelated fields.\n"
    "D. Copy all observed identifiers, enum values and nested signals from "
    "the supplied facts without substitutions or invented zeros. Preserve "
    "integer versus boolean types. For every selected action verify its "
    "required fields, their values and their relationship to the facts.\n"
    "E. Reconstruct output.state from a DEEP COPY of initial_state by applying "
    "the selected action effects strictly in order, as specified by the "
    "supplied public action-simulation instructions. Record operations append "
    "the action's fields except op; keep all existing elements. State-changing "
    "operations affect only their documented state keys. For blocking, use "
    "the exact reason-to-state mapping stated in the public action interface; "
    "a blocked operation is not equivalent to changing state arbitrarily. "
    "Do not invent state keys or output expected policy results from memory.\n"
    "F. Before final JSON, compare each claimed state field to the effects "
    "of the actual selected operations; if they differ, correct the model's "
    "proposed state by revisiting its own actions and the public reducer rules. "
    "This is a pre-generation self-check, not post-hoc rewriting, a second "
    "tool call, or permission to change the scoring contract.\n"
    "--- END GENERAL POLICY AND STATE CHECK ---\n"
)
FORBIDDEN_CASE_HINTS = (
    "TLR-001", "TLR-007", "CCA-003", "CCA-006",
    "TLR-003", "TLR-004", "reference_actions", "expected_state",
    "scorer_results", "task-occurrence-001", "workflow-gap-001",
    "mutable_pin", "expired_or_mismatched", "pin_upgrade_without_adoption",
    "feedback_then_promotion", "block_capability",
)


def coaching_text() -> str:
    if any(secret in GENERAL_POLICY_STATE_CHECK for secret in FORBIDDEN_CASE_HINTS):
        raise gemini.GeminiAdapterError("case-specific guidance not allowed")
    return GENERAL_POLICY_STATE_CHECK


response_json_schema = v4.response_json_schema


def build_candidate_body(prompt: str, *, model: str) -> bytes:
    """Only append fixed generic coaching to V4 prompt. V4 schema unchanged."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise gemini.GeminiAdapterError("empty input prompt")
    body = json.loads(v4.build_candidate_body(prompt, model=model))
    # V4 already appends V3 guidance. Extend the FINAL serialized prompt so
    # the V5 request remains a strict prefix-preserving append from V4.
    body["contents"][0]["parts"][0]["text"] += coaching_text()
    raw = json.dumps(
        body, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    if len(raw) > gemini.MAX_REQUEST_BYTES:
        raise gemini.GeminiAdapterError("V5 request exceeds byte bound")
    return raw


def inspect_offline(target_root: Path, adapter_root: Path, *,
                    case_id: str, model: str) -> dict:
    """No Gemini API, no receipts modified, only public request diff."""
    prepared = smoke.prepare(target_root, case_id, adapter_root)
    prior = v4.build_candidate_body(prepared["prompt"], model=model)
    proposed = build_candidate_body(prepared["prompt"], model=model)
    a, b = json.loads(prior), json.loads(proposed)
    if a.get("generationConfig") != b.get("generationConfig"):
        raise gemini.GeminiAdapterError("V5 generation schema/settings drift")
    t0 = a["contents"][0]["parts"][0]["text"]
    t1 = b["contents"][0]["parts"][0]["text"]
    if t1 != t0 + coaching_text() or {k:v for k,v in a.items() if k!="contents"} != {k:v for k,v in b.items() if k!="contents"}:
        raise gemini.GeminiAdapterError("V5 changes outside fixed policy coaching")
    return {
        "kind": "CORE13_V5_STATIC_POLICY_CHECK",
        "status": "SOURCE_ONLY_NO_API",
        "experiment": EXPERIMENT, "previous_experiment": BASE,
        "model": model, "case_id": case_id,
        "frozen_target_head": gemini.EXPECTED_TARGET_HEAD,
        "prior_body_sha256": hashlib.sha256(prior).hexdigest(),
        "v5_body_sha256": hashlib.sha256(proposed).hexdigest(),
        "v5_coaching_sha256": hashlib.sha256(coaching_text().encode("utf-8")).hexdigest(),
        "delta_only_generic_coaching": True,
        "response_schema_identical": True,
        "model_calls": 0, "network_requests": 0,
        "live_model_behavior_observed": False,
        "behavioral_improvement_proven": False,
        "independently_accepted": False, "stable_ready": False,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target-root", type=Path, required=True)
    p.add_argument("--case-id", choices=sorted(
        case for group in smoke.CASES.values() for case in group), required=True)
    p.add_argument("--model", choices=gemini.CORE_MODELS, default="gemini-3.5-flash-lite")
    a = p.parse_args(argv)
    try:
        result = inspect_offline(a.target_root, Path(__file__).resolve().parents[2], case_id=a.case_id, model=a.model)
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception:
        print(json.dumps({"kind": "CORE13_V5_STATIC_POLICY_CHECK",
                          "status": "OFFLINE_INSPECTION_BLOCKED",
                          "model_calls": 0, "network_requests": 0,
                          "independently_accepted": False,
                          "stable_ready": False}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
