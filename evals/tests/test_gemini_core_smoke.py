"""Real-model smoke receipt safety tests. No Google network or credentials."""
from __future__ import annotations
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from evals import run_gemini_core_smoke as smoke


def good_raw():
    return json.dumps({
        "modelVersion": "gemini-3.8-flash",
        "responseId": "synthetic-response-id",
        "usageMetadata": {"promptTokenCount": 88, "candidatesTokenCount": 33,
                          "totalTokenCount": 121},
        "candidates": [{
            "finishReason": "STOP",
            "content": {"parts": [{
                "text": json.dumps({
                    "output": {
                        "contract": "erei-action-simulation-v1",
                        "decision": "omit_task",
                        "actions": [],
                        "state": {"task_events": []},
                    },
                    "metadata": {"risk": "L0"},
                }),
            }]},
        }],
    }).encode("utf-8")


class FrozenRunnerStub:
    def score(self, expectation, result, case_input):
        assert "reference_actions" not in case_input
        return result["output"]["decision"] == "omit_task", "synthetic-scored"


def prepared():
    return {
        "root": Path(".").resolve(),
        "runner": FrozenRunnerStub(),
        "suite": {"suite_id": "task-learning-review-v1"},
        "case": {
            "id": "TLR-001-SUCCESS-STILL-LEARNING-DATA",
            "input": {"prompt": "public synthetic"},
            "expectations": [{"type": "behavioral_simulation"}],
        },
        "request": {
            "protocol_version": "2.0",
            "suite_id": "blind-suite-0123456789abcdef",
            "case_id": "blind-case-fedcba9876543210",
            "input": {"prompt": "public synthetic"},
        },
        "prompt": "public synthetic prompt only",
        "adapter_source": {"adapter_source_revision": "a" * 40},
    }


