"""OFFLINE verification: compact V2 schema is general, bounded and distinct.

No provider calls, no live Free-tier quota consumption, no key material.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from evals.adapters import gemini_core13_exact_target as gemini
from evals.experiments import gemini_core13_schema_compact_v2 as v2
from evals.experiments import gemini_core13_schema_candidate as v1


class CompactV2Tests(unittest.TestCase):
    def test_schema_only_requires_action_op_and_preserves_extra_arguments(self):
        s = v2.response_json_schema()
        a = s["properties"]["output"]["properties"]["actions"]
        self.assertNotIn("maxItems", a)
        self.assertEqual(a["type"], "array")
        fields = a["items"]
        self.assertEqual(fields["required"], ["op"])
        self.assertEqual(fields["properties"], {"op": {"type": "string"}})
        self.assertIs(fields["additionalProperties"], True)
        self.assertIs(s["properties"]["output"]["properties"]["state"][
            "additionalProperties"], True)
        self.assertNotIn("enum", fields["properties"]["op"])
        self.assertNotIn("enum", s["properties"]["output"]["properties"]["decision"])

    def test_no_case_specific_answers_and_forbidden_action_not_suppressed(self):
        s = v2.response_json_schema()
        data = json.dumps(s)
        for forbidden_oracle in (
            "TLR-003", "TLR-004", "TLR-007", "CCA-006", "mutable_pin",
            "expired_or_mismatched", "feedback_then_promotion",
            "record_feedback", "nominate_candidate", "modify_core",
            "persist_sensitive", "reference_actions", "expected_state",
        ):
            self.assertNotIn(forbidden_oracle, data)
        self.assertNotIn("op", s["properties"]["output"]["required"])

    def test_fewer_schema_constraints_than_failed_v1(self):
        old = v1.response_json_schema()
        new = v2.response_json_schema()
        old_size = len(json.dumps(old))
        new_size = len(json.dumps(new))
        self.assertLess(new_size, old_size // 2)
        self.assertLess(new_size, 1100)
        self.assertEqual(new["properties"]["output"]["required"],
                         ["contract", "decision", "actions", "state"])
        self.assertEqual(new["required"], ["output", "metadata"])
        self.assertEqual(new["properties"]["metadata"]["required"], ["risk"])

    def test_baseline_delta_only_native_response_json_schema(self):
        prompt = "PUBLIC MOCK INPUT / DOES NOT CONNECT"
        original = json.loads(gemini.build_generation_body(
            prompt, model="gemini-3.5-flash-lite"))
        compact = json.loads(v2.build_candidate_body(
            prompt, model="gemini-3.5-flash-lite"))
        sch = compact["generationConfig"].pop("responseJsonSchema")
        self.assertEqual(sch, v2.response_json_schema())
        self.assertEqual(original, compact)
        self.assertEqual(v2.EXPERIMENT,
                         "core13_native_response_json_schema_compact_v2")

    def test_inspection_no_model_call_or_secret_leak(self):
        fake = {
            "prompt": "PUBLIC BUT NEVER PRINT SOME_SECRET_CANARY",
            "case": {"id": "TLR-003-VERIFICATION-ESCAPE"},
        }
        with (
            mock.patch.object(v2.smoke, "prepare", return_value=fake),
            mock.patch.object(gemini, "generate_raw_once") as transport,
            mock.patch.object(gemini.urllib.request, "build_opener") as opener,
        ):
            report = v2.inspect_offline(
                Path("fake-target"), Path("fake-adapter"),
                case_id="TLR-003-VERIFICATION-ESCAPE",
                model="gemini-3.5-flash-lite",
            )
        self.assertTrue(report["delta_only_response_json_schema"])
        self.assertFalse(report["provider_schema_supported_live"])
        self.assertFalse(report["v1_http400_cause_established"])
        self.assertFalse(report["behavioral_improvement_proven"])
        self.assertEqual(report["network_requests"], 0)
        self.assertEqual(report["model_calls"], 0)
        self.assertEqual(report["evidence_files_written"], 0)
        self.assertNotIn("SOME_SECRET_CANARY", json.dumps(report))
        opener.assert_not_called()
        transport.assert_not_called()

    def test_unapproved_model_rejected_without_network(self):
        with mock.patch.object(gemini.urllib.request, "build_opener") as opener:
            with self.assertRaises(gemini.GeminiAdapterError):
                v2.build_candidate_body("synthetic", model="gemini-latest")
        opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
