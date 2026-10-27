"""Offline pilot tests: no model/provider, persistence or project execution."""
from __future__ import annotations

import copy
import unittest
from datetime import datetime, timezone

from tools import learning_proposal_runtime as pilot
from evals import runner as frozen_reference

SHA = "a" * 40


def proposal(decision, actions, claimed_state=None):
    value = {"contract": pilot.CONTRACT, "decision": decision, "actions": actions}
    if claimed_state is not None:
        value["claimed_state"] = claimed_state
    return value


def activation_context(maturity="candidate", *, pin_type="commit", adopted=False,
                       version="v1", ref=SHA, expiry="2026-11-10T00:00:00Z",
                       pin_upgraded=False):
    adoption = None
    if adopted:
        adoption = {"schema_version": 1, "framework_ref": SHA, "adoptions": [{
            "adoption_id": "CAD-20261027T120000Z-ABCD1234",
            "capability": "learning_pattern_analysis",
            "version": version, "approved_at": "2026-10-27T12:00:00Z",
            "expires_at": expiry, "approved_by_role": "project_owner",
            "risk": "L2",
            "purpose": "Synthetic review of a bounded candidate in an isolated project",
            "evidence": ["synthetic-approved-record"],
        }]}
    return {
        "domain": "capability_activation",
        "capability": "learning_pattern_analysis",
        "manifest": {
            "schema_version": 1, "framework": {
                "repository": "lijust/EREI-Engineering-Framework",
                "baseline": "V1", "ref_type": pin_type, "ref": ref,
            },
            "project": {}, "overlays": [], "runtime_adapters": [],
        },
        "registry": {"schema_version": 1, "development_line": {
            "capabilities": {
                "learning_pattern_analysis": {"status": maturity, "version": "v1"},
            }}},
        "adoption_document": adoption,
        "loaded_framework_ref": SHA,
        "now": datetime(2026, 11, 1, tzinfo=timezone.utc),
        "pin_upgraded": pin_upgraded,
    }


