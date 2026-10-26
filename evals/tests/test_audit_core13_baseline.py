"""Mock-only regression suite for read-only frozen Core13 receipt audit."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from evals.experiments import audit_core13_baseline as audit


class FrozenRunner:
    def score(self, expectation, result, case_input):
        return result["output"]["decision"] == "omit_task", "synthetic evidence"


class Core13AuditTests(unittest.TestCase):
    def test_expected_thirteen_are_fixed_and_unique(self):
        self.assertEqual(len(audit.CASES), 13)
        self.assertEqual(len(set(id for id, folder in audit.CASES)), 13)
        self.assertEqual(audit.CASES[0][1], "smoke-005")
        self.assertEqual(audit.CASES[-1][1], "smoke-017")
        self.assertEqual(audit.EXPECTED_MODEL, "gemini-3.5-flash-lite")

    def test_fails_closed_on_missing_evidence_without_network(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(audit.gemini, "generate_raw_once") as net:
                result = audit.audit(Path(d), Path(d), Path(d))
        self.assertEqual(result["status"], "AUDIT_BLOCKED_UNVERIFIED")
        self.assertEqual(result["observed_cases"], 0)
        self.assertEqual(result["passed"], 0)
        self.assertEqual(result["independently_accepted_cases"], 0)
        self.assertFalse(result["stable_ready"])
        net.assert_not_called()

    def test_thirteen_replays_only_offline_and_no_partial_counts(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            mocked_case = {
                "id": "synthetic-only",
                "input": {"prompt": "synthetic public"},
                "expectations": [{"type": "behavioral_simulation"}],
            }
            with (
                mock.patch.object(audit.gemini, "verify_frozen_target"),
                mock.patch.object(audit.smoke, "frozen_runner", return_value=FrozenRunner()),
                mock.patch.object(audit.smoke, "load_one", side_effect=lambda *_: (
                    {"suite_id": "test", "artifact": "synthetic"},
                    {**mocked_case, "id": _[1]}, {"protocol_version": "2.0"})),
                mock.patch.object(audit.gemini, "prepare_one", return_value="PUBLIC"),
                mock.patch.object(audit, "inspect_case", side_effect=lambda _folder, *,
                                  case_id, **kw: {
                                      "case_id": case_id,
                                      "scored_pass": not case_id.endswith("MUTABLE-PIN-BLOCKED"),
                                      "failure_categories": [],
                                      "sha256_bound": True,
                                  }) as checked,
                mock.patch.object(audit.gemini, "generate_raw_once") as net,
            ):
                result = audit.audit(root, root, root)
            self.assertEqual(result["status"],
                             "OWNER_LOCAL_RESCORING_COMPLETE_UNVERIFIED")
            self.assertEqual(result["observed_cases"], 13)
            self.assertEqual(result["passed"], 12)
            self.assertEqual(result["failed"], 1)
            self.assertEqual(checked.call_count, 13)
            self.assertEqual(result["model_calls"], 0)
            self.assertEqual(result["network_requests"], 0)
            self.assertEqual(result["evidence_files_written"], 0)
            net.assert_not_called()

    def test_safe_category_maps_not_provider_text(self):
        self.assertEqual(audit.SAFE_FAIL_CODES[
            "simulation action must contain op"], "ACTION_OP_INVALID")
        self.assertEqual(audit.SAFE_FAIL_CODES[
            "capability blocking reason contradicts the required behavior"],
            "WRONG_BLOCK_CAUSE")
        self.assertNotIn("prompt", json.dumps(audit.SAFE_FAIL_CODES).lower())


if __name__ == "__main__":
    unittest.main()
