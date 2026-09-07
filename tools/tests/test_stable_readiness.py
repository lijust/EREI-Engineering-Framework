import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.stable_readiness import (
    StableReadinessError,
    _event_target_revision,
    approval_gate,
    derive_readiness,
)


class StableReadinessTests(unittest.TestCase):
    def test_current_shape_can_close_cycle_without_claiming_stable(self):
        result = derive_readiness(
            cycle_pass=True,
            eval_pass=False,
            enforcement_pass=False,
            approvals_pass=False,
        )
        self.assertFalse(result["ready_for_final_approvals"])
        self.assertFalse(result["stable_ready"])
        self.assertNotIn("prospective_cycle_incomplete", result["blockers"])
        self.assertIn("exact_target_runtime_evidence_incomplete", result["blockers"])
        self.assertIn("release_enforcement_not_satisfied", result["blockers"])

    def test_preapproval_requires_cycle_eval_and_enforcement(self):
        result = derive_readiness(
            cycle_pass=True,
            eval_pass=True,
            enforcement_pass=True,
            approvals_pass=False,
        )
        self.assertTrue(result["ready_for_final_approvals"])
        self.assertFalse(result["stable_ready"])
        self.assertEqual(result["blockers"], ["final_architecture_security_approvals_not_bound"])

    def test_all_four_gates_are_required_for_stable(self):
        result = derive_readiness(
            cycle_pass=True,
            eval_pass=True,
            enforcement_pass=True,
            approvals_pass=True,
        )
        self.assertTrue(result["ready_for_final_approvals"])
        self.assertTrue(result["stable_ready"])
        self.assertEqual(result["blockers"], [])

    def test_missing_cycle_blocks_preapproval(self):
        result = derive_readiness(
            cycle_pass=False,
            eval_pass=True,
            enforcement_pass=True,
            approvals_pass=False,
        )
        self.assertFalse(result["ready_for_final_approvals"])
        self.assertIn("prospective_cycle_incomplete", result["blockers"])

    def test_pull_request_event_resolves_head_sha_not_synthetic_merge_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            path.write_text(json.dumps({
                "pull_request": {
                    "head": {"sha": "a" * 40},
                }
            }), encoding="utf-8")
            self.assertEqual(_event_target_revision(path), "a" * 40)

    def test_non_pull_request_event_has_no_event_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            path.write_text(json.dumps({"ref": "refs/heads/main"}), encoding="utf-8")
            self.assertIsNone(_event_target_revision(path))

    def test_malformed_pull_request_head_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            path.write_text(json.dumps({"pull_request": {"head": {"sha": "main"}}}), encoding="utf-8")
            with self.assertRaises(StableReadinessError):
                _event_target_revision(path)


class StructuredApprovalReadinessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "user.name", "EREI Test")
        self._write("README.md", "target\n")
        self.target = self._commit("target")
        self.target_tree = self._git("rev-parse", f"{self.target}^{{tree}}")

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

    def _approval(self, approval_type, *, decision="approved", rationale_suffix=""):
        architecture = approval_type == "architecture"
        return {
            "schema_version": 1,
            "approval_id": "EAPP-20260907T130000Z-A1B2C3D4" if architecture else "EAPP-20260907T130100Z-E5F6A7B8",
            "approval_type": approval_type,
            "target_framework_ref": self.target,
            "target_tree": self.target_tree,
            "decision": decision,
            "recorded_at": "2026-09-07T13:00:00Z" if architecture else "2026-09-07T13:01:00Z",
            "reviewer": {
                "kind": "framework_role",
                "id": "system-architect" if architecture else "security-engineer",
            },
            "evidence": ["github-actions:123", "release-target:vnext-rc1"],
            "rationale": f"Reviewed immutable target for {approval_type} Stable promotion{rationale_suffix}.",
        }

    def _build(self, *, rejected_security=False, wrong_arch_ref=False, rewrite_architecture=False):
        self._write("releases/approvals/architecture.json", self._approval("architecture"))
        architecture_ref = self._commit("architecture approval")
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
        stable = {
            "schema_version": 1,
            "assurance_contract_version": 2,
            "release_id": "vnext-assurance-v2",
            "baseline": "vnext-assurance-v2",
            "status": "stable",
            "framework_ref": self.target,
            "released_at": "2026-09-07T13:02:00Z",
            "capabilities": {"assurance": "stable-v2"},
            "notes": "structured approval readiness test",
            "approval_ref": security_ref if wrong_arch_ref else architecture_ref,
            "security_review_ref": security_ref,
        }
        self._write("releases/vnext-assurance-v2-stable.json", stable)
        self._commit("stable manifest")
        return architecture_ref, security_ref

    def test_structured_approved_records_pass_readiness_gate(self):
        architecture_ref, security_ref = self._build()
        result = approval_gate(self.repo, self.target, True)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["validated_records"], 2)
        self.assertEqual(result["approvals"]["architecture"]["bound_ref"], architecture_ref)
        self.assertEqual(result["approvals"]["security"]["bound_ref"], security_ref)

    def test_rejected_security_record_blocks(self):
        self._build(rejected_security=True)
        result = approval_gate(self.repo, self.target, True)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("security approval invalid", result["reason"])

    def test_sha_shaped_but_wrong_approval_ref_blocks(self):
        self._build(wrong_arch_ref=True)
        result = approval_gate(self.repo, self.target, True)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("must equal first post-target write", result["reason"])

    def test_rewritten_approval_record_blocks(self):
        self._build(rewrite_architecture=True)
        result = approval_gate(self.repo, self.target, True)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("changed after its bound approval ref", result["reason"])

    def test_no_manifest_remains_pending_only_after_preapproval(self):
        self.assertEqual(approval_gate(self.repo, self.target, True)["status"], "pending")
        self.assertEqual(approval_gate(self.repo, self.target, False)["status"], "deferred")


if __name__ == "__main__":
    unittest.main()
