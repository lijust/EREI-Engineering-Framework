import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evals" / "runner.py"
CASES = ROOT / "evals" / "cases"
ORACLE = ROOT / "evals" / "fixtures" / "reference_oracle_adapter.py"


def published_case_count():
    total = 0
    for path in sorted(CASES.rglob("*.eval.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        total += len(data["cases"])
    return total


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
        total = published_case_count()
        self.assertIn(f"Summary: {total} passed, 0 failed, {total} total", result.stdout)


if __name__ == "__main__":
    unittest.main()
