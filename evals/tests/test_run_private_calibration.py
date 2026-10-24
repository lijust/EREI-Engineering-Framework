"""Synthetic local-only tests for the private one-task calibration orchestrator."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1] / "benchmarks"
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location(
    "private_calibration_orchestrator", ROOT / "run_private_calibration.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class PrivateCalibrationOrchestratorTests(unittest.TestCase):
    def setUp(self):
        clean = patch.object(
            runner, "verified_framework_checkout",
            return_value="a" * 40,
        )
        clean.start()
        self.addCleanup(clean.stop)
        self.package = {
            "task_id": "PY-04",
            "runtime": "python",
            "test_path": "tests/unit/test_project_update_presets.py",
            "source": {
                "repository": "lijust/EREI-3.2",
                "commit": "87d730ddc3547f863de2a6895e91f9b83e9c6e72",
            },
            "files": [{"path": "core/project_update_presets.py", "git_blob": "a" * 40}],
        }
        self.catalog = {"execution_authorized": False, "packages": [self.package]}
        self.baseline = {
            "returncode": 0, "stdout": '{"tests":6,"failures":[],"errors":[],"skipped":0}',
            "stderr": "",
            "checks": {"tests": 6, "failures": [], "errors": [], "skipped": 0},
        }
        self.mutant = {
            "returncode": 1,
            "stdout": '{"tests":6,"failures":["test_full_project_details_preset_tracks_registry_without_duplicate_allowlist"],"errors":[],"skipped":0}',
            "stderr": "DO-NOT-PUBLISH-PRIVATE-TEST-PATH",
            "checks": {
                "tests": 6, "failures": [
                    "test_full_project_details_preset_tracks_registry_without_duplicate_allowlist"
                ], "errors": [], "skipped": 0,
            },
        }
        self.raw_catalog = json.dumps(self.catalog).encode()

    def test_single_task_end_to_end_prepares_and_deletes_source_outside_checkout(self):
        with (
            patch.object(runner.check_calibration, "CATALOG") as catalog_path,
            patch.object(runner.prepare_private_exports, "prepare",
                         return_value={"file_count": 1}) as exporter,
            patch.object(runner.check_calibration, "read_inputs",
                         return_value={"source": b"private source"}),
            patch.object(runner.check_calibration, "starter_inputs",
                         return_value={"source": b"private mutant"}),
            patch.object(runner.check_calibration, "run_copy",
                         side_effect=[self.baseline, self.mutant]) as executor,
            patch.object(runner.check_calibration, "assess", return_value=True),
        ):
            catalog_path.read_bytes.return_value = self.raw_catalog
            result = runner.run_one("PY-04")
        self.assertTrue(result["public_calibration_passed"])
        self.assertTrue(result["private_export_cleaned_on_exit"])
        self.assertTrue(result["original_consumer_test_blob_unchanged"])
        self.assertEqual(result["pinned_files_verified"], 1)
        self.assertEqual(result["framework_commit_sha"], "a" * 40)
        self.assertEqual(result["consumer_source_repository"], "lijust/EREI-3.2")
        self.assertEqual(result["consumer_source_commit_sha"],
                         "87d730ddc3547f863de2a6895e91f9b83e9c6e72")
        self.assertEqual(result["execution_scope"],
                         "UNCHANGED_ORIGINAL_CONSUMER_FUNCTIONS_OFFLINE_UNITTEST_ADAPTER")
        self.assertTrue(result["python_runtime_version"])
        self.assertTrue(result["host_os_family"])
        self.assertEqual(result["reference"]["returncode"], 0)
        self.assertEqual(result["starter"]["returncode"], 1)
        self.assertEqual(result["starter"]["checks"]["failed_count"], 1)
        self.assertNotIn("stdout", result["starter"])
        self.assertNotIn("stderr", result["starter"])
        self.assertNotIn("DO-NOT-PUBLISH-PRIVATE-TEST-PATH", json.dumps(result))
        self.assertEqual(result["model_executions"], 0)
        self.assertFalse(result["release_authorized"])
        self.assertEqual(result["independent_review"], "NOT_PERFORMED")
        destination = exporter.call_args.args[0]
        self.assertEqual(exporter.call_args.args[1], "PY-04")
        self.assertFalse(destination.is_relative_to(ROOT.parents[1]))
        self.assertFalse(destination.exists(), "private source temp must be deleted")
        self.assertEqual(executor.call_count, 2)

    def test_cli_returns_nonzero_when_consumer_mutant_not_caught(self):
        result = {
            "task_id": "PY-04", "public_calibration_passed": False,
            "model_executions": 0, "independent_review": "NOT_PERFORMED",
            "release_authorized": False,
        }
        output = io.StringIO()
        with (patch.object(runner, "run_one", return_value=result) as invoke,
              patch.object(sys, "argv",
                           ["run_private_calibration.py", "--task", "py-04"]),
              contextlib.redirect_stdout(output)):
            self.assertEqual(runner.main(), 1)
        invoke.assert_called_once_with("PY-04")
        self.assertFalse(json.loads(output.getvalue())["public_calibration_passed"])

    def test_private_error_is_redacted_and_invalid_task_never_prepares(self):
        with (patch.object(runner.prepare_private_exports, "prepare") as exporter,
              self.assertRaisesRegex(ValueError, "explicit pinned")):
            runner.run_one("--all")
        exporter.assert_not_called()
        private_path = "C:/Users/Private-Client-Secret/records.xlsx"
        output, errors = io.StringIO(), io.StringIO()
        with (patch.object(runner, "run_one",
                           side_effect=OSError(private_path)),
              patch.object(sys, "argv",
                           ["run_private_calibration.py", "--task", "PY-04"]),
              contextlib.redirect_stdout(output),
              contextlib.redirect_stderr(errors)):
            self.assertEqual(runner.main(), 2)
        self.assertEqual(output.getvalue(), "")
        self.assertNotIn(private_path, errors.getvalue())
        self.assertNotIn("Traceback", errors.getvalue())
        self.assertEqual(json.loads(errors.getvalue())["error_type"], "OSError")

    def test_missing_task_or_wrong_export_inventory_fails_closed(self):
        with patch.object(runner.check_calibration, "CATALOG") as catalog_path:
            catalog_path.read_bytes.return_value = self.raw_catalog
            with self.assertRaisesRegex(ValueError, "Missing or duplicate"):
                runner.run_one("PY-01")
        with (patch.object(runner.check_calibration, "CATALOG") as catalog_path,
              patch.object(runner.prepare_private_exports, "prepare",
                           return_value={"file_count": 0}),
              patch.object(runner.check_calibration, "run_copy") as executor):
            catalog_path.read_bytes.return_value = self.raw_catalog
            with self.assertRaisesRegex(ValueError, "inventory"):
                runner.run_one("PY-04")
        executor.assert_not_called()



class ExactFrameworkIdentityTests(unittest.TestCase):
    def test_checkout_clean_head_is_a_pinned_hex_sha(self):
        import subprocess
        cmd = [
            subprocess.CompletedProcess([], 0, stdout=b"c" * 40 + b"\\n", stderr=b""),
            subprocess.CompletedProcess([], 0, stdout=b"", stderr=b""),
        ]
        with patch.object(runner.subprocess, "run", side_effect=cmd) as git:
            self.assertEqual(runner.verified_framework_checkout(), "c" * 40)
        self.assertEqual(git.call_count, 2)
        for call in git.call_args_list:
            self.assertEqual(call.kwargs["shell"], False)
            self.assertEqual(call.kwargs["timeout"], 15)
            self.assertEqual(call.kwargs["capture_output"], True)
            self.assertEqual(call.args[0][:3],
                             ["git", "-C", str(runner.FRAMEWORK_ROOT)])

    def test_changed_checkout_bad_revision_or_git_errors_refuse_attestation(self):
        import subprocess
        scenarios = [
            (subprocess.CompletedProcess([], 1, stdout=b"",
                                         stderr=b"PRIVATE_TOKEN_DO_NOT_LEAK"), "Cannot bind"),
            (subprocess.CompletedProcess([], 0, stdout=b"HEAD\\n", stderr=b""), "Invalid Framework"),
            (subprocess.CompletedProcess([], 0, stdout=b"z" * 40 + b"\\n", stderr=b""), "Invalid Framework"),
        ]
        for response, fragment in scenarios:
            with self.subTest(error=fragment), patch.object(
                    runner.subprocess, "run", return_value=response):
                with self.assertRaisesRegex(ValueError, fragment):
                    runner.verified_framework_checkout()
        pristine = subprocess.CompletedProcess([], 0, stdout=b"c" * 40 + b"\\n", stderr=b"")
        untracked = subprocess.CompletedProcess([], 0, stdout=b"?? PRIVATE-CLIENT-FILE\\n", stderr=b"")
        with patch.object(runner.subprocess, "run", side_effect=[pristine, untracked]):
            with self.assertRaisesRegex(ValueError, "must be clean"):
                runner.verified_framework_checkout()

    def test_source_behavior_oracle_must_not_claim_original_consumer_suite(self):
        package = {"runtime": "node", "behavioral_oracle": "APP04_PROJECT_ID_MAX_PLUS_ONE"}
        self.assertEqual(runner.execution_scope(package),
                         "FRAMEWORK_OWNED_BOUNDED_SOURCE_BEHAVIOR_ORACLE")
        self.assertEqual(runner.execution_scope({"runtime": "node"}),
                         "UNCHANGED_ORIGINAL_NODE_CONSUMER_TEST")
        self.assertEqual(runner.execution_scope({"runtime": "python"}),
                         "UNCHANGED_ORIGINAL_CONSUMER_FUNCTIONS_OFFLINE_UNITTEST_ADAPTER")


if __name__ == "__main__":
    unittest.main()
