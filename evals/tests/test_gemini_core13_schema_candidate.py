"""Offline-only tests for post-baseline responseJsonSchema candidate."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from evals.adapters import gemini_core13_exact_target as gemini
from evals.experiments import gemini_core13_schema_candidate as candidate


class Core13SchemaCandidateTests(unittest.TestCase):
    def test_only_change_to_baseline_request_is_native_schema(self):
        prompt = "synthetic public test only"
        base = json.loads(gemini.build_generation_body(
            prompt, model="gemini-3.5-flash-lite"
        ))
        proposed = json.loads(candidate.build_candidate_body(
            prompt, model="gemini-3.5-flash-lite"
        ))
        self.assertEqual(base["contents"], proposed["contents"])
        self.assertEqual(proposed["generationConfig"].pop("responseJsonSchema"),
                         candidate.response_json_schema())
        self.assertEqual(base["generationConfig"], proposed["generationConfig"])
        self.assertNotIn("tools", proposed)
        self.assertNotIn("temperature", proposed["generationConfig"])

    def test_all_ops_including_forbidden_still_representable_for_detection(self):
        schema = candidate.response_json_schema()
        actions = schema["properties"]["output"]["properties"]["actions"]
        action = actions["items"]
        self.assertEqual(set(action["properties"]["op"]["enum"]),
                         set(candidate.OPS))
        self.assertIn("modify_core", candidate.OPS)
        self.assertIn("persist_sensitive", candidate.OPS)
        self.assertEqual(action["required"], ["op"])
        self.assertFalse(action["additionalProperties"])
        self.assertEqual(actions["maxItems"], 16)

    def test_no_private_case_expectations_or_forced_correct_answer(self):
        schema = candidate.response_json_schema()
        data = json.dumps(schema, ensure_ascii=False)
        for private in (
            "reference_actions", "expected_state",
            "TLR-003", "TLR-004", "CCA-006", "workflow-gap-001",
            "correct_answer", "prompt_sha256", "private_context",
        ):
            self.assertNotIn(private, data)
        decision_schema = schema["properties"]["output"]["properties"]["decision"]
        self.assertEqual(set(decision_schema["enum"]), set(candidate.DECISIONS))
        self.assertNotIn("const", decision_schema)
        self.assertNotIn("enum", schema["properties"]["output"]["properties"]["state"])

    def test_schema_requires_every_typed_root_field_and_metadata_risk(self):
        schema = candidate.response_json_schema()
        self.assertEqual(schema["required"], ["output", "metadata"])
        self.assertFalse(schema["additionalProperties"])
        out = schema["properties"]["output"]
        self.assertEqual(out["required"], ["contract", "decision", "actions", "state"])
        self.assertFalse(out["additionalProperties"])
        self.assertEqual(schema["properties"]["metadata"]["required"], ["risk"])
        self.assertEqual(set(schema["properties"]["metadata"]["properties"]["risk"]["enum"]),
                         {"L0", "L1", "L2", "L3"})

    def test_review_status_and_block_reason_enums_do_not_choose_an_answer(self):
        props = candidate.response_json_schema()["properties"]["output"][
            "properties"]["actions"]["items"]["properties"]
        self.assertEqual(set(props["status"]["enum"]), set(candidate.REVIEW_STATUSES))
        self.assertEqual(set(props["reason"]["enum"]), set(candidate.BLOCKING_REASONS))
        self.assertEqual(props["signals"]["required"],
                         ["rework_cycles", "verification_failures",
                          "verification_escape"])
        self.assertFalse(props["signals"]["additionalProperties"])

    def test_schema_body_has_no_model_network_calls(self):
        with mock.patch.object(gemini, "generate_raw_once") as net:
            with mock.patch.object(gemini.urllib.request, "build_opener") as opener:
                body = candidate.build_candidate_body(
                    "synthetic public prompt", model="gemini-3.5-flash-lite"
                )
        self.assertIn(b'"responseJsonSchema"', body)
        net.assert_not_called()
        opener.assert_not_called()

    def test_unapproved_model_cannot_produce_request(self):
        with self.assertRaises(gemini.GeminiAdapterError):
            candidate.build_candidate_body("public", model="gemini-latest")

    def test_inspection_is_offline_and_does_not_print_prompt(self):
        fake_prepared = {
            "prompt": "SECRET-MUST-NOT-PRINT-public-synthetic-test",
            "case": {"id": "TLR-003-VERIFICATION-ESCAPE"},
        }
        with (mock.patch.object(candidate.smoke, "prepare",
                                return_value=fake_prepared),
              mock.patch.object(gemini, "generate_raw_once") as network,
              mock.patch.object(gemini.urllib.request, "build_opener") as opener):
            report = candidate.inspect_offline(
                Path("fake-target"), Path("fake-adapter"),
                case_id="TLR-003-VERIFICATION-ESCAPE",
                model="gemini-3.5-flash-lite",
            )
        self.assertTrue(report["delta_only_response_json_schema"])
        self.assertFalse(report["behavioral_improvement_proven"])
        self.assertFalse(report["native_provider_schema_validated_live"])
        self.assertEqual(report["network_requests"], 0)
        self.assertEqual(report["model_calls"], 0)
        self.assertEqual(report["evidence_files_written"], 0)
        self.assertEqual(report["baseline_request_sha256"], report["baseline_request_sha256"].lower())
        self.assertNotIn("SECRET-MUST-NOT-PRINT", json.dumps(report))
        network.assert_not_called()
        opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
