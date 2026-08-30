#!/usr/bin/env python3

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evals" / "runner.py"
SMOKE = ROOT / "evals" / "cases" / "harness-smoke.eval.json"
MOCK = ROOT / "evals" / "fixtures" / "mock_adapter.py"


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
            [
                sys.executable,
                str(RUNNER),
                "run",
                str(SMOKE),
                "--adapter",
                f"{sys.executable} {MOCK}",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS harness-smoke/SMOKE-001", result.stdout)
        self.assertIn("Summary: 1 passed, 0 failed, 1 total", result.stdout)


if __name__ == "__main__":
    unittest.main()
