"""Public safety checks: no source observation can become release approval."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest


MODULE = Path(__file__).resolve().parents[1] / "benchmarks/summarize_calibration_evidence.py"
spec = importlib.util.spec_from_file_location("source_evidence_summary", MODULE)
summarizer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summarizer)


class EvidenceSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(summarizer.CATALOG.read_text(encoding="utf-8"))
        cls.receipt = json.loads(summarizer.RECEIPT.read_text(encoding="utf-8"))

    def test_immutable_denominator_and_disjoint_provenance_levels(self):
        result = summarizer.summarize(self.catalog, self.receipt)
        self.assertEqual(result["recipe_preparation"], "12/12")
        self.assertEqual(result["source_behavior_observations"], "9/12")
        self.assertEqual(result["stage_counts"], {
            summarizer.FULL: 3,
            summarizer.PARTIAL: 1,
            summarizer.V8: 3,
            summarizer.METHOD: 2,
            summarizer.NONE: 3,
        })
        self.assertEqual(result["task_states"]["APP-04"], summarizer.METHOD)
        self.assertEqual(result["task_states"]["PY-03"], summarizer.PARTIAL)
        self.assertEqual(result["task_states"]["PY-01"], summarizer.NONE)
        self.assertEqual(result["task_states"]["PY-04"], summarizer.NONE)
        self.assertEqual(result["task_states"]["PY-06"], summarizer.NONE)
        self.assertEqual(result["independent_full_source_calibrations"], "0/12")
        self.assertEqual(result["model_comparisons"], "0/48")
        self.assertEqual(result["exact_target_runtime_evidence"], "0/13")
        self.assertEqual(result["effectiveness"], "NOT_ESTABLISHED")
        self.assertFalse(result["release_authorized"])
        self.assertEqual(result["stable_release"], "BLOCKED")

    def test_any_unreviewed_record_cannot_assert_authority_or_pilot(self):
        for key, value in (
            ("execution_authorized", True),
            ("model_executions", 1),
            ("independent_review", "APPROVED"),
            ("stable_release", "READY"),
            ("sampled_study_runs", "1/48"),
            ("exact_target_runtime_evidence", "1/13"),
        ):
            with self.subTest(key=key):
                receipt = copy.deepcopy(self.receipt)
                receipt["authority"][key] = value
                with self.assertRaises(ValueError):
                    summarizer.summarize(self.catalog, receipt)

    def test_app04_static_test_survivor_must_be_explicit(self):
        receipt = copy.deepcopy(self.receipt)
        item = next(r for r in receipt["source_executions"]
                    if r["task_id"] == "APP-04")
        item["original_unchanged_consumer_test_probe"]["mutant_detected"] = True
        with self.assertRaisesRegex(ValueError, "false-negative"):
            summarizer.summarize(self.catalog, receipt)

    def test_partial_py03_and_v8_tests_never_count_as_full_consumer(self):
        receipt = copy.deepcopy(self.receipt)
        record = next(r for r in receipt["source_executions"]
                      if r["task_id"] == "PY-03")
        record["unchanged_original_consumer_test"]["executed"] = 3
        with self.assertRaisesRegex(ValueError, "partial"):
            summarizer.summarize(self.catalog, receipt)
        receipt = copy.deepcopy(self.receipt)
        record = next(r for r in receipt["source_executions"]
                      if r["task_id"] == "APP-01")
        record["full_node_runtime_executed"] = True
        with self.assertRaisesRegex(ValueError, "virtualized"):
            summarizer.summarize(self.catalog, receipt)

    def test_duplicate_unknown_or_changed_denominator_fail_closed(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["source_executions"].append(copy.deepcopy(receipt["source_executions"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            summarizer.summarize(self.catalog, receipt)
        receipt = copy.deepcopy(self.receipt)
        receipt["source_executions"][0]["task_id"] = "UNDEFINED"
        with self.assertRaisesRegex(ValueError, "unknown"):
            summarizer.summarize(self.catalog, receipt)
        catalog = copy.deepcopy(self.catalog)
        catalog["packages"].pop()
        with self.assertRaisesRegex(ValueError, "twelve"):
            summarizer.summarize(catalog, self.receipt)
        catalog = copy.deepcopy(self.catalog)
        catalog["execution_authorized"] = True
        with self.assertRaisesRegex(ValueError, "authorizes"):
            summarizer.summarize(catalog, self.receipt)


if __name__ == "__main__":
    unittest.main()
