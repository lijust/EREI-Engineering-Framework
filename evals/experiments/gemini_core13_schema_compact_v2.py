#!/usr/bin/env python3
"""Compact Gemini JSON Schema candidate V2, distinct from immutable rejected V1.

One general structural constraint is intentional: actions[*].op MUST exist.
No oracle labels, case outcomes, required action count, review statuses,
forbidden-action filtering, provider calls or keys. The frozen Core13 scorer
still judges the complete typed action contract and behavioral correctness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from evals import run_gemini_core_smoke as smoke
from evals.adapters import gemini_core13_exact_target as gemini

EXPERIMENT = "core13_native_response_json_schema_compact_v2"


def response_json_schema() -> dict:
    """Minimal JSON grammar to avoid v1 optional-property/array-state explosion.

    States and action extras remain flexible so the model can emit real
    required arguments OR invalid/forbidden ones; frozen scorer rejects wrong
    effects. This schema does NOT guarantee a valid reducer action beyond op.
    """
    return {
        "type": "object",
        "properties": {
            "output": {
                "type": "object",
                "properties": {
                    "contract": {"type": "string"},
                    "decision": {"type": "string"},
                    "actions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"op": {"type": "string"}},
                            "required": ["op"],
                            "additionalProperties": True,
                        },
                    },
                    "state": {
                        "type": "object",
                        "additionalProperties": True,
                    },
                },
                "required": ["contract", "decision", "actions", "state"],
            },
            "metadata": {
                "type": "object",
                "properties": {"risk": {"type": "string"}},
                "required": ["risk"],
            },
        },
        "required": ["output", "metadata"],
    }


def build_candidate_body(prompt: str, *, model: str) -> bytes:
    baseline = json.loads(gemini.build_generation_body(prompt, model=model))
    config = baseline["generationConfig"]
    if "responseJsonSchema" in config or "responseSchema" in config:
        raise gemini.GeminiAdapterError("baseline unexpectedly has response schema")
    config["responseJsonSchema"] = response_json_schema()
    body = json.dumps(
        baseline, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    if len(body) > gemini.MAX_REQUEST_BYTES:
        raise gemini.GeminiAdapterError("compact candidate exceeds request bound")
    return body


def inspect_offline(target_root: Path, adapter_root: Path, *,
                    case_id: str, model: str) -> dict:
    prepared = smoke.prepare(target_root, case_id, adapter_root)
    original = json.loads(
        gemini.build_generation_body(prepared["prompt"], model=model)
    )
    compact = build_candidate_body(prepared["prompt"], model=model)
    changed = json.loads(compact)
    cfg = changed["generationConfig"]
    if (original["contents"] != changed["contents"]
            or original["generationConfig"] != {
                k: v for k, v in cfg.items() if k != "responseJsonSchema"
            }):
        raise gemini.GeminiAdapterError("unexpected compact schema request drift")
    old_body = gemini.build_generation_body(prepared["prompt"], model=model)
    return {
        "kind": "CORE13_COMPACT_SCHEMA_V2_OFFLINE_PREVIEW",
        "status": "SOURCE_ONLY_NO_API",
        "experiment": EXPERIMENT,
        "case_id": case_id,
        "model": model,
        "frozen_target_head": gemini.EXPECTED_TARGET_HEAD,
        "frozen_target_tree": gemini.EXPECTED_TARGET_TREE,
        "baseline_request_sha256": hashlib.sha256(old_body).hexdigest(),
        "compact_request_sha256": hashlib.sha256(compact).hexdigest(),
        "baseline_bytes": len(old_body),
        "compact_bytes": len(compact),
        "delta_only_response_json_schema": True,
        "v1_http400_cause_established": False,
        "provider_schema_supported_live": False,
        "behavioral_improvement_proven": False,
        "scorer_changed": False,
        "model_calls": 0,
        "network_requests": 0,
        "evidence_files_written": 0,
        "independently_accepted": False,
        "stable_ready": False,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target-root", type=Path, required=True)
    p.add_argument("--case-id", choices=sorted(
        c for ids in smoke.CASES.values() for c in ids), required=True)
    p.add_argument("--model", choices=gemini.CORE_MODELS,
                   default="gemini-3.5-flash-lite")
    a = p.parse_args(argv)
    try:
        result = inspect_offline(
            a.target_root, Path(__file__).resolve().parents[2],
            case_id=a.case_id, model=a.model,
        )
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception:
        print(json.dumps({
            "kind": "CORE13_COMPACT_SCHEMA_V2_OFFLINE_PREVIEW",
            "status": "OFFLINE_INSPECTION_BLOCKED",
            "model_calls": 0,
            "network_requests": 0,
            "evidence_files_written": 0,
            "independently_accepted": False,
            "stable_ready": False,
        }, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
