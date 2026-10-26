#!/usr/bin/env python3
"""Read-only offline replay of one existing Gemini Core13 receipt.

Replays the provider's UNCHANGED bytes through the current strict adapter and
the immutable PR98 scorer. Makes NO model/network calls or evidence writes.
No independent acceptance or Stable credit is possible from this command.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from evals import diagnose_gemini_core_receipt as diagnosis
from evals import run_gemini_core_smoke as smoke

MAX_REQUEST_BYTES = 200_000


class ReplayBlocked(Exception):
    """Do not expose raw model text, prompt, or stored artifact paths."""


def result(status: str, **data) -> dict:
    return {
        "kind": "OFFLINE_GEMINI_CORE13_REPLAY",
        "status": status,
        "network_requests": 0,
        "model_calls": 0,
        "evidence_files_written": 0,
        "original_receipt_unchanged": True,
        "independently_accepted": False,
        "stable_ready": False,
        "accepted_core_cases": 0,
        **data,
    }


def replay(evidence_dir: Path, target_root: Path) -> dict:
    try:
        # Do not trust a symlink for the directory containing raw evidence.
        if evidence_dir.is_symlink() or not evidence_dir.is_dir():
            raise ReplayBlocked()
        verdict = diagnosis.strict_json(
            diagnosis.bounded_read(evidence_dir / "verdict.json",
                                   diagnosis.MAX_VERDICT_BYTES)
        )
        request = diagnosis.strict_json(
            diagnosis.bounded_read(evidence_dir / "blind-request.json",
                                   MAX_REQUEST_BYTES)
        )
        raw = diagnosis.bounded_read(
            evidence_dir / "provider-raw.json", diagnosis.MAX_RAW_BYTES
        )
        if not isinstance(verdict, dict) or not isinstance(request, dict):
            raise ReplayBlocked()
        if (verdict.get("status") != "MODEL_RESPONSE_INVALID_UNVERIFIED"
                or verdict.get("passed") is not False
                or verdict.get("independently_accepted") is not False
                or verdict.get("stable_ready") is not False):
            raise ReplayBlocked()
        if (verdict.get("source_head") != smoke.gemini.EXPECTED_TARGET_HEAD
                or verdict.get("source_tree") != smoke.gemini.EXPECTED_TARGET_TREE):
            raise ReplayBlocked()
        case_id = verdict.get("case_id")
        if not isinstance(case_id, str) or case_id not in {
            case for cases in smoke.CASES.values() for case in cases
        }:
            raise ReplayBlocked()
        model = verdict.get("model_requested")
        if (model not in smoke.gemini.CORE_MODELS
                or verdict.get("provider_model_version") != model):
            raise ReplayBlocked()
        original_adapter = verdict.get("adapter_source_revision")
        if (not isinstance(original_adapter, str)
                or re.fullmatch(r"[0-9a-f]{40}", original_adapter) is None):
            raise ReplayBlocked()
        if (smoke.sha(raw) != verdict.get("provider_response_sha256")
                or smoke.sha(smoke.canonical_bytes(request))
                != verdict.get("blind_request_sha256")):
            return result("RECEIPT_HASH_MISMATCH")
        checked = diagnosis.diagnose(evidence_dir)
        if (not checked.get("raw_sha256_verified")
                or checked.get("model_requested") != model
                or checked.get("classification")
                != "MODEL_SHAPE_VALID_BUT_PRIOR_SCORING_EXCEPTION"):
            return result("REPLAY_STRICT_SHAPE_INVALID",
                          diagnosis_category=checked["classification"])

        root = target_root.resolve()
        smoke.gemini.verify_frozen_target(root)
        runner = smoke.frozen_runner(root)
        suite, case, _ = smoke.load_one(root, case_id, runner)
        # Match the blinded input to the exact original frozen case.
        if (verdict.get("suite_id") != suite["suite_id"]
                or request.get("artifact") != suite["artifact"]
                or request.get("input") != case["input"]
                or request.get("context") != case.get("context", {})
                or set(request) != {
                    "protocol_version", "suite_id", "case_id",
                    "artifact", "input", "context"
                }):
            raise ReplayBlocked()
        prompt = smoke.gemini.prepare_one(request, root)
        if smoke.sha(prompt.encode("utf-8")) != verdict.get("prompt_sha256"):
            return result("PROMPT_HASH_MISMATCH")
        # parse_gemini_result reads model text only, not thoughtSignature.
        normalized = smoke.gemini.parse_gemini_result(raw)
        # Score with ORIGINAL PR98 Git blobs, not a local modified/pyc scorer.
        scores = [
            bool(runner.score(expectation, normalized, case["input"])[0])
            for expectation in case["expectations"]
        ]
        if not scores:
            raise ReplayBlocked()
        passed = all(scores)
        return result(
            "MODEL_RESPONSE_SCORED_PASS_REPLAY_UNVERIFIED"
            if passed else "MODEL_RESPONSE_SCORED_FAIL_REPLAY_UNVERIFIED",
            case_id=case_id,
            model_requested=model,
            original_adapter_sha=original_adapter,
            raw_sha256_verified=True,
            prompt_sha256_verified=True,
            blind_request_sha256_verified=True,
            scored_expectations=len(scores),
            passing_expectations=sum(scores),
            failing_expectation_indexes=[i for i, passed in enumerate(scores)
                                         if not passed],
            behavioral_pass_observed=passed,
        )
    except (OSError, ValueError, TypeError, KeyError, AttributeError,
            ReplayBlocked, diagnosis.ReceiptDiagnosticError,
            smoke.gemini.GeminiAdapterError):
        return result("REPLAY_BLOCKED_UNVERIFIED")
    except Exception:
        # The frozen scorer may throw. Never echo arbitrary response contents
        # or scorer criteria in errors.
        return result("FROZEN_SCORER_EXCEPTION_UNVERIFIED")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", required=True, type=Path)
    parser.add_argument("--target-root", required=True, type=Path)
    args = parser.parse_args(argv)
    result_data = replay(args.evidence_dir, args.target_root)
    print(json.dumps(result_data, sort_keys=True))
    return (0 if result_data["status"].startswith("MODEL_RESPONSE_SCORED_")
            else 2)


if __name__ == "__main__":
    raise SystemExit(main())
