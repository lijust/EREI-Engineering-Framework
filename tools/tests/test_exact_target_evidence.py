import json
import tempfile
import unittest
from pathlib import Path

from tools import exact_target_evidence


class ExactTargetEvidenceTests(unittest.TestCase):
    def manifest(self):
        return {
            "schema_version": 1,
            "run_id": "ETR-20260907T120000Z-ABCDEF12",
            "produced_at": "2026-09-07T12:00:00Z",
            "framework_revision": "b" * 40,
            "adapter": {"id": "external-adapter", "revision": "a" * 40},
            "runtime": {
                "id": "external-runtime",
                "version": "1",
                "independent_runtime": True,
                "identity_evidence": ["github-actions:123"],
            },
            "adapter_command_digest": "c" * 64,
            "executions": [{
                "suite_id": "suite",
                "case_id": "case",
                "status": "pass",
                "response_digest": "d" * 64,
            }],
        }

    def execution(self):
        return {
            "suite_id": "suite",
            "case_id": "case",
            "status": "pass",
            "adapter_id": "external-adapter",
            "adapter_revision": "a" * 40,
            "assurance_level": "exact_target_runtime",
            "independent_runtime": True,
            "evidence_ref": "exact-target-run:evals/exact-target-runs/run.json#suite/case",
        }

    def test_binding_matches_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "evals" / "exact-target-runs" / "run.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(self.manifest()), encoding="utf-8")
            result = exact_target_evidence.validate_binding(root, "b" * 40, self.execution())
            self.assertEqual(result["run_id"], "ETR-20260907T120000Z-ABCDEF12")

    def test_binding_rejects_status_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "evals" / "exact-target-runs" / "run.json"
            path.parent.mkdir(parents=True)
            value = self.manifest()
            value["executions"][0]["status"] = "fail"
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "status mismatch"):
                exact_target_evidence.validate_binding(root, "b" * 40, self.execution())

    def test_rejects_path_escape(self):
        execution = self.execution()
        execution["evidence_ref"] = "exact-target-run:../outside.json#suite/case"
        with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "relative JSON path"):
            exact_target_evidence.validate_binding(Path("."), "b" * 40, execution)

    def test_manifest_requires_identity_evidence(self):
        value = self.manifest()
        value["runtime"]["identity_evidence"] = []
        with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "identity_evidence"):
            exact_target_evidence.validate_run_manifest(value)


if __name__ == "__main__":
    unittest.main()
