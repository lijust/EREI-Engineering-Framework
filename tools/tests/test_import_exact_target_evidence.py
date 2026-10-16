import json
import os
import shutil
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import (
    build_exact_target_package_identity,
    exact_target_evidence,
    exact_target_package_identity,
    import_exact_target_evidence,
)


ROOT = Path(__file__).resolve().parents[2]
CLI_INTEGRITY = "sha512-AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8gISIjJCUmJygpKissLS4vMDEyMzQ1Njc4OTo7PD0+Pw=="
OTHER_CLI_INTEGRITY = "sha512-Pz49PDs6OTg3NjU0MzIxMC8uLSwrKikoJyYlJCMiISAfHh0cGxoZGBcWFRQTEhEQDw4NDAsKCQgHBgUEAwIBAA=="
SKILL_TRANSPORT = exact_target_package_identity.SKILL_EVENT_TRANSPORT_EVIDENCE


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

        self._write(".gitignore", "__pycache__/\n*.pyc\n")
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
        self._provenance_patch = mock.patch.object(
            import_exact_target_evidence.github_actions_artifact_provenance,
            "verify_official_run_artifact",
            return_value={"authenticated": True, "repository": "lijust/EREI-Engineering-Framework"},
        )
        self._provenance_patch.start()

    def tearDown(self):
        self._provenance_patch.stop()
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
        identity_path = "evals/exact-target-runs/copilot-123-1.identity.json"
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
                    f"copilot-package-integrity:{CLI_INTEGRITY}",
                    SKILL_TRANSPORT,
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
            requested_cli_integrity=CLI_INTEGRITY,
            model="gpt-5.4",
            github_run_id=123,
            github_run_attempt=1,
            run_manifest_path=manifest_path,
            execution_evidence_path=evidence_path,
            runtime_identity_path=identity_path,
        )
        (self.package / "runtime-identity.json").write_text(
            json.dumps(identity, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def test_importer_cli_does_not_generate_sibling_bytecode(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "tools"
            shutil.copytree(
                ROOT / "tools",
                copied,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            env = dict(os.environ)
            env.pop("PYTHONDONTWRITEBYTECODE", None)
            process = subprocess.run(
                [sys.executable, str(copied / "import_exact_target_evidence.py"), "--help"],
                text=True, capture_output=True, check=False, env=env
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(list(copied.rglob("*.pyc")), [])

    def test_valid_package_imports_all_three_governed_files_then_binds_committed_history(self):
        result = import_exact_target_evidence.import_package(self.repo, self.package)
        self.assertEqual(result["case_count"], 1)
        manifest = self.repo / result["manifest_destination"]
        evidence = self.repo / result["evidence_destination"]
        identity = self.repo / result["identity_destination"]
        self.assertTrue(manifest.is_file())
        self.assertTrue(evidence.is_file())
        self.assertTrue(identity.is_file())
        self.assertEqual(manifest.read_bytes(), (self.package / "exact-target-run.json").read_bytes())
        self.assertEqual(evidence.read_bytes(), (self.package / "execution-evidence.json").read_bytes())
        self.assertEqual(identity.read_bytes(), (self.package / "runtime-identity.json").read_bytes())
        evidence_commit = self._commit("commit exact-target evidence")
        self.assertEqual(self._git("rev-parse", f"{evidence_commit}^"), self.carrier_ref)
        row = json.loads(evidence.read_text(encoding="utf-8"))["executions"][0]
        exact_target_evidence.validate_binding(self.repo, self.target_ref, row)

    def test_rejects_foreign_repository_identity(self):
        identity_file = self.package / "runtime-identity.json"
        identity = json.loads(identity_file.read_text(encoding="utf-8"))
        identity["repository"] = "attacker/fork"
        identity_file.write_text(json.dumps(identity), encoding="utf-8")
        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "official release repository"):
            import_exact_target_evidence.validate_package(self.repo, self.package)

    def test_validated_package_load_does_not_create_bytecode_in_release_checkout(self):
        import_exact_target_evidence.validate_package(self.repo, self.package)
        self.assertFalse((self.repo / "evals" / "__pycache__").exists())

    def test_import_writes_validated_bytes_even_if_package_changes_after_validation(self):
        original_manifest = (self.package / "exact-target-run.json").read_bytes()
        original_identity = (self.package / "runtime-identity.json").read_bytes()
        original_evidence = (self.package / "execution-evidence.json").read_bytes()
        real_validate = import_exact_target_evidence.validate_package

        def mutate_after_validation(*args, **kwargs):
            result = real_validate(*args, **kwargs)
            (self.package / "exact-target-run.json").write_bytes(b"tampered after validation")
            (self.package / "runtime-identity.json").write_bytes(b"tampered after validation")
            (self.package / "execution-evidence.json").write_bytes(b"tampered after validation")
            return result

        with mock.patch.object(import_exact_target_evidence, "validate_package", side_effect=mutate_after_validation):
            result = import_exact_target_evidence.import_package(self.repo, self.package)
        self.assertEqual((self.repo / result["manifest_destination"]).read_bytes(), original_manifest)
        self.assertEqual((self.repo / result["evidence_destination"]).read_bytes(), original_evidence)
        self.assertEqual((self.repo / result["identity_destination"]).read_bytes(), original_identity)

    def test_runtime_cli_version_prefix_collision_is_rejected(self):
        identity_file = self.package / "runtime-identity.json"
        identity = json.loads(identity_file.read_text(encoding="utf-8"))
        identity["runtime_version"] = "GitHub Copilot CLI 1.2.30"
        identity_file.write_text(json.dumps(identity), encoding="utf-8")
        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "exact requested CLI version token"):
            import_exact_target_evidence.validate_package(self.repo, self.package)

    def test_nested_identity_path_is_rejected(self):
        identity_file = self.package / "runtime-identity.json"
        identity = json.loads(identity_file.read_text(encoding="utf-8"))
        identity["run_manifest_path"] = "evals/exact-target-runs/nested/copilot-123-1.json"
        identity["runtime_identity_path"] = "evals/exact-target-runs/nested/copilot-123-1.identity.json"
        identity_file.write_text(json.dumps(identity), encoding="utf-8")
        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "single relative JSON filename"):
            import_exact_target_evidence.validate_package(self.repo, self.package)

    def test_invalid_manifest_shape_has_governed_error(self):
        manifest = self.package / "exact-target-run.json"
        value = json.loads(manifest.read_text(encoding="utf-8"))
        del value["executions"]
        manifest.write_text(json.dumps(value), encoding="utf-8")
        identity_file = self.package / "runtime-identity.json"
        identity = json.loads(identity_file.read_text(encoding="utf-8"))
        identity["run_manifest_sha256"] = import_exact_target_evidence.hashlib.sha256(manifest.read_bytes()).hexdigest()
        identity_file.write_text(json.dumps(identity), encoding="utf-8")
        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "invalid run manifest"):
            import_exact_target_evidence.validate_package(self.repo, self.package)

    def test_hash_tamper_is_rejected_before_any_write(self):
        path = self.package / "execution-evidence.json"
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "digest mismatch"):
            import_exact_target_evidence.validate_package(self.repo, self.package)
        self.assertFalse((self.repo / "evals" / "exact-target-runs" / "copilot-123-1.json").exists())
        self.assertFalse((self.repo / "evals" / "exact-target-runs" / "copilot-123-1.identity.json").exists())

    def test_carrier_drift_is_rejected(self):
        self._write("notes.txt", "carrier moved\n")
        self._commit("move carrier")
        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "invalid or drifted frozen release carrier"):
            import_exact_target_evidence.validate_package(self.repo, self.package)

    def test_existing_any_destination_prevents_import(self):
        result = import_exact_target_evidence.import_package(self.repo, self.package)
        self.assertTrue((self.repo / result["identity_destination"]).exists())
        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "destination already exists"):
            import_exact_target_evidence.validate_package(self.repo, self.package)

    def test_runtime_identity_rejects_unknown_fields(self):
        identity_path = self.package / "runtime-identity.json"
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
        identity["unexpected"] = True
        identity_path.write_text(json.dumps(identity), encoding="utf-8")
        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "fields mismatch"):
            import_exact_target_evidence.validate_package(self.repo, self.package)

    def test_runtime_identity_rejects_invalid_cli_integrity(self):
        identity_path = self.package / "runtime-identity.json"
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
        identity["requested_cli_integrity"] = "sha256-not-allowed"
        identity_path.write_text(json.dumps(identity), encoding="utf-8")
        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "sha512"):
            import_exact_target_evidence.validate_package(self.repo, self.package)

    def test_runtime_identity_integrity_must_match_manifest_provenance(self):
        identity_path = self.package / "runtime-identity.json"
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
        identity["requested_cli_integrity"] = OTHER_CLI_INTEGRITY
        identity_path.write_text(json.dumps(identity), encoding="utf-8")
        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "runtime identity evidence"):
            import_exact_target_evidence.validate_package(self.repo, self.package)

    def test_runtime_identity_run_attempt_must_match_manifest_provenance(self):
        identity_path = self.package / "runtime-identity.json"
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
        identity["github_run_attempt"] = 2
        identity_path.write_text(json.dumps(identity), encoding="utf-8")
        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "runtime identity evidence"):
            import_exact_target_evidence.validate_package(self.repo, self.package)

    def test_runtime_identity_destination_must_be_derived_from_manifest(self):
        identity_path = self.package / "runtime-identity.json"
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
        identity["runtime_identity_path"] = "evals/exact-target-runs/other.identity.json"
        identity_path.write_text(json.dumps(identity), encoding="utf-8")
        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "must equal"):
            import_exact_target_evidence.validate_package(self.repo, self.package)

    def test_exclusive_write_set_rolls_back_prior_reservations_if_later_destination_exists(self):
        scratch = Path(self.tmp.name) / "write-set-existing"
        sources = [scratch / f"source-{index}" for index in range(3)]
        destinations = [scratch / "dest" / f"{index}.json" for index in range(3)]
        scratch.mkdir(parents=True)
        for index, source in enumerate(sources):
            source.write_bytes(str(index).encode())
        destinations[2].parent.mkdir(parents=True)
        destinations[2].write_bytes(b"existing")

        with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "already exists"):
            import_exact_target_evidence._exclusive_write_set(tuple(zip(sources, destinations)))

        self.assertFalse(destinations[0].exists())
        self.assertFalse(destinations[1].exists())
        self.assertEqual(destinations[2].read_bytes(), b"existing")

    def test_exclusive_write_set_rolls_back_all_three_on_source_failure(self):
        scratch = Path(self.tmp.name) / "write-set-failure"
        sources = [scratch / f"source-{index}" for index in range(3)]
        destinations = [scratch / "dest" / f"{index}.json" for index in range(3)]
        scratch.mkdir(parents=True)
        for index, source in enumerate(sources):
            source.write_bytes(str(index).encode())
        original_read_bytes = Path.read_bytes

        def failing_read(path):
            if path == sources[2]:
                raise OSError("simulated third-source failure")
            return original_read_bytes(path)

        with mock.patch.object(Path, "read_bytes", failing_read):
            with self.assertRaisesRegex(import_exact_target_evidence.ExactTargetImportError, "rolled back"):
                import_exact_target_evidence._exclusive_write_set(tuple(zip(sources, destinations)))

        self.assertTrue(all(not destination.exists() for destination in destinations))


if __name__ == "__main__":
    unittest.main()
