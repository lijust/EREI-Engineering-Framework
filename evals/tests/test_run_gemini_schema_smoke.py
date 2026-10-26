"""Offline-only regressions for explicitly owner-operated schema experiment."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from evals.experiments import run_gemini_schema_smoke as runner
from evals.experiments import gemini_core13_schema_candidate as schema
from evals.adapters import gemini_core13_exact_target as gemini


MODEL = "gemini-3.5-flash-lite"


def raw_response(*, decision="omit_task", model=MODEL, extra=None) -> bytes:
    part = {
        "text": json.dumps({
            "output": {
                "contract": "erei-action-simulation-v1",
                "decision": decision,
                "actions": [],
                "state": {"task_events": []},
            },
            "metadata": {"risk": "L0"},
        })
    }
    if extra:
        part.update(extra)
    return json.dumps({
        "modelVersion": model,
        "responseId": "mock-receipt-01",
        "usageMetadata": {
            "promptTokenCount": 2,
            "candidatesTokenCount": 6,
            "totalTokenCount": 8,
        },
        "candidates": [{
            "finishReason": "STOP",
            "content": {"parts": [part]},
        }],
    }).encode("utf-8")


class FrozenFakeScorer:
    def score(self, expectation, response, case_input):
        return (
            response["output"]["decision"] == expectation["decision"],
            "synthetic-scored"
        )


def prepared():
    return {
        "prompt": "PUBLIC SYNTHETIC PROMPT",
        "suite": {"suite_id": "synthetic-suite"},
        "case": {
            "id": "TLR-002-EXPLANATION-NO-EVENT",
            "input": {"response_contract": "erei-action-simulation-v1"},
            "expectations": [{"decision": "omit_task"}],
        },
        "request": {
            "protocol_version": "2.0",
            "suite_id": "blind-suite-0123456789abcdef",
            "case_id": "blind-case-0123456789abcdef",
            "artifact": "synthetic-only",
            "input": {"response_contract": "erei-action-simulation-v1"},
            "context": {},
        },
        "runner": FrozenFakeScorer(),
        "adapter_source": {"adapter_source_revision": "a" * 40},
    }


class GeminiSchemaLiveIsolationTests(unittest.TestCase):
    def test_one_post_uses_only_candidate_body_and_no_inline_api_key(self):
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *_):
                return False
            def read(self, n):
                return raw_response(extra={"thoughtSignature": "opaque-signature"})
        opener = mock.Mock()
        opener.open.return_value = Response()
        with mock.patch.object(runner.urllib.request, "build_opener",
                               return_value=opener):
            raw, payload = runner.generate_candidate_raw_once(
                "PUBLIC SYNTHETIC PROMPT",
                key="secret-test-placeholder",
                model=MODEL, timeout=90,
            )
        self.assertEqual(raw, raw_response(extra={"thoughtSignature": "opaque-signature"}))
        opener.open.assert_called_once()
        req = opener.open.call_args.args[0]
        self.assertEqual(req.full_url, gemini.model_endpoint(MODEL))
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.get_header("X-goog-api-key"), "secret-test-placeholder")
        self.assertEqual(req.data, schema.build_candidate_body(
            "PUBLIC SYNTHETIC PROMPT", model=MODEL
        ))
        self.assertEqual(req.data, payload)
        self.assertNotIn(b"secret-test-placeholder", payload)
        self.assertNotIn("tools", json.loads(payload))

    def test_invalid_header_unapproved_model_and_timeout_no_network(self):
        for key in ("", "secret\nshould-not-echo", "invalid\rkey"):
            with self.subTest(key=bool(key)), mock.patch.object(
                runner.urllib.request, "build_opener"
            ) as opener:
                with self.assertRaises(gemini.GeminiAdapterError):
                    runner.generate_candidate_raw_once(
                        "PUBLIC", key=key, model=MODEL, timeout=90)
                opener.assert_not_called()
        with mock.patch.object(runner.urllib.request, "build_opener") as opener:
            with self.assertRaises(gemini.GeminiAdapterError):
                runner.generate_candidate_raw_once(
                    "PUBLIC", key="mock-key",
                    model="gemini-latest", timeout=90)
            with self.assertRaises(gemini.GeminiAdapterError):
                runner.generate_candidate_raw_once(
                    "PUBLIC", key="mock-key",
                    model=MODEL, timeout=121)
            opener.assert_not_called()

    def test_provider_http_400_does_not_leak_body_or_retry(self):
        opener = mock.Mock()
        opener.open.side_effect = urllib.error.HTTPError(
            "https://generativelanguage.googleapis.com", 400,
            "PRIVATE_KEY_SHOULD_NOT_ESCAPE", {}, None,
        )
        with mock.patch.object(runner.urllib.request, "build_opener",
                               return_value=opener):
            with self.assertRaises(gemini.GeminiAdapterError) as caught:
                runner.generate_candidate_raw_once(
                    "PUBLIC", key="mock-key", model=MODEL, timeout=90)
        self.assertEqual(caught.exception.safe_code, "CANDIDATE_HTTP_ERROR")
        self.assertEqual(caught.exception.http_status, 400)
        self.assertNotIn("PRIVATE_KEY_SHOULD_NOT_ESCAPE", str(caught.exception))
        opener.open.assert_called_once()

    def test_genuine_raw_saved_and_frozen_scorer_result_labeled_experiment_only(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            sample = raw_response(extra={"thoughtSignature": "synthetic-signature"})
            with mock.patch.object(runner, "generate_candidate_raw_once",
                                   return_value=(sample, schema.build_candidate_body(
                                       "PUBLIC SYNTHETIC PROMPT", model=MODEL,
                                   ))) as api:
                verdict = runner.record_candidate(
                    prepared(), folder, key="mock-key", model=MODEL, timeout=60)
            api.assert_called_once()
            self.assertEqual(verdict["status"],
                             "EXPERIMENTAL_MODEL_RESPONSE_SCORED_PASS_UNVERIFIED")
            self.assertTrue(verdict["passed"])
            self.assertFalse(verdict["independently_accepted"])
            self.assertFalse(verdict["stable_ready"])
            self.assertTrue(verdict["experimental_schema"])
            self.assertEqual(verdict["provider_response_sha256"],
                             hashlib.sha256(sample).hexdigest())
            self.assertEqual((folder / "provider-raw.json").read_bytes(), sample)
            self.assertTrue((folder / "adapter-normalized.json").exists())
            self.assertEqual(json.loads((folder / "verdict.json").read_text())["status"],
                             "EXPERIMENTAL_MODEL_RESPONSE_SCORED_PASS_UNVERIFIED")
            self.assertNotIn("mock-key", (folder / "verdict.json").read_text())

    def test_wrong_decision_is_scored_fail_not_new_semantic_pass(self):
        with tempfile.TemporaryDirectory() as root:
            sample = raw_response(decision="capture_task")
            with mock.patch.object(runner, "generate_candidate_raw_once",
                                   return_value=(sample, b'{"synthetic":true}')):
                verdict = runner.record_candidate(
                    prepared(), Path(root), key="mock-key", model=MODEL, timeout=60)
            self.assertEqual(verdict["status"],
                             "EXPERIMENTAL_MODEL_RESPONSE_SCORED_FAIL_UNVERIFIED")
            self.assertFalse(verdict["passed"])

    def test_model_mismatch_is_not_scored_and_evidence_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            sample = raw_response(model="gemini-3.6-flash")
            with mock.patch.object(runner, "generate_candidate_raw_once",
                                   return_value=(sample, b'{"synthetic":true}')):
                verdict = runner.record_candidate(
                    prepared(), Path(root), key="mock-key", model=MODEL, timeout=60)
            self.assertEqual(verdict["status"],
                             "EXPERIMENTAL_MODEL_RESPONSE_INVALID_UNVERIFIED")
            self.assertFalse(verdict["passed"])
            self.assertFalse((Path(root) / "adapter-normalized.json").exists())
            self.assertEqual((Path(root) / "provider-raw.json").read_bytes(), sample)

    def test_main_requires_three_explicit_flags_and_does_not_make_network_call(self):
        with mock.patch.object(runner, "generate_candidate_raw_once") as network:
            status = runner.main([
                "--target-root", ".",
                "--case-id", "TLR-003-VERIFICATION-ESCAPE",
                "--output-dir", "must-not-create",
            ])
        self.assertEqual(status, 2)
        network.assert_not_called()


if __name__ == "__main__":
    unittest.main()
