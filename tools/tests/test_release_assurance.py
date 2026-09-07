import json
import tempfile
import unittest
from pathlib import Path

from tools import release_assurance


class ReleaseAssuranceTests(unittest.TestCase):
    def base(self, **overrides):
        value = {
            "schema_version": 1,
            "assurance_contract_version": 2,
            "release_id": "vnext",
            "baseline": "vnext",
            "status": "candidate",
            "framework_ref": "a" * 40,
            "released_at": "2026-09-07T02:30:00Z",
            "capabilities": {"hardening": "candidate"},
            "notes": "Candidate assurance release.",
            "stable_blockers": ["prospective cycle pending"],
        }
        value.update(overrides)
        return value

    def stable(self, **overrides):
        value = self.base(
            status="stable",
            approval_ref="b" * 40,
            security_review_ref="c" * 40,
            minimum_eval_assurance_level="exact_target_runtime",
            behavioral_eval_evidence="evals/evidence.json",
            prospective_learning_cycle={
                "capture_ref": "capture",
                "review_ref": "review",
                "feedback_ref": "feedback",
                "improvement_ref": "improvement",
                "adoption_ref": "adoption",
                "measured_outcome_ref": "outcome",
            },
        )
        value.pop("stable_blockers", None)
        value.update(overrides)
        return value

    def enforcement(self, *, equivalent=False):
        return {
            "schema_version": 1,
            "repository": "lijust/EREI-Engineering-Framework",
            "main_branch": "main",
            "status": "enforced" if equivalent else "candidate_control",
            "server_enforcement": {
                "branch_protection_enabled": False,
                "required_status_checks_enforced": False,
                "source": "test",
            },
            "fallback": {
                "mode": "controlled_release_v2",
                "required_workflow": "Framework Assurance Gate",
                "release_branch_prefix": "release/",
                "exact_candidate_sha_required": True,
                "release_assurance_contract_version": 2,
                "architecture_approval_required": True,
                "security_approval_required": True,
                "exact_target_runtime_evidence_required": True,
                "complete_prospective_cycle_required": True,
                "equivalent_enforcement_verified": equivalent,
                "stable_promotion_policy": "blocked_until_server_or_equivalent_enforcement",
            },
            "evidence": ["test-evidence"],
            "limitations": ["test limitation"],
        }

    def test_candidate_requires_explicit_stable_blockers(self):
        value = self.base()
        del value["stable_blockers"]
        with self.assertRaisesRegex(release_assurance.ReleaseError, "stable_blockers"):
            release_assurance.validate_manifest(value)

    def test_candidate_with_blockers_is_valid(self):
        result = release_assurance.validate_manifest(self.base())
        self.assertEqual(result["status"], "candidate")
        self.assertFalse(result["next_stable_gate_applied"])
        self.assertIsNone(result["stable_enforcement_satisfied"])

    def test_v2_stable_requires_exact_target_runtime_level(self):
        value = self.stable(minimum_eval_assurance_level="reference_contract")
        with self.assertRaisesRegex(release_assurance.ReleaseError, "exact_target_runtime"):
            release_assurance.validate_manifest(value)

    def test_v2_stable_fails_before_eval_when_enforcement_is_not_satisfied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "security").mkdir()
            (root / "security" / "ASSURANCE_ENFORCEMENT.json").write_text(
                json.dumps(self.enforcement(equivalent=False)), encoding="utf-8"
            )
            with self.assertRaisesRegex(release_assurance.ReleaseError, "server branch/status-check enforcement"):
                release_assurance.validate_manifest(self.stable(), repo_root=root)

    def test_v2_stable_reaches_eval_gate_when_equivalent_enforcement_is_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "security").mkdir()
            (root / "security" / "ASSURANCE_ENFORCEMENT.json").write_text(
                json.dumps(self.enforcement(equivalent=True)), encoding="utf-8"
            )
            with self.assertRaises((FileNotFoundError, release_assurance.ReleaseError)):
                release_assurance.validate_manifest(self.stable(), repo_root=root)


if __name__ == "__main__":
    unittest.main()