class LearningProposalPilotTests(unittest.TestCase):
    def assert_denied(self, result, reason):
        self.assertEqual(result["status"], "DENIED")
        self.assertEqual(result["reason_code"], reason)
        self.assertFalse(result["executed"])
        self.assertNotIn("materialized_state", result)
        self.assertFalse(result["independently_verified"])

    def test_task_capture_authorized_with_exact_observed_signals(self):
        facts = {"engineering_execution": True, "occurrence_id": "synthetic-01",
                 "outcome": "success",
                 "signals": {"rework_cycles": 0, "verification_failures": 0,
                             "verification_escape": False}}
        action = {"op": "record_task", "occurrence_id": facts["occurrence_id"],
                  "outcome": facts["outcome"], "signals": facts["signals"]}
        initial = {"task_events": []}
        before = copy.deepcopy(initial)
        prop = proposal("capture_task", [action], {"task_events": []})
        before_proposal = copy.deepcopy(prop)
        result = pilot.evaluate_proposal(prop, initial,
                                         {"domain": "task_capture", "facts": facts})
        self.assertEqual(result["status"], "AUTHORIZED_IN_MEMORY_PREVIEW")
        self.assertFalse(result["model_claimed_state_matches_reducer"])
        self.assertEqual(result["materialized_state"],
                         frozen_reference.simulate_actions(initial, [action]))
        self.assertEqual(initial, before)
        self.assertEqual(prop, before_proposal)
        self.assertFalse(result["executed"])
        self.assertFalse(result["independently_verified"])

    def test_task_capture_denies_fabrication_and_boolean_for_integer(self):
        facts = {"engineering_execution": True, "occurrence_id": "synthetic-02",
                 "outcome": "success",
                 "signals": {"rework_cycles": 1, "verification_failures": 0,
                             "verification_escape": False}}
        good = {"op": "record_task", **{k: facts[k] for k in (
            "occurrence_id", "outcome", "signals")}}
        altered = copy.deepcopy(good)
        altered["signals"]["rework_cycles"] = True
        for action in (altered, {**good, "occurrence_id": "invented"}):
            with self.subTest(action=action):
                self.assert_denied(pilot.evaluate_proposal(
                    proposal("capture_task", [action]), {"task_events": []},
                    {"domain": "task_capture", "facts": facts}),
                    "TASK_FACT_MISMATCH")

    def test_nonexecution_omitted_and_sensitive_data_rejected(self):
        base = {"task_events": []}
        omitted = pilot.evaluate_proposal(
            proposal("omit_task", []), base,
            {"domain": "task_capture", "facts": {"engineering_execution": False}})
        self.assertEqual(omitted["materialized_state"], base)
        self.assert_denied(pilot.evaluate_proposal(
            proposal("capture_task", [{"op": "record_task"}]), base,
            {"domain": "task_capture", "facts": {"engineering_execution": False}}),
            "PROPOSAL_ACTIONS_INVALID")
        sensitive = {"engineering_execution": False,
                     "requested_storage": ["credentials", "private_reasoning"]}
        bad = pilot.evaluate_proposal(
            proposal("reject_sensitive_capture",
                     [{"op": "persist_sensitive", "kind": "credentials"}]), base,
            {"domain": "task_capture", "facts": sensitive})
        self.assert_denied(bad, "DECISION_ACTION_MISMATCH")
        good = pilot.evaluate_proposal(
            proposal("reject_sensitive_capture", []), base,
            {"domain": "task_capture", "facts": sensitive})
        self.assertEqual(good["status"], "AUTHORIZED_IN_MEMORY_PREVIEW")
        self.assertEqual(good["materialized_state"], base)

    def test_review_is_only_allowed_with_upstream_trusted_status(self):
        initial = {"review_status": "LEARNING_HEALTHY"}
        request = proposal("request_review",
                           [{"op": "request_review", "status": "REVIEW_DUE"}])
        self.assert_denied(pilot.evaluate_proposal(
            request, initial, {"domain": "learning_review"}),
            "REVIEW_AUTHORITY_NOT_ESTABLISHED")
        ok = pilot.evaluate_proposal(
            request, initial, {"domain": "learning_review",
                               "authorized_review_status": "REVIEW_DUE"})
        self.assertEqual(ok["materialized_state"],
                         frozen_reference.simulate_actions(initial, request["actions"]))

    def test_feedback_proposal_is_only_staged_not_core_modified(self):
        initial = {"feedback": [], "promotion_queue": [], "core_modified": False}
        context = {"domain": "feedback_promotion",
                   "facts": {"finding_fingerprint": "synthetic-gap",
                             "evidence_ref": "synthetic-ref",
                             "core_change_approved": False}}
        actions = [{"op": "record_feedback", "fingerprint": "synthetic-gap",
                    "evidence_ref": "synthetic-ref"},
                   {"op": "nominate_candidate", "fingerprint": "synthetic-gap"}]
        result = pilot.evaluate_proposal(
            proposal("feedback_then_promotion", actions), initial, context)
        self.assertEqual(result["materialized_state"],
                         frozen_reference.simulate_actions(initial, actions))
        self.assertFalse(result["materialized_state"]["core_modified"])
        self.assert_denied(pilot.evaluate_proposal(
            proposal("block_capability", [{"op": "block_capability",
                                           "reason": "mutable_pin"}]), initial, context),
            "WRONG_WORKFLOW")

    def test_valid_bounded_candidate_calls_existing_policy(self):
        initial = {"capability_status": "DORMANT", "executions": []}
        action = {"op": "execute_capability", "capability": "learning_pattern_analysis",
                  "version": "v1", "mode": "candidate"}
        result = pilot.evaluate_proposal(
            proposal("allow_capability", [action]), initial,
            activation_context(adopted=True))
        self.assertEqual(result["status"], "AUTHORIZED_IN_MEMORY_PREVIEW")
        self.assertEqual(result["materialized_state"],
                         frozen_reference.simulate_actions(initial, [action]))
        self.assertFalse(result["executed"])

    def test_stable_capability_requires_no_candidate_adoption(self):
        context = activation_context(maturity="stable")
        initial = {"capability_status": "DORMANT", "executions": []}
        action = {"op": "execute_capability", "capability": "learning_pattern_analysis",
                  "version": "v1", "mode": "stable"}
        result = pilot.evaluate_proposal(
            proposal("allow_capability", [action]), initial, context)
        self.assertEqual(result["status"], "AUTHORIZED_IN_MEMORY_PREVIEW")
        self.assertEqual(result["materialized_state"]["capability_status"], "STABLE")

    def test_branch_pin_forbidden_even_with_adoption_and_model_claim(self):
        initial = {"capability_status": "DORMANT", "executions": []}
        context = activation_context(pin_type="branch", ref="main", adopted=True)
        action = {"op": "execute_capability", "capability": "learning_pattern_analysis",
                  "version": "v1", "mode": "candidate"}
        self.assert_denied(pilot.evaluate_proposal(
            proposal("allow_capability", [action],
                     {"capability_status": "ACTIVE_CANDIDATE", "executions": []}),
            initial, context), "CAPABILITY_NOT_ACTIVE")
        blocked = pilot.evaluate_proposal(
            proposal("block_capability", [{"op": "block_capability",
                                           "reason": "mutable_pin"}]),
            initial, context)
        self.assertEqual(blocked["materialized_state"]["capability_status"], "BLOCKED")
        self.assertEqual(blocked["materialized_state"]["executions"], [])

    def test_expired_candidate_cannot_execute_or_be_misclassified(self):
        context = activation_context(adopted=True, expiry="2026-10-31T00:00:00Z")
        initial = {"capability_status": "DORMANT", "executions": []}
        action = {"op": "execute_capability", "capability": "learning_pattern_analysis",
                  "version": "v1", "mode": "candidate"}
        self.assert_denied(pilot.evaluate_proposal(
            proposal("allow_capability", [action]), initial, context),
            "CAPABILITY_NOT_ACTIVE")
        self.assert_denied(pilot.evaluate_proposal(
            proposal("block_capability", [{"op": "block_capability",
                                           "reason": "mutable_pin"}]), initial, context),
            "BLOCK_REASON_NOT_ESTABLISHED")
        correct = pilot.evaluate_proposal(
            proposal("block_capability", [{"op": "block_capability",
                                           "reason": "expired_or_mismatched"}]),
            initial, context)
        self.assertEqual(correct["materialized_state"]["capability_status"], "BLOCKED")

    def test_upgrade_and_adoption_are_separate(self):
        initial = {"capability_status": "DORMANT", "executions": []}
        context = activation_context(pin_upgraded=True)
        actual = pilot.evaluate_proposal(
            proposal("block_capability", [{"op": "block_capability",
                                           "reason": "pin_upgrade_without_adoption"}]),
            initial, context)
        self.assertEqual(actual["materialized_state"]["capability_status"], "DORMANT")
        self.assert_denied(pilot.evaluate_proposal(
            proposal("block_capability", [{"op": "block_capability",
                                           "reason": "expired_or_mismatched"}]),
            initial, context), "BLOCK_REASON_NOT_ESTABLISHED")

    def test_authority_missing_and_unrecognized_status_are_fail_closed(self):
        initial = {"capability_status": "DORMANT", "executions": []}
        action = {"op": "execute_capability", "capability": "learning_pattern_analysis",
                  "version": "v1", "mode": "candidate"}
        context = activation_context(adopted=True)
        del context["registry"]
        self.assert_denied(pilot.evaluate_proposal(
            proposal("allow_capability", [action]), initial, context),
            "ACTIVATION_EVIDENCE_MISSING")
        no_registry_entry = activation_context(adopted=True)
        no_registry_entry["registry"]["development_line"]["capabilities"] = {}
        self.assert_denied(pilot.evaluate_proposal(
            proposal("allow_capability", [action]), initial, no_registry_entry),
            "CAPABILITY_NOT_ACTIVE")

    def test_model_cannot_supply_policy_context_or_override_decision_contract(self):
        base = {"task_events": []}
        policy = {"domain": "task_capture",
                  "facts": {"engineering_execution": False}}
        tampered = proposal("omit_task", [])
        tampered["policy_override"] = {"engineering_execution": True}
        self.assert_denied(pilot.evaluate_proposal(tampered, base, policy),
                           "PROPOSAL_CONTRACT_INVALID")
        self.assert_denied(pilot.evaluate_proposal(
            {"contract": pilot.CONTRACT, "decision": "modify_core",
             "actions": []}, base, policy), "PROPOSAL_CONTRACT_INVALID")

    def test_missing_materialization_field_denies_without_mutating_input(self):
        base = {"task_events": []}
        copy_before = copy.deepcopy(base)
        result = pilot.evaluate_proposal(
            proposal("request_review", [{"op": "request_review",
                                         "status": "REVIEW_DUE"}]),
            base, {"domain": "learning_review",
                   "authorized_review_status": "REVIEW_DUE"})
        self.assert_denied(result, "STATE_FIELD_MISSING")
        self.assertEqual(base, copy_before)


if __name__ == "__main__":
    unittest.main()
