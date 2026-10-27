"""Synthetic, offline task-ledger cohort binding tests. No provider or real project."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest import mock

from tools import learning_intervention_sources as source
from tools import task_learning

SHA = "a" * 40
T0 = datetime(2026, 10, 27, 14, 0, tzinfo=timezone.utc)


def args(**changes):
    value = dict(
        task_id=None, occurrence_id=None, task_group=None,
        project_repository="example/project", project_name="Synthetic Project",
        framework_ref=SHA, workflow="bug-fix", risk="L2",
        terminal_state="COMPLETE_VERIFIED", outcome_class="verified_success",
        material=True, rework_cycles=0, verification_failures=0,
        verification_escape=False, framework_feedback_created=False,
        manual_workaround=False, context_gap=False,
        unexpected_scope_growth=False, security_or_data_critical_event=False,
        duration_class="short", failure_stage="none", failure_subject=None,
        feedback_id=[], feedback_fingerprint=[], tag=[],
    )
    value.update(changes)
    return argparse.Namespace(**value)


class InterventionLedgerBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".erei").mkdir()
        (self.root / ".erei" / "framework.json").write_text("{}", encoding="utf-8")

    def add(self, i, **changes):
        event = task_learning.build_event(args(**changes), now=T0 + timedelta(minutes=i))
        task_learning.capture(self.root, event)
        return event

    def data(self, events, *, epoch="EPOCH-001", exposure=None, recurrence=None,
             prospective=True):
        ledger_path = self.root / ".erei" / "learning" / "TASK_EVENTS.jsonl"
        digest = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
        rows = [
            {
                "occurrence_id": event["occurrence_id"],
                "identity_basis": "prospective" if prospective else "legacy_assumed",
                "exposed": exposure,
                "recurred": recurrence,
                "evidence": ["synthetic:review-of-" + event["occurrence_id"]],
            }
            for event in events
        ]
        return {
            "schema_version": 1, "intervention_id": "synthetic-intervention",
            "finding_refs": ["synthetic:finding"],
            "root_cause": "synthetic repeat issue",
            "development_output_ref": "synthetic:LDO",
            "implementation": {"repository": "example/framework", "ref": SHA},
            "adoption": {
                "repository": "example/project", "ref": "b" * 40,
                "implementation_ref": SHA, "evidence": ["synthetic:adoption"],
            },
            "cohort": {
                "repository": "example/project", "ref": "c" * 40,
                "ledger_sha256": digest, "epoch_id": epoch,
                "eligibility_rule": source.SELECTION_RULE,
                "selection_ref": "d" * 40, "tasks": rows,
            },
        }

    def selector(self, **changes):
        result = {
            "schema_version": 1, "rule_id": source.SELECTION_RULE,
            "selection_ref": "d" * 40,
            "workflow": "bug-fix", "risk": "L2",
            "material_only": True,
            "from_inclusive": "2026-10-27T14:00:00Z",
            "to_exclusive": "2026-10-27T15:00:00Z",
        }
        result.update(changes)
        return result

    def check_denied(self, result, reason):
        self.assertEqual(result["status"], "DENIED")
        self.assertEqual(result["reason_code"], reason)
        self.assertFalse(result["project_files_written"])
        self.assertFalse(result["stable_ready"])
        self.assertEqual(result["causation"], "NOT_ESTABLISHED")
        self.assertNotIn("intervention_accounting", result)

    def test_exact_cohort_and_quality_accounting_are_local_only(self):
        good = self.add(0, verification_escape=True, verification_failures=1,
                        outcome_class="failed", terminal_state="FAILED",
                        failure_stage="runtime")
        success = self.add(1)
        data = self.data([good, success], exposure=True, recurrence=False)
        original = copy.deepcopy(data)
        ledgers = task_learning.authoritative_snapshot(self.root)
        response = source.assess_intervention_against_ledger(
            self.root, data, self.selector()
        )
        self.assertEqual(response["status"], "LOCAL_COHORT_MEMBERSHIP_MATCHED")
        self.assertEqual(response["membership"]["eligible_local_source"], 2)
        self.assertEqual(response["source_binding"]["ledger_generation_sha256"],
                         ledgers["generation"])
        self.assertEqual(response["source_outcomes"]["failed_tasks"], 1)
        self.assertEqual(response["source_outcomes"]["verified_successes"], 1)
        self.assertEqual(response["source_outcomes"]["verification_escapes"], 1)
        self.assertEqual(response["source_outcomes"]["verification_escape_assessed"], 2)
        self.assertEqual(response["intervention_accounting"]["prospective"]["exposed"], 2)
        self.assertFalse(response["exposure_verified"])
        self.assertFalse(response["adoption_authenticity_verified"])
        self.assertFalse(response["cohort_selection_pre_registered"])
        self.assertEqual(response["effectiveness"], "NOT_ESTABLISHED")
        self.assertEqual(response["causation"], "NOT_ESTABLISHED")
        self.assertEqual(data, original)
        self.assertEqual(task_learning.authoritative_snapshot(self.root)["generation"],
                         ledgers["generation"])

    def test_missing_failed_occurrence_rejects_incomplete_denominator(self):
        failure = self.add(0, outcome_class="failed", terminal_state="FAILED")
        success = self.add(1)
        d = self.data([success], exposure=True, recurrence=False)
        result = source.assess_intervention_against_ledger(
            self.root, d, self.selector()
        )
        self.check_denied(result, "COHORT_SELECTION_MISMATCH")
        self.assertEqual(result["membership_diagnostic"]["missing_count"], 1)
        self.assertEqual(result["membership_diagnostic"]["eligible_local_source"], 2)

    def test_extra_or_wrong_epoch_occurrence_rejected(self):
        first = self.add(0)
        second = self.add(1, workflow="review")
        d = self.data([first, second])
        self.check_denied(
            source.assess_intervention_against_ledger(self.root, d, self.selector()),
            "COHORT_SELECTION_MISMATCH"
        )
        d2 = self.data([first], epoch="EPOCH-999")
        self.check_denied(
            source.assess_intervention_against_ledger(self.root, d2, self.selector()),
            "EPOCH_NOT_SUPPORTED_OR_NOT_FOUND"
        )

    def test_out_of_scope_tasks_are_not_counted_in_cohort(self):
        first = self.add(0)
        self.add(1, material=False)
        self.add(2, risk="L3")
        self.add(3, workflow="release")
        d = self.data([first])
        result = source.assess_intervention_against_ledger(self.root, d, self.selector())
        self.assertEqual(result["status"], "LOCAL_COHORT_MEMBERSHIP_MATCHED")
        self.assertEqual(result["membership"]["eligible_local_source"], 1)

    def test_wrong_ledger_digest_fails_before_any_rate(self):
        first = self.add(0)
        d = self.data([first], exposure=True)
        d["cohort"]["ledger_sha256"] = "f" * 64
        self.check_denied(
            source.assess_intervention_against_ledger(self.root, d, self.selector()),
            "EVENT_LEDGER_SHA256_MISMATCH"
        )

    def test_selection_rule_and_reference_are_not_trusted_from_text(self):
        first = self.add(0)
        d = self.data([first])
        self.check_denied(
            source.assess_intervention_against_ledger(
                self.root, d, self.selector(selection_ref="f" * 40)
            ), "SELECTION_REFERENCE_MISMATCH"
        )
        d["cohort"]["eligibility_rule"] = "All tasks except failures"
        self.check_denied(
            source.assess_intervention_against_ledger(self.root, d, self.selector()),
            "SELECTION_REFERENCE_MISMATCH"
        )

    def test_window_and_scope_must_be_strict(self):
        first = self.add(0)
        d = self.data([first])
        for broken in (
            {"material_only": False}, {"risk": []},
            {"from_inclusive": "2026-10-27"},
            {"from_inclusive": "2026-10-27T16:00:00Z"},
            {"schema_version": True},
        ):
            with self.subTest(broken=broken):
                result = source.assess_intervention_against_ledger(
                    self.root, d, self.selector(**broken)
                )
                self.assertEqual(result["status"], "DENIED")

    def test_fabricated_repository_and_invalid_claims_fail_closed(self):
        first = self.add(0)
        d = self.data([first])
        d["cohort"]["repository"] = "example/another"
        d["adoption"]["repository"] = "example/another"
        self.check_denied(
            source.assess_intervention_against_ledger(self.root, d, self.selector()),
            "PROJECT_REPOSITORY_MISMATCH"
        )
        d2 = self.data([first], exposure="yes")
        self.check_denied(
            source.assess_intervention_against_ledger(self.root, d2, self.selector()),
            "INTERVENTION_CONTRACT_INVALID"
        )

    def test_detect_mid_assessment_mutation(self):
        event = self.add(0)
        d = self.data([event])
        original = task_learning._ledger_generation
        # Authoritative read calls generation at least twice. Final check is third.
        reads = 0
        def final_different(paths):
            nonlocal reads
            reads += 1
            return ("f" * 64) if reads == 3 else original(paths)
        with mock.patch.object(task_learning, "_ledger_generation",
                               side_effect=final_different):
            result = source.assess_intervention_against_ledger(
                self.root, d, self.selector()
            )
        self.check_denied(result, "LEDGER_CHANGED_DURING_ASSESSMENT")
        self.assertEqual(reads, 3)

    def test_closed_v2_epoch_is_supported_without_ignoring_new_tasks(self):
        first = self.add(0)
        task_learning.close_review(
            self.root,
            argparse.Namespace(
                review_id=None, findings="Synthetic review", decision="No changes",
                evidence=["synthetic:review"], action=[],
            ),
            now=T0 + timedelta(minutes=4),
        )
        self.add(5)
        d = self.data([first], epoch="EPOCH-001")
        result = source.assess_intervention_against_ledger(self.root, d, self.selector())
        self.assertEqual(result["status"], "LOCAL_COHORT_MEMBERSHIP_MATCHED")
        self.assertEqual(result["membership"]["eligible_local_source"], 1)

    def test_no_provider_or_real_dispatch_and_no_legacy_prospective_upgrade(self):
        first = self.add(0)
        d = self.data([first], exposure=None, recurrence=None, prospective=False)
        result = source.assess_intervention_against_ledger(self.root, d, self.selector())
        self.assertEqual(result["status"], "LOCAL_COHORT_MEMBERSHIP_MATCHED")
        self.assertEqual(result["intervention_accounting"]["prospective"]["eligible"], 0)
        self.assertEqual(result["effectiveness"], "NOT_ESTABLISHED")
        self.check_denied(
            source.assess_intervention_against_ledger(None, d, self.selector()),
            "PROJECT_PATH_INVALID"
        )


    def test_timestamp_normalization_overflow_denied_at_selector(self):
        first = self.add(0)
        d = self.data([first])
        for field, stamp in (
            ("from_inclusive", "0001-01-01T00:00:00+01:00"),
            ("to_exclusive", "9999-12-31T23:59:59-01:00"),
        ):
            with self.subTest(field=field):
                result = source.assess_intervention_against_ledger(
                    self.root, d, self.selector(**{field: stamp})
                )
                self.check_denied(result, "SELECTION_WINDOW_INVALID")

    def test_timestamp_normalization_overflow_denied_for_ledger_event(self):
        event = self.add(0)
        d = self.data([event])
        normal = source.capability_activation._time

        def injected_ledger_boundary(value, label):
            if label == "task.recorded_at":
                raise OverflowError("utc normalization")
            return normal(value, label)

        with mock.patch.object(source.capability_activation, "_time",
                               side_effect=injected_ledger_boundary):
            result = source.assess_intervention_against_ledger(
                self.root, d, self.selector()
            )
        self.check_denied(result, "LEDGER_EVIDENCE_INVALID")



if __name__ == "__main__":
    unittest.main()
