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
        self.assertEqual(result["source_behavior_observations"], "12/12")
        self.assertEqual(result["source_structural_observations"], "0/12")
        self.assertEqual(result["source_evidence_coverage"], "12/12")
        self.assertEqual(result["stage_counts"], {
            summarizer.FULL: 4,
            summarizer.PARTIAL: 1,
            summarizer.V8: 3,
            summarizer.METHOD: 2,
            summarizer.STUBBED_METHOD: 2,
            summarizer.STRUCTURAL: 0,
            summarizer.NONE: 0,
        })
        self.assertEqual(result["task_states"]["APP-04"], summarizer.METHOD)
        self.assertEqual(result["task_states"]["PY-03"], summarizer.PARTIAL)
        self.assertEqual(result["task_states"]["PY-01"], summarizer.STUBBED_METHOD)
        self.assertEqual(result["task_states"]["PY-04"], summarizer.FULL)
        self.assertEqual(result["task_states"]["PY-06"], summarizer.STUBBED_METHOD)
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

    def test_py04_original_consumer_calibration_keeps_rejected_mutant_history(self):
        receipt = copy.deepcopy(self.receipt)
        old = receipt["historical_source_structural_observations"]
        self.assertEqual(len(old), 1)
        self.assertEqual(old[0]["task_id"], "PY-04")
        self.assertIs(old[0]["python_runtime_executed"], False)
        task = next(item for item in receipt["source_executions"]
                    if item["task_id"] == "PY-04")
        run = task["original_consumer_run"]
        self.assertEqual(run["reference"]["passed"], 6)
        self.assertEqual(run["mutant"]["passed"], 5)
        self.assertEqual(run["mutant"]["failed"], 1)
        self.assertEqual(run["initial_mutant_rejected"]["failed"], 2)
        for path, fake_value in (
            (("mutant", "failed_name"), "unrelated_test"),
            (("mutant", "starter_sha256"), "bad_sha"),
            (("initial_mutant_rejected", "failed"), 1),
        ):
            with self.subTest(path=path):
                changed = copy.deepcopy(receipt)
                item = next(r for r in changed["source_executions"]
                            if r["task_id"] == "PY-04")
                item["original_consumer_run"][path[0]][path[1]] = fake_value
                with self.assertRaisesRegex(ValueError, "PY-04 original consumer"):
                    summarizer.summarize(self.catalog, changed)
        changed = copy.deepcopy(receipt)
        changed["source_executions"].append(copy.deepcopy(old[0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            summarizer.summarize(self.catalog, changed)

    def test_stubbed_source_method_never_counts_as_original_consumer_suite(self):
        for task, expected_method in (
            ("PY-01", "SemanticPaymentPlanNormalizer.normalize"),
            ("PY-06", "_validate_grounding"),
        ):
            record = next(row for row in self.receipt["source_executions"]
                          if row["task_id"] == task)
            self.assertEqual(record["source_method"], expected_method)
            self.assertFalse(record["original_consumer_test_executed"])
            self.assertTrue(record["stubbed_dependencies"])
            for corrupt in (
                ("original_consumer_test_executed", True),
                ("independent_reviewer", True),
            ):
                with self.subTest(task=task, key=corrupt[0]):
                    poisoned = copy.deepcopy(self.receipt)
                    row = next(x for x in poisoned["source_executions"]
                               if x["task_id"] == task)
                    row[corrupt[0]] = corrupt[1]
                    with self.assertRaisesRegex(ValueError, "method smoke"):
                        summarizer.summarize(self.catalog, poisoned)
            poisoned = copy.deepcopy(self.receipt)
            row = next(x for x in poisoned["source_executions"]
                       if x["task_id"] == task)
            row["checks"]["expected_mutant_discrimination"] = 2
            with self.assertRaisesRegex(ValueError, "method smoke"):
                summarizer.summarize(self.catalog, poisoned)

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



class CurrentOperatorEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog_bytes = summarizer.CATALOG.read_bytes()
        cls.catalog = json.loads(cls.catalog_bytes)
        cls.index = json.loads(summarizer.LATEST_INDEX.read_text(encoding="utf-8"))

    def summary(self, index=None):
        return summarizer.summarize_current_operator(
            self.catalog, self.index if index is None else index,
            self.catalog_bytes,
        )

    def test_exact_sha_bound_current_snapshot_separates_origin_from_environment(self):
        result = self.summary()
        self.assertEqual(result["self_reported_local_baseline_mutant_pass"], "12/12")
        self.assertEqual(result["bound_framework_commit"],
                         "8bc26deddcb9ebd10c24d5cb482b6b8e50827d9d")
        self.assertEqual(result["original_consumer_test_files_invoked"], "9/12")
        self.assertEqual(result["complete_original_consumer_offline"], "6/12")
        self.assertEqual(result["original_js_tests_with_app_shims"], "3/12")
        self.assertEqual(result["framework_owned_bounded_oracles"], "3/12")
        self.assertEqual(result["task_scope"]["APP-01"]["test_origin"],
                         "ORIGINAL_CONSUMER_TEST_FILE")
        self.assertEqual(result["task_scope"]["APP-01"]["execution_environment"],
                         "NODE_OFFLINE_WITH_APPS_SCRIPT_SHIMS")
        self.assertFalse(result["task_scope"]["APP-01"]
                         ["complete_original_consumer_offline"])
        self.assertEqual(result["task_scope"]["APP-04"]["test_origin"],
                         "FRAMEWORK_OWNED_BOUNDED_ORACLE")
        self.assertFalse(result["task_scope"]["PY-03"]
                         ["complete_original_consumer_offline"])
        self.assertTrue(result["task_scope"]["PY-01"]
                        ["complete_original_consumer_offline"])
        self.assertFalse(result["operator_evidence_independently_verified"])
        self.assertEqual(result["independent_source_acceptance"], "0/12")
        self.assertEqual(result["internal_admission"], "HOLD_NOT_ADMITTED")
        self.assertFalse(result["release_authorized"])

    def test_history_is_not_rewritten_by_current_operator_index(self):
        old = summarizer.summarize(self.catalog, json.loads(
            summarizer.RECEIPT.read_text(encoding="utf-8")
        ))
        self.assertEqual(old["stage_counts"][summarizer.FULL], 4)
        self.assertEqual(old["stage_counts"][summarizer.STUBBED_METHOD], 2)
        self.assertEqual(self.summary()["complete_original_consumer_offline"], "6/12")

    def test_promoted_authority_wrong_sha_and_wrong_catalog_fail_closed(self):
        for key, value in [
            ("independent_review", "APPROVED"),
            ("model_comparisons", "1/48"),
            ("internal_admission", "ADMITTED"),
            ("release_authorized", True),
        ]:
            with self.subTest(key=key):
                index = copy.deepcopy(self.index)
                index["authority"][key] = value
                with self.assertRaisesRegex(ValueError, "authority"):
                    self.summary(index)
        index = copy.deepcopy(self.index)
        index["framework_commit_sha"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "Unbound"):
            self.summary(index)
        with self.assertRaisesRegex(ValueError, "Unbound"):
            summarizer.summarize_current_operator(
                self.catalog, self.index, b"changed catalog"
            )

    def test_catalog_binding_is_eol_independent_but_content_locked(self):
        # Preserve operator's original CRLF-byte digest without accepting
        # a modified catalog on LF hosts or in Linux dev environments.
        lf = self.catalog_bytes.replace(b"\r\n", b"\n")
        self.assertNotIn(b"\r", lf)
        crlf = lf.replace(b"\n", b"\r\n")
        for candidate in (lf, crlf):
            with self.subTest(eol="crlf" if candidate == crlf else "lf"):
                result = summarizer.summarize_current_operator(
                    self.catalog, self.index, candidate
                )
                self.assertEqual(
                    result["complete_original_consumer_offline"], "6/12"
                )
        self.assertNotEqual(lf, crlf)
        changed_catalog = lf.replace(b"APP-01", b"APP-99", 1)
        self.assertNotEqual(changed_catalog, lf)
        with self.assertRaisesRegex(ValueError, "Unbound"):
            summarizer.summarize_current_operator(
                self.catalog, self.index, changed_catalog
            )
        forged = copy.deepcopy(self.index)
        forged["catalog_canonical_lf_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Unbound"):
            summarizer.summarize_current_operator(
                self.catalog, forged, lf
            )
        forged = copy.deepcopy(self.index)
        forged["catalog_sha256"] = self.index["catalog_canonical_lf_sha256"]
        with self.assertRaisesRegex(ValueError, "Unbound"):
            summarizer.summarize_current_operator(
                self.catalog, forged, crlf
            )

    def test_scope_tampering_and_duplicates_fail_closed(self):
        scenarios = [
            ("test_origin", "ORIGINAL_CONSUMER_TEST_FILE"),
            ("complete_original_consumer_offline", True),
            ("execution_environment", "PRODUCTION_INTEGRATION"),
            ("independently_verified", True),
            ("consumer_integration_executed", True),
            ("production_writes", 1),
        ]
        for key, value in scenarios:
            with self.subTest(key=key):
                index = copy.deepcopy(self.index)
                record = next(r for r in index["observations"]
                              if r["task_id"] == "APP-04")
                record[key] = value
                with self.assertRaisesRegex(ValueError, "scope"):
                    self.summary(index)
        index = copy.deepcopy(self.index)
        index["observations"][1]["task_id"] = "APP-01"
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.summary(index)
        index = copy.deepcopy(self.index)
        index["observations"][0]["reference"]["stdout_sha256"] = "zz"
        with self.assertRaisesRegex(ValueError, "Unqualified"):
            self.summary(index)
        index = copy.deepcopy(self.index)
        index["observations"][0]["mutant"]["returncode"] = 0
        with self.assertRaisesRegex(ValueError, "Unqualified"):
            self.summary(index)


if __name__ == "__main__":
    unittest.main()
