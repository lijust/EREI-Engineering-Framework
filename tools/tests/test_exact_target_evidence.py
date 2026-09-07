import json
import tempfile
import unittest
from pathlib import Path

from tools import exact_target_evidence


ROOT = Path(__file__).resolve().parents[2]


class ExactTargetEvidenceTests(unittest.TestCase):
    def response(self):
        return {"output": "required behavior", "metadata": {"risk": "L2"}}

    def manifest(self):
        response = self.response()
        return {
            "schema_version": 2,
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
                "response_digest": exact_target_evidence._canonical_digest(response),
                "response": response,
                "adapter_error": False,
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

    def write_repo(self, root: Path, *, assurance_scope="behavioral_runtime"):
        (root / "evals" / "cases").mkdir(parents=True)
        (root / "evals" / "exact-target-runs").mkdir(parents=True)
        (root / "evals" / "runner.py").write_text(
            (ROOT / "evals" / "runner.py").read_text(encoding="utf-8"), encoding="utf-8"
        )
        suite = {
            "schema_version": "1.0",
            "suite_id": "suite",
            "artifact": "skills/impact-analysis",
            "assurance_scope": assurance_scope,
            "cases": [{
                "id": "case",
                "input": {"prompt": "evaluate"},
                "expectations": [
                    {"type": "output_contains_all", "values": ["required"]},
                    {"type": "metadata_equals", "key": "risk", "value": "L2"},
                ],
            }],
        }
        (root / "evals" / "cases" / "suite.eval.json").write_text(json.dumps(suite), encoding="utf-8")
        (root / "evals" / "exact-target-runs" / "run.json").write_text(
            json.dumps(self.manifest()), encoding="utf-8"
        )

    def test_binding_reconstructs_published_scorers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_repo(root)
            result = exact_target_evidence.validate_binding(root, "b" * 40, self.execution())
            self.assertEqual(result["run_id"], "ETR-20260907T120000Z-ABCDEF12")

    def test_manifest_rejects_response_digest_tamper(self):
        value = self.manifest()
        value["executions"][0]["response_digest"] = "d" * 64
        with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "response_digest"):
            exact_target_evidence.validate_run_manifest(value)

    def test_binding_rejects_stored_pass_when_retained_response_fails_scorers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_repo(root)
            path = root / "evals" / "exact-target-runs" / "run.json"
            value = self.manifest()
            value["executions"][0]["response"] = {"output": "wrong", "metadata": {"risk": "L2"}}
            value["executions"][0]["response_digest"] = exact_target_evidence._canonical_digest(
                value["executions"][0]["response"]
            )
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "rescoring mismatch"):
                exact_target_evidence.validate_binding(root, "b" * 40, self.execution())

    def test_binding_rejects_harness_only_case_as_exact_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_repo(root, assurance_scope="harness_only")
            with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "not eligible"):
                exact_target_evidence.validate_binding(root, "b" * 40, self.execution())

    def test_binding_rejects_execution_status_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_repo(root)
            execution = self.execution()
            execution["status"] = "fail"
            with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "status mismatch"):
                exact_target_evidence.validate_binding(root, "b" * 40, execution)

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

    def test_manifest_rejects_legacy_digest_only_shape(self):
        value = self.manifest()
        value["schema_version"] = 1
        for item in value["executions"]:
            item.pop("response")
            item.pop("adapter_error")
        with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "schema_version must be 2"):
            exact_target_evidence.validate_run_manifest(value)


if __name__ == "__main__":
    unittest.main()
