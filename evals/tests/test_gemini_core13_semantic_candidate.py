"""Offline tests: generic semantic candidate never leaks scorer answers."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from evals.experiments import gemini_core13_semantic_candidate as semantic
from evals.adapters import gemini_core13_exact_target as gemini


class Core13SemanticCandidateTests(unittest.TestCase):
    def test_suffix_not_oracle_or_per_case_answer(self):
        note = semantic.SEMANTIC_ROUTING_ADVICE
        self.assertTrue(note)
        for oracle in (
            "TLR-007", "CCA-006", "mutable_pin",
            "expired_or_mismatched", "feedback_then_promotion",
            "nominate_candidate", "record_feedback",
            "reference_actions", "expected_state",
            "learning_pattern_analysis", "workflow-gap-001",
        ):
            self.assertNotIn(oracle, note)

    def test_candidate_only_appends_generic_text_without_changing_baseline(self):
        base = "PUBLIC SYNTHETIC CORE PROMPT\n"
        candidate = semantic.build_semantic_candidate_prompt(base)
        self.assertEqual(candidate, base + semantic.SEMANTIC_ROUTING_ADVICE)
        self.assertTrue(candidate.startswith(base))
        baseline = json.loads(gemini.build_generation_body(
            base, model="gemini-3.5-flash-lite"))
        proposed = json.loads(gemini.build_generation_body(
            candidate, model="gemini-3.5-flash-lite"))
        self.assertEqual(baseline["generationConfig"], proposed["generationConfig"])
        self.assertNotIn("responseJsonSchema", proposed["generationConfig"])
        self.assertNotIn("tools", proposed)
        self.assertEqual(baseline["contents"][0]["parts"][0]["text"], base)
        self.assertEqual(proposed["contents"][0]["parts"][0]["text"], candidate)

    def test_inspect_has_no_api_and_never_prints_full_prompt(self):
        fake = {
            "prompt": "SECRET-DO-NOT-PRINT synthetic Framework prompt",
            "case": {"id": "TLR-007-REVIEW-NOT-SELF-MODIFICATION"},
        }
        with (
            mock.patch.object(semantic.smoke, "prepare", return_value=fake),
            mock.patch.object(gemini, "generate_raw_once") as network,
            mock.patch.object(gemini.urllib.request, "build_opener") as opener,
        ):
            result = semantic.inspect_offline(
                Path("fake-target"), Path("fake-adapter"),
                case_id="TLR-007-REVIEW-NOT-SELF-MODIFICATION",
                model="gemini-3.5-flash-lite",
            )
        self.assertEqual(result["status"], "SOURCE_ONLY_NO_API")
        self.assertTrue(result["delta_only_generic_semantic_suffix"])
        self.assertFalse(result["behavioral_improvement_proven"])
        self.assertEqual(result["network_requests"], 0)
        self.assertEqual(result["model_calls"], 0)
        self.assertEqual(result["evidence_files_written"], 0)
        self.assertNotIn("SECRET-DO-NOT-PRINT", json.dumps(result))
        network.assert_not_called()
        opener.assert_not_called()

    def test_disallow_empty_and_oversize_prompt(self):
        with self.assertRaises(gemini.GeminiAdapterError):
            semantic.build_semantic_candidate_prompt("")
        with self.assertRaises(gemini.GeminiAdapterError):
            semantic.build_semantic_candidate_prompt("x" * gemini.MAX_REQUEST_BYTES)


if __name__ == "__main__":
    unittest.main()
