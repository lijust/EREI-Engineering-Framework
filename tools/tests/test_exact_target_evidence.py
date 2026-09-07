import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools import exact_target_evidence, exact_target_package_identity


ROOT = Path(__file__).resolve().parents[2]
FRAMEWORK_REF = "b" * 40
ADAPTER_REF = "a" * 40
CARRIER_REF = "d" * 40
TARGET_TREE = "e" * 40
CLI_INTEGRITY = "sha512-AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8gISIjJCUmJygpKissLS4vMDEyMzQ1Njc4OTo7PD0+Pw=="
MANIFEST_REL = Path("evals/exact-target-runs/run.json")
IDENTITY_REL = Path("evals/exact-target-runs/run.identity.json")
EVIDENCE_REL = Path("evals/EXECUTION_EVIDENCE.run.json")


class ExactTargetEvidenceTests(unittest.TestCase):
    def response(self):
        return {"output": "required behavior", "metadata": {"risk": "L2"}}

    def manifest(self):
        response = self.response()
        return {
            "schema_version": 2,
            "run_id": "ETR-20260907T120000Z-ABCDEF12",
            "produced_at": "2026-09-07T12:00:00Z",
            "framework_revision": FRAMEWORK_REF,
            "adapter": {"id": "external-adapter", "revision": ADAPTER_REF},
            "runtime": {
                "id": "github-copilot-cli",
                "version": "GitHub Copilot CLI 1.2.3",
                "independent_runtime": True,
                "identity_evidence": [
                    "github-actions:lijust/EREI-Engineering-Framework/run/123/attempt/1",
                    f"release-carrier:{CARRIER_REF}",
                    "copilot-model:gpt-5.4",
                    f"copilot-package-integrity:{CLI_INTEGRITY}",
                ],
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
            "adapter_revision": ADAPTER_REF,
            "assurance_level": "exact_target_runtime",
            "independent_runtime": True,
            "evidence_ref": f"exact-target-run:{MANIFEST_REL.as_posix()}#suite/case",
        }

    def evidence(self, execution=None):
        return {
            "schema_version": 2,
            "framework_revision": FRAMEWORK_REF,
            "produced_at": "2026-09-07T12:00:00Z",
            "executions": [execution or self.execution()],
        }

    @staticmethod
    def digest(path: Path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def write_bound_files(self, root: Path, manifest=None, evidence=None, *, assurance_scope="behavioral_runtime"):
        (root / "evals" / "cases").mkdir(parents=True, exist_ok=True)
        (root / "evals" / "exact-target-runs").mkdir(parents=True, exist_ok=True)
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
        manifest_value = manifest or self.manifest()
        evidence_value = evidence or self.evidence()
        manifest_path = root / MANIFEST_REL
        evidence_path = root / EVIDENCE_REL
        manifest_path.write_text(json.dumps(manifest_value), encoding="utf-8")
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(json.dumps(evidence_value), encoding="utf-8")
        identity = {
            "schema_version": 2,
            "repository": "lijust/EREI-Engineering-Framework",
            "target_id": "vnext-rc2",
            "framework_ref": FRAMEWORK_REF,
            "target_tree": TARGET_TREE,
            "release_carrier_ref": CARRIER_REF,
            "adapter_id": "external-adapter",
            "adapter_revision": ADAPTER_REF,
            "runtime_id": "github-copilot-cli",
            "runtime_version": "GitHub Copilot CLI 1.2.3",
            "requested_cli_version": "1.2.3",
            "requested_cli_integrity": CLI_INTEGRITY,
            "model": "gpt-5.4",
            "github_run_id": 123,
            "github_run_attempt": 1,
            "run_id": manifest_value["run_id"],
            "run_manifest_path": MANIFEST_REL.as_posix(),
            "execution_evidence_path": EVIDENCE_REL.as_posix(),
            "runtime_identity_path": IDENTITY_REL.as_posix(),
            "run_manifest_sha256": self.digest(manifest_path),
            "execution_evidence_sha256": self.digest(evidence_path),
        }
        exact_target_package_identity.validate_runtime_identity(identity)
        (root / IDENTITY_REL).write_text(json.dumps(identity), encoding="utf-8")
        return identity

    def test_binding_reconstructs_published_scorers_and_durable_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_bound_files(root)
            result = exact_target_evidence.validate_binding(root, FRAMEWORK_REF, self.execution())
            self.assertEqual(result["run_id"], "ETR-20260907T120000Z-ABCDEF12")

    def test_manifest_rejects_response_digest_tamper(self):
        value = self.manifest()
        value["executions"][0]["response_digest"] = "d" * 64
        with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "response_digest"):
            exact_target_evidence.validate_run_manifest(value)

    def test_binding_rejects_manifest_tamper_against_retained_identity_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_bound_files(root)
            path = root / MANIFEST_REL
            value = json.loads(path.read_text(encoding="utf-8"))
            value["produced_at"] = "2026-09-07T12:01:00Z"
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "run manifest digest"):
                exact_target_evidence.validate_binding(root, FRAMEWORK_REF, self.execution())

    def test_binding_rejects_execution_evidence_tamper_against_retained_identity_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_bound_files(root)
            path = root / EVIDENCE_REL
            value = json.loads(path.read_text(encoding="utf-8"))
            value["produced_at"] = "2026-09-07T12:01:00Z"
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "execution evidence digest"):
                exact_target_evidence.validate_binding(root, FRAMEWORK_REF, self.execution())

    def test_binding_rejects_stored_pass_when_retained_response_fails_scorers_even_if_rehashed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            value = self.manifest()
            value["executions"][0]["response"] = {"output": "wrong", "metadata": {"risk": "L2"}}
            value["executions"][0]["response_digest"] = exact_target_evidence._canonical_digest(
                value["executions"][0]["response"]
            )
            self.write_bound_files(root, manifest=value)
            with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "rescoring mismatch"):
                exact_target_evidence.validate_binding(root, FRAMEWORK_REF, self.execution())

    def test_binding_rejects_harness_only_case_as_exact_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_bound_files(root, assurance_scope="harness_only")
            with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "not eligible"):
                exact_target_evidence.validate_binding(root, FRAMEWORK_REF, self.execution())

    def test_binding_rejects_caller_row_not_present_in_digest_bound_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_bound_files(root)
            execution = self.execution()
            execution["status"] = "fail"
            with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "caller execution row"):
                exact_target_evidence.validate_binding(root, FRAMEWORK_REF, execution)

    def test_binding_rejects_runtime_identity_provenance_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_bound_files(root)
            path = root / IDENTITY_REL
            identity = json.loads(path.read_text(encoding="utf-8"))
            identity["github_run_attempt"] = 2
            path.write_text(json.dumps(identity), encoding="utf-8")
            with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "runtime provenance"):
                exact_target_evidence.validate_binding(root, FRAMEWORK_REF, self.execution())

    def test_adapter_error_still_requires_published_behavioral_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            value = self.manifest()
            item = value["executions"][0]
            item["suite_id"] = "invented-suite"
            item["case_id"] = "invented-case"
            item["status"] = "fail"
            item["response"] = None
            item["adapter_error"] = True
            item["response_digest"] = exact_target_evidence._adapter_error_digest(
                item["suite_id"], item["case_id"]
            )
            execution = self.execution()
            execution.update({
                "suite_id": "invented-suite",
                "case_id": "invented-case",
                "status": "fail",
                "evidence_ref": f"exact-target-run:{MANIFEST_REL.as_posix()}#invented-suite/invented-case",
            })
            self.write_bound_files(root, manifest=value, evidence=self.evidence(execution))
            with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "published behavioral case"):
                exact_target_evidence.validate_binding(root, FRAMEWORK_REF, execution)

    def test_rejects_path_escape(self):
        execution = self.execution()
        execution["evidence_ref"] = "exact-target-run:../outside.json#suite/case"
        with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "relative JSON path"):
            exact_target_evidence.validate_binding(Path("."), FRAMEWORK_REF, execution)

    def test_rejects_identity_file_as_manifest_evidence_ref(self):
        execution = self.execution()
        execution["evidence_ref"] = "exact-target-run:evals/exact-target-runs/run.identity.json#suite/case"
        with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "identity file"):
            exact_target_evidence.validate_binding(Path("."), FRAMEWORK_REF, execution)

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
