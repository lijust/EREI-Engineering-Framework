#!/usr/bin/env python3
"""OFFLINE-ONLY candidate Gemini JSON Schema request for Core13.

This deliberately does NOT modify the observed 13-case baseline, frozen
Framework target, original scorer, parser, or smoke launcher. It builds a
distinct provider-native structured-output request proposal for an A/B
experiment. The command never calls Gemini, reads credentials or writes files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from evals.adapters import gemini_core13_exact_target as gemini
from evals.adapters import copilot_cli_exact_target as contract
from evals import run_gemini_core_smoke as smoke

# Preserve the opportunity for the model to propose *forbidden* operations:
# removing them from the schema could hide real unsafe decisions.
OPS = (
    "record_task", "request_review", "record_feedback",
    "nominate_candidate", "execute_capability", "block_capability",
    "modify_core", "persist_sensitive",
)
REVIEW_STATUSES = ("IMMEDIATE_REVIEW", "REVIEW_DUE", "REVIEW_RECOMMENDED")
BLOCKING_REASONS = (
    "no_adoption", "pin_upgrade_without_adoption",
    "expired_or_mismatched", "mutable_pin",
)
DECISIONS = (
    "capture_task", "omit_task", "request_review",
    "reject_sensitive_capture", "feedback_then_promotion",
    "allow_capability", "block_capability",
)


def response_json_schema() -> dict:
    """Schema enforces action.op presence; frozen reducer stays authoritative.

    Deliberately does not encode case-specific correct decisions or action
    counts; those are private to the original scorer and MUST NOT be sent.
    The state shape remains flexible: frozen behavioral scorer checks exact
    state/action consistency, including unknown/forbidden effects.
    """
    action = {
        "type": "object",
        "properties": {
            "op": {"type": "string", "enum": list(OPS)},
            "occurrence_id": {"type": "string"},
            "outcome": {"type": "string", "enum": ["success", "failure", "partial"]},
            "signals": {
                "type": "object",
                "properties": {
                    "rework_cycles": {"type": "integer"},
                    "verification_failures": {"type": "integer"},
                    "verification_escape": {"type": "boolean"},
                },
                "required": [
                    "rework_cycles", "verification_failures",
                    "verification_escape",
                ],
                "additionalProperties": False,
            },
            "status": {"type": "string", "enum": list(REVIEW_STATUSES)},
            "fingerprint": {"type": "string"},
            "evidence_ref": {"type": "string"},
            "capability": {"type": "string"},
            "version": {"type": "string"},
            "mode": {"type": "string", "enum": ["candidate", "stable"]},
            "reason": {"type": "string", "enum": list(BLOCKING_REASONS)},
            "kind": {"type": "string", "enum": ["credentials", "private_reasoning"]},
        },
        "required": ["op"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "output": {
                "type": "object",
                "properties": {
                    "contract": {
                        "type": "string",
                        "enum": [contract.SIMULATION_CONTRACT],
                    },
                    "decision": {"type": "string", "enum": list(DECISIONS)},
                    "actions": {
                        "type": "array",
                        "items": action,
                        "maxItems": 16,
                    },
                    "state": {
                        "type": "object",
                        # The original scorer is responsible for exact
                        # state keys/values, not the model-facing schema.
                        "additionalProperties": True,
                    },
                },
                "required": ["contract", "decision", "actions", "state"],
                "additionalProperties": False,
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "risk": {
                        "type": "string",
                        "enum": ["L0", "L1", "L2", "L3"],
                    },
                },
                "required": ["risk"],
                "additionalProperties": False,
            },
        },
        "required": ["output", "metadata"],
        "additionalProperties": False,
    }


def build_candidate_body(prompt: str, *, model: str) -> bytes:
    """Baseline request bytes plus exactly one responseJsonSchema setting."""
    baseline = json.loads(gemini.build_generation_body(prompt, model=model))
    config = baseline["generationConfig"]
    if "responseJsonSchema" in config or "responseSchema" in config:
        raise gemini.GeminiAdapterError("baseline unexpectedly has response schema")
    config["responseJsonSchema"] = response_json_schema()
    body = json.dumps(
        baseline, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    if len(body) > gemini.MAX_REQUEST_BYTES:
        raise gemini.GeminiAdapterError("schema candidate request exceeds bound")
    return body


def inspect_offline(target_root: Path, adapter_root: Path, *, case_id: str,
                    model: str) -> dict:
    """Read only frozen public source, never transmit the prompt."""
    prepared = smoke.prepare(target_root, case_id, adapter_root)
    plain = gemini.build_generation_body(prepared["prompt"], model=model)
    with_schema = build_candidate_body(prepared["prompt"], model=model)
    before = json.loads(plain)
    after = json.loads(with_schema)
    baseline_cfg = before["generationConfig"]
    candidate_cfg = after["generationConfig"]
    if (before["contents"] != after["contents"]
            or baseline_cfg != {
                key: value for key, value in candidate_cfg.items()
                if key != "responseJsonSchema"
            }):
        raise gemini.GeminiAdapterError("unexpected drift beyond output schema")
    return {
        "kind": "CORE13_SCHEMA_CANDIDATE_OFFLINE_INSPECTION",
        "status": "SOURCE_ONLY_NO_API",
        "model": model,
        "case_id": case_id,
        "frozen_target_head": gemini.EXPECTED_TARGET_HEAD,
        "frozen_target_tree": gemini.EXPECTED_TARGET_TREE,
        "baseline_request_sha256": hashlib.sha256(plain).hexdigest(),
        "candidate_request_sha256": hashlib.sha256(with_schema).hexdigest(),
        "baseline_bytes": len(plain),
        "candidate_bytes": len(with_schema),
        "delta_only_response_json_schema": True,
        "native_provider_schema_validated_live": False,
        "behavioral_improvement_proven": False,
        "scorer_changed": False,
        "model_calls": 0,
        "network_requests": 0,
        "evidence_files_written": 0,
        "independently_accepted": False,
        "stable_ready": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--case-id", choices=sorted(
        c for items in smoke.CASES.values() for c in items), required=True)
    parser.add_argument("--model", choices=gemini.CORE_MODELS,
                        default="gemini-3.5-flash-lite")
    args = parser.parse_args(argv)
    try:
        report = inspect_offline(
            args.target_root, Path(__file__).resolve().parents[2],
            case_id=args.case_id, model=args.model,
        )
        print(json.dumps(report, sort_keys=True))
        return 0
    except Exception:
        # Do not print prompt, paths, provider contents or hidden scoring rules.
        print(json.dumps({
            "kind": "CORE13_SCHEMA_CANDIDATE_OFFLINE_INSPECTION",
            "status": "OFFLINE_INSPECTION_BLOCKED",
            "model_calls": 0, "network_requests": 0,
            "evidence_files_written": 0, "independently_accepted": False,
            "stable_ready": False,
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
