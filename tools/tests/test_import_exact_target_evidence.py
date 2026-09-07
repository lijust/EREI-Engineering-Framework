import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import build_exact_target_package_identity, exact_target_evidence, import_exact_target_evidence


ROOT = Path(__file__).resolve().parents[2]


class ExactTargetEvidenceImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.package = Path(self.tmp.name) / "package"
        self.repo.mkdir()
        self.package.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "user.name", "EREI Test")

        self._write("README.md", "stable root\n")
        self.stable_ref = self._commit("stable root")

        (self.repo / "evals" / "cases").mkdir(parents=True)
        (self.repo / "evals" / "runner.py").write_text(
            (ROOT / "evals" / "runner.py").read_text(encoding="utf-8"), encoding="utf-8"
        )
        suite = {
            "schema_version": "1.0",
            "suite_id": "behavioral-suite",
            "artifact": "skills/impact-analysis",
            "assurance_scope": "behavioral_runtime",
            "cases": [{
                "id": "CASE-1",
                "input": {"prompt": "evaluate"},
                "expectations": [
                    {"type": "output_contains_all", "values": ["required"]},
                    {"type": "metadata_equals", "key": "risk", "value": "L2"},
                ],
            }],
        }
        self._write("evals/cases/behavioral.eval.json", suite)
        self._write("CAPABILITIES.json", {
            "stable_release": {
                "baseline": "stable-v1",
                "framework_ref": self.stable_ref,
            }
        })
        self.target_ref = self._commit("candidate target")
        self.target_tree = self._git("rev-parse", f"{self.target_ref}^{{tree}}")

        self._write("releases/VNEXT_TARGET.json", {
            "schema_version": 1,
            "target_id": "vnext-rc2",
            "status": "frozen_candidate",
            "framework_ref": self.target_ref,
            "target_tree": self.target_tree,
            "selected_at": "2026-09-07T16:00:00Z",
            "source_branch": "main",
            "assurance": {
                "workflow": "Framework Assurance Gate",
                "run_id": 123,
                "event": "push",
                "conclusion": "success",
            },
            "stable_baseline": {
                "baseline": "stable-v1",
                "framework_ref": self.stable_ref,
            },
            "promotion_authorized": False,
        })
        self.carrier_ref = self._commit("freeze rc2")
        self._write_package()

    def tearDown(self):
        self.tmp.cleanup()

    def _git(self, *args):
        process = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        if process.returncode != 0:
            self.fail(f"git {' '.join(args)} failed: {process.stderr}")
        return process.stdout.strip()

    def _write(self, path, value):
        full = self.repo / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(value if isinstance(value, str) else json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def _commit(self, message):
        self._git("add", "-A")
        self._git("commit", "-q", "-m", message)
        return self._git("rev-parse", "HEAD")

    def _write_package(self):
        response = {"output": "required behavior", "metadata": {"risk": "L2"}}
        run_id = "ETR-20260907T160100Z-A1B2C3D4"
        manifest_path = "evals/exact-target-runs/copilot-123-1.json"
        evidence_path = "evals/EXECUTION_EVIDENCE.copilot-123-1.json"
        manifest = {
            "schema_version": 2,
            "run_id": run_id,
            "produced_at": "2026-09-07T16:01:00Z",
            "framework_revision": self.target_ref,
            "adapter": {"id": "external-adapter", "revision": self.target_ref},
            "runtime": {
                "id": "github-copilot-cli",
                "version": "GitHub Copilot CLI 1.2.3",
                "independent_runtime": True,
                "identity_evidence": [
                    "github-actions:lijust/EREI-Engineering-Framework/run/123/attempt/1",
                    f"release-carrier:{self.carrier_ref}",
                    "copilot-model:gpt-5.4",
                ],
            },
            "adapter_command_digest": "a" * 64,
            "executions": [{
                "suite_id": "behavioral-suite",
                "case_id": "CASE-1",
                "status": "pass",
                "response_digest": exact_target_evidence._canonical_digest(response),
                "response": response,
                "adapter_error": False,
            }],
        }
        evidence = {
            "schema_version": 2,
            "framework_revision": self.target_ref,
            "produced_at": "2026-09-07T16:01:00Z",
            "executions": [{
                "suite_id": "behavioral-suite",
                "case_id": "CASE-1",
                "status": "pass",
                "adapter_id": "external-adapter",
                "adapter_revision": self.target_ref,
                "assurance_level": "exact_target_runtime",
                "independent_runtime": True,
                "evidence_ref": f"exact-target-run:{manifest_path}#behavioral-suite/CASE-1",
            }],
        }
        (self.package / "exact-target-run.json").write_text(json.dumps(manifest), encoding="utf-8")
        (self.package / "execution-evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
        identity = build_exact_target_package_identity.build_identity(
            package_dir=self.package,
            repository="lijust/EREI-Engineering-Framework",
            target_id="vnext-rc2",
            framework_ref=self.target_ref,
            target_tree=self.target_tree,
            release_carrier_ref=self.carrier_ref,
            adapter_id="external-adapter",
            adapter_revision=self.target_ref,
            runtime_id="github-copilot-cli",
            runtime_version="GitHub Copilot CLI 1.2.3",
            requested_cli_version="1.2.3",
            model="gpt-5.4",
            github_run_id=123,
            github_run_attempt=1,
            run_manifest_path=manifest_path,
            execution_evidence_path=evidence_path,
        )
        (self.package / "runtime-identity.json").write_text(
            json.dumps(identity, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def test_valid_package_is_imported_only_to_governed_destinations(self):
        result = import_exact_target_evidence.import_package(self.repo, self.package)
        self.assertEqual(result["case_count"], 1)
        manifest = self.repo / result["manifest_destination"]
        evidence = self.repo / result["evidence_destination"]
        self.assertTrue(manifest.is_file())
        self.assertTrue(evidence.is_file())
        self.assertEqual(manifest.read_bytes(), (self.package / "exact-target-run.json").read_bytes())
        self.assertEqual(evidence.read_bytes(), (self.package / "execution-evidence.json").read_bytes())

    def test_hash_tamper_is_rejected_before_write(self):
        path = self.package / "execution-evidence.json"
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "digest mismatch"):
            import_exact_target_evidence.validate_package(self.repo, self.package)
        self.assertFalse((self.repo / "evals" / "exact-target-runs" / "copilot-123-1.json").exists())

    def test_carrier_drift_is_rejected(self):
        self._write("notes.txt", "carrier moved\n")
        self._commit("move carrier")
        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "exact release carrier"):
            import_exact_target_evidence.validate_package(self.repo, self.package)

    def test_existing_destination_is_never_overwritten(self):
        import_exact_target_evidence.import_package(self.repo, self.package)
        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "destination already exists"):
            import_exact_target_evidence.validate_package(self.repo, self.package)

    def test_runtime_identity_rejects_unknown_fields(self):
        identity_path = self.package / "runtime-identity.json"
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
        identity["unexpected"] = True
        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "fields mismatch"):
            import_exact_target_evidence.validate_runtime_identity(identity)

    def test_runtime_identity_run_attempt_must_match_manifest_provenance(self):
        identity_path = self.package / "runtime-identity.json"
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
        identity["github_run_attempt"] = 2
        identity_path.write_text(json.dumps(identity), encoding="utf-8")
        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "runtime identity evidence"):
            import_exact_target_evidence.validate_package(self.repo, self.package)

    def test_exclusive_write_pair_rolls_back_first_reservation_if_second_destination_exists(self):
        scratch = Path(self.tmp.name) / "write-pair-existing"
        source_one = scratch / "source-one"
        source_two = scratch / "source-two"
        destination_one = scratch / "dest" / "one.json"
        destination_two = scratch / "dest" / "two.json"
        scratch.mkdir(parents=True)
        source_one.write_bytes(b"one")
        source_two.write_bytes(b"two")
        destination_two.parent.mkdir(parents=True)
        destination_two.write_bytes(b"existing")

        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "already exists"):
            import_exact_target_evidence._exclusive_write_pair((
                (source_one, destination_one),
                (source_two, destination_two),
            ))

        self.assertFalse(destination_one.exists())
        self.assertEqual(destination_two.read_bytes(), b"existing")

    def test_exclusive_write_pair_rolls_back_both_reservations_on_source_failure(self):
        scratch = Path(self.tmp.name) / "write-pair-failure"
        source_one = scratch / "source-one"
        source_two = scratch / "source-two"
        destination_one = scratch / "dest" / "one.json"
        destination_two = scratch / "dest" / "two.json"
        scratch.mkdir(parents=True)
        source_one.write_bytes(b"one")
        source_two.write_bytes(b"two")

        original_read_bytes = Path.read_bytes

        def failing_read(path):
            if path == source_two:
                raise OSError("simulated second-source failure")
            return original_read_bytes(path)

        with mock.patch.object(Path, "read_bytes", failing_read):
            with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "rolled back"):
                import_exact_target_evidence._exclusive_write_pair((
                    (source_one, destination_one),
                    (source_two, destination_two),
                ))

        self.assertFalse(destination_one.exists())
        self.assertFalse(destination_two.exists())


if __name__ == "__main__":
    unittest.main()
