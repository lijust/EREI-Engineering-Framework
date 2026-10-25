"""Real-model smoke receipt safety tests. No Google network or credentials."""
from __future__ import annotations
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from evals import run_gemini_core_smoke as smoke


def good_raw(model="gemini-3.8-flash"):
    return json.dumps({
        "modelVersion": model,
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

    def test_selected_36_real_core_case_retains_version_and_no_false_release(self):
        with tempfile.TemporaryDirectory() as folder:
            raw = good_raw("gemini-3.6-flash")
            with mock.patch.object(smoke.gemini, "generate_raw_once", return_value=raw) as request:
                verdict = smoke.record_one(
                    prepared(), Path(folder), "mock-secret", 90,
                    model="gemini-3.6-flash",
                )
            request.assert_called_once_with(
                "public synthetic prompt only", key="mock-secret", timeout=90,
                model="gemini-3.6-flash",
            )
            self.assertEqual(verdict["model_requested"], "gemini-3.6-flash")
            self.assertEqual(verdict["provider_model_version"], "gemini-3.6-flash")
            self.assertTrue(verdict["passed"])
            self.assertFalse(verdict["independently_accepted"])
            self.assertFalse(verdict["stable_ready"])
            self.assertEqual(json.loads((Path(folder) / "verdict.json").read_text())
                             ["model_requested"], "gemini-3.6-flash")

    def test_wrong_provider_model_never_scores_as_valid_core(self):
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(smoke.gemini, "generate_raw_once",
                                   return_value=good_raw("gemini-3.8-flash")):
                verdict = smoke.record_one(
                    prepared(), Path(folder), "mock-secret", 90,
                    model="gemini-3.6-flash"
                )
            self.assertFalse(verdict["passed"])
            self.assertEqual(verdict["status"], "MODEL_RESPONSE_INVALID_UNVERIFIED")
            self.assertEqual(verdict["model_requested"], "gemini-3.6-flash")
            self.assertEqual(verdict["provider_model_version"], "gemini-3.8-flash")
            self.assertFalse((Path(folder) / "adapter-normalized.json").exists())

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

    def test_suites_are_read_only_immutable_git_blobs_not_worktree(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            rel = "evals/cases/task-learning-review.eval.json"
            path = root / rel
            path.parent.mkdir(parents=True)
            path.write_bytes(b'{"poisoned_worktree": "PRIVATE-MUST-NOT-SEND"}')
            blob = json.dumps({
                "suite_id": "task-learning-review-v1",
                "artifact": "skills/task-learning-capture + workflows/learning-review",
                "cases": [{
                    "id": key, "input": {"prompt": "TRUSTED COMMITTED CASE"},
                    "expectations": [{"type": "behavioral_simulation"}],
                } for key in smoke.CASES["task-learning-review.eval.json"]],
            }).encode("utf-8")
            fake_runner = mock.Mock()
            fake_runner.strict_json_loads.side_effect = json.loads
            fake_runner.validate_suite.return_value = []
            with mock.patch.object(smoke.subprocess, "check_output", return_value=blob) as git:
                suite, case, req = smoke.load_one(
                    root, "TLR-001-SUCCESS-STILL-LEARNING-DATA", fake_runner
                )
                self.assertEqual(case["input"]["prompt"], "TRUSTED COMMITTED CASE")
                self.assertNotIn("PRIVATE-MUST-NOT-SEND", str(req))
                self.assertIn("show", git.call_args.args[0])
                self.assertEqual(git.call_args.args[0][-1],
                                 smoke.gemini.EXPECTED_TARGET_HEAD + ":" + rel)
            with self.assertRaisesRegex(
                smoke.gemini.GeminiAdapterError, "unexpected target evaluation"
            ):
                smoke.frozen_blob(root, "secrets/private.env")

    def test_real_git_replace_ref_cannot_substitute_frozen_scorer_blob(self):
        import subprocess
        import os
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            env = {k: v for k, v in os.environ.items()
                   if not k.upper().startswith("GIT_")}
            def git(*args, input=None):
                return subprocess.check_output(
                    ["git", "-C", str(root), *args],
                    input=input, stderr=subprocess.DEVNULL, env=env,
                    timeout=15,
                ).strip()
            git("init", "-q")
            git("config", "core.autocrlf", "false")
            filename = root / "evals" / "runner.py"
            filename.parent.mkdir(parents=True)
            genuine = b"MARKER = 'ORIGINAL_FROZEN'\n"
            malicious = b"MARKER = 'POISONED_REPLACEMENT'\n"
            filename.write_bytes(genuine)
            git("add", "evals/runner.py")
            git("-c", "user.email=test@example.invalid", "-c",
                "user.name=Core13-Test", "commit", "-qm", "source test")
            commit = git("rev-parse", "HEAD").decode()
            original_blob = git("rev-parse", "HEAD:evals/runner.py").decode()
            replacement_blob = git("hash-object", "-w", "--stdin",
                                   input=malicious).decode()
            git("replace", original_blob, replacement_blob)
            self.assertEqual(
                git("show", f"{commit}:evals/runner.py"), malicious.strip()
            )
            with mock.patch.object(smoke.gemini, "EXPECTED_TARGET_HEAD", commit):
                self.assertEqual(
                    smoke.frozen_blob(root, "evals/runner.py"), genuine
                )
                self.assertEqual(
                    smoke.frozen_runner(root).MARKER, "ORIGINAL_FROZEN"
                )
            # Fixture is isolated in temporary local test repo: no production refs.

    def test_scorer_executes_git_blob_without_loading_poisoned_pyc(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            py_file = root / "evals" / "runner.py"
            py_file.parent.mkdir(parents=True)
            py_file.write_text(
                "MARKER = 'PRIVATE-MUST-NOT-EXECUTE'\n",
                encoding="utf-8",
            )
            pycache = py_file.parent / "__pycache__"
            pycache.mkdir()
            (pycache / "runner.cpython-312.pyc").write_bytes(b"POISONED-PYC")
            git_source = b"MARKER = 'ORIGINAL_VERIFIED_GIT_BLOB'\n"
            with mock.patch.object(
                smoke.subprocess, "check_output", return_value=git_source
            ) as git:
                loaded = smoke.frozen_runner(root)
            self.assertEqual(loaded.MARKER, "ORIGINAL_VERIFIED_GIT_BLOB")
            self.assertIn("show", git.call_args.args[0])
            self.assertEqual(git.call_args.args[0][-1],
                             smoke.gemini.EXPECTED_TARGET_HEAD + ":evals/runner.py")
            self.assertEqual(len(list(pycache.iterdir())), 1)

    def test_crlf_worktree_cannot_block_valid_git_blob_case_or_scorer(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "evals" / "runner.py"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"MARKER = 'WORKTREE'\r\n")
            with mock.patch.object(
                smoke.subprocess, "check_output",
                return_value=b"MARKER = 'PINNED'\n",
            ):
                scorer = smoke.frozen_runner(root)
            self.assertEqual(scorer.MARKER, "PINNED")

    def test_frozen_suite_tamper_fails_before_model_prompt_or_network(self):
        with (
            mock.patch.object(smoke.gemini, "verify_frozen_target"),
            mock.patch.object(smoke, "frozen_runner", return_value=mock.Mock()),
            mock.patch.object(smoke, "frozen_blob",
                              side_effect=smoke.gemini.GeminiAdapterError("blob unavailable")),
            mock.patch.object(smoke.gemini, "prepare_one") as build,
            mock.patch.object(smoke.gemini, "generate_raw_once") as api,
        ):
            with self.assertRaisesRegex(smoke.gemini.GeminiAdapterError, "blob unavailable"):
                smoke.prepare(Path("."), "TLR-001-SUCCESS-STILL-LEARNING-DATA", Path("."))
            build.assert_not_called()
            api.assert_not_called()

    def test_offline_preflight_uses_target_runner_and_single_case(self):
        fake = mock.Mock()
        fake.strict_json_loads.return_value = {
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
            mock.patch.object(smoke, "frozen_blob", return_value=b'{"synthetic":"fixture"}'),
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
            with (
                self.subTest(args=args),
                mock.patch("sys.stderr", new_callable=io.StringIO),
                mock.patch.object(smoke.gemini, "generate_raw_once") as api,
                mock.patch.object(smoke, "prepare") as prep,
            ):
                self.assertEqual(smoke.main(args), 2)
                api.assert_not_called()
                prep.assert_not_called()

    def test_failed_remote_call_produces_redacted_http_diagnostic(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)
            out = source / "evidence" / "attempt-002"
            fake_prepared = prepared()
            fake_prepared["root"] = source / "target"
            (source / "target").mkdir()
            with (
                mock.patch.object(smoke, "prepare", return_value=fake_prepared),
                mock.patch.object(
                    smoke.gemini, "generate_raw_once",
                    side_effect=smoke.gemini.GeminiAdapterError(
                        "provider original response deliberately redacted",
                        safe_code="GEMINI_HTTP_ERROR", http_status=403,
                    ),
                ) as api,
                mock.patch.object(smoke.getpass, "getpass", return_value="secret-not-logged"),
                mock.patch("sys.stderr", new_callable=io.StringIO) as stderr,
            ):
                result = smoke.main([
                    "--target-root", str(fake_prepared["root"]),
                    "--case-id", "TLR-001-SUCCESS-STILL-LEARNING-DATA",
                    "--output-dir", str(out),
                    "--timeout", "90", "--live", "--confirm-free-tier",
                ])
            self.assertEqual(result, 2)
            api.assert_called_once()
            journal = json.loads((out / "attempt-failed.json").read_text())
            self.assertEqual(journal["reason_category"], "GEMINI_HTTP_ERROR")
            self.assertEqual(journal["provider_http_status"], 403)
            self.assertFalse(journal["stable_ready"])
            self.assertIn("HTTP_403", stderr.getvalue())
            self.assertNotIn("secret-not-logged", (out / "attempt-failed.json").read_text())
            self.assertNotIn("provider original", stderr.getvalue())

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
