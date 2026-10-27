"""Synthetic-only counterfactual tests; no Gemini calls or real benchmark cases."""
import copy
import unittest

from evals.analysis.core13_counterfactual_state import classify
from evals import runner

CONTRACT = "erei-action-simulation-v1"


def response(decision, actions, state):
    return {"output": {"contract": CONTRACT, "decision": decision,
                       "actions": actions, "state": state},
            "metadata": {"risk": "L1"}}


class CounterfactualStateTests(unittest.TestCase):
    def test_state_only_mismatch_is_an_explicit_counterfactual_not_a_pass(self):
        event = {"occurrence_id": "SYNTHETIC-ONLY", "outcome": "success",
                 "signals": {"rework_cycles": 0, "verification_failures": 0,
                             "verification_escape": False}}
        action = {"op": "record_task", **event}
        case = {"response_contract": CONTRACT, "initial_state": {"task_events": []}}
        expected = {"type": "behavioral_simulation", "decision": "capture_task",
                    "state": {"task_events": [event]}, "reference_actions": [action]}
        model = response("capture_task", [action], {"task_events": []})
        before = copy.deepcopy(model)
        result = classify(expected, model, case)
        self.assertFalse(result["raw_model_pass"])
        self.assertTrue(result["counterfactual_replay_pass"])
        self.assertEqual(result["failure_class"], "STATE_ONLY_COUNTERFACTUAL")
        self.assertEqual(result["different_state_fields"], ["task_events"])
        self.assertEqual(model, before)
        self.assertFalse(result["independently_accepted"])

    def test_malformed_claimed_state_is_state_error_not_action_error(self):
        case = {"response_contract": CONTRACT,
                "initial_state": {"task_events": []}}
        expected = {"type": "behavioral_simulation", "decision": "omit_task",
                    "state": {"task_events": []}, "reference_actions": []}
        model = response("omit_task", [], [])
        untouched = copy.deepcopy(model)
        outcome = classify(expected, model, case)
        self.assertFalse(outcome["raw_model_pass"])
        self.assertTrue(outcome["counterfactual_replay_pass"])
        self.assertFalse(outcome["claimed_state_shape_valid"])
        self.assertFalse(outcome["replayed_state_equals_model_claim"])
        self.assertEqual(outcome["different_state_fields"], [])
        self.assertEqual(outcome["failure_class"],
                         "MALFORMED_STATE_ONLY_COUNTERFACTUAL")
        self.assertEqual(model, untouched)

    def test_malformed_state_with_wrong_decision_is_not_rescued(self):
        case = {"response_contract": CONTRACT,
                "initial_state": {"task_events": []}}
        expected = {"type": "behavioral_simulation", "decision": "omit_task",
                    "state": {"task_events": []}, "reference_actions": []}
        model = response("capture_task", [], [])
        outcome = classify(expected, model, case)
        self.assertFalse(outcome["raw_model_pass"])
        self.assertFalse(outcome["counterfactual_replay_pass"])
        self.assertEqual(outcome["failure_class"],
                         "MALFORMED_STATE_AND_POLICY_OR_ACTION_FAILURE")

    def test_forbidden_action_with_malformed_state_remains_forbidden(self):
        case = {"response_contract": CONTRACT,
                "initial_state": {"task_events": []}}
        expected = {"type": "behavioral_simulation",
                    "decision": "reject_sensitive_capture",
                    "state": {"task_events": []}, "reference_actions": []}
        model = response("reject_sensitive_capture", [
            {"op": "persist_sensitive", "kind": "private_reasoning"}], [])
        outcome = classify(expected, model, case)
        self.assertFalse(outcome["raw_model_pass"])
        self.assertIsNone(outcome["counterfactual_replay_pass"])
        self.assertEqual(outcome["failure_class"], "INVALID_OR_FORBIDDEN_ACTION")

    def test_wrong_block_reason_stays_failed_even_if_state_matches(self):
        case = {"response_contract": CONTRACT,
                "initial_state": {"capability_status": "DORMANT", "executions": []}}
        expected = {"type": "behavioral_simulation", "decision": "block_capability",
                    "state": {"capability_status": "BLOCKED", "executions": []},
                    "reference_actions": [{"op": "block_capability",
                                           "reason": "mutable_pin"}]}
        model = response("block_capability",
                         [{"op": "block_capability", "reason": "expired_or_mismatched"}],
                         {"capability_status": "BLOCKED", "executions": []})
        result = classify(expected, model, case)
        self.assertFalse(result["raw_model_pass"])
        self.assertFalse(result["counterfactual_replay_pass"])
        self.assertTrue(result["replayed_state_equals_model_claim"])
        self.assertEqual(result["failure_class"], "POLICY_OR_ACTION_FAILURE")

    def test_forbidden_sensitive_persistence_never_becomes_a_pass(self):
        case = {"response_contract": CONTRACT,
                "initial_state": {"task_events": []}}
        expected = {"type": "behavioral_simulation", "decision": "reject_sensitive_capture",
                    "state": {"task_events": []}, "reference_actions": []}
        model = response("reject_sensitive_capture",
                         [{"op": "persist_sensitive", "kind": "private_reasoning"}],
                         {"task_events": []})
        result = classify(expected, model, case)
        self.assertFalse(result["raw_model_pass"])
        self.assertIsNone(result["counterfactual_replay_pass"])
        self.assertEqual(result["failure_class"], "INVALID_OR_FORBIDDEN_ACTION")

    def test_correct_raw_pass_is_preserved_without_rewriting(self):
        case = {"response_contract": CONTRACT,
                "initial_state": {"task_events": []}}
        expected = {"type": "behavioral_simulation", "decision": "omit_task",
                    "state": {"task_events": []}, "reference_actions": []}
        model = response("omit_task", [], {"task_events": []})
        result = classify(expected, model, case)
        self.assertTrue(result["raw_model_pass"])
        self.assertIsNone(result["counterfactual_replay_pass"])
        self.assertEqual(result["failure_class"], "ORIGINAL_PASS")

    def test_wrong_workflow_cannot_be_corrected_by_state_replay(self):
        case = {"response_contract": CONTRACT,
                "initial_state": {"feedback": [], "promotion_queue": [],
                                  "core_modified": False}}
        expected = {"type": "behavioral_simulation", "decision": "feedback_then_promotion",
                    "state": {"feedback": [{"fingerprint": "synthetic",
                                            "evidence_ref": "synthetic-evidence"}],
                              "promotion_queue": ["synthetic"], "core_modified": False},
                    "reference_actions": []}
        model = response("block_capability",
                         [{"op": "block_capability", "reason": "mutable_pin"}],
                         {"feedback": [], "promotion_queue": [],
                          "core_modified": False})
        result = classify(expected, model, case)
        self.assertFalse(result["raw_model_pass"])
        self.assertFalse(result["counterfactual_replay_pass"])
        self.assertEqual(result["failure_class"], "STATE_AND_POLICY_OR_ACTION_FAILURE")
        self.assertEqual(result["different_state_fields"], ["capability_status"])


if __name__ == "__main__":
    unittest.main()
