"""No-provider git-backed source preflight regressions. Never use live project DB."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest import mock

from tools import core13_real_project_trial_preflight as checker

CURRENT = "a" * 40
OLDER = "b" * 40
UTC = datetime(2026, 10, 28, 7, 0, tzinfo=timezone.utc)
CAP = "learning_pattern_analysis"


class SourceOnlyPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.erei = self.root / ".erei"
        self.erei.mkdir()
        self.manifest = self.erei / "framework.json"
        self.adoption = self.erei / "CANDIDATE_CAPABILITIES.json"
        self.knowledge = self.erei / "knowledge"
        self.manifest_data = {
            "schema_version": 1, "framework": {
                "repository": "lijust/EREI-Engineering-Framework",
                "baseline": "task-learning-review-v1",
                "ref_type": "commit", "ref": OLDER,
            }, "project": {}, "overlays": [], "runtime_adapters": [],
        }
        self._save_manifest()
        self.git("init", "-q")
        self.git("config", "user.name", "Synthetic Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("add", ".erei/framework.json")
        self.git("commit", "-q", "-m", "Synthetic fixture: pinned older stable")
        self.ref = self.git("rev-parse", "HEAD")
        self.ref_before = self.ref

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.root, capture_output=True,
            text=True, check=True, timeout=10,
        ).stdout.strip()

    def _save_manifest(self):
        self.manifest.write_text(json.dumps(self.manifest_data), encoding="utf-8")

    def commit_fixture(self):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "Synthetic test revision")
        self.ref = self.git("rev-parse", "HEAD")

    def assess(self, sha=None):
        return checker.inspect_trial_admission(
            self.root, self.ref if sha is None else sha, CURRENT, now=UTC,
        )

    def _write_valid_adoption(self):
        self.adoption.write_text(json.dumps({
            "schema_version": 1, "framework_ref": CURRENT, "adoptions": [{
                "adoption_id": "CAD-20261028T060000Z-ABCDEF12",
                "capability": CAP, "version": "v1",
                "approved_at": "2026-10-28T06:00:00Z",
                "expires_at": "2026-10-29T06:00:00Z",
                "approved_by_role": "project_owner", "risk": "L2",
                "purpose": "Synthetic trial admission test for source pinning",
                "evidence": ["synthetic:explicit-approval"],
            }]
        }), encoding="utf-8")

    def test_real_immutable_old_pin_is_blocked_without_mutation(self):
        before = self.manifest.read_bytes()
        output = self.assess()
        self.assertEqual(output["status"], "BLOCKED")
        self.assertTrue(output["project_commit_verified"])
        self.assertIn("PROJECT_PIN_DIFFERS_FROM_CANDIDATE", output["blockers"])
        self.assertIn("CANDIDATE_ADOPTION_NOT_PRESENT_OR_INVALID", output["blockers"])
        self.assertIn("PROJECT_KNOWLEDGE_ARTIFACT_NOT_PRESENT", output["blockers"])
        self.assertFalse(output["admission_authorized"])
        self.assertFalse(output["real_project_trial_executed"])
        self.assertFalse(output["files_written"])
        self.assertEqual(self.manifest.read_bytes(), before)
        self.assertEqual(self.git("rev-parse", "HEAD"), self.ref_before)

    def test_wrong_expected_git_revision_rejected_before_project_reads(self):
        response = self.assess("f" * 40)
        self.assertEqual(response["blockers"], ["PROJECT_COMMIT_NOT_AT_EXPECTED_SHA"])
        self.assertFalse(response.get("project_commit_verified", False))

    def test_not_even_matching_pin_and_adoption_self_authorize(self):
        self.manifest_data["framework"]["ref"] = CURRENT
        self._save_manifest()
        self._write_valid_adoption()
        self.knowledge.mkdir()
        (self.knowledge / "approved.txt").write_text("synthetic knowledge", encoding="utf-8")
        self.commit_fixture()
        result = self.assess()
        self.assertEqual(result["blockers"], ["INDEPENDENT_TRIAL_AUTHORIZATION_NOT_ESTABLISHED"])
        self.assertFalse(result["admission_authorized"])
        self.assertFalse(result["knowledge_consumption_verified"])
        self.assertEqual(result["manifest_sha256"],
                         hashlib.sha256(self.manifest.read_bytes()).hexdigest())

    def test_stale_adoption_is_blocked_even_with_correct_pin(self):
        self.manifest_data["framework"]["ref"] = CURRENT
        self._save_manifest()
        self._write_valid_adoption()
        val = json.loads(self.adoption.read_text())
        val["adoptions"][0]["expires_at"] = "2026-10-28T06:30:00Z"
        self.adoption.write_text(json.dumps(val), encoding="utf-8")
        self.commit_fixture()
        output = self.assess()
        self.assertIn("NO_ACTIVE_MATCHING_CANDIDATE_ADOPTION", output["blockers"])

    def test_symlinked_external_manifest_is_never_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp) / "external-manifest.json"
            outside.write_text(json.dumps(self.manifest_data), encoding="utf-8")
            self.manifest.unlink()
            try:
                self.manifest.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            self.commit_fixture()
            result = self.assess()
            self.assertIn("PROJECT_MANIFEST_UNAVAILABLE", result["blockers"])
            self.assertIsNone(result["manifest_sha256"])

    def test_symlinked_knowledge_root_not_treated_as_project_knowledge(self):
        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp) / "external"
            other.mkdir()
            (other / "knowledge.txt").write_text("outside", encoding="utf-8")
            try:
                self.knowledge.symlink_to(other, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            self.commit_fixture()
            result = self.assess()
            self.assertIn("PROJECT_KNOWLEDGE_ARTIFACT_NOT_PRESENT", result["blockers"])

    def test_dirty_source_tree_denied_even_with_correct_git_head(self):
        self._write_valid_adoption()
        response = self.assess()
        self.assertEqual(response["blockers"], ["PROJECT_CHECKOUT_DIRTY"])
        self.assertFalse(response.get("project_commit_verified", False))
        self.adoption.unlink()
        self.manifest_data["framework"]["ref"] = CURRENT
        self._save_manifest()
        response2 = self.assess()
        self.assertEqual(response2["blockers"], ["PROJECT_CHECKOUT_DIRTY"])

    def test_cli_readonly_returns_blocked_with_exact_commit(self):
        cli = subprocess.run([
            sys.executable, "-m", "tools.core13_real_project_trial_preflight",
            "--project-root", str(self.root),
            "--project-sha", self.ref,
            "--framework-sha", CURRENT,
        ], cwd=Path(__file__).resolve().parents[2],
           capture_output=True, text=True, check=False, timeout=20)
        self.assertEqual(cli.returncode, 0, cli.stderr)
        obj = json.loads(cli.stdout)
        self.assertTrue(obj["project_commit_verified"])
        self.assertEqual(obj["status"], "BLOCKED")
        self.assertIn("PROJECT_PIN_DIFFERS_FROM_CANDIDATE", obj["blockers"])
        self.assertEqual(self.git("rev-parse", "HEAD"), self.ref_before)

    def test_cli_fail_closed_unrecognized_commit(self):
        cli = subprocess.run([
            sys.executable, "-m", "tools.core13_real_project_trial_preflight",
            "--project-root", str(self.root),
            "--project-sha", "f" * 40,
            "--framework-sha", CURRENT,
        ], cwd=Path(__file__).resolve().parents[2],
           capture_output=True, text=True, check=False, timeout=20)
        self.assertEqual(cli.returncode, 2)
        self.assertEqual(json.loads(cli.stdout)["blockers"],
                         ["PROJECT_COMMIT_NOT_AT_EXPECTED_SHA"])

    def test_invalid_clock_and_nonsha_deny(self):
        invalid = checker.inspect_trial_admission(
            self.root, self.ref, CURRENT, now=datetime(2026, 10, 28)
        )
        self.assertEqual(invalid["blockers"], ["INPUT_INVALID"])
        invalid2 = checker.inspect_trial_admission(
            self.root, self.ref, "main", now=UTC
        )
        self.assertEqual(invalid2["blockers"], ["INPUT_INVALID"])


if __name__ == "__main__":
    unittest.main()
