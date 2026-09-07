import json
import sys
import tempfile
import unittest
from pathlib import Path

from evals import exact_target_run


class ExactTargetRunTests(unittest.TestCase):
    def suite(self, root: Path, *, assurance_scope: str = "behavioral_runtime", suite_id: str = "target-smoke") -> Path:
        path = root / f"{suite_id}.eval.json"
        path.write_text(json.dumps({
            "schema_version": "1.0",
            "suite_id": suite_id,
            "artifact": "skills/impact-analysis",
            "assurance_scope": assurance_scope,
            "cases": [{
                "id": "CASE-1-L3-SECRET-HINT",
                "input": {"prompt": "hello"},
                "context": {"project": "demo"},
                "tags": ["L3", "security", "expected-hint"],
                "expectations": [{"type": "output_contains_all", "values": ["hello"]}],
            }],
        }), encoding="utf-8")
        return path

    def adapter(self, root: Path) -> Path:
        path = root / "target_adapter.py"
        path.write_text(
            "import json,sys\n"
            "request=json.loads(sys.stdin.read())\n"
            "print(json.dumps({'output':'hello from external runtime'}))\n",
            encoding="utf-8",
        )
        return path

    def blind_asserting_adapter(self, root: Path) -> Path:
        path = root / "blind_asserting_adapter.py"
        path.write_text(
            "import json,sys\n"
            "r=json.loads(sys.stdin.read())\n"
            "ok=(set(r)=={'protocol_version','suite_id','case_id','artifact','input','context'} "
            "and r['suite_id'].startswith('blind-suite-') "
            "and r['case_id'].startswith('blind-case-') "
            "and r['suite_id']!='target-smoke' "
            "and r['case_id']!='CASE-1-L3-SECRET-HINT' "
            "and 'tags' not in r and 'expectations' not in r "
            "and r['artifact']=='skills/impact-analysis' "
            "and r['input']=={'prompt':'hello'} "
            "and r['context']=={'project':'demo'})\n"
            "if not ok:\n"
            "    print(json.dumps(r), file=sys.stderr); sys.exit(7)\n"
            "print(json.dumps({'output':'hello from blinded external runtime'}))\n",
            encoding="utf-8",
        )
        return path

    def test_blinded_request_removes_identity_tags_and_expectations(self):
        suite = {
            "suite_id": "impact-analysis-v1",
            "artifact": "skills/impact-analysis",
        }
        case = {
            "id": "T-001-AUTH-TENANT",
            "input": {"prompt": "analyze"},
            "context": {"tenant": "unknown"},
            "tags": ["L3", "security"],
            "expectations": [{"type": "metadata_equals", "key": "risk", "value": "L3"}],
        }
        first = exact_target_run._blinded_request(suite, case)
        second = exact_target_run._blinded_request(suite, case)
        self.assertEqual(first, second)
        self.assertEqual(set(first), {"protocol_version", "suite_id", "case_id", "artifact", "input", "context"})
        self.assertTrue(first["suite_id"].startswith("blind-suite-"))
        self.assertTrue(first["case_id"].startswith("blind-case-"))
        self.assertNotEqual(first["suite_id"], suite["suite_id"])
        self.assertNotEqual(first["case_id"], case["id"])
        self.assertNotIn("tags", first)
        self.assertNotIn("expectations", first)
        self.assertEqual(first["artifact"], "skills/impact-analysis")
        self.assertEqual(first["input"], {"prompt": "analyze"})
        self.assertEqual(first["context"], {"tenant": "unknown"})

    def test_blinded_case_id_changes_across_cases(self):
        suite = {"suite_id": "suite", "artifact": "skills/impact-analysis"}
        one = exact_target_run._blinded_request(suite, {"id": "CASE-A", "input": {}})
        two = exact_target_run._blinded_request(suite, {"id": "CASE-B", "input": {}})
        self.assertEqual(one["suite_id"], two["suite_id"])
        self.assertNotEqual(one["case_id"], two["case_id"])

    def test_run_suites_uses_blinded_transport_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite = self.suite(root)
            adapter = self.blind_asserting_adapter(root)
            manifest, _ = exact_target_run.run_suites(
                [str(suite)],
                adapter_command=f"{sys.executable} {adapter}",
                adapter_id="external-test-adapter",
                adapter_revision="a" * 40,
                runtime_id="external-runtime",
                runtime_version="1",
                runtime_evidence=["test-runtime:external-process"],
                framework_ref="b" * 40,
                manifest_relpath="evals/exact-target-runs/test.json",
                produced_at="2026-09-07T12:00:00Z",
                run_id="ETR-20260907T120000Z-ABCDEF12",
            )
            self.assertEqual(manifest["executions"][0]["status"], "pass")

    def test_generates_bound_v2_reconstructible_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite = self.suite(root)
            adapter = self.adapter(root)
            manifest, evidence = exact_target_run.run_suites(
                [str(suite)],
                adapter_command=f"{sys.executable} {adapter}",
                adapter_id="external-test-adapter",
                adapter_revision="a" * 40,
                runtime_id="external-runtime",
                runtime_version="1",
                runtime_evidence=["test-runtime:external-process"],
                framework_ref="b" * 40,
                manifest_relpath="evals/exact-target-runs/test.json",
                produced_at="2026-09-07T12:00:00Z",
                run_id="ETR-20260907T120000Z-ABCDEF12",
            )
            self.assertEqual(manifest["schema_version"], 2)
            execution = manifest["executions"][0]
            self.assertEqual(execution["status"], "pass")
            self.assertFalse(execution["adapter_error"])
            self.assertEqual(execution["response"], {"output": "hello from external runtime"})
            self.assertEqual(execution["response_digest"], exact_target_run._canonical_digest(execution["response"]))
            self.assertEqual(evidence["schema_version"], 2)
            row = evidence["executions"][0]
            self.assertEqual(row["assurance_level"], "exact_target_runtime")
            self.assertTrue(row["independent_runtime"])
            self.assertEqual(row["evidence_ref"], "exact-target-run:evals/exact-target-runs/test.json#target-smoke/CASE-1-L3-SECRET-HINT")

    def test_harness_only_suite_is_not_sent_to_external_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            harness = self.suite(root, assurance_scope="harness_only", suite_id="harness-only")
            behavioral = self.suite(root, assurance_scope="behavioral_runtime", suite_id="behavioral")
            adapter = self.adapter(root)
            manifest, evidence = exact_target_run.run_suites(
                [str(harness), str(behavioral)],
                adapter_command=f"{sys.executable} {adapter}",
                adapter_id="external-test-adapter",
                adapter_revision="a" * 40,
                runtime_id="external-runtime",
                runtime_version="1",
                runtime_evidence=["test-runtime:external-process"],
                framework_ref="b" * 40,
                manifest_relpath="evals/exact-target-runs/test.json",
                produced_at="2026-09-07T12:00:00Z",
                run_id="ETR-20260907T120000Z-ABCDEF12",
            )
            manifest_keys = {(item["suite_id"], item["case_id"]) for item in manifest["executions"]}
            evidence_keys = {(item["suite_id"], item["case_id"]) for item in evidence["executions"]}
            self.assertEqual(manifest_keys, {("behavioral", "CASE-1-L3-SECRET-HINT")})
            self.assertEqual(evidence_keys, {("behavioral", "CASE-1-L3-SECRET-HINT")})

    def test_harness_only_selection_fails_instead_of_emitting_empty_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            harness = self.suite(root, assurance_scope="harness_only", suite_id="harness-only")
            with self.assertRaisesRegex(exact_target_run.ExactTargetRunError, "no behavioral_runtime"):
                exact_target_run.run_suites(
                    [str(harness)],
                    adapter_command=f"{sys.executable} {self.adapter(root)}",
                    adapter_id="external-test-adapter",
                    adapter_revision="a" * 40,
                    runtime_id="external-runtime",
                    runtime_version="1",
                    runtime_evidence=["test-runtime:external-process"],
                    framework_ref="b" * 40,
                    manifest_relpath="evals/exact-target-runs/test.json",
                    produced_at="2026-09-07T12:00:00Z",
                    run_id="ETR-20260907T120000Z-ABCDEF12",
                )

    def test_rejects_reference_oracle_as_exact_target(self):
        with self.assertRaisesRegex(exact_target_run.ExactTargetRunError, "reference/mock"):
            exact_target_run.run_suites(
                ["evals/cases"],
                adapter_command="python evals/fixtures/reference_oracle_adapter.py",
                adapter_id="fake",
                adapter_revision="a" * 40,
                runtime_id="fake",
                runtime_version="1",
                runtime_evidence=["fake"],
                framework_ref="b" * 40,
                manifest_relpath="evals/exact-target-runs/fake.json",
            )

    def test_requires_runtime_identity_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(exact_target_run.ExactTargetRunError, "runtime identity evidence"):
                exact_target_run.run_suites(
                    [str(self.suite(root))],
                    adapter_command=f"{sys.executable} {self.adapter(root)}",
                    adapter_id="external-test-adapter",
                    adapter_revision="a" * 40,
                    runtime_id="external-runtime",
                    runtime_version="1",
                    runtime_evidence=[],
                    framework_ref="b" * 40,
                    manifest_relpath="evals/exact-target-runs/test.json",
                )


if __name__ == "__main__":
    unittest.main()
