"""V4 typed-action grammar tests. Offline, no credentials, no Gemini calls."""
from __future__ import annotations

import copy
import json
import unittest
from unittest import mock

from evals.adapters import gemini_core13_exact_target as gemini
from evals.experiments import gemini_core13_learning_contract_v3 as v3
from evals.experiments import gemini_core13_typed_action_schema_v4 as v4


class Core13TypedActionV4Tests(unittest.TestCase):
    def test_all_public_operations_including_disallowed_effects_remain_selectable(self):
        action_item = v4.response_json_schema()["properties"]["output"][
            "properties"]["actions"]["items"]
        variants = action_item["anyOf"]
        self.assertEqual(len(variants), 8)
        self.assertEqual(
            {variant["properties"]["op"]["enum"][0] for variant in variants},
            set(v4.ACTION_FIELDS),
        )
        self.assertIn("modify_core", v4.ACTION_FIELDS)
        self.assertIn("persist_sensitive", v4.ACTION_FIELDS)
        self.assertEqual(len(variants), len(v4.ACTION_FIELDS))

    def test_schema_rejects_incomplete_action_and_extra_field_by_construction(self):
        variants = v4.response_json_schema()["properties"]["output"][
            "properties"]["actions"]["items"]["anyOf"]
        for op, fields in v4.ACTION_FIELDS.items():
            with self.subTest(operation=op):
                matching = [v for v in variants
                            if v["properties"]["op"]["enum"] == [op]]
                self.assertEqual(len(matching), 1)
                item = matching[0]
                self.assertEqual(item["required"], ["op", *fields])
                self.assertFalse(item["additionalProperties"])
                self.assertEqual(set(item["properties"]), {"op", *fields})
        review = next(v for v in variants
                      if v["properties"]["op"]["enum"] == ["request_review"])
        self.assertIn("status", review["required"])
        task = next(v for v in variants
                    if v["properties"]["op"]["enum"] == ["record_task"])
        self.assertIn("signals", task["required"])
        signals = task["properties"]["signals"]
        self.assertEqual(set(signals["required"]), {
            "rework_cycles", "verification_failures", "verification_escape"
        })

    def test_only_action_item_schema_changes_against_v3(self):
        for prompt in (
            "public synthetic action request",
            "public synthetic explanation request",
            "public synthetic authorization request",
        ):
            with self.subTest(prompt=prompt):
                previous = json.loads(v3.build_candidate_body(
                    prompt, model="gemini-3.5-flash-lite"))
                proposed = json.loads(v4.build_candidate_body(
                    prompt, model="gemini-3.5-flash-lite"))
                self.assertEqual(previous["contents"], proposed["contents"])
                self.assertEqual(
                    previous["generationConfig"]["thinkingConfig"],
                    proposed["generationConfig"]["thinkingConfig"])
                report = v4.inspect_diff_offline(
                    prompt, model="gemini-3.5-flash-lite")
                self.assertTrue(report["delta_only_action_item_schema"])
                self.assertFalse(report["provider_schema_support_proven"])
                self.assertFalse(report["behavioral_improvement_proven"])
                self.assertFalse(report["independently_accepted"])
                self.assertFalse(report["stable_ready"])

    def test_no_oracle_case_or_score_text_in_schema(self):
        schema = json.dumps(v4.response_json_schema())
        for forbidden in (
            "TLR-003", "TLR-004", "TLR-007", "CCA-006",
            "reference_actions", "expected_state", "scorer_results",
            "github-issue-", "PASS", "FAIL",
        ):
            self.assertNotIn(forbidden, schema)

    def test_no_provider_or_response_transformation(self):
        self.assertFalse(hasattr(v4, "record_candidate"))
        self.assertFalse(hasattr(v4, "parse_gemini_result"))
        self.assertFalse(hasattr(v4, "score"))
        self.assertFalse(hasattr(v4, "normalize_output"))
        with mock.patch.object(gemini.urllib.request, "build_opener") as network:
            candidate = v4.build_candidate_body(
                "PUBLIC_OFFLINE", model="gemini-3.5-flash-lite")
            self.assertLess(len(candidate), gemini.MAX_REQUEST_BYTES)
            network.assert_not_called()

    def test_v4_one_call_runner_is_exact_v3_transport_and_scorer_copy(self):
        import inspect
        from evals.experiments import run_gemini_learning_v3_smoke as old
        from evals.experiments import run_gemini_typed_action_v4_smoke as new
        previous = inspect.getsource(old)
        proposed = inspect.getsource(new)
        expected = (previous
            .replace(
                "One owner-authorized local Gemini Learning V3 experiment call, never CI.",
                "One owner-authorized local Gemini typed-action V4 experiment call, never CI.")
            .replace(
                "but Gemini request appends general coaching over compact responseJsonSchema.",
                "but Gemini response schema adds conditional action arguments over V3.")
            .replace(
                "from evals.experiments import gemini_core13_learning_contract_v3 as candidate",
                "from evals.experiments import gemini_core13_typed_action_schema_v4 as candidate"))
        self.assertEqual(proposed, expected)
        self.assertIs(new.candidate, v4)

    def test_v4_authorized_preflight_is_offline_with_mock_provider(self):
        import os
        import tempfile
        from pathlib import Path
        from evals.experiments import run_gemini_typed_action_v4_smoke as runner
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            target = root / "target"
            target.mkdir()
            output = root / "evidence"
            prepared = {
                "root": target.resolve(),
                "prompt": "PUBLIC_MOCK_ONLY",
                "case": {"id": "TLR-003-VERIFICATION-ESCAPE"},
                "suite": {"suite_id": "synthetic"},
                "request": {"synthetic": True},
                "adapter_source": {"adapter_source_revision": "fake"},
            }
            mock_result = {
                "status": "EXPERIMENTAL_MODEL_RESPONSE_SCORED_FAIL_UNVERIFIED",
                "passed": False,
                "provider_model_version": "gemini-3.5-flash-lite",
                "usage_metadata": {"totalTokenCount": 1},
            }
            with (
                mock.patch.object(runner.smoke, "prepare", return_value=prepared),
                mock.patch.object(runner, "record_candidate",
                                  return_value=mock_result) as fake_scoring,
                mock.patch.object(runner.urllib.request, "build_opener") as network,
                mock.patch.dict(os.environ, {"GEMINI_API_KEY": "TEST_FAKE_KEY"}),
                mock.patch.object(runner, "print"),
            ):
                rc = runner.main([
                    "--target-root", str(target), "--output-dir", str(output),
                    "--case-id", "TLR-003-VERIFICATION-ESCAPE",
                    "--model", "gemini-3.5-flash-lite",
                    "--live", "--confirm-free-tier", "--confirm-experimental-schema",
                ])
            self.assertEqual(rc, 1)
            fake_scoring.assert_called_once()
            network.assert_not_called()
            provenance = json.loads(
                (output / "candidate-provenance.json").read_text(encoding="utf-8"))
            self.assertEqual(provenance["experiment"], v4.EXPERIMENT)
            self.assertFalse(provenance["stable_ready"])
            self.assertFalse(provenance["independently_accepted"])

    def test_unknown_model_rejected_with_zero_network(self):
        with mock.patch.object(gemini.urllib.request, "build_opener") as network:
            with self.assertRaises(gemini.GeminiAdapterError):
                v4.build_candidate_body("PUBLIC_OFFLINE", model="gemini-latest")
            network.assert_not_called()

    def test_schema_objects_are_fresh_and_original_v3_never_mutated(self):
        v3_schema = v3.response_json_schema()
        original = copy.deepcopy(v3_schema)
        v4_schema = v4.response_json_schema()
        v4_schema["properties"]["output"]["properties"]["actions"]["items"] = {}
        self.assertEqual(v3.response_json_schema(), original)
        self.assertNotEqual(v3_schema, v4_schema)


if __name__ == "__main__":
    unittest.main()
