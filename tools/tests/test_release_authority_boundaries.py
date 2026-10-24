"""Reviews authenticate evidence; they are not release authority."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import assurance_enforcement as enforcement, release_approval, release_assurance
from tools.tests import test_release_assurance as release_fixtures
from tools.tests import test_assurance_enforcement as fixtures


class AuthorityBoundaryTests(unittest.TestCase):
    def asserted_fallback(self):
        record = fixtures.AssuranceEnforcementTests().base(status="enforced")
        record["fallback"].update(
            equivalent_enforcement_verified=True,
            equivalence_target_ref="a" * 40,
            review_provenance={
                "provider": "github_codex_review",
                "reviewer_login": "chatgpt-codex-connector[bot]",
                "review_type": "security_review",
                "purpose": "enforcement_equivalence",
            },
        )
        return record

    def test_authenticated_clean_review_is_not_effective_enforcement(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            enforcement.github_review_provenance, "verify_artifact_review",
            return_value={"status": "verified", "pull_request_number": 77},
        ):
            result = enforcement.verify_authenticated_equivalence(
                Path(directory), self.asserted_fallback(), expected_target="a" * 40
            )
            self.assertEqual(result["status"], "authenticated_review_only")
            self.assertFalse(result["authority_verified"])
            with self.assertRaisesRegex(enforcement.EnforcementError, "review.*does not establish"):
                enforcement.verify_effective_enforcement(
                    Path(directory), self.asserted_fallback(), expected_target="a" * 40
                )

    def test_claimed_verified_status_from_review_cannot_grant_fallback(self):
        with mock.patch.object(enforcement, "verify_authenticated_equivalence",
                               return_value={"status": "verified"}):
            with self.assertRaisesRegex(enforcement.EnforcementError, "review.*does not establish"):
                enforcement.verify_effective_enforcement(
                    Path("."), self.asserted_fallback(), expected_target="a" * 40
                )

    def test_role_labels_do_not_create_two_independent_principals(self):
        records = [{"reviewer": {"kind": "framework_role", "id": role},
                    "review_provenance": {"reviewer_login": "same-review-bot"}}
                   for role in ("architect", "security")]
        with self.assertRaisesRegex(release_approval.ReleaseApprovalError, "independent principals"):
            release_approval.verify_approval_authority(records)

    def test_release_gate_rejects_two_authenticated_reviews_without_authority(self):
        helper = release_fixtures.ReleaseAssuranceTests()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            helper.write_stable_root(root)
            with mock.patch.object(release_assurance.github_review_provenance,
                                   "verify_artifact_review", return_value={"status": "verified"}) as reviews:
                with self.assertRaisesRegex(release_assurance.ReleaseError, "independent principals"):
                    release_assurance._validate_structured_approvals(
                        helper.stable(), root, provenance_git_repo=root, provenance_closure_ref="HEAD"
                    )
                self.assertEqual(reviews.call_count, 2)

    def test_distinct_review_names_still_need_authority_verification(self):
        records = [{"reviewer": {"kind": "github_user", "id": actor},
                    "review_provenance": {"reviewer_login": actor}}
                   for actor in ("reviewer-one", "reviewer-two")]
        with self.assertRaisesRegex(release_approval.ReleaseApprovalError, "authority verifier is unavailable"):
            release_approval.verify_approval_authority(records)


if __name__ == "__main__":
    unittest.main()
