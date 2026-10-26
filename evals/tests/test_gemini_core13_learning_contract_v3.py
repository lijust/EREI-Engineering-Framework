"""Offline-only tests: V3 general learning coach must not know case outcomes."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from evals.adapters import gemini_core13_exact_target as gemini
from evals.experiments import gemini_core13_learning_contract_v3 as v3
from evals.experiments import gemini_core13_schema_compact_v2 as v2


class Core13LearningV3Tests(unittest.TestCase):
    def test_coaching_has_no_failing_case_ids_or_oracle_answers(self):
        guide = v3.coaching_text()
        self.assertIn("initial_state", guide)
        self.assertIn("all and only", guide)
        self.assertIn("policy", guide)
        self.assertEqual(guide, v3.coaching_text())
        for disallowed in v3.FORBIDDEN_HINTS:
            self.assertNotIn(disallowed, guide)
        for source_case in ("TLR-001", "TLR-002", "CCA-001", "CCA-005"):
            self.assertNotIn(source_case, guide)
        self.assertNotIn("review_status", guide)
        self.assertNotIn("fingerprint", guide)

    def test_exact_request_delta_is_appended_generic_text_only(self):
        prompt = "PUBLIC CONTRACT SYNTHETIC EXAMPLE"
        v2_body = json.loads(v2.build_candidate_body(
            prompt, model="gemini-3.5-flash-lite"))
        v3_body = json.loads(v3.build_candidate_body(
            prompt, model="gemini-3.5-flash-lite"))
        self.assertEqual(v2_body["generationConfig"], v3_body["generationConfig"])
        self.assertEqual(v2_body["contents"][0]["role"], "user")
        self.assertEqual(v3_body["contents"][0]["role"], "user")
        self.assertEqual(
            v3_body["contents"][0]["parts"][0]["text"],
            prompt + v3.coaching_text(),
        )
        self.assertEqual(
            v3_body["generationConfig"]["responseJsonSchema"],
            v2.response_json_schema(),
        )
        self.assertNotIn("systemInstruction", v3_body)
        self.assertNotIn("responseSchema", v3_body["generationConfig"])

    def test_case_independence_and_unchanged_selection(self):
        for prompt in (
            "EXPLANATION - NO ACTION",
            "LEARNING SIGNAL / TWO TASKS",
            "PROJECT CAPABILITY / UNKNOWN POLICY",
        ):
            candidate = json.loads(v3.build_candidate_body(
                prompt, model="gemini-3.5-flash-lite"))
            self.assertEqual(candidate["contents"][0]["parts"][0]["text"],
                             prompt + v3.coaching_text())
            self.assertNotIn("case_id", candidate)

    def test_reject_unknown_model_without_asking_provider(self):
        with mock.patch.object(gemini.urllib.request, "build_opener") as op:
            with self.assertRaises(gemini.GeminiAdapterError):
                v3.build_candidate_body("SYNTHETIC", model="gemini-latest")
            op.assert_not_called()

    def test_offline_inspection_is_redacted_and_never_calls_model(self):
        fake = {
            "prompt": "CANARY_NEVER_DISCLOSE_IN_REPORT",
            "case": {"id": "TLR-003-VERIFICATION-ESCAPE"},
        }
        with (
            mock.patch.object(v3.smoke, "prepare", return_value=fake),
            mock.patch.object(gemini, "generate_raw_once") as generate,
            mock.patch.object(gemini.urllib.request, "build_opener") as req,
        ):
            result = v3.inspect_offline(
                Path("/tmp/frozen-target"), Path("/tmp/source"),
                case_id="TLR-003-VERIFICATION-ESCAPE",
                model="gemini-3.5-flash-lite",
            )
        self.assertEqual(result["status"], "SOURCE_ONLY_NO_API")
        self.assertEqual(result["model_calls"], 0)
        self.assertEqual(result["network_requests"], 0)
        self.assertTrue(result["delta_only_generic_coaching"])
        self.assertTrue(result["response_schema_identical"])
        self.assertFalse(result["frozen_scorer_changed"])
        self.assertFalse(result["behavioral_improvement_proven"])
        self.assertFalse(result["independently_accepted"])
        self.assertFalse(result["stable_ready"])
        self.assertNotEqual(
            result["previous_request_sha256"], result["new_request_sha256"])
        self.assertNotIn("CANARY_NEVER_DISCLOSE", json.dumps(result))
        req.assert_not_called()
        generate.assert_not_called()

    def test_no_model_response_rewrite_or_scorer_import(self):
        # V3 only builds a provider request and compares request shapes.
        self.assertFalse(hasattr(v3, "record_candidate"))
        self.assertFalse(hasattr(v3, "score"))
        self.assertFalse(hasattr(v3, "normalize_output"))
        self.assertFalse(hasattr(v3, "apply_actions"))

    def test_empty_prompt_rejected_without_any_network(self):
        with mock.patch.object(gemini.urllib.request, "build_opener") as op:
            for prompt in ("", "   ", None):
                with self.subTest(prompt=prompt):
                    with self.assertRaises(gemini.GeminiAdapterError):
                        v3.build_candidate_body(
                            prompt, model="gemini-3.5-flash-lite")
            op.assert_not_called()


if __name__ == "__main__":
    unittest.main()
