"""Fail-closed regression tests for authenticated GitHub server enforcement."""
import unittest
from unittest import mock

from tools import assurance_enforcement


def record():
    return {
        "schema_version": 2,
        "repository": "lijust/EREI-Engineering-Framework",
        "main_branch": "main",
        "status": "enforced",
        "server_enforcement": {
            "branch_protection_enabled": True,
            "required_status_checks_enforced": True,
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
        "evidence": ["declaration is not proof"],
        "limitations": ["server checks still require live verification"],
    }


def responses():
    return [
        {"protected": True},
        {
            "enforce_admins": {"enabled": True},
            "required_status_checks": {
                "strict": True,
                "checks": [{"context": "assurance", "app_id": 15368}],
            },
            "required_pull_request_reviews": {
                "required_approving_review_count": 1,
                "dismiss_stale_reviews": True,
                "bypass_pull_request_allowances": {"users": [], "teams": [], "apps": []},
            },
            "allow_force_pushes": {"enabled": False},
            "allow_deletions": {"enabled": False},
        },
    ]


class LiveServerEnforcementTests(unittest.TestCase):
    def verify(self, pair):
        with mock.patch.object(
            assurance_enforcement.github_review_provenance,
            "_github_json",
            side_effect=pair,
        ) as api:
            try:
                return assurance_enforcement.verify_live_server_enforcement(
                    record(), token="test-token"
                )
            finally:
                self.assertEqual(api.call_count, 2)

    def test_classic_protection_cannot_authenticate_mutable_workflow_identity(self):
        with self.assertRaisesRegex(assurance_enforcement.EnforcementError, "trusted assurance workflow identity"):
            self.verify(responses())

    def test_green_context_and_trusted_app_cannot_prove_workflow_code(self):
        # Simulates malicious PR changing assurance-gate.yml while retaining
        # the same status check name and GitHub Actions application identity.
        # GitHub's classic protection API returns the same valid-looking data.
        pair = responses()
        self.assertEqual(pair[1]["required_status_checks"]["checks"][0], {"context": "assurance", "app_id": 15368})
        with self.assertRaisesRegex(assurance_enforcement.EnforcementError, "server equivalence is blocked"):
            self.verify(pair)

    def test_server_only_promotion_rejects_even_fully_valid_classic_controls(self):
        with mock.patch.object(assurance_enforcement.github_review_provenance, "_github_json", side_effect=responses()):
            with self.assertRaisesRegex(assurance_enforcement.EnforcementError, "trusted assurance workflow identity"):
                assurance_enforcement.verify_effective_enforcement(
                    __import__("pathlib").Path("."), record(), expected_target="a" * 40, token="test-token"
                )

    def test_self_asserted_server_flags_rejected_without_authentication(self):
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "", "GH_TOKEN": ""}):
            with self.assertRaisesRegex(assurance_enforcement.EnforcementError, "authenticated GitHub"):
                assurance_enforcement.verify_live_server_enforcement(record())

    def test_live_unprotected_main_fails_even_when_record_claims_enforced(self):
        pair = responses()
        pair[0]["protected"] = False
        with self.assertRaisesRegex(assurance_enforcement.EnforcementError, "not live-protected"):
            self.verify(pair)

    def test_server_admin_bypass_is_rejected(self):
        pair = responses()
        pair[1]["enforce_admins"]["enabled"] = False
        with self.assertRaisesRegex(assurance_enforcement.EnforcementError, "administrators"):
            self.verify(pair)

    def test_server_must_require_workflow_job_bound_to_github_actions(self):
        for context, app in [("assurance", None), ("other", 15368), ("assurance", 1)]:
            with self.subTest(context=context, app=app):
                pair = responses()
                pair[1]["required_status_checks"]["checks"] = [
                    {"context": context, "app_id": app}
                ]
                with self.assertRaisesRegex(assurance_enforcement.EnforcementError, "not required"):
                    self.verify(pair)

    def test_non_strict_or_missing_required_reviews_are_rejected(self):
        cases = [
            ("strict", lambda p: p[1]["required_status_checks"].update(strict=False)),
            ("PR reviews", lambda p: p[1].update(required_pull_request_reviews=None)),
            ("stale reviews", lambda p: p[1]["required_pull_request_reviews"].update(dismiss_stale_reviews=False)),
        ]
        for name, mutate in cases:
            with self.subTest(name=name):
                pair = responses()
                mutate(pair)
                with self.assertRaises(assurance_enforcement.EnforcementError):
                    self.verify(pair)

    def test_explicit_bypass_or_force_push_fails_closed(self):
        for mutate in [
            lambda p: p[1]["required_pull_request_reviews"]["bypass_pull_request_allowances"]["users"].append({"login": "bypass"}),
            lambda p: p[1]["allow_force_pushes"].update(enabled=True),
            lambda p: p[1]["allow_deletions"].update(enabled=True),
        ]:
            pair = responses()
            mutate(pair)
            with self.assertRaises(assurance_enforcement.EnforcementError):
                self.verify(pair)


    def test_missing_or_malformed_pr_bypass_allowances_fail_closed(self):
        for variant in ("missing", "null", "malformed", "missing_users", "bypass_actor"):
            with self.subTest(variant=variant):
                pair = responses()
                reviews = pair[1]["required_pull_request_reviews"]
                if variant == "missing":
                    reviews.pop("bypass_pull_request_allowances")
                elif variant == "null":
                    reviews["bypass_pull_request_allowances"] = None
                elif variant == "malformed":
                    reviews["bypass_pull_request_allowances"] = "no-bypass"
                elif variant == "missing_users":
                    reviews["bypass_pull_request_allowances"].pop("users")
                else:
                    reviews["bypass_pull_request_allowances"]["apps"] = [{"slug": "bypass-app"}]
                with self.assertRaisesRegex(assurance_enforcement.EnforcementError, "bypass allowances"):
                    self.verify(pair)

    def test_missing_or_malformed_force_push_and_delete_flags_are_rejected(self):
        for flag in ("allow_force_pushes", "allow_deletions"):
            for missing in (True, False):
                with self.subTest(flag=flag, missing=missing):
                    pair = responses()
                    if missing:
                        pair[1].pop(flag)
                    else:
                        pair[1][flag] = {"enabled": "false"}
                    with self.assertRaisesRegex(assurance_enforcement.EnforcementError, flag):
                        self.verify(pair)

    def test_server_proof_is_distinct_from_review_only_fallback(self):
        both = record()
        both["fallback"]["equivalent_enforcement_verified"] = True
        both["fallback"]["equivalence_target_ref"] = "a" * 40
        both["fallback"]["review_provenance"] = {
            "provider": "github_codex_review",
            "reviewer_login": "chatgpt-codex-connector[bot]",
            "review_type": "security_review",
            "purpose": "enforcement_equivalence",
        }
        with mock.patch.object(
            assurance_enforcement,
            "verify_live_server_enforcement",
            side_effect=assurance_enforcement.EnforcementError("server unavailable"),
        ), mock.patch.object(
            assurance_enforcement,
            "verify_authenticated_equivalence",
            return_value={"status": "verified", "review": {"pull_request_number": 77}},
        ):
            with self.assertRaisesRegex(assurance_enforcement.EnforcementError, "review.*does not establish"):
                assurance_enforcement.verify_effective_enforcement(
                    __import__("pathlib").Path("."), both, expected_target="a" * 40,
                )

        with mock.patch.object(
            assurance_enforcement, "verify_live_server_enforcement",
            return_value={"status": "verified_live_server_enforcement"},
        ), mock.patch.object(
            assurance_enforcement, "verify_authenticated_equivalence",
            side_effect=AssertionError("fallback must not be called when live server is valid"),
        ):
            proof = assurance_enforcement.verify_effective_enforcement(
                __import__("pathlib").Path("."), both, expected_target="a" * 40,
            )
            self.assertEqual(proof["mode"], "server")

    def test_all_asserted_proof_failures_block_promotion(self):
        both = record()
        both["fallback"]["equivalent_enforcement_verified"] = True
        both["fallback"]["equivalence_target_ref"] = "a" * 40
        both["fallback"]["review_provenance"] = {
            "provider": "github_codex_review",
            "reviewer_login": "chatgpt-codex-connector[bot]",
            "review_type": "security_review",
            "purpose": "enforcement_equivalence",
        }
        with mock.patch.object(
            assurance_enforcement, "verify_live_server_enforcement",
            side_effect=assurance_enforcement.EnforcementError("server 403"),
        ), mock.patch.object(
            assurance_enforcement, "verify_authenticated_equivalence",
            side_effect=assurance_enforcement.EnforcementError("review stale"),
        ):
            with self.assertRaisesRegex(
                assurance_enforcement.EnforcementError, "server 403.*review stale"
            ):
                assurance_enforcement.verify_effective_enforcement(
                    __import__("pathlib").Path("."), both, expected_target="a" * 40
                )

    def test_self_asserted_server_without_live_proof_fails_effective_enforcement(self):
        with mock.patch.object(
            assurance_enforcement, "verify_live_server_enforcement",
            side_effect=assurance_enforcement.EnforcementError("API unavailable"),
        ):
            with self.assertRaisesRegex(assurance_enforcement.EnforcementError, "API unavailable"):
                assurance_enforcement.verify_effective_enforcement(
                    __import__("pathlib").Path("."), record(), expected_target="a" * 40
                )

    def test_unavailable_github_protection_api_is_not_a_pass(self):
        with mock.patch.object(
            assurance_enforcement.github_review_provenance, "_github_json",
            side_effect=assurance_enforcement.github_review_provenance.ReviewProvenanceError("403"),
        ):
            with self.assertRaisesRegex(assurance_enforcement.EnforcementError, "unable to authenticate"):
                assurance_enforcement.verify_live_server_enforcement(
                    record(), token="test-token"
                )


if __name__ == "__main__":
    unittest.main()
