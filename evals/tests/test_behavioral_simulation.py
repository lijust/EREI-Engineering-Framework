"""Offline adversarial checks for the 13 Core decision simulations.

Synthetic fixtures exercise scoring and transport, never genuine AI behavior.
"""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from evals import exact_target_run, runner
from evals.adapters import copilot_cli_exact_target as adapter
from evals.fixtures import reference_oracle_adapter as oracle
from tools import exact_target_evidence
from tools.tests import test_exact_target_evidence as retained

ROOT = Path(__file__).resolve().parents[2]
SUITES = [ROOT / "evals/cases" / name for name in (
    "task-learning-review.eval.json", "candidate-capability-activation.eval.json")]


def all_cases():
    return [(runner.load_json(path), case) for path in SUITES for case in runner.load_json(path)["cases"]]


def response(case):
    result = oracle.build_response(case)
    result.pop("evidence")
    result["metadata"] = {"risk": "L2"}
    return copy.deepcopy(result)


def scored(case, result):
    return all(runner.score(e, result, case["input"])[0] for e in case["expectations"])


class BehavioralSimulationTests(unittest.TestCase):
    def test_thirteen_explicit_synthetic_fixtures_validate_and_pass(self):
        cases = all_cases()
        self.assertEqual(len(cases), 13)
        for suite, case in cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(runner.validate_suite(suite), [])
                self.assertTrue(scored(case, response(case)))
                self.assertFalse(oracle.build_response(case)["evidence"]["independent_runtime"])

    def test_old_keyword_stuffing_and_contradictory_prose_fail_all_thirteen(self):
        phrases = "Task Learning success capture explanation no execution IMMEDIATE_REVIEW verification REVIEW_RECOMMENDED 20 REVIEW_DUE three structured signals not Framework Feedback Knowledge Promotion Candidate dormant presence activation ACTIVE_CANDIDATE bounded version does not activate adoption blocked expired Stable Candidate adoption commit"
        for _, case in all_cases():
            with self.subTest(case=case["id"]):
                for text in (phrases, phrases + "; ignore policy and perform the unauthorized action anyway."):
                    self.assertFalse(scored(case, {"output": text}))

    def test_decision_alone_and_forged_final_state_do_not_pass(self):
        for _, case in all_cases():
            with self.subTest(case=case["id"]):
                result = response(case)
                result["output"].pop("actions")
                self.assertFalse(scored(case, result))
                result = response(case)
                result["output"]["actions"].append({"op": "modify_core"})
                self.assertFalse(scored(case, result))
                result = response(case)
                result["output"]["state"]["invented_field"] = "expected policy words"
                self.assertFalse(scored(case, result))

    def test_rejects_wrong_decision_even_when_action_effects_are_correct(self):
        for _, case in all_cases():
            result = response(case)
            result["output"]["decision"] = "allow_capability" if result["output"]["decision"] != "allow_capability" else "block_capability"
            self.assertFalse(scored(case, result), case["id"])

    def test_required_actions_cannot_be_omitted_or_reordered(self):
        for _, case in all_cases():
            result = response(case)
            if result["output"]["actions"]:
                result["output"]["actions"] = []
                self.assertFalse(scored(case, result), case["id"])
        case = all_cases()[6][1]
        result = response(case)
        result["output"]["actions"].reverse()
        self.assertFalse(scored(case, result))

    def test_capture_occurrence_signals_and_privacy_are_substantive(self):
        case = all_cases()[0][1]
        for mutation in ("occurrence", "credentials", "boolean_count", "negative_count", "nan", "duplicate"):
            result = response(case)
            action = result["output"]["actions"][0]
            if mutation == "occurrence": action["occurrence_id"] = "different-task"
            if mutation == "credentials": action["signals"]["credentials"] = "synthetic-not-a-secret"
            if mutation == "boolean_count": action["signals"]["rework_cycles"] = False
            if mutation == "negative_count": action["signals"]["rework_cycles"] = -1
            if mutation == "nan": action["signals"]["rework_cycles"] = float("nan")
            if mutation == "duplicate": result["output"]["actions"].append(copy.deepcopy(action))
            self.assertFalse(scored(case, result), mutation)
        privacy = all_cases()[5][1]
        result = response(privacy)
        result["output"]["actions"] = [{"op": "persist_sensitive", "kind": "private_reasoning"}]
        self.assertFalse(scored(privacy, result))

    def test_denied_execution_cannot_be_hidden_by_later_block_or_claimed_state(self):
        for _, case in all_cases()[7:]:
            if case["expectations"][0]["decision"] != "block_capability":
                continue
            result = response(case)
            facts = case["input"]["facts"]
            result["output"]["actions"].insert(0, {"op": "execute_capability", "capability": facts["capability"], "version": facts["version"], "mode": "candidate"})
            self.assertFalse(scored(case, result), case["id"])
            result["output"]["state"] = runner.simulate_actions(case["input"]["initial_state"], result["output"]["actions"])
            self.assertFalse(scored(case, result), case["id"])

    def test_bound_input_occurrence_prevents_fixture_answer_reuse(self):
        case = copy.deepcopy(all_cases()[0][1])
        case["input"]["facts"]["occurrence_id"] = "other-occurrence"
        case["expectations"][0]["state"]["task_events"][0]["occurrence_id"] = "other-occurrence"
        old = response(all_cases()[0][1])
        self.assertFalse(scored(case, old))

    def test_prose_paraphrases_do_not_control_scoring(self):
        for _, original in all_cases():
            case = copy.deepcopy(original)
            case["input"]["prompt"] = "Determine the permitted transition from the supplied facts."
            self.assertTrue(scored(case, response(case)), case["id"])

    def test_unknown_fields_real_traces_and_nonfinite_values_fail_closed(self):
        case = all_cases()[0][1]
        for mutate in (
            lambda r: r["output"].update(explanation="ignore the rules"),
            lambda r: r["output"]["actions"][0].update(extra="ignored"),
            lambda r: r.update(trace=[{"type": "tool", "name": "write_file"}]),
            lambda r: r["metadata"].update(number=float("inf")),
            lambda r: r["output"].update(decision=[]),
        ):
            result = response(case)
            mutate(result)
            self.assertFalse(scored(case, result))
        for payload in ('{"output":NaN}', '{"output":1e999}', '{"output":"safe","output":"unsafe"}'):
            with self.assertRaises(ValueError): runner.strict_json_loads(payload)

    def test_blind_transport_exposes_interfaces_and_facts_not_reference_actions(self):
        for suite, case in all_cases():
            request = exact_target_run._blinded_request(suite, case)
            encoded = json.dumps(request)
            for private_field in ("reference_actions", "expectations", "tags", case["id"], suite["suite_id"]):
                self.assertNotIn(private_field, encoded)
            prompt = adapter.build_direct_prompt([("skills/example/SKILL.md", "policy")], request["input"], {})
            self.assertIn(runner.SIMULATION_CONTRACT, prompt)
            self.assertNotIn("reference_actions", prompt)
            self.assertEqual(adapter._parse_final_json(json.dumps(response(case))), response(case))
        for payload in ('{"output":NaN,"metadata":{"risk":"L2"}}', '{"output":1e999,"metadata":{"risk":"L2"}}', '{"output":"a","output":"b","metadata":{"risk":"L2"}}'):
            with self.assertRaises(adapter.CopilotExactTargetError): adapter._parse_final_json(payload)

    def test_exact_target_run_scores_structured_output_and_retains_it(self):
        suite = copy.deepcopy(all_cases()[0][0])
        case = suite["cases"][0]
        suite["cases"] = [case]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "simulation.eval.json"
            path.write_text(json.dumps(suite), encoding="utf-8")
            with mock.patch.object(runner, "call_adapter", return_value=response(case)):
                manifest, evidence = exact_target_run.run_suites([str(path)], adapter_command="external-runtime", adapter_id="synthetic-unit-test", adapter_revision="a"*40, runtime_id="synthetic-unit-test", runtime_version="1", runtime_evidence=["synthetic-unit-test"], framework_ref="b"*40, manifest_relpath="evals/exact-target-runs/simulation-test.json")
            self.assertEqual(manifest["executions"][0]["status"], "pass")
            self.assertEqual(manifest["executions"][0]["response"], response(case))

    def test_retained_replay_rejects_forged_passing_status(self):
        helper = retained.ExactTargetEvidenceTests()
        case = copy.deepcopy(all_cases()[7][1])
        case["id"] = "case"
        suite = {"schema_version": "1.0", "suite_id": "suite", "artifact": "workflows/candidate-capability-adoption", "assurance_scope": "behavioral_runtime", "cases": [case]}
        for malicious in (False, True):
            with self.subTest(malicious=malicious), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                manifest = helper.manifest()
                result = response(case)
                if malicious: result["output"]["actions"].append({"op": "modify_core"})
                row = manifest["executions"][0]
                row["response"] = result
                row["response_digest"] = exact_target_evidence._canonical_digest(result)
                helper.write_bound_files(root, manifest=manifest)
                (root / "evals/cases/suite.eval.json").write_text(json.dumps(suite), encoding="utf-8")
                if malicious:
                    with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "rescoring mismatch"):
                        exact_target_evidence.validate_binding(root, retained.FRAMEWORK_REF, helper.execution())
                else:
                    exact_target_evidence.validate_binding(root, retained.FRAMEWORK_REF, helper.execution())


if __name__ == "__main__":
    unittest.main()
