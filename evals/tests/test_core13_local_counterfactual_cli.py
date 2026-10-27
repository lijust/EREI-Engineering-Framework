"""Synthetic-only integrity regressions for owner-local counterfactual CLI."""
import json
import tempfile
import unittest
from pathlib import Path

from evals.analysis import core13_local_counterfactual_cli as cli
from evals import runner


class LocalCounterfactualCliTests(unittest.TestCase):
    def test_range_parser_rejects_duplicates_and_oversized_input(self):
        self.assertEqual(cli.ids("5-7,10,12"), [5, 6, 7, 10, 12])
        for spec in ("5-3", "3,3", "0", "-9", "1-200", "text"):
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                cli.ids(spec)

    def test_local_receipt_classified_without_promotion_or_mutation(self):
        event = {"occurrence_id": "synthetic", "outcome": "success",
                 "signals": {"rework_cycles": 0, "verification_failures": 0,
                             "verification_escape": False}}
        action = {"op": "record_task", **event}
        inp = {"response_contract": "erei-action-simulation-v1",
               "initial_state": {"task_events": []}}
        fixture = {"input": inp, "expectations": [{
            "type": "behavioral_simulation", "decision": "capture_task",
            "state": {"task_events": [event]}, "reference_actions": [action]}]}
        model = {"output": {"contract": "erei-action-simulation-v1",
                            "decision": "capture_task", "actions": [action],
                            "state": {"task_events": []}},
                 "metadata": {"risk": "L0"}}
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            files = {
                "verdict.json": {
                    "case_id": "TLR-999-SYNTHETIC-ONLY",
                    "experiment": "core13_learning_policy_state_replay_v5",
                    "status": "EXPERIMENTAL_MODEL_RESPONSE_SCORED_FAIL_UNVERIFIED",
                    "passed": False, "independently_accepted": False,
                    "stable_ready": False,
                },
                "adapter-normalized.json": model,
                "blind-request.json": {"input": inp},
            }
            for name,obj in files.items():
                (folder/name).write_text(json.dumps(obj),encoding="utf-8")
            result = cli.case_audit(
                folder, {"TLR-999-SYNTHETIC-ONLY": fixture},
                runner.score_simulation, runner.simulate_actions)
            self.assertFalse(result["raw_model_pass"])
            self.assertTrue(result["replay_counterfactual_pass"])
            self.assertEqual(result["difference_fields"], ["task_events"])
            self.assertFalse(result["independently_accepted"])
            self.assertFalse(result["stable_ready"])
            self.assertEqual(
                json.loads((folder/"adapter-normalized.json").read_text()),
                model)
            self.assertNotIn("synthetic", json.dumps(result))

    def test_inconsistent_receipt_cannot_override_frozen_raw_scorer(self):
        inp={"response_contract":"erei-action-simulation-v1",
             "initial_state":{"task_events":[]}}
        fixture={"input":inp,"expectations":[{
            "type":"behavioral_simulation","decision":"omit_task",
            "state":{"task_events":[]},"reference_actions":[]}]}
        model={"output":{"contract":"erei-action-simulation-v1",
                         "decision":"omit_task","actions":[],
                         "state":{"task_events":[]}},
               "metadata":{"risk":"L0"}}
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            rows={
                "verdict.json":{"case_id":"TLR-998-SYNTHETIC-ONLY",
                                "experiment":"core13_learning_action_union_schema_v4",
                                "status":"EXPERIMENTAL_MODEL_RESPONSE_SCORED_FAIL_UNVERIFIED",
                                "passed":False,"independently_accepted":False,
                                "stable_ready":False},
                "adapter-normalized.json":model,
                "blind-request.json":{"input":inp},
            }
            for name,content in rows.items():
                (folder/name).write_text(json.dumps(content),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"raw scorer diverges"):
                cli.case_audit(folder,
                    {"TLR-998-SYNTHETIC-ONLY":fixture},
                    runner.score_simulation,runner.simulate_actions)


if __name__=="__main__":
    unittest.main()
