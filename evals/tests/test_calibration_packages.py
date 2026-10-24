"""Guard the offline calibration checker; no consumer/model execution."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "calibration", Path(__file__).resolve().parents[1] / "benchmarks/check_calibration.py")
calibration = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(calibration)


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = b"value = 1\n"
        target = self.root / "py/module.py"
        target.parent.mkdir()
        target.write_bytes(self.source)
        blob = hashlib.sha1(b"blob 10\0" + self.source).hexdigest()
        self.package = {
            "source": {"export_directory": "py"},
            "files": [{"path": "module.py", "git_blob": blob},
                      {"path": "test.py", "git_blob": blob}],
            "test_path": "test.py",
            "mutation": {"path": "module.py", "before": "value = 1", "after": "value = 2"},
            "starter_file_sha256": {
                "module.py": hashlib.sha256(b"value = 2\n").hexdigest(),
                "test.py": hashlib.sha256(self.source).hexdigest()},
        }
        (target.parent / "test.py").write_bytes(self.source)

    def test_public_calibration_result_redacts_private_consumer_output_and_frames(self):
        secret = "PRIVATE_SHEET_PASSWORD=redacted-source-should-never-appear"
        source = "/home/private-source/internal/normalizer.py:432"
        records = [
            {
                "returncode": 0, "stdout": "PASS " + secret + "\\n",
                "stderr": "",
                "checks": {"tests": 3, "failures": [], "errors": [], "skipped": 0},
            },
            {
                "returncode": 1, "stdout": "FAIL " + secret + "\\n",
                "stderr": "AssertionError: " + secret + "\\n" + source,
                "checks": {
                    "tests": 3,
                    "failures": ["test_error " + secret],
                    "errors": [],
                    "skipped": 0,
                },
            },
        ]
        published = [calibration.sanitized_result(r) for r in records]
        serialized = json.dumps(published, sort_keys=True)
        self.assertNotIn(secret, serialized)
        self.assertNotIn(source, serialized)
        self.assertNotIn("test_error", serialized)
        self.assertNotIn("AssertionError", serialized)
        self.assertNotIn("stdout\"", serialized)
        self.assertNotIn("stderr\"", serialized)
        self.assertEqual(published[0]["returncode"], 0)
        self.assertEqual(published[1]["returncode"], 1)
        self.assertEqual(published[1]["checks"], {
            "tests": 3, "failed_count": 1, "error_count": 0, "skipped_count": 0,
        })
        self.assertEqual(
            published[1]["stderr_sha256"],
            hashlib.sha256(records[1]["stderr"].encode("utf-8")).hexdigest(),
        )

    def test_private_source_exports_cannot_be_inside_public_framework_checkout(self):
        public_checkout = Path(calibration.__file__).resolve().parents[2]
        for location in (public_checkout, public_checkout / "private-exports",
                         public_checkout / "evals/benchmarks/exports"):
            with self.subTest(path=str(location)), self.assertRaisesRegex(
                    ValueError, "outside the public Framework checkout"):
                calibration.forbid_checkout_local_exports(location)
        calibration.forbid_checkout_local_exports(self.root)

    def test_verified_bytes_are_reused_without_mutating_source_export(self):
        reference = calibration.read_inputs(self.package, self.root)
        # An external change after the read cannot replace bytes used by the checker.
        (self.root / "py/module.py").write_bytes(b"changed after read")
        starter = calibration.starter_inputs(self.package, reference)
        self.assertEqual(reference["module.py"], self.source)
        self.assertEqual(starter["module.py"], b"value = 2\n")
        self.assertEqual(reference["test.py"], starter["test.py"])
        self.assertEqual((self.root / "py/module.py").read_bytes(), b"changed after read")

    def test_source_mismatch_fails_before_consumer_execution(self):
        (self.root / "py/module.py").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "blob mismatch"):
            calibration.read_inputs(self.package, self.root)

    def test_unsafe_paths_are_rejected(self):
        for value in ("", "../a", "/a", "C:/a", "a\\b", "a/../b", "a//b"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calibration.relative_path(value)

    def test_duplicate_inputs_are_rejected(self):
        self.package["files"].append(self.package["files"][0])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            calibration.read_inputs(self.package, self.root)

    def test_mutation_cannot_modify_tests_or_silently_drift(self):
        reference = calibration.read_inputs(self.package, self.root)
        changed = copy.deepcopy(self.package)
        changed["mutation"]["path"] = "test.py"
        with self.assertRaisesRegex(ValueError, "cannot change the test"):
            calibration.starter_inputs(changed, reference)
        for before in ("missing", "", "value"):
            changed = copy.deepcopy(self.package)
            changed["mutation"]["before"] = before
            with self.subTest(before=before), self.assertRaises(ValueError):
                calibration.starter_inputs(changed, reference)

    def test_python_errors_missing_tests_and_wrong_assertions_do_not_count(self):
        package = {"runtime": "python", "python_tests": ["test_a", "test_b"],
                   "expected_assertion": "test_a"}
        reference = {"returncode": 0, "checks": {
            "tests": 2, "failures": [], "errors": [], "skipped": 0}}
        starter = {"returncode": 1, "checks": {
            "tests": 2, "failures": ["test_a"], "errors": [], "skipped": 0}}
        self.assertTrue(calibration.assess(package, reference, starter))
        for field, value in (("tests", 1), ("errors", ["test_b"]),
                             ("skipped", 1), ("failures", ["test_b"]),
                             ("failures", ["test_a", "test_b"]),
                             ("failures", ["test_b", "test_a"]),
                             ("failures", ["test_a", "test_a"])):
            invalid = copy.deepcopy(starter)
            invalid["checks"][field] = value
            self.assertFalse(calibration.assess(package, reference, invalid))

    def test_node_startup_errors_are_not_successful_mutant_detection(self):
        package = {"runtime": "node", "expected_assertion": "Missing expected rejection.",
                   "test_path": "tests/behavior.test.js", "expected_assertion_line": 57}
        reference = {"returncode": 0}
        for message in ("Cannot find module", "SyntaxError", "Missing expected rejection."):
            self.assertFalse(calibration.assess(package, reference,
                             {"returncode": 1, "stderr": message}))
        self.assertTrue(calibration.assess(package, reference, {"returncode": 1,
                        "stderr": "AssertionError [ERR_ASSERTION]: Missing expected rejection.\n"
                        "    at async /tmp/fixture/tests/behavior.test.js:57:3\n"}))


    def test_node_unrelated_assertions_do_not_count_as_detection(self):
        package = {"runtime": "node", "expected_assertion": "AssertionError [ERR_ASSERTION]",
                   "test_path": "tests/behavior.test.js", "expected_assertion_line": 41}
        reference = {"returncode": 0}
        for location in ("tests/behavior.test.js:40:10", "tests/other.test.js:41:10"):
            with self.subTest(location=location):
                self.assertFalse(calibration.assess(package, reference, {
                    "returncode": 1, "stderr": "AssertionError [ERR_ASSERTION]: unrelated\n"
                    "    at Object.<anonymous> (/tmp/fixture/" + location + ")\n"}))
        self.assertFalse(calibration.assess(package, reference, {
            "returncode": 1, "stderr": "AssertionError [ERR_ASSERTION]: "
            "mention /tmp/fixture/tests/behavior.test.js:41:10 without a stack frame"}))
        for frame in ("    at Object.<anonymous> (/tmp/fixture/tests/behavior.test.js:41:10)",
                      r"    at Object.<anonymous> (C:\temp\fixture\tests\behavior.test.js:41:10)",
                      "    at async /tmp/fixture/tests/behavior.test.js:41:10"):
            with self.subTest(frame=frame):
                self.assertTrue(calibration.assess(package, reference, {
                    "returncode": 1, "stderr": "AssertionError [ERR_ASSERTION]\n" + frame + "\n"}))

    def test_app04_public_oracle_reports_only_the_expected_gap_reuse_violation(self):
        package = {"runtime": "node", "behavioral_oracle": "APP04_PROJECT_ID_MAX_PLUS_ONE",
                   "test_path": "tests/developer-validation-project-id-policy.test.js"}
        success = {"returncode": 0, "stdout": "APP04_BEHAVIORAL_ORACLE_PASS\n", "stderr": ""}
        failure = {"returncode": 1, "stdout": "",
                   "stderr": "AssertionError [ERR_ASSERTION]: APP04_MAX_PLUS_ONE_NO_GAP_REUSE\n"
                             "    at [eval]:34:8\n"}
        self.assertTrue(calibration.assess(package, success, failure))
        self.assertFalse(calibration.assess(package, success, {**failure,
                         "stderr": "Error: Cannot find module APP04_MAX_PLUS_ONE_NO_GAP_REUSE"}))
        self.assertFalse(calibration.assess(package, success, {**failure,
                         "stderr": "AssertionError [ERR_ASSERTION]: unrelated assertion"}))
        self.assertFalse(calibration.assess(package, {**success, "stdout": ""}, failure))
        self.assertFalse(calibration.assess(package, success,
                         {**failure, "returncode": 0}))

    def test_app04_public_oracle_invokes_node_without_google_or_network(self):
        node = __import__("shutil").which("node")
        if node is None:
            self.skipTest("Node executable unavailable")
        package = {"runtime": "node", "behavioral_oracle": "APP04_PROJECT_ID_MAX_PLUS_ONE",
                   "test_path": "tests/developer-validation-project-id-policy.test.js"}
        path = "apps/developer-validation-intake/MissingProjectInsertReadiness.gs"
        base = ("function dviMissingProjectInsertMasterInventory_() {"
                "return {projectIdMin:2,projectIdMax:5,projectIdGapCount:2,"
                "projectIdNonblankAll:true,projectIdUnique:true,"
                "projectIdPositiveInteger:true,projectIdNextCandidate:6};}")
        mutant = base.replace("projectIdNextCandidate:6", "projectIdNextCandidate:3")
        good = calibration.run_copy(package, {path: base.encode()}, node)
        bad = calibration.run_copy(package, {path: mutant.encode()}, node)
        self.assertTrue(calibration.assess(package, good, bad),
                        (good, bad))
        self.assertNotIn("GOOGLE", good["stdout"])
        self.assertNotIn("GOOGLE", bad["stderr"])

    def test_app05_public_oracle_detects_broken_repository_cache_with_provider_parity(self):
        node = __import__("shutil").which("node")
        if node is None:
            self.skipTest("Node executable unavailable")
        package = {"runtime": "node", "behavioral_oracle": "APP05_REPOSITORY_CACHE_PARITY",
                   "test_path": "tests/error-catalog-repository-candidate.test.js"}
        # This micro-fixture is only a smoke test for the Framework-owned oracle:
        # the real pinned builder, legacy service and test remain sourced by
        # immutable git blobs and checked separately by read_inputs.
        legacy = """const ErrorService = (function() {
          var cache_ = null;
          function catalog_() {
            if (cache_) return cache_;
            var t = getTable_(openSheetById_(getAdminId_(), EREI.ADMIN_SHEETS.ERRORS), 1), map = {};
            t.rows.forEach(function(r) {
              var o = rowToObject_(t.headers, r); if (o.error_code) map[o.error_code] = o;
            });
            cache_ = map; return map;
          }
          function fromCode(code, details) {
            var row = catalog_()[code] || catalog_().INTERNAL_ERROR || {};
            var quota429 = ['SEARCH_LIMIT','EXPORT_LIMIT','RESULT_EXPOSURE_LIMIT'].indexOf(code) >= 0;
            var http = code.indexOf('AUTH_') === 0 ? 401 : (code === 'PERMISSION_DENIED' ? 403 : (code === 'NOT_FOUND' ? 404 : (code.indexOf('RATE_LIMIT') >= 0 || code === 'RATE_LIMIT' || quota429 ? 429 : 400)));
            if (code === 'INTERNAL_ERROR') http = 500;
            return new EreiError_(code, normalizeString_(row.user_message) || code, details || null, http);
          }
          return {fromCode:fromCode};
        })();"""
        candidate = legacy.replace("const ErrorService = (function() {",
            "const ErrorCatalogRepository = (function() {"
            "var cache_ = null;"
            "function catalog() {"
            "if (cache_) return cache_;"
            "var t = getTable_(openSheetById_(getAdminId_(), EREI.ADMIN_SHEETS.ERRORS), 1), map = {};"
            "t.rows.forEach(function(r) { var o = rowToObject_(t.headers,r); if (o.error_code) map[o.error_code] = o; });"
            "cache_ = map; return map;"
            "}"
            "return {catalog:catalog};"
            "})();"
            "const ErrorService = (function() {").replace(
            """var cache_ = null;
          function catalog_() {
            if (cache_) return cache_;
            var t = getTable_(openSheetById_(getAdminId_(), EREI.ADMIN_SHEETS.ERRORS), 1), map = {};
            t.rows.forEach(function(r) {
              var o = rowToObject_(t.headers, r); if (o.error_code) map[o.error_code] = o;
            });
            cache_ = map; return map;
          }""", "").replace("catalog_()", "ErrorCatalogRepository.catalog()")
        builder = ("function candidateErrorServiceSource() { return "
                   + json.dumps(candidate) + "; }"
                   "module.exports = {candidateErrorServiceSource};")
        path = "tools/build-error-catalog-repository-candidate.js"
        original_path = "src/11_ErrorService.gs"
        good = calibration.run_copy(package, {path: builder.encode(),
                                            original_path: legacy.encode()}, node)
        mutant = builder.replace("if (cache_) return cache_;",
                                 "if (false) return cache_;")
        bad = calibration.run_copy(package, {path: mutant.encode(),
                                           original_path: legacy.encode()}, node)
        self.assertTrue(calibration.assess(package, good, bad), (good, bad))
        self.assertFalse(calibration.assess(package, good, {**bad,
                         "stderr": "Error: Cannot find module APP05_REPOSITORY_PARITY_AND_CACHE"}))
        self.assertFalse(calibration.assess(package, good, {**bad, "returncode": 0}))

    def test_py03_boundaries_detect_only_substring_regression_without_extractor_stack(self):
        package = {
            "runtime": "python", "behavioral_oracle": "PY03_NAWY_EXACT_BOUNDARY",
            "test_path": "tests/unit/test_nawy_payment_section_boundary.py",
            "python_tests": [
                "test_exact_english_marker", "test_exact_arabic_marker",
                "test_exact_not_substring_boundary",
            ],
            "expected_assertion": "test_exact_not_substring_boundary",
        }
        source = '''
from typing import Iterable
class NawyExtractor(_PaymentNawyExtractor):
    _PAYMENT_STOP_EN = {"location on map", "call us"}
    _PAYMENT_STOP_AR = {"الموقع على الخريطة", "اتصل بنا"}
    @classmethod
    def _normalized_boundary_text(cls, value: str) -> str:
        return " ".join(cls._clean_text(value).casefold().split())
    @classmethod
    def _trim_payment_page_chrome(cls, lines: Iterable[str], *, locale: str) -> list[str]:
        stops = cls._PAYMENT_STOP_AR if locale == "ar" else cls._PAYMENT_STOP_EN
        result = []
        for line in lines:
            if cls._normalized_boundary_text(line) in stops:
                break
            result.append(line)
        return result
    @classmethod
    def _payment_section_lines(cls, raw_html: str, locale: str) -> list[str]:
        lines = super()._payment_section_lines(raw_html, locale)
        return cls._trim_payment_page_chrome(lines, locale=locale)
'''
        path = "extractors/nawy/payment_section_boundary_extractor.py"
        starter = source.replace(
            "if cls._normalized_boundary_text(line) in stops:",
            "if any(stop in cls._normalized_boundary_text(line) for stop in stops):"
        )
        reference = calibration.run_copy(package, {path: source.encode()}, None)
        mutant = calibration.run_copy(package, {path: starter.encode()}, None)
        self.assertTrue(calibration.assess(package, reference, mutant),
                        (reference, mutant))
        self.assertEqual(reference["checks"]["tests"], 3)
        self.assertEqual(mutant["checks"]["failures"],
                         ["test_exact_not_substring_boundary"])
        # Reject a mere parsing/import error, and off-target failures.
        for changes in (
            {"returncode": 2},
            {"checks": {**mutant["checks"], "errors": ["test_exact_english_marker"]}},
            {"checks": {**mutant["checks"],
                        "failures": ["test_exact_english_marker"]}},
        ):
            self.assertFalse(calibration.assess(
                package, reference, {**mutant, **changes}
            ))

    def test_python_dependency_pin_opt_in_is_fail_closed_and_preserves_isolation(self):
        package = {"runtime": "python", "test_path": "tests/unit/test_recovery.py",
                   "python_tests": ["test_error"], "dependency_versions": {
                       "jsonschema": "4.26.0", "attrs": "26.1.0",
                   }}
        checks = {"tests": 1, "failures": [], "errors": [], "skipped": 0}
        response = calibration.subprocess.CompletedProcess(
            ["python"], 0, stdout=json.dumps(checks), stderr="")
        with patch.object(calibration.subprocess, "run", return_value=response) as run:
            result = calibration.run_copy(
                package, {"tests/unit/test_recovery.py": b"def test_error(): pass\n"},
                None)
        command = run.call_args.args[0]
        self.assertIn("-I", command)
        self.assertIn("-B", command)
        self.assertNotIn("-S", command, "pinned site mode must be explicit")
        self.assertEqual(json.loads(command[-1]), package["dependency_versions"])
        self.assertEqual(result["checks"]["tests"], 1)
        self.assertEqual(run.call_args.kwargs["shell"], False)
        self.assertEqual(run.call_args.kwargs["timeout"], 30)
        self.assertNotIn("PYTHONPATH", run.call_args.kwargs["env"])
        unpinned = {**package, "dependency_versions": {}}
        with patch.object(calibration.subprocess, "run", return_value=response) as unpinned_run:
            calibration.run_copy(
                unpinned, {"tests/unit/test_recovery.py": b""}, None)
        self.assertIn("-S", unpinned_run.call_args.args[0],
                      "default Python mode must still disable site packages")
        for bad in ([], {"jsonschema": ""}, {"jsonschema": 12}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                calibration.run_copy({**package, "dependency_versions": bad},
                                     {"tests/unit/test_recovery.py": b""}, None)

    def test_timeout_is_not_converted_to_a_successful_calibration(self):
        self.package.update(runtime="python", python_tests=[])
        with patch.object(calibration.subprocess, "run",
                          side_effect=calibration.subprocess.TimeoutExpired("check", 30)):
            with self.assertRaises(calibration.subprocess.TimeoutExpired):
                calibration.run_copy(self.package, {"test.py": b""}, None)

    def test_prepared_catalog_remains_public_and_has_no_execution_authority(self):
        catalog = json.loads(calibration.CATALOG.read_text(encoding="utf-8"))
        self.assertIs(catalog["execution_authorized"], False)
        self.assertEqual(catalog["purpose"], "PUBLIC_CALIBRATION_NOT_HIDDEN_ACCEPTANCE")
        ids = [package["task_id"] for package in catalog["packages"]]
        self.assertEqual(len(ids), len(set(ids)))
        for package in catalog["packages"]:
            self.assertEqual(package["state"], "PUBLIC_CALIBRATION_ONLY")
            self.assertEqual(package["prompt_sha256"],
                             hashlib.sha256(package["prompt"].encode()).hexdigest())

    def test_python_provider_recipes_are_source_pinned_and_version_locked(self):
        catalog = json.loads(calibration.CATALOG.read_text(encoding="utf-8"))
        entries = {package["task_id"]: package for package in catalog["packages"]}
        expected_versions = {
            "jsonschema": "4.26.0", "attrs": "26.1.0",
            "referencing": "0.37.0", "rpds-py": "2026.5.1",
            "jsonschema-specifications": "2025.9.1",
        }
        self.assertEqual(len(entries), 12)
        self.assertEqual({p["task_id"] for p in catalog["packages"]
                          if p.get("dependency_versions")}, {"PY-01", "PY-06"})
        for task_id, num_source_files, num_tests, target in (
            ("PY-01", 3, 20, "test_provider_failure_does_not_destroy_raw_evidence"),
            ("PY-06", 10, 4,
             "test_word_number_grounding_does_not_allow_derived_year_to_month_conversion"),
        ):
            package = entries[task_id]
            self.assertEqual(package["runtime"], "python")
            self.assertEqual(package["dependency_versions"], expected_versions)
            self.assertEqual(len(package["files"]), num_source_files)
            self.assertEqual(len(package["python_tests"]), num_tests)
            self.assertEqual(len(set(package["python_tests"])), num_tests)
            self.assertEqual(package["expected_assertion"], target)
            self.assertIn(target, package["python_tests"])
            self.assertEqual(set(package["starter_file_sha256"]),
                             {f["path"] for f in package["files"]})
            self.assertNotEqual(package["mutation"]["before"],
                                package["mutation"]["after"])
        self.assertEqual(entries["PY-06"]["source"]["repository"], "lijust/EREI-3.2")
        self.assertEqual(entries["PY-06"]["source"]["commit"],
                         "87d730ddc3547f863de2a6895e91f9b83e9c6e72")

    def test_plan_digests_bind_prepared_starters_without_removing_pending_slots(self):
        catalog = json.loads(calibration.CATALOG.read_text(encoding="utf-8"))
        plan = json.loads(calibration.CATALOG.with_name("v1-v2-pilot.json").read_text(
            encoding="utf-8"))
        self.assertEqual(len(plan["tasks"]), 12)
        by_id = {package["task_id"]: package for package in catalog["packages"]}
        self.assertEqual(len(by_id), 12)
        linked = set()
        for task in plan["tasks"]:
            self.assertIsNone(task["hidden_acceptance_sha256"])
            if task["task_id"] in by_id:
                package = by_id[task["task_id"]]
                self.assertEqual(task["state"], "PUBLIC_CALIBRATION_RECIPE_PREPARED")
                self.assertEqual(task.get("calibration_package"), {
                    "path": "evals/benchmarks/calibration-packages.json",
                    "task_id": task["task_id"],
                }, "prepared recipe must resolve to its own package")
                linked.add(task["task_id"])
                encoded = json.dumps(package["starter_file_sha256"],
                                     sort_keys=True, separators=(",", ":")).encode()
                self.assertEqual(task["fixture_sha256"], hashlib.sha256(encoded).hexdigest())
                self.assertEqual(task["prompt_sha256"], package["prompt_sha256"])
            else:
                self.assertEqual(task["state"], "PROPOSAL_FIXTURE_NOT_PREPARED")
                self.assertNotIn("calibration_package", task)
                self.assertIsNone(task["fixture_sha256"])
                self.assertIsNone(task["prompt_sha256"])
        self.assertEqual(linked, set(by_id))


if __name__ == "__main__":
    unittest.main()
