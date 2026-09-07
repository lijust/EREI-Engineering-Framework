import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools import release_target


class ReleaseTargetTests(unittest.TestCase):
    def manifest(self, target_ref="a" * 40, target_tree="b" * 40):
        return {
            "schema_version": 1,
            "target_id": "vnext-rc1",
            "status": "frozen_candidate",
            "framework_ref": target_ref,
            "target_tree": target_tree,
            "selected_at": "2026-09-07T12:10:00Z",
            "source_branch": "main",
            "assurance": {
                "workflow": "Framework Assurance Gate",
                "run_id": 123,
                "event": "push",
                "conclusion": "success",
            },
            "stable_baseline": {
                "baseline": "task-learning-review-v1",
                "framework_ref": "6" * 40,
            },
            "promotion_authorized": False,
        }

    def git(self, root: Path, *args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

    def setup_repo(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        subprocess.check_call(["git", "init", "-b", "main"], cwd=root, stdout=subprocess.DEVNULL)
        self.git(root, "config", "user.email", "test@example.com")
        self.git(root, "config", "user.name", "Test")
        (root / "CAPABILITIES.json").write_text(json.dumps({
            "stable_release": {
                "baseline": "task-learning-review-v1",
                "framework_ref": "6" * 40,
            }
        }), encoding="utf-8")
        (root / "code.txt").write_text("candidate\n", encoding="utf-8")
        self.git(root, "add", ".")
        self.git(root, "commit", "-m", "candidate")
        target_ref = self.git(root, "rev-parse", "HEAD")
        target_tree = self.git(root, "rev-parse", "HEAD^{tree}")
        manifest = self.manifest(target_ref, target_tree)
        target_path = root / "releases" / "VNEXT_TARGET.json"
        target_path.parent.mkdir(parents=True)
        target_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
        self.git(root, "add", ".")
        self.git(root, "commit", "-m", "select target")
        return temp, root, manifest

    def test_manifest_rejects_boolean_run_id(self):
        value = self.manifest()
        value["assurance"]["run_id"] = True
        with self.assertRaises(release_target.ReleaseTargetError):
            release_target.validate_manifest_shape(value)

    def test_manifest_rejects_unknown_field(self):
        value = self.manifest()
        value["extra"] = "no"
        with self.assertRaises(release_target.ReleaseTargetError):
            release_target.validate_manifest_shape(value)

    def test_fixed_closure_allowlist(self):
        self.assertTrue(release_target.allowed_closure_path("releases/VNEXT_TARGET.json"))
        self.assertTrue(release_target.allowed_closure_path("evals/exact-target-runs/run.json"))
        self.assertTrue(release_target.allowed_closure_path("evals/EXECUTION_EVIDENCE.ETR-1.json"))
        self.assertTrue(release_target.allowed_closure_path("releases/approvals/security.json"))
        self.assertTrue(release_target.allowed_closure_path("security/ASSURANCE_ENFORCEMENT.json"))
        self.assertFalse(release_target.allowed_closure_path("tools/release_target.py"))
        self.assertFalse(release_target.allowed_closure_path("evals/cases/impact-analysis.eval.json"))
        self.assertFalse(release_target.allowed_closure_path("CAPABILITIES.json"))

    def test_target_selection_closure_is_valid(self):
        temp, root, _ = self.setup_repo()
        try:
            manifest = release_target.load_and_validate_target(root)
            result = release_target.validate_closure(root, manifest)
            self.assertEqual(result["changed_paths"], ["releases/VNEXT_TARGET.json"])
        finally:
            temp.cleanup()

    def test_behavior_drift_after_freeze_fails_closed(self):
        temp, root, _ = self.setup_repo()
        try:
            (root / "tools").mkdir()
            (root / "tools" / "drift.py").write_text("print('drift')\n", encoding="utf-8")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "behavior drift")
            manifest = release_target.load_and_validate_target(root)
            with self.assertRaisesRegex(release_target.ReleaseTargetError, "outside the fixed allowlist"):
                release_target.validate_closure(root, manifest)
        finally:
            temp.cleanup()

    def test_rewriting_first_closure_artifact_fails(self):
        temp, root, manifest = self.setup_repo()
        try:
            manifest["assurance"]["run_id"] = 124
            (root / "releases" / "VNEXT_TARGET.json").write_text(
                json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8"
            )
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", "rewrite target")
            current = release_target.load_and_validate_target(root)
            with self.assertRaisesRegex(release_target.ReleaseTargetError, "changed after its first post-freeze write"):
                release_target.validate_closure(root, current)
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
