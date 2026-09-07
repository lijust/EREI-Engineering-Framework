import json
import tempfile
import unittest
from pathlib import Path

from tools.stable_readiness import StableReadinessError, _event_target_revision, derive_readiness


class StableReadinessTests(unittest.TestCase):
    def test_current_shape_can_close_cycle_without_claiming_stable(self):
        result = derive_readiness(
            cycle_pass=True,
            eval_pass=False,
            enforcement_pass=False,
            approvals_pass=False,
        )
        self.assertFalse(result["ready_for_final_approvals"])
        self.assertFalse(result["stable_ready"])
        self.assertNotIn("prospective_cycle_incomplete", result["blockers"])
        self.assertIn("exact_target_runtime_evidence_incomplete", result["blockers"])
        self.assertIn("release_enforcement_not_satisfied", result["blockers"])

    def test_preapproval_requires_cycle_eval_and_enforcement(self):
        result = derive_readiness(
            cycle_pass=True,
            eval_pass=True,
            enforcement_pass=True,
            approvals_pass=False,
        )
        self.assertTrue(result["ready_for_final_approvals"])
        self.assertFalse(result["stable_ready"])
        self.assertEqual(result["blockers"], ["final_architecture_security_approvals_not_bound"])

    def test_all_four_gates_are_required_for_stable(self):
        result = derive_readiness(
            cycle_pass=True,
            eval_pass=True,
            enforcement_pass=True,
            approvals_pass=True,
        )
        self.assertTrue(result["ready_for_final_approvals"])
        self.assertTrue(result["stable_ready"])
        self.assertEqual(result["blockers"], [])

    def test_missing_cycle_blocks_preapproval(self):
        result = derive_readiness(
            cycle_pass=False,
            eval_pass=True,
            enforcement_pass=True,
            approvals_pass=False,
        )
        self.assertFalse(result["ready_for_final_approvals"])
        self.assertIn("prospective_cycle_incomplete", result["blockers"])

    def test_pull_request_event_resolves_head_sha_not_synthetic_merge_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            path.write_text(json.dumps({
                "pull_request": {
                    "head": {"sha": "a" * 40},
                }
            }), encoding="utf-8")
            self.assertEqual(_event_target_revision(path), "a" * 40)

    def test_non_pull_request_event_has_no_event_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            path.write_text(json.dumps({"ref": "refs/heads/main"}), encoding="utf-8")
            self.assertIsNone(_event_target_revision(path))

    def test_malformed_pull_request_head_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            path.write_text(json.dumps({"pull_request": {"head": {"sha": "main"}}}), encoding="utf-8")
            with self.assertRaises(StableReadinessError):
                _event_target_revision(path)


if __name__ == "__main__":
    unittest.main()
