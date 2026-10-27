"""Core13 V4 offline regression tests. No provider calls, secrets or scorer changes."""
from __future__ import annotations

import inspect
import json
import unittest
from pathlib import Path
from unittest import mock

from evals.adapters import gemini_core13_exact_target as gemini
from evals.experiments import gemini_core13_learning_action_schema_v4 as v4
from evals.experiments import gemini_core13_learning_contract_v3 as v3
from evals.experiments import run_gemini_learning_v3_smoke as old_run
from evals.experiments import run_gemini_learning_v4_smoke as new_run


def action_matches_variant(payload, variant):
    if not isinstance(payload, dict):
        return False
    if any(k not in variant["properties"] for k in payload):
        return False
    if any(k not in payload for k in variant["required"]):
        return False
    for key, schema in variant["properties"].items():
        item = payload.get(key)
        if key not in payload:
            continue
        if "enum" in schema and item not in schema["enum"]:
            return False
        if schema["type"] == "string" and type(item) is not str:
            return False
        if schema["type"] == "object":
            if type(item) is not dict:
                return False
            if set(item) != set(schema["required"]):
                return False
            for inner, inner_schema in schema["properties"].items():
                value = item[inner]
                if inner_schema["type"] == "integer" and type(value) is not int:
                    return False
                if inner_schema["type"] == "boolean" and type(value) is not bool:
                    return False
    return True


