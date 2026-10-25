"""T11 public main ruleset observation is intentionally never release authority."""
import copy
import unittest
from unittest import mock

from tools import github_ruleset_observation as obs


def sample():
    common = {
        "id": obs.EXPECTED_RULESET_ID,
        "name": "EREI-Main-Protection",
        "enforcement": "active",
        "target": "branch",
        "source_type": "Repository",
        "source": obs.REPOSITORY,
    }
    details = {
        **common,
        "conditions": {"ref_name": {"exclude": [], "include": ["~DEFAULT_BRANCH"]}},
        "bypass_actors": [],
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {
                "type": "pull_request",
                "parameters": {
                    "required_approving_review_count": 0,
                    "required_reviewers": [],
                    "require_code_owner_review": False,
                    "require_extra_approval_for_unattributed_changes": True,
                    "dismiss_stale_reviews_on_push": False,
                },
            },
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": True,
                    "do_not_enforce_on_create": False,
                    "required_status_checks": [
                        {"context": "assurance", "integration_id": 15368}
                    ],
                },
            },
        ],
    }
    return {
        "branch": {
            "name": "main",
            "protected": True,
            "commit": {"sha": "c4a3f0caaf81430c8ff1f3b09fefd50d821f8300"},
        },
        "rulesets": [copy.deepcopy(common)],
        "details": details,
    }


def assess(data=None, *, mode="LIVE_PUBLIC_API"):
    d = sample() if data is None else data
    return obs.assess_public_main_ruleset(
        d["branch"], d["rulesets"], d["details"], mode=mode
    )


