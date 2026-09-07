import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "evals" / "runner.py"
spec = importlib.util.spec_from_file_location("erei_eval_runner_evidence", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class ExecutionEvidenceTests(unittest.TestCase):
    def test_v1_evidence_is_legacy_harness_smoke_level(self):
        data = {
            "schema_version": 1,
            "framework_revision": "a" * 40,
            "executions": [{
                "suite_id": "suite",
                "case_id": "case",
                "status": "pass",
                "adapter_id": "legacy",
                "evidence_ref": "ci:1",
            }],
        }
        validated = runner.validate_execution_evidence(data)
        self.assertEqual(runner.execution_assurance_level(validated["executions"][0], 1), "harness_smoke")

    def test_v2_exact_target_requires_independent_runtime(self):
        data = {
            "schema_version": 2,
            "framework_revision": "a" * 40,
            "produced_at": "2026-09-07T02:30:00Z",
            "executions": [{
                "suite_id": "suite",
                "case_id": "case",
                "status": "pass",
                "adapter_id": "target-runtime",
                "adapter_revision": "b" * 40,
                "assurance_level": "exact_target_runtime",
                "independent_runtime": False,
                "evidence_ref": "ci:2",
            }],
        }
        with self.assertRaisesRegex(RuntimeError, "requires independent_runtime=true"):
            runner.validate_execution_evidence(data)

    def test_reference_contract_cannot_claim_independent_runtime(self):
        data = {
            "schema_version": 2,
            "framework_revision": "a" * 40,
            "produced_at": "2026-09-07T02:30:00Z",
            "executions": [{
                "suite_id": "suite",
                "case_id": "case",
                "status": "pass",
                "adapter_id": "reference-oracle",
                "adapter_revision": "b" * 40,
                "assurance_level": "reference_contract",
                "independent_runtime": True,
                "evidence_ref": "ci:3",
            }],
        }
        with self.assertRaisesRegex(RuntimeError, "cannot claim independent runtime"):
            runner.validate_execution_evidence(data)

    def test_valid_exact_target_evidence_passes(self):
        data = {
            "schema_version": 2,
            "framework_revision": "a" * 40,
            "produced_at": "2026-09-07T02:30:00Z",
            "executions": [{
                "suite_id": "suite",
                "case_id": "case",
                "status": "pass",
                "adapter_id": "target-runtime",
                "adapter_revision": "b" * 40,
                "assurance_level": "exact_target_runtime",
                "independent_runtime": True,
                "evidence_ref": "ci:4",
            }],
        }
        self.assertEqual(runner.validate_execution_evidence(data)["schema_version"], 2)


if __name__ == "__main__":
    unittest.main()
