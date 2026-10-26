#!/usr/bin/env python3
"""Read-only owner-local Core13 baseline audit: verify and re-score 13 receipts.

All raw/provider content and scorer-private details remain on owner computer.
Only an allow-listed JSON count/status summary is printed. This does NOT grant
independent release acceptance or alter original evidence / frozen scorer.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from evals import diagnose_gemini_core_receipt as diag
from evals import run_gemini_core_smoke as smoke
from evals.adapters import gemini_core13_exact_target as gemini

# Original explicitly owner-attempted Core13 order, NEVER autodiscovery.
CASES = [
    (case, f"smoke-{n:03d}")
    for n, case in enumerate(
        [c for ids in smoke.CASES.values() for c in ids], start=5
    )
]
EXPECTED_MODEL = "gemini-3.5-flash-lite"
SAFE_FAIL_CODES = {
    "simulation action must contain op": "ACTION_OP_INVALID",
    "proposed actions produce an incorrect state": "STATE_EFFECT_MISMATCH",
    "capability blocking reason contradicts the required behavior": "WRONG_BLOCK_CAUSE",
    "claimed state contradicts the proposed action effects": "CLAIMED_STATE_MISMATCH",
    "decision contradicts the required behavior": "DECISION_MISMATCH",
    "unknown operation or fields": "ACTION_FIELDS_INVALID",
    "decision/action contradiction or additional unauthorized effects": "DECISION_ACTION_MISMATCH",
}


def inspect_case(folder: Path, *, case_id: str, expected_suite: dict,
                 expected_case: dict, runner, expected_prompt_sha: str) -> dict:
    """All checks are local, read-only, and fail closed."""
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("missing/symlink evidence folder")
    raw = diag.bounded_read(folder / "provider-raw.json", diag.MAX_RAW_BYTES)
    verdict = diag.strict_json(diag.bounded_read(
        folder / "verdict.json", diag.MAX_VERDICT_BYTES))
    request = diag.strict_json(diag.bounded_read(
        folder / "blind-request.json", 200_000))
    if not isinstance(verdict, dict) or not isinstance(request, dict):
        raise ValueError("bad baseline evidence root")
    if (
        verdict.get("case_id") != case_id
        or verdict.get("suite_id") != expected_suite["suite_id"]
        or verdict.get("source_head") != gemini.EXPECTED_TARGET_HEAD
        or verdict.get("source_tree") != gemini.EXPECTED_TARGET_TREE
        or verdict.get("model_requested") != EXPECTED_MODEL
        or verdict.get("provider_model_version") != EXPECTED_MODEL
        or verdict.get("prompt_sha256") != expected_prompt_sha
        or verdict.get("provider_response_sha256") != smoke.sha(raw)
        or verdict.get("blind_request_sha256") != smoke.sha(
            smoke.canonical_bytes(request)
        )
        or verdict.get("independently_accepted") is not False
        or verdict.get("stable_ready") is not False
        or verdict.get("evidence_kind") != "observed_unverified"
        or not isinstance(verdict.get("usage_metadata"), dict)
        or request.get("protocol_version") != "2.0"
        or set(request) != {
            "protocol_version", "suite_id", "case_id",
            "artifact", "input", "context"
        }
        or request.get("artifact") != expected_suite["artifact"]
        or request.get("input") != expected_case["input"]
        or request.get("context") != expected_case.get("context", {})
    ):
        raise ValueError("baseline source/custody mismatch")
    parsed = diag.strict_json(raw)
    if not isinstance(parsed, dict) or parsed.get("modelVersion") != EXPECTED_MODEL:
        raise ValueError("wrong provider identity")
    if parsed.get("usageMetadata") != verdict.get("usage_metadata"):
        raise ValueError("usage metadata mismatch")
    normalized = gemini.parse_gemini_result(raw)
    scores = [
        runner.score(expectation, normalized, expected_case["input"])
        for expectation in expected_case["expectations"]
    ]
    if not scores:
        raise ValueError("frozen scorer expectations missing")
    observed_pass = all(bool(ok) for ok, _ in scores)
    previous_status = verdict.get("status")
    if previous_status == "MODEL_RESPONSE_INVALID_UNVERIFIED":
        # Exactly the first receipt is eligible for provider thoughtSignature
        # parser compatibility replay; no other scored output is reclassified.
        if case_id != "TLR-001-SUCCESS-STILL-LEARNING-DATA" or verdict.get("passed") is not False:
            raise ValueError("unexpected invalid original receipt")
    elif previous_status in {
        "MODEL_RESPONSE_SCORED_PASS_UNVERIFIED",
        "MODEL_RESPONSE_SCORED_FAIL_UNVERIFIED",
    }:
        if verdict.get("passed") is not observed_pass or (
            previous_status == "MODEL_RESPONSE_SCORED_PASS_UNVERIFIED"
        ) is not observed_pass:
            raise ValueError("original scorer verdict differs from frozen replay")
    else:
        raise ValueError("unsupported baseline status")
    issues = []
    for passed, reason in scores:
        if not passed:
            issues.append(next((
                category for prefix, category in SAFE_FAIL_CODES.items()
                if isinstance(reason, str) and reason.startswith(prefix)
            ), "OTHER_SCORER_FAILURE"))
    return {
        "case_id": case_id,
        "scored_pass": observed_pass,
        "failure_categories": issues,
        "sha256_bound": True,
        "model_identity_bound": True,
        "frozen_scorer_replayed": True,
    }


def audit(evidence_root: Path, target_root: Path, adapter_root: Path) -> dict:
    summary = {
        "kind": "CORE13_OWNER_LOCAL_BASELINE_AUDIT",
        "status": "AUDIT_BLOCKED_UNVERIFIED",
        "expected_cases": len(CASES),
        "observed_cases": 0,
        "passed": 0,
        "failed": 0,
        "cases": [],
        "model_calls": 0,
        "network_requests": 0,
        "evidence_files_written": 0,
        "independently_accepted_cases": 0,
        "stable_ready": False,
    }
    try:
        if evidence_root.is_symlink() or not evidence_root.is_dir():
            raise ValueError("evidence root unavailable")
        target = target_root.resolve()
        gemini.verify_frozen_target(target)
        runner = smoke.frozen_runner(target)
        seen = set()
        for case_id, folder in CASES:
            suite, case, blinded = smoke.load_one(target, case_id, runner)
            if case["id"] != case_id or case_id in seen:
                raise ValueError("suite target mismatch")
            seen.add(case_id)
            prompt = gemini.prepare_one(blinded, target)
            item = inspect_case(
                evidence_root / folder, case_id=case_id,
                expected_suite=suite, expected_case=case, runner=runner,
                expected_prompt_sha=smoke.sha(prompt.encode("utf-8")),
            )
            summary["cases"].append(item)
        summary["observed_cases"] = len(summary["cases"])
        summary["passed"] = sum(bool(x["scored_pass"]) for x in summary["cases"])
        summary["failed"] = summary["observed_cases"] - summary["passed"]
        summary["status"] = "OWNER_LOCAL_RESCORING_COMPLETE_UNVERIFIED"
    except Exception:
        # No partial scores when one case has an untrusted/missing receipt.
        summary["cases"] = []
        summary["observed_cases"] = 0
        summary["passed"] = 0
        summary["failed"] = 0
    return summary


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--evidence-root", type=Path, required=True)
    p.add_argument("--target-root", type=Path, required=True)
    args = p.parse_args(argv)
    result = audit(args.evidence_root, args.target_root,
                   Path(__file__).resolve().parents[2])
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "OWNER_LOCAL_RESCORING_COMPLETE_UNVERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
