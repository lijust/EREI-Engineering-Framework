import json
import tempfile
import unittest
from pathlib import Path

from tools import build_exact_target_package_identity, exact_target_evidence, exact_target_package_identity


FRAMEWORK_REF = "b" * 40
ADAPTER_REF = "a" * 40
CARRIER_REF = "d" * 40
TARGET_TREE = "e" * 40
CLI_INTEGRITY = "sha512-AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8gISIjJCUmJygpKissLS4vMDEyMzQ1Njc4OTo7PD0+Pw=="
SKILL_TRANSPORT = exact_target_package_identity.SKILL_EVENT_TRANSPORT_EVIDENCE


class BuildExactTargetPackageIdentityTests(unittest.TestCase):
    def manifest(self):
        response = {"output": "ok", "metadata": {"risk": "L1"}}
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
                    SKILL_TRANSPORT,
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

    def kwargs(self, root):
        return {
            "package_dir": root,
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
            "run_manifest_path": "evals/exact-target-runs/copilot-123-1.json",
            "execution_evidence_path": "evals/EXECUTION_EVIDENCE.copilot-123-1.json",
            "runtime_identity_path": "evals/exact-target-runs/copilot-123-1.identity.json",
        }

    def write_package(self, root, manifest):
        (root / "exact-target-run.json").write_text(json.dumps(manifest), encoding="utf-8")
        (root / "execution-evidence.json").write_text("{}\n", encoding="utf-8")

    def test_valid_manifest_provenance_builds_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_package(root, self.manifest())
            identity = build_exact_target_package_identity.build_identity(**self.kwargs(root))
            self.assertEqual(identity["run_id"], "ETR-20260907T120000Z-ABCDEF12")
            self.assertEqual(
                set(self.manifest()["runtime"]["identity_evidence"]),
                exact_target_package_identity.expected_runtime_evidence(identity),
            )

    def test_missing_skill_transport_marker_fails_before_identity_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.manifest()
            manifest["runtime"]["identity_evidence"].remove(SKILL_TRANSPORT)
            self.write_package(root, manifest)
            with self.assertRaisesRegex(
                exact_target_package_identity.ExactTargetPackageIdentityError,
                "runtime identity evidence",
            ):
                build_exact_target_package_identity.build_identity(**self.kwargs(root))

    def test_adapter_or_runtime_drift_fails_at_producer_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.manifest()
            manifest["adapter"]["id"] = "wrong-adapter"
            self.write_package(root, manifest)
            with self.assertRaisesRegex(
                exact_target_package_identity.ExactTargetPackageIdentityError,
                "adapter id",
            ):
                build_exact_target_package_identity.build_identity(**self.kwargs(root))


if __name__ == "__main__":
    unittest.main()