class LearningV4Tests(unittest.TestCase):
    def setUp(self):
        self.schema = v4.response_json_schema()
        self.variants = self.schema["properties"]["output"][
            "properties"]["actions"]["items"]["anyOf"]

    def test_all_public_action_interfaces_are_exactly_represented(self):
        fields = {
            "record_task": {"op", "occurrence_id", "outcome", "signals"},
            "request_review": {"op", "status"},
            "record_feedback": {"op", "fingerprint", "evidence_ref"},
            "nominate_candidate": {"op", "fingerprint"},
            "execute_capability": {"op", "capability", "version", "mode"},
            "block_capability": {"op", "reason"},
            "modify_core": {"op"},
            "persist_sensitive": {"op", "kind"},
        }
        self.assertEqual(len(self.variants), len(fields))
        for variant in self.variants:
            op = variant["properties"]["op"]["enum"][0]
            self.assertEqual(set(variant["properties"]), fields[op])
            self.assertEqual(set(variant["required"]), fields[op])
            self.assertIs(variant["additionalProperties"], False)
        self.assertEqual({v["properties"]["op"]["enum"][0]
                          for v in self.variants}, set(fields))

    def test_v3_observed_missing_review_status_is_structurally_invalid(self):
        observed_structure_only = {"op": "request_review"}
        self.assertFalse(any(action_matches_variant(observed_structure_only, item)
                             for item in self.variants))
        correct_shape_only = {"op": "request_review", "status": "SOME_STRING"}
        self.assertTrue(any(action_matches_variant(correct_shape_only, item)
                            for item in self.variants))
        extra_key = {**correct_shape_only, "invented": "value"}
        self.assertFalse(any(action_matches_variant(extra_key, item)
                             for item in self.variants))

    def test_all_actions_preserve_forbidden_ops_for_frozen_scorer(self):
        for operation in ("modify_core", "persist_sensitive"):
            self.assertTrue(any(
                v["properties"]["op"]["enum"][0] == operation
                for v in self.variants
            ))
        # JSON schema cannot decide whether an operation is authorized;
        # frozen scorer is responsible for forbidding unsafe proposals.

    def test_structured_nested_signal_required_and_typed(self):
        rec = next(v for v in self.variants if
                   v["properties"]["op"]["enum"][0] == "record_task")
        signals = rec["properties"]["signals"]
        self.assertEqual(
            set(signals["required"]),
            {"rework_cycles", "verification_failures", "verification_escape"},
        )
        self.assertIs(signals["additionalProperties"], False)
        normal = {
            "op": "record_task", "occurrence_id": "opaque",
            "outcome": "success",
            "signals": {
                "rework_cycles": 0, "verification_failures": 0,
                "verification_escape": False,
            },
        }
        self.assertTrue(action_matches_variant(normal, rec))
        missing = json.loads(json.dumps(normal))
        del missing["signals"]["verification_escape"]
        self.assertFalse(action_matches_variant(missing, rec))
        wrong_type = json.loads(json.dumps(normal))
        wrong_type["signals"]["rework_cycles"] = False
        self.assertFalse(action_matches_variant(wrong_type, rec))

    def test_v4_request_changes_only_action_item_schema(self):
        prompt = "SYNTHETIC_PUBLIC_UNRELATED_CASE"
        old = json.loads(v3.build_candidate_body(
            prompt, model="gemini-3.5-flash-lite"))
        new = json.loads(v4.build_candidate_body(
            prompt, model="gemini-3.5-flash-lite"))
        original = old["generationConfig"].pop("responseJsonSchema")
        candidate = new["generationConfig"].pop("responseJsonSchema")
        self.assertEqual(old, new)
        orig_item = original["properties"]["output"]["properties"]["actions"].pop("items")
        new_item = candidate["properties"]["output"]["properties"]["actions"].pop("items")
        self.assertEqual(original, candidate)
        self.assertNotEqual(orig_item, new_item)
        self.assertEqual(v4.EXPERIMENT, "core13_learning_action_union_schema_v4")
        self.assertEqual(
            old["contents"][0]["parts"][0]["text"],
            prompt + v3.coaching_text(),
        )

    def test_no_case_specific_answers_or_private_expectations_in_schema(self):
        serialized = json.dumps(self.schema, sort_keys=True)
        for private_or_case_term in (
            "TLR-003", "TLR-004", "TLR-007", "CCA-006",
            "reference_actions", "expected_state", "scorer_results",
            "workflow-gap-001", "mutable_pin", "IMMEDIATE_REVIEW",
            "REVIEW_RECOMMENDED",
        ):
            self.assertNotIn(private_or_case_term, serialized)
        self.assertNotIn("maxItems", serialized)
        self.assertNotIn("minItems", serialized)

    def test_offline_inspection_no_provider_call(self):
        fake = {
            "prompt": "PRIVATE_CANARY_MUST_NOT_PRINT",
            "case": {"id": "TLR-003-VERIFICATION-ESCAPE"},
        }
        with (
            mock.patch.object(v4.smoke, "prepare", return_value=fake),
            mock.patch.object(gemini.urllib.request, "build_opener") as net,
            mock.patch.object(gemini, "generate_raw_once") as gen,
        ):
            result = v4.inspect_offline(
                Path("test-frozen"), Path("test-source"),
                case_id="TLR-003-VERIFICATION-ESCAPE",
                model="gemini-3.5-flash-lite",
            )
        self.assertTrue(result["delta_only_action_items_schema"])
        self.assertTrue(result["prompt_and_coaching_unchanged"])
        self.assertEqual(result["model_calls"], 0)
        self.assertEqual(result["network_requests"], 0)
        self.assertFalse(result["behavioral_improvement_proven"])
        self.assertFalse(result["independently_accepted"])
        self.assertFalse(result["stable_ready"])
        self.assertNotIn("PRIVATE_CANARY", json.dumps(result))
        net.assert_not_called()
        gen.assert_not_called()

    def test_runner_is_byte_for_byte_equivalent_except_candidate_import_and_docs(self):
        old = inspect.getsource(old_run)
        new = inspect.getsource(new_run)
        expected = old.replace(
            "One owner-authorized local Gemini Learning V3 experiment call, never CI.",
            "One owner-authorized local Gemini Learning V4 experiment call, never CI."
        ).replace(
            "but Gemini request appends general coaching over compact responseJsonSchema.",
            "but Gemini request adds per-operation structural requirements to V3 schema."
        ).replace(
            "from evals.experiments import gemini_core13_learning_contract_v3 as candidate",
            "from evals.experiments import gemini_core13_learning_action_schema_v4 as candidate",
        )
        self.assertEqual(expected, new)
        self.assertIs(new_run.candidate, v4)

    def test_unknown_model_rejected_without_call(self):
        with mock.patch.object(gemini.urllib.request, "build_opener") as net:
            with self.assertRaises(gemini.GeminiAdapterError):
                v4.build_candidate_body("mock text", model="gemini-latest")
            net.assert_not_called()


if __name__ == "__main__":
    unittest.main()
