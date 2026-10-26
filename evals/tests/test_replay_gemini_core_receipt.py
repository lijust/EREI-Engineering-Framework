"""Offline-only regression coverage for immutable Gemini receipt rescoring."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from evals import replay_gemini_core_receipt as replay
from evals import run_gemini_core_smoke as smoke


CASE = "TLR-001-SUCCESS-STILL-LEARNING-DATA"
MODEL = "gemini-3.5-flash-lite"
PROMPT = "synthetic frozen public prompt"


def synthetic_receipt(folder: Path):
    normalized = {
        "output": {
            "contract": "erei-action-simulation-v1",
            "decision": "omit_task",
            "actions": [],
            "state": {"task_events": []},
        },
        "metadata": {"risk": "L0"},
    }
    raw = json.dumps({
        "modelVersion": MODEL,
        "usageMetadata": {"totalTokenCount": 7},
        "candidates": [{
            "finishReason": "STOP",
            "content": {"parts": [{
                "text": json.dumps(normalized),
                "thoughtSignature": "opaque-test-signature",
            }]},
        }],
    }).encode("utf-8")
    request = {
        "protocol_version": "2.0",
        "suite_id": "blind-suite-0123456789abcdef",
        "case_id": "blind-case-0123456789abcdef",
        "artifact": "skills/task-learning-capture + workflows/learning-review",
        "input": {"prompt": "synthetic-only"},
        "context": {},
    }
    verdict = {
        "status": "MODEL_RESPONSE_INVALID_UNVERIFIED",
        "passed": False,
        "independently_accepted": False,
        "stable_ready": False,
        "source_head": smoke.gemini.EXPECTED_TARGET_HEAD,
        "source_tree": smoke.gemini.EXPECTED_TARGET_TREE,
        "model_requested": MODEL,
        "provider_model_version": MODEL,
        "case_id": CASE,
        "suite_id": "synthetic-suite",
        "adapter_source_revision": "a" * 40,
        "provider_response_sha256": hashlib.sha256(raw).hexdigest(),
        "blind_request_sha256": smoke.sha(smoke.canonical_bytes(request)),
        "prompt_sha256": smoke.sha(PROMPT.encode("utf-8")),
    }
    (folder / "provider-raw.json").write_bytes(raw)
    (folder / "blind-request.json").write_text(json.dumps(request), encoding="utf-8")
    (folder / "verdict.json").write_text(json.dumps(verdict), encoding="utf-8")
    return request, verdict


class FakeFrozenRunner:
    def score(self, expectation, output, case_input):
        return output["output"]["decision"] == expectation["expect"], "no raw leaks"


class ReceiptReplayTests(unittest.TestCase):
    def test_signed_original_replay_scored_without_any_api_or_evidence_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            req, v = synthetic_receipt(path)
            before = {f.name: f.read_bytes() for f in path.iterdir()}
            suite = {"suite_id": v["suite_id"], "artifact": req["artifact"]}
            case = {"input": req["input"], "expectations": [{"expect": "omit_task"}]}
            with (
                mock.patch.object(smoke.gemini, "verify_frozen_target"),
                mock.patch.object(smoke, "frozen_runner", return_value=FakeFrozenRunner()),
                mock.patch.object(smoke, "load_one",
                                  return_value=(suite, case, req)),
                mock.patch.object(smoke.gemini, "prepare_one", return_value=PROMPT),
                mock.patch.object(smoke.gemini, "generate_raw_once") as api,
            ):
                result = replay.replay(path, path / "frozen-target")
            self.assertEqual(result["status"],
                             "MODEL_RESPONSE_SCORED_PASS_REPLAY_UNVERIFIED")
            self.assertTrue(result["raw_sha256_verified"])
            self.assertTrue(result["prompt_sha256_verified"])
            self.assertEqual(result["passing_expectations"], 1)
            self.assertTrue(result["behavioral_pass_observed"])
            self.assertFalse(result["independently_accepted"])
            self.assertEqual(result["accepted_core_cases"], 0)
            self.assertEqual(result["model_calls"], 0)
            self.assertEqual(result["evidence_files_written"], 0)
            self.assertEqual({f.name: f.read_bytes() for f in path.iterdir()}, before)
            api.assert_not_called()

    def test_scored_failure_remains_unverified_and_not_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            req, v = synthetic_receipt(path)
            suite = {"suite_id": v["suite_id"], "artifact": req["artifact"]}
            case = {"input": req["input"],
                    "expectations": [{"expect": "capture_task"}]}
            with (
                mock.patch.object(smoke.gemini, "verify_frozen_target"),
                mock.patch.object(smoke, "frozen_runner", return_value=FakeFrozenRunner()),
                mock.patch.object(smoke, "load_one",
                                  return_value=(suite, case, req)),
                mock.patch.object(smoke.gemini, "prepare_one", return_value=PROMPT),
            ):
                result = replay.replay(path, path / "target")
            self.assertEqual(result["status"],
                             "MODEL_RESPONSE_SCORED_FAIL_REPLAY_UNVERIFIED")
            self.assertFalse(result["behavioral_pass_observed"])
            self.assertEqual(result["failing_expectation_indexes"], [0])
            self.assertEqual(result["accepted_core_cases"], 0)

    def test_bad_hash_or_tampered_blind_request_blocks_without_scoring(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            request, v = synthetic_receipt(path)
            (path / "provider-raw.json").write_bytes(b"altered-provider-data")
            result = replay.replay(path, path / "target")
            self.assertEqual(result["status"], "RECEIPT_HASH_MISMATCH")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            request, v = synthetic_receipt(path)
            request["input"]["prompt"] = "tampered"
            (path / "blind-request.json").write_text(json.dumps(request), encoding="utf-8")
            result = replay.replay(path, path / "target")
            self.assertEqual(result["status"], "RECEIPT_HASH_MISMATCH")

    def test_bad_provider_model_and_missing_receipt_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            result = replay.replay(path, path / "target")
            self.assertEqual(result["status"], "REPLAY_BLOCKED_UNVERIFIED")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            request, v = synthetic_receipt(path)
            v["provider_model_version"] = "gemini-3.6-flash"
            (path / "verdict.json").write_text(json.dumps(v), encoding="utf-8")
            result = replay.replay(path, path / "target")
            self.assertEqual(result["status"], "REPLAY_BLOCKED_UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
