"""Cross-repository retrospective receipt acceptance, synthetic-only checks."""
from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

from tools import core13_external_historical_receipt_boundary as boundary


def sample():
    return {
        "contract": boundary.CONTRACT,
        "project": "example/sample-repository",
        "source": {
            "origin": "git_pinned_historical",
            "old_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "fixed_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        },
        "runtime": {
            "kind": "docker_trusted_historical_only",
            "known_canary_verified": True,
            "host_mounts": 0,
            "model_calls": 0,
            "model_generated_code_executed": False,
            "untrusted_execution_certified": False,
        },
        "result": {
            "status": "SYNTHETIC_HISTORICAL_WITNESS_PASS",
            "checks": [
                {"id": "case_old_failure", "passed": True},
                {"id": "case_fixed_recovery", "passed": True},
                {"id": "case_old_positive", "passed": True},
                {"id": "case_fixed_positive", "passed": True},
            ],
        },
        "attestation": {
            "level": "operator_observed_not_independently_attested",
            "source_verified_claim": True,
            "independent_model_patch_oracle": False,
        },
    }


class HistoricalReceiptBoundaryTests(TestCase):
    def test_01_real_mainline_policy_used_to_omit_retrospective(self):
        result = boundary.inspect(sample())
        self.assertEqual(result["status"], boundary.STATUS)
        self.assertEqual(result["framework_decision"], "omit_task")
        self.assertEqual(result["prospective_task_events_added"], 0)
        self.assertEqual(result["framework_policy_preview"],
                         "AUTHORIZED_IN_MEMORY_PREVIEW")

    def test_02_refuses_model_or_stable_claim(self):
        result = boundary.inspect(sample())
        self.assertFalse(result["learning_exposure_confirmed"])
        self.assertFalse(result["independent_model_patch_oracle_established"])
        self.assertFalse(result["stable_promotable"])
        self.assertEqual(result["learning_effectiveness"], "NOT_ESTABLISHED")
        self.assertEqual(result["decision"], "BLOCK_AI_ACCEPTANCE")
        self.assertFalse(result["producer_claim_rechecked_from_git"])

    def test_03_untrusted_model_code_denied(self):
        case = sample()
        case["runtime"]["model_generated_code_executed"] = True
        with self.assertRaisesRegex(boundary.ReceiptDenied, "RUNTIME_SCOPE"):
            boundary.inspect(case)

    def test_04_cannot_claim_independent_oracle(self):
        case = sample()
        case["attestation"]["independent_model_patch_oracle"] = True
        with self.assertRaisesRegex(boundary.ReceiptDenied, "ATTESTATION_LEVEL"):
            boundary.inspect(case)

    def test_05_attested_docker_volumes_denied(self):
        case = sample()
        case["runtime"]["host_mounts"] = 1
        with self.assertRaisesRegex(boundary.ReceiptDenied, "RUNTIME_SCOPE"):
            boundary.inspect(case)

    def test_06_simulated_historical_is_not_prospective(self):
        case = sample()
        case["attestation"]["level"] = "prospective_task_learning"
        with self.assertRaisesRegex(boundary.ReceiptDenied, "ATTESTATION_LEVEL"):
            boundary.inspect(case)

    def test_07_contract_is_project_neutral(self):
        case = sample()
        case["project"] = "australia/real-estate-market"
        result = boundary.inspect(case)
        self.assertEqual(result["framework_decision"], "omit_task")
        self.assertFalse(result["stable_promotable"])

    def test_08_non_matching_fake_source_hash_denied(self):
        case = sample()
        case["source"]["old_sha256"] = case["source"]["fixed_sha256"]
        with self.assertRaisesRegex(boundary.ReceiptDenied, "SOURCE_IDENTITY"):
            boundary.inspect(case)

    def test_09_duplicate_check_id_denied(self):
        case = sample()
        case["result"]["checks"].append({"id": "case_old_failure", "passed": True})
        with self.assertRaisesRegex(boundary.ReceiptDenied, "HISTORICAL_CHECK"):
            boundary.inspect(case)

    def test_10_malformed_check_is_not_pass(self):
        case = sample()
        case["result"]["checks"][0]["passed"] = False
        with self.assertRaisesRegex(boundary.ReceiptDenied, "HISTORICAL_CHECK"):
            boundary.inspect(case)

    def test_11_deny_if_framework_policy_fails(self):
        with patch.object(boundary, "evaluate_proposal",
                          return_value={"status": "DENIED"}) as policy:
            with self.assertRaisesRegex(
                boundary.ReceiptDenied, "FRAMEWORK_POLICY_REDUCER_BOUNDARY",
            ):
                boundary.inspect(sample())
        policy.assert_called_once()

    def test_12_cli_redacts_failed_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text('{"contract": "secret-sentinel"}', encoding="utf-8")
            with patch("builtins.print") as printer:
                code = boundary.main(["--receipt", str(path)])
        self.assertEqual(code, 2)
        raw = printer.call_args.args[0]
        self.assertNotIn("secret-sentinel", raw)
        self.assertEqual(json.loads(raw)["status"], boundary.BLOCKED)

    def test_13_duplicate_json_fields_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text('{"contract":1,"contract":2}', encoding="utf-8")
            with patch("builtins.print") as printer:
                code = boundary.main(["--receipt", str(path)])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(printer.call_args.args[0])["status"],
                         boundary.BLOCKED)


if __name__ == "__main__":
    main()
