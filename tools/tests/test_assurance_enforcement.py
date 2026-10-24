import unittest

from tools import assurance_enforcement


class AssuranceEnforcementTests(unittest.TestCase):
    def base(self, **overrides):
        value = {
            "schema_version": 2,
            "repository": "lijust/EREI-Engineering-Framework",
            "main_branch": "main",
            "status": "candidate_control",
            "server_enforcement": {
                "branch_protection_enabled": False,
                "required_status_checks_enforced": False,
                "source": "github-api-branch-metadata",
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
                "equivalent_enforcement_verified": False,
                "equivalence_target_ref": None,
                "review_provenance": None,
                "stable_promotion_policy": "blocked_until_server_or_equivalent_enforcement",
            },
            "evidence": ["github-branch:main protected=false"],
            "limitations": ["CI cannot prevent a direct write to an unprotected main branch."],
        }
        value.update(overrides)
        return value

    def test_candidate_control_truth_is_valid_but_not_stable_equivalent(self):
        result = assurance_enforcement.validate_enforcement(self.base())
        self.assertFalse(result["server_enforcement_satisfied"])
        self.assertFalse(result["fallback_equivalent_verified"])
        self.assertFalse(result["stable_enforcement_satisfied"])

    def test_enforced_status_fails_without_real_or_verified_equivalent_enforcement(self):
        with self.assertRaisesRegex(assurance_enforcement.EnforcementError, "status=enforced"):
            assurance_enforcement.validate_enforcement(self.base(status="enforced"))

    def test_declared_equivalence_is_shape_valid_but_not_effective_proof(self):
        value = self.base(status="enforced")
        value["fallback"] = {
            **value["fallback"],
            "equivalent_enforcement_verified": True,
            "equivalence_target_ref": "a" * 40,
            "review_provenance": {
                "provider": "github_codex_review",
                "reviewer_login": "chatgpt-codex-connector[bot]",
                "review_type": "security_review",
                "purpose": "enforcement_equivalence",
            },
        }
        result = assurance_enforcement.validate_enforcement(value, expected_target="a" * 40)
        self.assertTrue(result["stable_enforcement_satisfied"])
        self.assertTrue(result["fallback_equivalent_verified"])

    def test_verified_equivalence_is_target_bound(self):
        value = self.base(status="enforced")
        value["fallback"] = {
            **value["fallback"],
            "equivalent_enforcement_verified": True,
            "equivalence_target_ref": "a" * 40,
            "review_provenance": {
                "provider": "github_codex_review",
                "reviewer_login": "chatgpt-codex-connector[bot]",
                "review_type": "security_review",
                "purpose": "enforcement_equivalence",
            },
        }
        with self.assertRaisesRegex(assurance_enforcement.EnforcementError, "target mismatch"):
            assurance_enforcement.validate_enforcement(value, expected_target="b" * 40)

    def test_unverified_equivalence_cannot_carry_target_or_review(self):
        value = self.base()
        value["fallback"] = {**value["fallback"], "equivalence_target_ref": "a" * 40}
        with self.assertRaisesRegex(assurance_enforcement.EnforcementError, "must be null"):
            assurance_enforcement.validate_enforcement(value)

    def test_boolean_fields_reject_integer_aliases(self):
        value = self.base()
        value["fallback"] = {**value["fallback"], "exact_candidate_sha_required": 1}
        with self.assertRaisesRegex(assurance_enforcement.EnforcementError, "must be boolean"):
            assurance_enforcement.validate_enforcement(value)

    def test_unknown_fields_fail_closed(self):
        value = self.base(extra="nope")
        with self.assertRaisesRegex(assurance_enforcement.EnforcementError, "unknown fields"):
            assurance_enforcement.validate_enforcement(value)


if __name__ == "__main__":
    unittest.main()
