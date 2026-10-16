"""Blind external-runtime transport regressions, no real model or credentials."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from evals import exact_target_run


class BlindExternalTransportTests(unittest.TestCase):
    def suite(self):
        return {
            "schema_version": "1.0",
            "suite_id": "human-readable-security-eval",
            "artifact": "skills/impact-analysis",
            "assurance_scope": "behavioral_runtime",
            "cases": [
                {
                    "id": "CASE-HIGH-RISK",
                    "input": {"prompt": "analyze"},
                    "context": {"project": "test"},
                    "tags": ["secret-risk-hint", "L3"],
                    "expectations": [{"type": "metadata_equals", "key": "risk", "value": "L3"}],
                }
            ],
        }

    def test_external_request_has_only_opaque_one_use_ids_and_task_material(self):
        suite = self.suite()
        a = exact_target_run._blinded_request(suite, suite["cases"][0])
        b = exact_target_run._blinded_request(suite, suite["cases"][0])
        self.assertEqual(set(a), {"protocol_version", "suite_id", "case_id", "artifact", "input", "context"})
        self.assertEqual(a["protocol_version"], "2.0")
        self.assertRegex(a["suite_id"], r"^blind-suite-[0-9a-f]{16}$")
        self.assertRegex(a["case_id"], r"^blind-case-[0-9a-f]{16}$")
        self.assertNotEqual(a["suite_id"], b["suite_id"])
        self.assertNotEqual(a["case_id"], b["case_id"])
        self.assertNotIn("secret-risk-hint", json.dumps(a))
        self.assertNotIn("CASE-HIGH-RISK", json.dumps(a))
        self.assertNotIn("L3", json.dumps(a))
        self.assertEqual(a["input"], {"prompt": "analyze"})
        self.assertEqual(a["context"], {"project": "test"})

    def test_runtime_gets_blind_ids_but_authoritative_evidence_keeps_originals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite_file = root / "case.eval.json"
            suite_file.write_text(json.dumps(self.suite()), encoding="utf-8")
            adapter = root / "adapter.py"
            adapter.write_text(
                "import json,sys\n"
                "r=json.loads(sys.stdin.read())\n"
                "assert set(r)=={'protocol_version','suite_id','case_id','artifact','input','context'}\n"
                "assert r['protocol_version']=='2.0'\n"
                "assert r['suite_id'].startswith('blind-suite-')\n"
                "assert r['case_id'].startswith('blind-case-')\n"
                "assert 'L3' not in json.dumps(r)\n"
                "print(json.dumps({'output':'ok','metadata':{'risk':'L3'}}))\n",
                encoding="utf-8",
            )
            manifest, evidence = exact_target_run.run_suites(
                [str(suite_file)],
                adapter_command=f"{sys.executable} {adapter}",
                adapter_id="independent-test",
                adapter_revision="a"*40,
                runtime_id="isolated-test",
                runtime_version="1",
                runtime_evidence=["unit-test"],
                framework_ref="b"*40,
                manifest_relpath="evals/exact-target-runs/test-blind.json",
                produced_at="2026-10-16T00:00:00Z",
                run_id="ETR-20261016T000000Z-AB123456",
            )
            self.assertEqual(manifest["executions"][0]["status"], "pass")
            self.assertEqual(evidence["executions"][0]["case_id"], "CASE-HIGH-RISK")
            self.assertEqual(evidence["executions"][0]["suite_id"], "human-readable-security-eval")


if __name__ == "__main__":
    unittest.main()
