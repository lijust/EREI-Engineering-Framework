#!/usr/bin/env python3
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evals" / "runner.py"
SMOKE = ROOT / "evals" / "cases" / "harness-smoke.eval.json"
MOCK = ROOT / "evals" / "fixtures" / "mock_adapter.py"
spec = importlib.util.spec_from_file_location("erei_eval_runner", RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class EvalHarnessSelfTest(unittest.TestCase):
    def test_validate_smoke_suite(self):
        result = subprocess.run(
            [sys.executable, str(RUNNER), "validate", str(SMOKE)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS validate", result.stdout)

    def test_run_smoke_suite(self):
        result = subprocess.run(
            [sys.executable, str(RUNNER), "run", str(SMOKE), "--adapter", f"{sys.executable} {MOCK}"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS harness-smoke/SMOKE-001", result.stdout)
        self.assertIn("Summary: 1 passed, 0 failed, 1 total", result.stdout)

    def test_windows_adapter_command_preserves_backslashes_and_spaces(self):
        command = r'"C:\Program Files\Python312\python.exe" "C:\repo path\mock_adapter.py"'
        self.assertEqual(
            runner.split_adapter_command(command, platform_name="nt"),
            [r"C:\Program Files\Python312\python.exe", r"C:\repo path\mock_adapter.py"],
        )

    def test_trace_null_is_invalid(self):
        with self.assertRaisesRegex(RuntimeError, "trace must be an array"):
            runner.validate_adapter_response(
                {"output": "ok", "trace": None},
                [{"type": "trace_tool_not_called", "tool": "danger"}],
            )

    def test_trace_object_is_invalid(self):
        with self.assertRaisesRegex(RuntimeError, "trace must be an array"):
            runner.validate_adapter_response(
                {"output": "ok", "trace": {"type": "tool", "name": "danger"}},
                [{"type": "max_trace_steps", "value": 1}],
            )

    def test_missing_trace_is_not_negative_evidence(self):
        with self.assertRaisesRegex(RuntimeError, "trace evidence is required"):
            runner.validate_adapter_response(
                {"output": "ok"},
                [{"type": "trace_tool_not_called", "tool": "danger"}],
            )

    def test_malformed_tool_step_is_invalid(self):
        with self.assertRaisesRegex(RuntimeError, "requires name"):
            runner.validate_adapter_response(
                {"output": "ok", "trace": [{"type": "tool"}]},
                [{"type": "trace_tool_called", "tool": "safe"}],
            )

    def test_missing_metadata_is_not_evidence(self):
        with self.assertRaisesRegex(RuntimeError, "metadata evidence is required"):
            runner.validate_adapter_response(
                {"output": "ok"},
                [{"type": "metadata_equals", "key": "risk", "value": "L3"}],
            )


if __name__ == "__main__":
    unittest.main()
