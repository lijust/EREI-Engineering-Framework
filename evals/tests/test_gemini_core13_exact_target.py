"""Offline-only adapter tests: no live Google service, no credential or paid calls."""
import io
import json
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from evals.adapters import gemini_core13_exact_target as gemini


def blind_request():
    return {
        "protocol_version": "2.0",
        "suite_id": "blind-suite-0123456789abcdef",
        "case_id": "blind-case-fedcba9876543210",
        "artifact": "skills/task-learning-capture + workflows/learning-review",
        "input": {
            "prompt": "Synthetic engineering decision only.",
            "response_contract": "erei-action-simulation-v1",
            "initial_state": {"task_events": []},
            "facts": {"occurrence_id": "synthetic-id", "engineering_execution": True},
        },
        "context": {},
    }


def good_response():
    return json.dumps({
        "candidates": [{
            "finishReason": "STOP",
            "content": {
                "parts": [{"text": json.dumps({
                    "output": {
                        "contract": "erei-action-simulation-v1",
                        "decision": "omit_task", "actions": [],
                        "state": {"task_events": []},
                    },
                    "metadata": {"risk": "L0"},
                })}]
            },
        }]
    }).encode()


class GeminiCore13AdapterTests(unittest.TestCase):
    def test_candidate_bound_and_contract_enforced_without_api(self):
        with mock.patch.object(gemini.contract, "resolve_artifact",
                               return_value=[("skills/task-learning-capture/SKILL.md", "public contract")]):
            prompt = gemini.prepare_one(blind_request(), Path("."))
            self.assertIn("Synthetic engineering decision", prompt)
            self.assertIn("public contract", prompt)
            self.assertNotIn("reference_actions", prompt)
        for change in ("version", "artifact", "private_context", "hidden_expectations"):
            req = blind_request()
            if change == "version":
                req["protocol_version"] = "1.0"
            elif change == "artifact":
                req["artifact"] = "evals/fixtures/reference_oracle_adapter.py"
            elif change == "private_context":
                req["context"] = {"secret": "must-never-cross"}
            elif change == "hidden_expectations":
                req["input"]["expectations"] = {"exact": "secret"}
            with self.subTest(change=change), self.assertRaises(Exception):
                gemini.prepare_one(req, Path("."))

    def test_selected_model_is_exact_stable_api_id_not_latest(self):
        self.assertEqual(gemini.MODEL, "gemini-3.8-flash")
        self.assertIn("/models/gemini-3.8-flash:generateContent", gemini.API_URL)

    def test_target_check_rejects_wrong_head_or_tree(self):
        values = [
            gemini.EXPECTED_TARGET_HEAD, gemini.EXPECTED_TARGET_TREE,
            str(Path(".").resolve()), ""
        ]
        with mock.patch.object(gemini.subprocess, "check_output", side_effect=values) as cmd:
            gemini.verify_frozen_target(Path("."))
            self.assertEqual(cmd.call_count, 4)
            self.assertNotIn("GIT_DIR", cmd.call_args.kwargs["env"])
        for pos in (0, 1):
            drift = list(values)
            drift[pos] = "a" * 40
            with mock.patch.object(gemini.subprocess, "check_output", side_effect=drift):
                with self.assertRaisesRegex(gemini.GeminiAdapterError, "mismatch"):
                    gemini.verify_frozen_target(Path("."))
        dirty = list(values)
        dirty[-1] = " M skills/task-learning-capture/SKILL.md"
        with mock.patch.object(gemini.subprocess, "check_output", side_effect=dirty):
            with self.assertRaisesRegex(gemini.GeminiAdapterError, "dirty"):
                gemini.verify_frozen_target(Path("."))

    def test_no_key_no_live_and_no_unbounded_timeout(self):
        with self.assertRaisesRegex(gemini.GeminiAdapterError, "missing"):
            gemini.generate_once("x", key="", timeout=90)
        for timeout in (0, 121):
            with self.subTest(timeout=timeout), self.assertRaisesRegex(
                gemini.GeminiAdapterError, "bounded"
            ):
                gemini.generate_once("x", key="mock-only", timeout=timeout)
        with mock.patch("sys.stderr", new_callable=io.StringIO) as output:
            self.assertEqual(gemini.main(["--target-root", "."]), 2)
            self.assertIn("explicit --live required", output.getvalue())

    def test_one_post_json_only_no_tools_and_safe_secret_redaction(self):
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *_):
                return False
            def read(self, n):
                return good_response()

        class Opener:
            def __init__(self):
                self.calls = 0
                self.request = None
            def open(self, req, timeout):
                self.calls += 1
                self.request = req
                self.timeout = timeout
                return Response()

        opener = Opener()
        with mock.patch.object(gemini.urllib.request, "build_opener", return_value=opener):
            result = gemini.generate_once("public synthetic prompt",
                                          key="mock-secret-only", timeout=90)
        self.assertEqual(opener.calls, 1)
        self.assertEqual(opener.request.get_method(), "POST")
        self.assertEqual(opener.request.full_url, gemini.API_URL)
        self.assertEqual(opener.request.get_header("X-goog-api-key"), "mock-secret-only")
        body = json.loads(opener.request.data)
        self.assertEqual(body["generationConfig"]["responseMimeType"], "application/json")
        self.assertEqual(body["generationConfig"]["thinkingConfig"], {"thinkingLevel": "low"})
        self.assertNotIn("temperature", body["generationConfig"])
        self.assertNotIn("tools", body)
        self.assertNotIn("mock-secret-only", opener.request.data.decode())
        self.assertEqual(result["output"]["decision"], "omit_task")
        self.assertNotIn("trace", result)

    def test_bad_model_response_never_counts(self):
        baseline = json.loads(good_response())
        samples = [
            {"candidates": []},
            {"candidates": [dict(baseline["candidates"][0], finishReason="MAX_TOKENS")]},
            {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"functionCall": {}}]}}]},
            {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "not-json"}]}}]},
        ]
        for candidate in samples:
            with self.subTest(candidate=candidate), self.assertRaises(gemini.GeminiAdapterError):
                gemini.parse_gemini_result(json.dumps(candidate).encode())

    def test_duplicate_provider_response_fields_rejected(self):
        original = good_response().decode()
        poisoned = original.replace(
            '"finishReason": "STOP"',
            '"finishReason": "SAFETY", "finishReason": "STOP"', 1
        )
        with self.assertRaisesRegex(gemini.GeminiAdapterError, "invalid/incomplete"):
            gemini.parse_gemini_result(poisoned.encode())

    def test_http_429_fails_once_never_retries_or_prints_response_body(self):
        import urllib.error
        from unittest.mock import Mock
        err = urllib.error.HTTPError(
            gemini.API_URL, 429, "quota", {}, io.BytesIO(b"private response echoed"))
        fake = Mock()
        fake.open.side_effect = err
        with mock.patch.object(gemini.urllib.request, "build_opener", return_value=fake):
            with self.assertRaisesRegex(gemini.GeminiAdapterError, "HTTP 429") as ex:
                gemini.generate_once("public", key="private-key", timeout=90)
        fake.open.assert_called_once()
        self.assertNotIn("private-key", str(ex.exception))
        self.assertNotIn("private response", str(ex.exception))


if __name__ == "__main__":
    unittest.main()