class CoreOneCaseTests(unittest.TestCase):
    def test_thirteen_exact_case_ids_and_no_unbounded_selector(self):
        self.assertEqual(sum(map(len, smoke.CASES.values())), 13)
        self.assertEqual(len({k for ids in smoke.CASES.values() for k in ids}), 13)
        self.assertNotIn("all", {k for ids in smoke.CASES.values() for k in ids})

    def test_single_valid_raw_response_has_local_custody_and_usage(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            raw = good_raw()
            with mock.patch.object(smoke.gemini, "generate_raw_once", return_value=raw) as api:
                verdict = smoke.record_one(prepared(), output, "synthetic-fake", 90)
            api.assert_called_once()
            self.assertTrue(verdict["passed"])
            self.assertEqual(verdict["status"], "MODEL_RESPONSE_SCORED_PASS_UNVERIFIED")
            self.assertEqual(verdict["usage_metadata"]["totalTokenCount"], 121)
            self.assertEqual(verdict["provider_model_version"], "gemini-3.8-flash")
            self.assertFalse(verdict["independently_accepted"])
            self.assertFalse(verdict["stable_ready"])
            self.assertEqual((output / "provider-raw.json").read_bytes(), raw)
            self.assertEqual(verdict["provider_response_sha256"], smoke.sha(raw))
            self.assertTrue((output / "adapter-normalized.json").is_file())
            self.assertNotIn("synthetic-fake", (output / "verdict.json").read_text())

    def test_invalid_provider_output_persists_raw_and_not_false_pass(self):
        for kind in ("no_usage", "invalid_json", "duplicate_provider_keys"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                if kind == "no_usage":
                    obj = json.loads(good_raw())
                    obj.pop("usageMetadata")
                    raw = json.dumps(obj).encode()
                elif kind == "invalid_json":
                    raw = b"not-json"
                else:
                    raw = good_raw().replace(
                        b'"modelVersion": "gemini-3.8-flash"',
                        b'"modelVersion": "invalid-model", "modelVersion": "gemini-3.8-flash"', 1,
                    )
                with mock.patch.object(smoke.gemini, "generate_raw_once", return_value=raw):
                    result = smoke.record_one(prepared(), Path(folder), "fake-key", 90)
                self.assertFalse(result["passed"])
                self.assertEqual(result["status"], "MODEL_RESPONSE_INVALID_UNVERIFIED")
                self.assertEqual((Path(folder) / "provider-raw.json").read_bytes(), raw)
                self.assertFalse((Path(folder) / "adapter-normalized.json").exists())

    def test_offline_preflight_uses_target_runner_and_single_case(self):
        fake = mock.Mock()
        fake.load_json.return_value = {
            "suite_id": "task-learning-review-v1",
            "artifact": "skills/task-learning-capture + workflows/learning-review",
            "cases": [{
                "id": key,
                "input": {"prompt": "public", "response_contract": "erei-action-simulation-v1",
                          "initial_state": {"task_events": []}, "facts": {}},
                "expectations": [{"type": "behavioral_simulation"}],
            } for key in smoke.CASES["task-learning-review.eval.json"]],
        }
        fake.validate_suite.return_value = []
        with (
            mock.patch.object(smoke.gemini, "verify_frozen_target") as identity,
            mock.patch.object(smoke, "frozen_runner", return_value=fake),
            mock.patch.object(smoke, "source_identity",
                              return_value={"adapter_source_revision": "a" * 40}),
            mock.patch.object(smoke.gemini, "prepare_one", return_value="prompt") as build,
            mock.patch.object(smoke.gemini, "generate_raw_once") as api,
        ):
            result = smoke.prepare(Path("."), "TLR-001-SUCCESS-STILL-LEARNING-DATA",
                                   Path("."))
            self.assertEqual(result["case"]["id"], "TLR-001-SUCCESS-STILL-LEARNING-DATA")
            self.assertTrue(result["request"]["case_id"].startswith("blind-case-"))
            self.assertTrue(result["request"]["suite_id"].startswith("blind-suite-"))
            self.assertNotIn("expectations", result["request"])
            identity.assert_called_once()
            build.assert_called_once()
            api.assert_not_called()

    def test_no_live_or_no_free_tier_owner_confirmation_never_calls_model(self):
        for args in (
            ["--target-root", ".", "--case-id", "TLR-001-SUCCESS-STILL-LEARNING-DATA",
             "--output-dir", "./not-created"],
            ["--target-root", ".", "--case-id", "TLR-001-SUCCESS-STILL-LEARNING-DATA",
             "--output-dir", "./not-created", "--live"],
        ):
            with self.subTest(args=args), (
                mock.patch("sys.stderr", new_callable=io.StringIO),
                mock.patch.object(smoke.gemini, "generate_raw_once") as api,
                mock.patch.object(smoke, "prepare") as prep,
            ):
                self.assertEqual(smoke.main(args), 2)
                api.assert_not_called()
                prep.assert_not_called()

    def test_cannot_write_evidence_into_either_checkout(self):
        with tempfile.TemporaryDirectory() as folder:
            cwd = Path(folder).resolve()
            data = prepared()
            data["root"] = cwd / "target"
            (cwd / "target").mkdir()
            with (
                mock.patch.object(smoke, "prepare", return_value=data),
                mock.patch.object(smoke, "source_identity",
                                  return_value={"adapter_source_revision": "a" * 40}),
                mock.patch.object(smoke.gemini, "generate_raw_once") as api,
                mock.patch("sys.stderr", new_callable=io.StringIO),
            ):
                self.assertEqual(smoke.main([
                    "--target-root", str(data["root"]),
                    "--case-id", "TLR-001-SUCCESS-STILL-LEARNING-DATA",
                    "--output-dir", str(data["root"] / "evidence"),
                    "--live", "--confirm-free-tier",
                ]), 2)
                api.assert_not_called()
                self.assertFalse((data["root"] / "evidence").exists())


if __name__ == "__main__":
    unittest.main()