class PublicRulesetObserverTests(unittest.TestCase):
    def test_exact_realistic_main_snapshot_yields_only_release_blocked(self):
        result = assess()
        self.assertEqual(result["status"], "MAIN_CI_OBSERVED_RELEASE_BLOCKED")
        self.assertEqual(result["ruleset_id"], 25712179)
        self.assertTrue(result["main_rule_require_pr"])
        self.assertTrue(result["main_rule_strict_assurance_app_bound"])
        self.assertEqual(result["required_approvals_on_main"], 0)
        for field in (
            "stable_ready", "stable_enforcement_verified",
            "workflow_source_authenticated", "release_branches_and_tags_covered",
            "consumer_release_authorized", "reviewer_independence_verified",
        ):
            with self.subTest(field=field):
                self.assertIs(result[field], False)

    def test_even_required_human_approvals_do_not_promote_stable(self):
        data = sample()
        data["details"]["rules"][2]["parameters"]["required_approving_review_count"] = 2
        result = assess(data)
        self.assertEqual(result["required_approvals_on_main"], 2)
        self.assertFalse(result["reviewer_independence_verified"])
        self.assertFalse(result["stable_ready"])

    def test_live_fetch_uses_three_exact_read_only_paths(self):
        inputs = sample()
        paths = [
            "/branches/main", "/rulesets",
            "/rulesets/25712179",
        ]
        fetch = mock.Mock(side_effect=[
            inputs["branch"], inputs["rulesets"], inputs["details"]
        ])
        result = obs.observe(fetch)
        self.assertEqual(fetch.call_args_list, [mock.call(s) for s in paths])
        self.assertEqual(result["observation_mode"], "LIVE_PUBLIC_API")
        self.assertFalse(result["stable_ready"])

    def test_offline_replay_never_authenticates_observation(self):
        x = assess(mode="OFFLINE_FIXTURE_UNTRUSTED")
        self.assertEqual(x["observation_mode"], "OFFLINE_FIXTURE_UNTRUSTED")
        self.assertFalse(x["consumer_release_authorized"])

    def test_missing_status_check_or_wrong_binding_rejected(self):
        for field, value in [
            ("context", "fake_green"),
            ("integration_id", 0),
            ("integration_id", "15368"),
        ]:
            with self.subTest(field=field, value=value):
                data = sample()
                data["details"]["rules"][3]["parameters"]["required_status_checks"][0][field] = value
                with self.assertRaisesRegex(obs.ObservationError, "binding"):
                    assess(data)
        for value in ([], None, [
            {"context": "assurance", "integration_id": 15368},
            {"context": "unknown", "integration_id": 0},
        ]):
            with self.subTest(value=value):
                data = sample()
                data["details"]["rules"][3]["parameters"]["required_status_checks"] = value
                with self.assertRaises(obs.ObservationError):
                    assess(data)

    def test_scope_excludes_release_and_tags_by_design(self):
        for scopes in (["refs/heads/main", "refs/heads/release/*"],
                       ["~ALL"], ["refs/tags/*"]):
            with self.subTest(scopes=scopes):
                data = sample()
                data["details"]["conditions"]["ref_name"]["include"] = scopes
                with self.assertRaisesRegex(obs.ObservationError, "scope"):
                    assess(data)

    def test_main_deletion_or_force_push_waiver_never_pass(self):
        for remove in ("deletion", "non_fast_forward"):
            with self.subTest(remove=remove):
                data = sample()
                data["details"]["rules"] = [
                    r for r in data["details"]["rules"] if r["type"] != remove
                ]
                with self.assertRaises(obs.ObservationError):
                    assess(data)

    def test_ruleset_bypass_or_deactivated_rejected(self):
        for target in ("rulesets", "details"):
            with self.subTest(target=target):
                data = sample()
                if target == "rulesets":
                    data[target][0]["enforcement"] = "disabled"
                else:
                    data[target]["bypass_actors"] = [{"actor_type": "User", "actor_id": 1}]
                with self.assertRaises(obs.ObservationError):
                    assess(data)

    def test_main_identity_must_be_40_char_commit_and_protected(self):
        variants = [
            ("protected", False),
            ("commit", {"sha": "0" * 40 + "junk"}),
            ("commit", {"sha": "Z" * 40}),
            ("name", "release"),
        ]
        for field, value in variants:
            with self.subTest(field=field, value=value):
                data = sample()
                data["branch"][field] = value
                with self.assertRaises(obs.ObservationError):
                    assess(data)

    def test_duplicate_or_mismatched_ruleset_fails(self):
        data = sample()
        data["rulesets"].append(copy.deepcopy(data["rulesets"][0]))
        with self.assertRaisesRegex(obs.ObservationError, "duplicate"):
            assess(data)
        data = sample()
        data["details"]["source"] = "not-the-owner"
        with self.assertRaisesRegex(obs.ObservationError, "identity"):
            assess(data)

    def test_strict_check_must_be_enforced_at_branch_creation(self):
        for field, value in [
            ("strict_required_status_checks_policy", False),
            ("do_not_enforce_on_create", True),
        ]:
            with self.subTest(field=field):
                data = sample()
                data["details"]["rules"][3]["parameters"][field] = value
                with self.assertRaisesRegex(obs.ObservationError, "strict"):
                    assess(data)

    def test_wrong_or_duplicate_rule_type_fail_closed(self):
        data = sample()
        data["details"]["rules"].append({"type": "deletion"})
        with self.assertRaisesRegex(obs.ObservationError, "duplicate"):
            assess(data)
        data = sample()
        data["details"]["rules"].append({"type": 4})
        with self.assertRaisesRegex(obs.ObservationError, "rule type"):
            assess(data)

    def test_public_get_has_fixed_api_paths_and_no_token(self):
        with self.assertRaisesRegex(obs.ObservationError, "unexpected"):
            obs.public_json("/issues/68")
        with mock.patch.object(obs.urllib.request, "build_opener") as opener:
            response = mock.MagicMock()
            response.__enter__.return_value.read.return_value = b'{"ok": true}'
            opener.return_value.open.return_value = response
            self.assertEqual(obs.public_json("/branches/main"), {"ok": True})
            req = opener.return_value.open.call_args.args[0]
            self.assertEqual(req.get_method(), "GET")
            self.assertNotIn("authorization", {
                k.lower() for k in req.headers
            })

    def test_nonfinite_json_rejected(self):
        with mock.patch.object(obs.urllib.request, "build_opener") as opener:
            response = mock.MagicMock()
            response.__enter__.return_value.read.return_value = b'{"bad":NaN}'
            opener.return_value.open.return_value = response
            with self.assertRaisesRegex(obs.ObservationError, "invalid GitHub REST JSON"):
                obs.public_json("/rulesets")


if __name__ == "__main__":
    unittest.main()
