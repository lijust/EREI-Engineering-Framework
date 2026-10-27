"""Separate verification-stage regressions; never invokes model or executes tasks."""
from __future__ import annotations
import copy
import unittest
from evals import runner
from evals.analysis.core13_pilot_reference_verifier import verify_preview
from tools.learning_proposal_runtime import evaluate_proposal, CONTRACT


class ProposalReferenceVerificationTests(unittest.TestCase):
    def test_preview_acceptance_only_proves_state_parity(self):
        initial = {"task_events": []}
        proposal = {"contract": CONTRACT, "decision": "omit_task", "actions": []}
        trusted = {"domain": "task_capture", "facts": {"engineering_execution": False}}
        preview = evaluate_proposal(proposal, initial, trusted)
        before = copy.deepcopy((proposal, initial, preview))
        check = verify_preview(proposal, initial, preview,
                               independent_reducer=runner.simulate_actions)
        self.assertEqual(check["status"], "REFERENCE_STATE_PARITY_PASS")
        self.assertTrue(check["state_parity"])
        self.assertEqual(check["policy_correctness"], "NOT_ASSESSED")
        self.assertFalse(check["independently_accepted"])
        self.assertFalse(check["real_execution_verified"])
        self.assertEqual((proposal, initial, preview), before)

    def test_modified_materialized_state_is_detected(self):
        initial = {"task_events": []}
        proposed = {"contract": CONTRACT, "decision": "omit_task", "actions": []}
        preview = evaluate_proposal(proposed, initial, {
            "domain": "task_capture",
            "facts": {"engineering_execution": False}})
        preview["materialized_state"] = {"task_events": ["tampered"]}
        check = verify_preview(proposed, initial, preview,
                               independent_reducer=runner.simulate_actions)
        self.assertEqual(check["status"], "REFERENCE_STATE_PARITY_FAIL")
        self.assertFalse(check["state_parity"])

    def test_denied_proposals_are_not_rescued_by_verification(self):
        initial = {"task_events": []}
        proposed = {"contract": CONTRACT, "decision": "capture_task",
                    "actions": [{"op": "persist_sensitive",
                                 "kind": "private_reasoning"}]}
        denied = evaluate_proposal(proposed, initial, {
            "domain": "task_capture",
            "facts": {"engineering_execution": False,
                      "requested_storage": ["private_reasoning"]}})
        check = verify_preview(proposed, initial, denied,
                               independent_reducer=runner.simulate_actions)
        self.assertEqual(check["status"], "NOT_AUTHORIZED_FOR_REPLAY")
        self.assertFalse(check["independently_accepted"])

    def test_reference_reducer_failure_does_not_change_original_result(self):
        initial = {"task_events": []}
        proposal = {"contract": CONTRACT, "decision": "omit_task", "actions": []}
        preview = evaluate_proposal(proposal, initial, {
            "domain": "task_capture", "facts": {"engineering_execution": False}})
        before = copy.deepcopy(preview)
        def reject(_initial, _actions):
            raise ValueError("simulated rejected reference input")
        check = verify_preview(proposal, initial, preview, independent_reducer=reject)
        self.assertEqual(check["status"], "REFERENCE_REPLAY_REJECTED")
        self.assertEqual(preview, before)


if __name__ == "__main__":
    unittest.main()
