"""Offline-only proof: V5 is generic and changes NO frozen scoring semantics."""
from __future__ import annotations
import inspect
import json
import unittest
from pathlib import Path
from unittest import mock

from evals.adapters import gemini_core13_exact_target as gemini
from evals.experiments import gemini_core13_learning_action_schema_v4 as v4
from evals.experiments import gemini_core13_learning_policy_state_v5 as v5
from evals.experiments import run_gemini_learning_v4_smoke as old_runner
from evals.experiments import run_gemini_learning_v5_smoke as new_runner


class LearningV5Tests(unittest.TestCase):
    def test_general_advice_cannot_encode_case_identifiers_or_scorer_answers(self):
        guide = v5.coaching_text()
        for hint in v5.FORBIDDEN_CASE_HINTS:
            self.assertNotIn(hint, guide)
        self.assertIn("initial_state", guide)
        self.assertIn("policy", guide)
        self.assertIn("state", guide)
        self.assertNotIn("expected_state", guide)
        self.assertNotIn("source case", guide)
        self.assertEqual(guide, v5.coaching_text())

    def test_v5_changes_only_static_prompt_append(self):
        for prompt in ("PUBLIC SYNTHETIC", "ANOTHER VALID GENERAL INPUT"):
            with self.subTest(prompt=prompt):
                a = json.loads(v4.build_candidate_body(prompt, model="gemini-3.5-flash-lite"))
                b = json.loads(v5.build_candidate_body(prompt, model="gemini-3.5-flash-lite"))
                self.assertEqual(a["generationConfig"], b["generationConfig"])
                self.assertEqual(b["contents"][0]["parts"][0]["text"],
                                 a["contents"][0]["parts"][0]["text"] + v5.coaching_text())
                self.assertEqual(
                    {k:v for k,v in a.items() if k!="contents"},
                    {k:v for k,v in b.items() if k!="contents"},
                )
                self.assertEqual(v5.response_json_schema(), v4.response_json_schema())

    def test_no_network_and_no_expectation_access_during_inspection(self):
        fixture={"prompt":"DONOT_EXPOSE_PRIVATE_CANARY",
                 "case":{"id":"TLR-001-SUCCESS-STILL-LEARNING-DATA"}}
        with (
            mock.patch.object(v5.smoke, "prepare", return_value=fixture),
            mock.patch.object(gemini.urllib.request, "build_opener") as net,
        ):
            proof=v5.inspect_offline(
                Path("mock-frozen"), Path("mock-adapter"),
                case_id=fixture["case"]["id"],
                model="gemini-3.5-flash-lite")
        self.assertEqual(proof["model_calls"], 0)
        self.assertTrue(proof["response_schema_identical"])
        self.assertFalse(proof["behavioral_improvement_proven"])
        self.assertFalse(proof["independently_accepted"])
        self.assertFalse(proof["stable_ready"])
        self.assertNotIn("DONOT_EXPOSE_PRIVATE_CANARY", json.dumps(proof))
        net.assert_not_called()

    def test_runner_is_unmodified_except_import_and_two_docstrings(self):
        old=inspect.getsource(old_runner)
        new=inspect.getsource(new_runner)
        expected=(old
            .replace("One owner-authorized local Gemini Learning V4 experiment call, never CI.",
                     "One owner-authorized local Gemini Learning V5 experiment call, never CI.")
            .replace("but Gemini request adds per-operation structural requirements to V3 schema.",
                     "but Gemini request appends source-neutral policy/state self-check to V4.")
            .replace("from evals.experiments import gemini_core13_learning_action_schema_v4 as candidate",
                     "from evals.experiments import gemini_core13_learning_policy_state_v5 as candidate"))
        self.assertEqual(new, expected)
        self.assertIs(new_runner.candidate, v5)

    def test_unknown_model_and_empty_prompt_fail_before_http(self):
        with mock.patch.object(gemini.urllib.request, "build_opener") as net:
            with self.assertRaises(gemini.GeminiAdapterError):
                v5.build_candidate_body("synthetic", model="gemini-latest")
            for value in ("", "  ", None):
                with self.assertRaises(gemini.GeminiAdapterError):
                    v5.build_candidate_body(value, model="gemini-3.5-flash-lite")
            net.assert_not_called()


if __name__=="__main__":
    unittest.main()
