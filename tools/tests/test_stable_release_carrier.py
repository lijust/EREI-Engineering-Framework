import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import stable_release_carrier as mod


class StableReleaseCarrierTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "user.name", "EREI Test")
        self._write("README.md", "target\n")
        self._write(mod.RELEASE_SCOPE_MANIFEST, {
            "schema_version": 1,
            "scope_id": "test-v2-scope",
            "status": "approved",
            "release_family": "test-v2",
            "target_baseline": "vnext-assurance-v2",
            "capabilities": [{"name": "assurance", "version": "stable-v2"}],
            "release_control_dependencies": [],
            "required_eval_suites": [{
                "path": "evals/cases/test.eval.json",
                "suite_id": "test-v1",
                "covers": ["assurance"],
            }],
            "excluded_candidate_capabilities": ["learning_to_development"],
            "post_promotion_gates": ["project_framework_pin_upgrade"],
            "rationale": "Test scope bound into the immutable target before release closure.",
        })
        self.target = self._commit("target")
        self.target_tree = self._git("rev-parse", f"{self.target}^{{tree}}")

    def tearDown(self):
        self.tmp.cleanup()

    def _git(self, *args):
        proc = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            self.fail(f"git {' '.join(args)} failed: {proc.stderr}")
        return proc.stdout.strip()

    def _write(self, path, value):
        full = self.repo / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(value if isinstance(value, str) else json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def _commit(self, message):
        self._git("add", "-A")
        self._git("commit", "-q", "-m", message)
        return self._git("rev-parse", "HEAD")

    def _target_manifest(self):
        return {
            "schema_version": 1,
            "target_id": "vnext-rc9",
            "status": "frozen_candidate",
            "framework_ref": self.target,
            "target_tree": self.target_tree,
            "selected_at": "2026-09-07T12:00:00Z",
            "source_branch": "main",
            "assurance": {
                "workflow": "Framework Assurance Gate",
                "run_id": 123,
                "event": "push",
                "conclusion": "success",
            },
            "stable_baseline": {
                "baseline": "task-learning-review-v1",
                "framework_ref": mod.LEGACY_STABLE_REF,
            },
            "promotion_authorized": False,
        }

    def _approval(self, approval_type, *, decision="approved", rationale_suffix=""):
        architecture = approval_type == "architecture"
        return {
            "schema_version": 2,
            "approval_id": "EAPP-20260907T120100Z-A1B2C3D4" if architecture else "EAPP-20260907T120200Z-E5F6A7B8",
            "approval_type": approval_type,
            "target_framework_ref": self.target,
            "target_tree": self.target_tree,
            "decision": decision,
            "recorded_at": "2026-09-07T12:01:00Z" if architecture else "2026-09-07T12:02:00Z",
            "reviewer": (
                {"kind": "github_user", "id": "lijust"}
                if architecture
                else {"kind": "external_reviewer", "id": "chatgpt-codex-connector"}
            ),
            "evidence": ["github-actions:123", "release-target:vnext-rc9"],
            "rationale": f"Reviewed immutable target for {approval_type} Stable promotion{rationale_suffix}.",
            "provenance": {
                "kind": "github_owner_approval_comment" if architecture else "github_codex_clean_security_review",
                "pr_number": 61 if architecture else 62,
                "actor_login": "lijust" if architecture else "chatgpt-codex-connector",
            },
        }

    def _build_v2_carrier(
        self,
        *,
        behavior_drift=False,
        rewrite_target=False,
        rewrite_architecture=False,
        rejected_security=False,
        wrong_architecture_ref=False,
        extra_excluded_capability=False,
        wrong_baseline=False,
    ):
        self._write(mod.TARGET_MANIFEST, self._target_manifest())
        self._commit("freeze target")
        if rewrite_target:
            target = self._target_manifest()
            target["selected_at"] = "2026-09-07T12:01:00Z"
            self._write(mod.TARGET_MANIFEST, target)
            self._commit("rewrite target")
        self._write("releases/approvals/architecture.json", self._approval("architecture"))
        approval_ref = self._commit("architecture approval")
        if rewrite_architecture:
            self._write(
                "releases/approvals/architecture.json",
                self._approval("architecture", rationale_suffix=" after rewrite"),
            )
            self._commit("rewrite architecture approval")
        self._write(
            "releases/approvals/security.json",
            self._approval("security", decision="rejected" if rejected_security else "approved"),
        )
        security_ref = self._commit("security approval")
        if behavior_drift:
            self._write("tools/forbidden-drift.txt", "drift\n")
            self._commit("forbidden behavior drift")
        stable = {
            "schema_version": 1,
            "assurance_contract_version": 2,
            "release_id": "vnext-assurance-v2",
            "baseline": "wrong-baseline" if wrong_baseline else "vnext-assurance-v2",
            "status": "stable",
            "framework_ref": self.target,
            "released_at": "2026-09-07T12:03:00Z",
            "capabilities": {
                "assurance": "stable-v2",
                **({"learning_to_development": "candidate-v1"} if extra_excluded_capability else {}),
            },
            "notes": "test carrier",
            "approval_ref": security_ref if wrong_architecture_ref else approval_ref,
            "security_review_ref": security_ref,
            "minimum_eval_assurance_level": "exact_target_runtime",
            "behavioral_eval_evidence": "evals/EXECUTION_EVIDENCE.vnext-rc9.json",
            "prospective_learning_cycle": {
                "capture_ref": "capture",
                "review_ref": "review",
                "feedback_ref": "feedback",
                "improvement_ref": "improvement",
                "adoption_ref": "adoption",
                "measured_outcome_ref": "outcome",
            },
        }
        self._write(mod.V2_STABLE_MANIFEST, stable)
        carrier = self._commit("stable manifest")
        return carrier

    def test_v1_is_grandfathered_only_for_exact_last_stable(self):
        manifest = {
            "schema_version": 1,
            "assurance_contract_version": 1,
            "release_id": mod.LEGACY_STABLE_ID,
            "baseline": mod.LEGACY_STABLE_ID,
            "status": "stable",
            "framework_ref": "f" * 40,
            "released_at": "2026-09-01T00:00:00Z",
            "capabilities": {"x": "stable"},
            "notes": "forged",
        }
        with self.assertRaisesRegex(mod.StableCarrierError, "grandfathered only"):
            mod._validate_legacy(mod.LEGACY_MANIFEST, manifest, "f" * 40)

    def test_valid_v2_structure_reaches_full_release_assurance(self):
        carrier = self._build_v2_carrier()
        fake_result = {
            "status": "stable",
            "framework_ref": self.target,
            "exact_target_bindings_validated": 44,
            "approval_records_validated": 2,
        }
        with mock.patch.object(mod.release_assurance, "validate_manifest", return_value=fake_result) as validate:
            result = mod.verify_stable_release_carrier(self.repo, self.target, carrier)
        self.assertEqual(result["status"], "verified_stable_release_carrier")
        self.assertEqual(result["framework_ref"], self.target)
        self.assertEqual(result["carrier_ref"], carrier)
        self.assertEqual(result["assurance_contract_version"], 2)
        self.assertFalse(result["grandfathered_v1"])
        self.assertIn(mod.TARGET_MANIFEST, result["closure_changed_paths"])
        self.assertIn(mod.V2_STABLE_MANIFEST, result["closure_changed_paths"])
        validate.assert_called_once()
        _, kwargs = validate.call_args
        self.assertTrue(Path(kwargs["scope_git_repo"]).samefile(self.repo))
        self.assertEqual(kwargs["scope_closure_ref"], carrier)
        self.assertNotEqual(kwargs["repo_root"], kwargs["scope_git_repo"])

    def test_scope_excluded_capability_blocks_before_release_assurance(self):
        carrier = self._build_v2_carrier(extra_excluded_capability=True)
        with mock.patch.object(mod.release_assurance, "validate_manifest") as validate:
            with self.assertRaisesRegex(mod.StableCarrierError, "violates frozen release scope"):
                mod.verify_stable_release_carrier(self.repo, self.target, carrier)
        validate.assert_not_called()

    def test_scope_baseline_mismatch_blocks_before_release_assurance(self):
        carrier = self._build_v2_carrier(wrong_baseline=True)
        with mock.patch.object(mod.release_assurance, "validate_manifest") as validate:
            with self.assertRaisesRegex(mod.StableCarrierError, "violates frozen release scope"):
                mod.verify_stable_release_carrier(self.repo, self.target, carrier)
        validate.assert_not_called()

    def test_behavior_drift_in_v2_carrier_fails_before_assurance(self):
        carrier = self._build_v2_carrier(behavior_drift=True)
        with mock.patch.object(mod.release_assurance, "validate_manifest") as validate:
            with self.assertRaisesRegex(mod.StableCarrierError, "behavior/governance drift"):
                mod.verify_stable_release_carrier(self.repo, self.target, carrier)
        validate.assert_not_called()

    def test_rewritten_frozen_target_fails(self):
        carrier = self._build_v2_carrier(rewrite_target=True)
        with mock.patch.object(mod.release_assurance, "validate_manifest") as validate:
            with self.assertRaisesRegex(mod.StableCarrierError, "changed after its first post-freeze write"):
                mod.verify_stable_release_carrier(self.repo, self.target, carrier)
        validate.assert_not_called()

    def test_rewritten_approval_record_fails_before_assurance(self):
        carrier = self._build_v2_carrier(rewrite_architecture=True)
        with mock.patch.object(mod.release_assurance, "validate_manifest") as validate:
            with self.assertRaisesRegex(mod.StableCarrierError, "changed after its first post-freeze write"):
                mod.verify_stable_release_carrier(self.repo, self.target, carrier)
        validate.assert_not_called()

    def test_rejected_security_approval_fails_before_assurance(self):
        carrier = self._build_v2_carrier(rejected_security=True)
        with mock.patch.object(mod.release_assurance, "validate_manifest") as validate:
            with self.assertRaisesRegex(mod.StableCarrierError, "invalid security approval record"):
                mod.verify_stable_release_carrier(self.repo, self.target, carrier)
        validate.assert_not_called()

    def test_sha_shaped_but_non_first_write_approval_ref_fails(self):
        carrier = self._build_v2_carrier(wrong_architecture_ref=True)
        with mock.patch.object(mod.release_assurance, "validate_manifest") as validate:
            with self.assertRaisesRegex(mod.StableCarrierError, "must equal the first commit"):
                mod.verify_stable_release_carrier(self.repo, self.target, carrier)
        validate.assert_not_called()

    def test_carrier_ref_must_be_exact_commit(self):
        with self.assertRaisesRegex(mod.StableCarrierError, "exact 40-character"):
            mod.verify_stable_release_carrier(self.repo, self.target, "HEAD")

    def test_target_must_be_ancestor_of_carrier(self):
        self._git("checkout", "-q", "--detach", self.target)
        self._write("other.txt", "other\n")
        other = self._commit("other")
        self._git("checkout", "-q", "--detach", self.target)
        self._write("releases/fake.json", {
            "schema_version": 1,
            "assurance_contract_version": 2,
            "release_id": "fake",
            "baseline": "fake",
            "status": "stable",
            "framework_ref": other,
            "released_at": "2026-09-07T00:00:00Z",
            "capabilities": {"x": "stable"},
            "notes": "fake",
        })
        carrier = self._commit("unrelated carrier")
        with self.assertRaisesRegex(mod.StableCarrierError, "must be an ancestor"):
            mod.verify_stable_release_carrier(self.repo, other, carrier)


if __name__ == "__main__":
    unittest.main()
