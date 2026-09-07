import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evals" / "runner.py"
CASES = ROOT / "evals" / "cases"
ORACLE = ROOT / "evals" / "fixtures" / "reference_oracle_adapter.py"


class ReferenceOracleExecutionTests(unittest.TestCase):
    def test_all_published_cases_execute_and_score(self):
        result = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "run",
                str(CASES),
                "--adapter",
                f"{sys.executable} {ORACLE}",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
        self.assertIn("Summary: 44 passed, 0 failed, 44 total", result.stdout)


if __name__ == "__main__":
    unittest.main()
