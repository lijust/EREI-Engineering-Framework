import copy
import unittest

from tools import release_approval as mod


class ReleaseApprovalTests(unittest.TestCase):
    def valid(self, approval_type="architecture"):
        return {
            "schema_version": 2,
            "approval_id": "EAPP-20260907T123000Z-A1B2C3D4",
            "approval_type": approval_type,
            "target_framework_ref": "a" * 40,
            "target_tree": "b" * 40,
            "decision": "approved",
            "recorded_at": "2026-09-07T12:30:00Z",
            "reviewer": {"kind": "framework_role", "id": "system-architect"},
            "review_provenance": {
                "provider": "github_codex_review",
                "reviewer_login": "chatgpt-codex-connector[bot]",
                "review_type": "code_review",
                "purpose": f"{approval_type}_approval",
            },
            "evidence": ["github-actions:123", "release-target:vnext-rc1"],
            "rationale": "Reviewed the immutable target and found the architecture acceptable for Stable promotion.",
        }

    def test_valid_approved_record(self):
        value = mod.validate_record(
            self.valid(),
            expected_type="architecture",
            expected_target="a" * 40,
            expected_tree="b" * 40,
            require_approved=True,
        )
        self.assertEqual(value["decision"], "approved")

    def test_unknown_field_fails_closed(self):
        value = self.valid()
        value["extra"] = True
        with self.assertRaisesRegex(mod.ReleaseApprovalError, "unknown fields"):
            mod.validate_record(value)

    def test_date_only_fails(self):
        value = self.valid()
        value["recorded_at"] = "2026-09-07"
        with self.assertRaisesRegex(mod.ReleaseApprovalError, "RFC3339"):
            mod.validate_record(value)

    def test_wrong_target_or_tree_fails(self):
        with self.assertRaisesRegex(mod.ReleaseApprovalError, "expected target"):
            mod.validate_record(self.valid(), expected_target="c" * 40)
        with self.assertRaisesRegex(mod.ReleaseApprovalError, "expected target tree"):
            mod.validate_record(self.valid(), expected_tree="c" * 40)

    def test_rejected_record_cannot_satisfy_stable(self):
        value = self.valid()
        value["decision"] = "rejected"
        with self.assertRaisesRegex(mod.ReleaseApprovalError, "not approved"):
            mod.validate_record(value, require_approved=True)

    def test_type_mismatch_fails(self):
        with self.assertRaisesRegex(mod.ReleaseApprovalError, "approval_type mismatch"):
            mod.validate_record(self.valid("security"), expected_type="architecture")

    def test_reviewer_shape_is_strict(self):
        value = self.valid()
        value["reviewer"]["extra"] = "x"
        with self.assertRaisesRegex(mod.ReleaseApprovalError, "exactly kind/id"):
            mod.validate_record(value)

    def test_review_provenance_is_required_and_purpose_bound(self):
        value = self.valid()
        del value["review_provenance"]
        with self.assertRaisesRegex(mod.ReleaseApprovalError, "missing fields"):
            mod.validate_record(value)

        value = self.valid()
        value["review_provenance"]["purpose"] = "security_approval"
        with self.assertRaisesRegex(mod.ReleaseApprovalError, "purpose mismatch"):
            mod.validate_record(value)

    def test_duplicate_evidence_fails(self):
        value = self.valid()
        value["evidence"] = ["same", "same"]
        with self.assertRaisesRegex(mod.ReleaseApprovalError, "unique"):
            mod.validate_record(value)


if __name__ == "__main__":
    unittest.main()
