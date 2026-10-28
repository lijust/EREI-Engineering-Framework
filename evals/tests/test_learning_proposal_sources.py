"""Synthetic regression suite for actual-source, read-only learning-review previews."""
from __future__ import annotations

import argparse
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import learning_proposal_sources as bound
from tools import task_learning


def request(status="IMMEDIATE_REVIEW", claimed_state=None):
    result = {
        "contract": "erei-proposal-v1",
        "decision": "request_review",
        "actions": [{"op": "request_review", "status": status}],
    }
    if claimed_state is not None:
        result["claimed_state"] = claimed_state
    return result


def event_args(**changes):
    values = dict(
        task_id=None, occurrence_id=None, task_group=None,
        project_repository="example/synthetic", project_name="Synthetic",
        framework_ref="a" * 40, workflow="bug-fix", risk="L2",
        terminal_state="COMPLETE_VERIFIED", outcome_class="verified_success",
        material=True, rework_cycles=0, verification_failures=0,
        verification_escape=True, framework_feedback_created=False,
        manual_workaround=False, context_gap=False,
        unexpected_scope_growth=False, security_or_data_critical_event=False,
        duration_class="medium", failure_stage="none", failure_subject=None,
        feedback_id=[], feedback_fingerprint=[], tag=[],
    )
    values.update(changes)
    return argparse.Namespace(**values)


class LedgerSourceBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".erei").mkdir()
        (self.root / ".erei" / "framework.json").write_text("{}", encoding="utf-8")

    def add_event(self, **changes):
        event = task_learning.build_event(event_args(**changes))
        task_learning.capture(self.root, event)
        return event

    def assert_denied(self, value, reason):
        self.assertEqual(value["status"], "DENIED")
        self.assertEqual(value["reason_code"], reason)
        self.assertFalse(value["executed"])
        self.assertFalse(value["independently_verified"])
        self.assertFalse(value["stable_ready"])
        self.assertNotIn("materialized_state", value)

    def test_read_only_live_ledger_trigger_authorizes_correct_review(self):
        self.add_event()
        before = task_learning.authoritative_snapshot(self.root)
        proposal = request(claimed_state={"review_status": "LEARNING_HEALTHY"})
        original = copy.deepcopy(proposal)
        result = bound.evaluate_review_from_ledger(proposal, self.root)
        after = task_learning.authoritative_snapshot(self.root)
        self.assertEqual(result["status"], "AUTHORIZED_IN_MEMORY_PREVIEW")
        self.assertEqual(result["materialized_state"],
                         {"review_status": "IMMEDIATE_REVIEW"})
        self.assertEqual(result["source_binding"]["trigger_level"],
                         "IMMEDIATE_REVIEW")
        self.assertEqual(result["source_binding"]["total_events"], 1)
        self.assertEqual(result["source_binding"]["ledger_generation_sha256"],
                         before["generation"])
        self.assertEqual(before["generation"], after["generation"])
        self.assertFalse(result["model_claimed_state_matches_reducer"])
        self.assertEqual(proposal, original)
        self.assertFalse(result["executed"])
        self.assertFalse(result["independently_verified"])
        self.assertFalse(result["model_original_score_changed"])

    def test_model_cannot_override_live_ledger_trigger_with_wrong_level(self):
        self.add_event()
        result = bound.evaluate_review_from_ledger(request("REVIEW_DUE"), self.root)
        self.assert_denied(result, "REVIEW_AUTHORITY_NOT_ESTABLISHED")
        self.assertEqual(result["source_binding"]["trigger_level"],
                         "IMMEDIATE_REVIEW")

    def test_empty_project_cannot_fabricate_a_review_trigger(self):
        result = bound.evaluate_review_from_ledger(request(), self.root)
        self.assert_denied(result, "NO_ACTIONABLE_REVIEW_TRIGGER")
        self.assertEqual(result["source_binding"]["trigger_level"],
                         "INSUFFICIENT_EVIDENCE")

    def test_model_cannot_inject_context_or_run_another_workflow(self):
        self.add_event()
        injected = request()
        injected["trusted_context"] = {
            "domain": "learning_review", "authorized_review_status": "REVIEW_DUE",
        }
        self.assert_denied(bound.evaluate_review_from_ledger(injected, self.root),
                           "PROPOSAL_CONTRACT_INVALID")
        forbidden = {"contract": "erei-proposal-v1",
                     "decision": "feedback_then_promotion",
                     "actions": [
                         {"op": "record_feedback", "fingerprint": "x", "evidence_ref": "x"},
                         {"op": "nominate_candidate", "fingerprint": "x"},
                     ]}
        self.assert_denied(bound.evaluate_review_from_ledger(forbidden, self.root),
                           "WRONG_WORKFLOW")

    def test_corrupt_fingerprint_fails_closed_not_approved(self):
        event = self.add_event()
        path = self.root / ".erei" / "learning" / "events" / (
            event["occurrence_id"] + ".json"
        )
        corrupted = json.loads(path.read_text(encoding="utf-8"))
        corrupted["verification_failures"] = 99
        path.write_text(json.dumps(corrupted), encoding="utf-8")
        self.assert_denied(bound.evaluate_review_from_ledger(request(), self.root),
                           "LEDGER_EVIDENCE_INVALID")

    def test_change_detected_after_snapshot_blocks_preview(self):
        self.add_event()
        genuine = task_learning._ledger_generation
        count = 0

        def changed_on_final_read(paths):
            nonlocal count
            count += 1
            return "f" * 64 if count == 3 else genuine(paths)

        with mock.patch.object(task_learning, "_ledger_generation",
                               side_effect=changed_on_final_read):
            result = bound.evaluate_review_from_ledger(request(), self.root)
        self.assert_denied(result, "LEDGER_CHANGED_DURING_PREVIEW")
        self.assertEqual(count, 3)

    def test_invalid_path_fails_closed(self):
        self.assert_denied(bound.evaluate_review_from_ledger(request(), None),
                           "PROJECT_PATH_INVALID")
        self.assert_denied(bound.evaluate_review_from_ledger(
            request(), self.root / "missing"), "LEDGER_EVIDENCE_INVALID")


if __name__ == "__main__":
    unittest.main()
