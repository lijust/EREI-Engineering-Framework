import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evals" / "runner.py"
CASES = ROOT / "evals" / "cases"

spec = importlib.util.spec_from_file_location("erei_eval_runner_scope", RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class AssuranceScopeTests(unittest.TestCase):
    def test_all_published_suites_declare_scope(self):
        suites = runner.discover_suites([str(CASES)])
        self.assertEqual(len(suites), 8)
        scopes = {}
        for path in suites:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("assurance_scope", data, path.name)
            self.assertIn(data["assurance_scope"], runner.ASSURANCE_SCOPES, path.name)
            scopes[data["suite_id"]] = data["assurance_scope"]
        self.assertEqual(scopes["harness-smoke"], "harness_only")
        self.assertEqual(sum(value == "harness_only" for value in scopes.values()), 1)
        self.assertEqual(sum(value == "behavioral_runtime" for value in scopes.values()), 7)

    def test_reference_contract_still_covers_all_44_cases(self):
        expected = runner._expected_cases([str(CASES)], minimum_level="reference_contract")
        self.assertEqual(len(expected), 44)
        self.assertIn(("harness-smoke", "SMOKE-001"), expected)

    def test_exact_target_runtime_requires_only_43_behavioral_cases(self):
        expected = runner._expected_cases([str(CASES)], minimum_level="exact_target_runtime")
        self.assertEqual(len(expected), 43)
        self.assertNotIn(("harness-smoke", "SMOKE-001"), expected)

    def test_unknown_assurance_scope_fails_validation(self):
        data = {
            "schema_version": "1.0",
            "suite_id": "bad-scope",
            "artifact": "skills/example",
            "assurance_scope": "runtime_if_convenient",
            "cases": [{
                "id": "CASE-1",
                "input": {"prompt": "x"},
                "expectations": [{"type": "output_contains_all", "values": ["x"]}],
            }],
        }
        errors = runner.validate_suite(data)
        self.assertTrue(any("assurance_scope" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
