"""Offline synthetic regression for source-bound per-task reuse marker claims."""
from __future__ import annotations

import copy
import unittest

from tools import learning_exposure_traces as trace
from tools import task_learning
from evals.tests.test_learning_intervention_sources import (
    InterventionLedgerBindingTests,
)


class TraceJoinTests(unittest.TestCase):
    def setUp(self):
        self.fixture = InterventionLedgerBindingTests(
            "test_exact_cohort_and_quality_accounting_are_local_only"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.tmp.cleanup)

    def scenario(self, *, outcomes=None):
        f = self.fixture
        first = f.add(0, **(outcomes or {}))
        second = f.add(1)
        intervention = f.data([first, second], exposure=None, recurrence=None)
        selector = f.selector()
        generation = task_learning.authoritative_snapshot(f.root)["generation"]
        receipts = []
        for index, event in enumerate((first, second)):
            receipts.append({
                "occurrence_id": event["occurrence_id"],
                "task_fingerprint": event["fingerprint"],
                "framework_ref": event["framework_ref"],
                "trace_ref": format(index + 1, "040x"),
                "capture_complete": False,
                "steps": [],
            })
        bundle = {
            "schema_version": 1,
            "intervention_id": intervention["intervention_id"],
            "epoch_id": intervention["cohort"]["epoch_id"],
            "ledger_generation_sha256": generation,
            "traces": receipts,
        }
        return intervention, selector, bundle

    def assess(self, d, s, b):
        return trace.reconcile_learning_trace_claims(self.fixture.root, d, s, b)

    def deny(self, result, code):
        self.assertEqual(result["status"], "DENIED")
        self.assertEqual(result["reason_code"], code)
        self.assertFalse(result["learning_exposure_independently_verified"])
        self.assertFalse(result["files_written"])
        self.assertNotIn("prospective_groups", result)

    def marked(self, d):
        return [{"op": "learning_reuse", "intervention_id": d["intervention_id"],
                 "implementation_ref": d["implementation"]["ref"]}]

    def test_source_join_has_positive_negative_and_unknown_without_effect_claim(self):
        d, s, b = self.scenario(outcomes={
            "outcome_class": "failed", "terminal_state": "FAILED",
            "verification_escape": True,
        })
        d["cohort"]["tasks"][0]["exposed"] = True
        d["cohort"]["tasks"][1]["exposed"] = False
        b["traces"][0]["steps"] = self.marked(d)
        b["traces"][0]["capture_complete"] = True
        b["traces"][1]["capture_complete"] = True
        before = copy.deepcopy((d, s, b))
        generation = task_learning.authoritative_snapshot(self.fixture.root)["generation"]
        response = self.assess(d, s, b)
        self.assertEqual(response["status"], "UNVERIFIED_TRACE_CLAIMS_RECONCILED")
        self.assertEqual(response["prospective_eligible"], 2)
        self.assertEqual(response["prospective_groups"]["reuse_marker_reported"]["failed_tasks"], 1)
        self.assertEqual(response["prospective_groups"]["reuse_marker_reported"]["verification_escapes"], 1)
        self.assertEqual(response["prospective_groups"]["no_marker_complete_trace_claim"]["verified_successes"], 1)
        self.assertEqual(response["prospective_groups"]["trace_incomplete_no_marker"]["tasks"], 0)
        self.assertFalse(response["learning_exposure_independently_verified"])
        self.assertFalse(response["root_cause_recurrence_verified"])
        self.assertEqual(response["effectiveness"], "NOT_ESTABLISHED")
        self.assertEqual(response["causation"], "NOT_ESTABLISHED")
        self.assertEqual((d, s, b), before)
        self.assertEqual(generation, task_learning.authoritative_snapshot(self.fixture.root)["generation"])

    def test_partial_trace_does_not_turn_missing_marker_into_false(self):
        d, s, b = self.scenario()
        good = self.assess(d, s, b)
        self.assertEqual(good["prospective_groups"]["trace_incomplete_no_marker"]["tasks"], 2)
        d["cohort"]["tasks"][0]["exposed"] = False
        self.deny(self.assess(d, s, b), "EXPOSURE_DECLARATION_CONFLICT")

    def test_positive_marker_cannot_be_faked_with_wrong_implementation(self):
        d, s, b = self.scenario()
        d["cohort"]["tasks"][0]["exposed"] = True
        b["traces"][0]["steps"] = self.marked(d)
        b["traces"][0]["steps"][0]["implementation_ref"] = "f" * 40
        self.deny(self.assess(d, s, b), "REUSE_MARKER_IDENTITY_MISMATCH")

    def test_marker_must_agree_with_declared_exposure(self):
        d, s, b = self.scenario()
        b["traces"][0]["steps"] = self.marked(d)
        self.deny(self.assess(d, s, b), "EXPOSURE_DECLARATION_CONFLICT")
        d["cohort"]["tasks"][0]["exposed"] = True
        result = self.assess(d, s, b)
        self.assertEqual(result["prospective_groups"]["reuse_marker_reported"]["tasks"], 1)

    def test_missing_or_duplicate_trace_denies_even_if_missing_task_failed(self):
        d, s, b = self.scenario(outcomes={
            "outcome_class": "failed", "terminal_state": "FAILED"
        })
        b["traces"] = b["traces"][1:]
        self.deny(self.assess(d, s, b), "TRACE_COHORT_MEMBERSHIP_MISMATCH")
        b["traces"] *= 2
        self.deny(self.assess(d, s, b), "DUPLICATE_TRACE_OCCURRENCE")

    def test_task_identity_fingerprint_and_framework_revision_must_match(self):
        d, s, b = self.scenario()
        b["traces"][0]["task_fingerprint"] = "invented"
        self.deny(self.assess(d, s, b), "TRACE_TASK_SOURCE_MISMATCH")
        b["traces"][0]["task_fingerprint"] = d["cohort"]["tasks"][0]["occurrence_id"]
        self.deny(self.assess(d, s, b), "TRACE_TASK_SOURCE_MISMATCH")
        b = self.scenario_new_bundle(d, s)
        b["traces"][0]["framework_ref"] = "f" * 40
        self.deny(self.assess(d, s, b), "TRACE_TASK_SOURCE_MISMATCH")

    def scenario_new_bundle(self, d, s):
        snapshot = task_learning.authoritative_snapshot(self.fixture.root)
        events = {e["occurrence_id"]: e for e in snapshot["events"]}
        rows = []
        for index, task in enumerate(d["cohort"]["tasks"]):
            e = events[task["occurrence_id"]]
            rows.append({
                "occurrence_id": task["occurrence_id"],
                "task_fingerprint": e["fingerprint"],
                "framework_ref": e["framework_ref"],
                "trace_ref": format(index + 1, "040x"),
                "capture_complete": False,
                "steps": [],
            })
        return {"schema_version": 1, "intervention_id": d["intervention_id"],
                "epoch_id": d["cohort"]["epoch_id"],
                "ledger_generation_sha256": snapshot["generation"], "traces": rows}

    def test_unknown_steps_and_malformed_capture_are_denied(self):
        d, s, b = self.scenario()
        b["traces"][0]["steps"] = [{"op": "persist_sensitive"}]
        self.deny(self.assess(d, s, b), "TRACE_CONTRACT_INVALID")
        b["traces"][0]["steps"] = []
        b["traces"][0]["capture_complete"] = 1
        self.deny(self.assess(d, s, b), "TRACE_CONTRACT_INVALID")

    def test_forged_ledger_generation_or_epoch_denied(self):
        d, s, b = self.scenario()
        b["ledger_generation_sha256"] = "f" * 64
        self.deny(self.assess(d, s, b), "TRACE_SOURCE_BINDING_MISMATCH")
        b = self.scenario_new_bundle(d, s)
        b["epoch_id"] = "EPOCH-999"
        self.deny(self.assess(d, s, b), "TRACE_SOURCE_BINDING_MISMATCH")

    def test_bundle_does_not_erase_missing_original_cohort_failures(self):
        d, s, b = self.scenario()
        d["cohort"]["tasks"] = d["cohort"]["tasks"][1:]
        b["traces"] = b["traces"][1:]
        self.deny(self.assess(d, s, b), "SOURCE_COHORT_NOT_ESTABLISHED")

    def test_no_adoption_with_reuse_marker_denied_by_existing_contract(self):
        d, s, b = self.scenario()
        d["adoption"] = None
        d["cohort"]["tasks"][0]["exposed"] = True
        b["traces"][0]["steps"] = self.marked(d)
        self.deny(self.assess(d, s, b), "SOURCE_COHORT_NOT_ESTABLISHED")


if __name__ == "__main__":
    unittest.main()
