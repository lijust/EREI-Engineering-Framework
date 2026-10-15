import argparse
import json
import tempfile
import unittest
from pathlib import Path

from tools import task_learning


class TaskLearningTests(unittest.TestCase):
    def make_project(self):
        temp = tempfile.TemporaryDirectory()
        target = Path(temp.name)
        (target / ".erei").mkdir()
        (target / ".erei" / "framework.json").write_text("{}", encoding="utf-8")
        return temp, target

    def event_args(self, **overrides):
        values = dict(
            task_id=None,
            occurrence_id=None,
            task_group=None,
            project_repository="example/demo",
            project_name="Demo",
            framework_ref="a" * 40,
            workflow="bug-fix",
            risk="L2",
            terminal_state="COMPLETE_VERIFIED",
            outcome_class="verified_success",
            material=True,
            rework_cycles=0,
            verification_failures=0,
            verification_escape=False,
            framework_feedback_created=False,
            manual_workaround=False,
            context_gap=False,
            unexpected_scope_growth=False,
            security_or_data_critical_event=False,
            duration_class="medium",
            failure_stage="none",
            failure_subject=None,
            feedback_id=[],
            feedback_fingerprint=[],
            tag=[],
        )
        values.update(overrides)
        return argparse.Namespace(**values)

    def review_args(self):
        return argparse.Namespace(
            review_id=None,
            findings="Reviewed current task-learning evidence.",
            decision="No Framework change yet.",
            evidence=["docs/evidence/learning-review.md"],
            action=[],
        )

    def capture_state(self, target, event):
        state, _ = task_learning.capture(target, event)
        return state

    def test_twenty_material_tasks_recommend_review(self):
        temp, target = self.make_project()
        try:
            for _ in range(20):
                state = self.capture_state(target, task_learning.build_event(self.event_args()))
            self.assertEqual(state["trigger"]["level"], "REVIEW_RECOMMENDED")
        finally:
            temp.cleanup()

    def test_forty_material_tasks_make_review_due(self):
        temp, target = self.make_project()
        try:
            for _ in range(40):
                state = self.capture_state(target, task_learning.build_event(self.event_args()))
            self.assertEqual(state["trigger"]["level"], "REVIEW_DUE")
        finally:
            temp.cleanup()

    def test_verification_escape_requires_immediate_review(self):
        temp, target = self.make_project()
        try:
            state = self.capture_state(target, task_learning.build_event(self.event_args(verification_escape=True)))
            self.assertEqual(state["trigger"]["level"], "IMMEDIATE_REVIEW")
        finally:
            temp.cleanup()

    def test_same_feedback_pattern_three_occurrences_makes_review_due(self):
        temp, target = self.make_project()
        try:
            for _ in range(3):
                state = self.capture_state(
                    target,
                    task_learning.build_event(
                        self.event_args(
                            framework_feedback_created=True,
                            feedback_fingerprint=["f" * 64],
                        )
                    ),
                )
            self.assertEqual(state["trigger"]["level"], "REVIEW_DUE")
        finally:
            temp.cleanup()

    def test_review_close_binds_occurrences_and_digest(self):
        temp, target = self.make_project()
        try:
            event = task_learning.build_event(self.event_args())
            self.capture_state(target, event)
            review, state = task_learning.close_review(target, self.review_args())
            self.assertEqual(review["schema_version"], 2)
            self.assertEqual(review["epoch_id"], "EPOCH-001")
            self.assertEqual(review["reviewed_occurrence_ids"], [event["occurrence_id"]])
            self.assertEqual(len(review["event_digest"]), 64)
            self.assertEqual(state["epoch_id"], "EPOCH-002")
            self.assertEqual(state["metrics_since_last_review"]["tasks"], 0)
            validation = task_learning.validate_ledgers(target)
            self.assertTrue(validation["valid"])
            self.assertEqual(validation["reviews"], 1)
        finally:
            temp.cleanup()

    def test_review_metrics_tampering_is_rejected(self):
        temp, target = self.make_project()
        try:
            event = task_learning.build_event(self.event_args())
            self.capture_state(target, event)
            review, _ = task_learning.close_review(target, self.review_args())
            path = target / ".erei" / "learning" / "reviews" / f"{review['review_id']}.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value["metrics"]["tasks"] = 999
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(task_learning.LearningError):
                task_learning.validate_ledgers(target)
        finally:
            temp.cleanup()

    def test_v2_projection_only_review_cannot_close_authoritative_event(self):
        temp, target = self.make_project()
        try:
            event = task_learning.build_event(self.event_args(verification_escape=True))
            self.capture_state(target, event)
            review, _ = task_learning.close_review(target, self.review_args())
            immutable_review = target / ".erei" / "learning" / "reviews" / f"{review['review_id']}.json"
            immutable_review.unlink()
            with self.assertRaisesRegex(
                task_learning.LearningError,
                "projection without immutable authority",
            ):
                task_learning.status(target)
        finally:
            temp.cleanup()

    def test_v2_projection_only_event_is_not_authoritative(self):
        temp, target = self.make_project()
        try:
            event = task_learning.build_event(self.event_args(verification_escape=True))
            self.capture_state(target, event)
            immutable_event = target / ".erei" / "learning" / "events" / f"{event['occurrence_id']}.json"
            immutable_event.unlink()
            with self.assertRaisesRegex(
                task_learning.LearningError,
                "projection without immutable authority",
            ):
                task_learning.status(target)
        finally:
            temp.cleanup()

    def test_immutable_v2_records_rebuild_missing_projections(self):
        temp, target = self.make_project()
        try:
            event = task_learning.build_event(self.event_args())
            self.capture_state(target, event)
            review, _ = task_learning.close_review(target, self.review_args())
            learning = target / ".erei" / "learning"
            (learning / "TASK_EVENTS.jsonl").write_text("", encoding="utf-8")
            (learning / "LEARNING_REVIEWS.jsonl").write_text("", encoding="utf-8")
            state = task_learning.status(target)
            self.assertEqual(state["epoch_id"], "EPOCH-002")
            self.assertEqual(state["reviewed_occurrence_count"], 1)
            rebuilt_events = [
                json.loads(line)
                for line in (learning / "TASK_EVENTS.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            rebuilt_reviews = [
                json.loads(line)
                for line in (learning / "LEARNING_REVIEWS.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(rebuilt_events, [event])
            self.assertEqual(rebuilt_reviews, [review])
        finally:
            temp.cleanup()

    def test_v2_projection_mismatch_with_immutable_record_is_rejected(self):
        temp, target = self.make_project()
        try:
            event = task_learning.build_event(self.event_args())
            self.capture_state(target, event)
            learning = target / ".erei" / "learning"
            projection = json.loads((learning / "TASK_EVENTS.jsonl").read_text(encoding="utf-8").strip())
            projection["duration_class"] = "long"
            projection["fingerprint"] = task_learning._fingerprint(projection)
            (learning / "TASK_EVENTS.jsonl").write_text(json.dumps(projection) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                task_learning.LearningError,
                "projection does not match immutable authority",
            ):
                task_learning.status(target)
        finally:
            temp.cleanup()

    def test_boolean_schema_version_projection_is_rejected(self):
        temp, target = self.make_project()
        try:
            event = task_learning.build_event(self.event_args())
            task_learning.capture(target, event)
            learning = target / ".erei" / "learning"
            projection = json.loads((learning / "TASK_EVENTS.jsonl").read_text(encoding="utf-8").strip())
            projection["schema_version"] = True
            (learning / "TASK_EVENTS.jsonl").write_text(json.dumps(projection) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(task_learning.LearningError, "schema_version must be an integer"):
                task_learning.status(target)
        finally:
            temp.cleanup()

    def test_boolean_schema_version_review_projection_is_rejected(self):
        temp, target = self.make_project()
        try:
            event = task_learning.build_event(self.event_args())
            task_learning.capture(target, event)
            review, _ = task_learning.close_review(target, self.review_args())
            learning = target / ".erei" / "learning"
            projection = json.loads((learning / "LEARNING_REVIEWS.jsonl").read_text(encoding="utf-8").strip())
            projection["schema_version"] = True
            (learning / "LEARNING_REVIEWS.jsonl").write_text(json.dumps(projection) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(task_learning.LearningError, "schema_version must be an integer"):
                task_learning.status(target)
        finally:
            temp.cleanup()

    def test_authoritative_snapshot_is_read_only(self):
        temp, target = self.make_project()
        try:
            event = task_learning.build_event(self.event_args(verification_escape=True))
            task_learning.capture(target, event)
            learning = target / ".erei" / "learning"
            watched = [
                learning / "TASK_EVENTS.jsonl",
                learning / "LEARNING_REVIEWS.jsonl",
                learning / "LEARNING_STATE.json",
                learning / "LEARNING_SUMMARY.md",
            ]
            before = {str(path): path.read_bytes() if path.exists() else None for path in watched}
            snapshot = task_learning.authoritative_snapshot(target)
            after = {str(path): path.read_bytes() if path.exists() else None for path in watched}
            self.assertEqual(before, after)
            self.assertEqual(snapshot["events"], [event])
            self.assertEqual(snapshot["state"]["trigger"]["level"], "IMMEDIATE_REVIEW")
        finally:
            temp.cleanup()

    def test_empty_epoch_cannot_be_closed(self):
        temp, target = self.make_project()
        try:
            with self.assertRaises(task_learning.LearningError):
                task_learning.close_review(target, self.review_args())
        finally:
            temp.cleanup()

    def test_invalid_feedback_fingerprint_is_rejected(self):
        with self.assertRaises(task_learning.LearningError):
            task_learning.build_event(
                self.event_args(
                    framework_feedback_created=True,
                    feedback_fingerprint=["not-a-sha256"],
                )
            )

    def test_duplicate_feedback_fingerprints_are_rejected_even_if_injected(self):
        event = task_learning.build_event(self.event_args(feedback_fingerprint=["f" * 64]))
        event["feedback_fingerprints"] = ["f" * 64, "f" * 64]
        event["fingerprint"] = task_learning._fingerprint(event)
        with self.assertRaises(task_learning.LearningError):
            task_learning.validate_event(event)

    def test_boolean_counter_is_rejected(self):
        event = task_learning.build_event(self.event_args())
        event["rework_cycles"] = True
        event["fingerprint"] = task_learning._fingerprint(event)
        with self.assertRaises(task_learning.LearningError):
            task_learning.validate_event(event)

    def test_invalid_date_and_unknown_field_are_rejected(self):
        event = task_learning.build_event(self.event_args())
        event["recorded_at"] = "2026-99-99"
        event["unexpected"] = "bad"
        event["fingerprint"] = task_learning._fingerprint(event)
        with self.assertRaises(task_learning.LearningError):
            task_learning.validate_event(event)

    def test_occurrence_retry_is_idempotent(self):
        temp, target = self.make_project()
        try:
            event = task_learning.build_event(self.event_args())
            _, first_idempotent = task_learning.capture(target, event)
            _, second_idempotent = task_learning.capture(target, event)
            self.assertFalse(first_idempotent)
            self.assertTrue(second_idempotent)
            self.assertEqual(task_learning.validate_ledgers(target)["events"], 1)
        finally:
            temp.cleanup()

    def test_occurrence_conflict_is_rejected(self):
        temp, target = self.make_project()
        try:
            event = task_learning.build_event(self.event_args())
            task_learning.capture(target, event)
            conflict = dict(event)
            conflict["duration_class"] = "long"
            conflict["fingerprint"] = task_learning._fingerprint(conflict)
            with self.assertRaisesRegex(task_learning.LearningError, "occurrence_id already exists"):
                task_learning.capture(target, conflict)
        finally:
            temp.cleanup()

    def test_unknown_signal_assessment_is_not_successful_zero(self):
        temp, target = self.make_project()
        try:
            args = self.event_args(
                rework_cycles=None,
                verification_failures=None,
                verification_escape=None,
                framework_feedback_created=None,
                manual_workaround=None,
                context_gap=None,
                unexpected_scope_growth=None,
                security_or_data_critical_event=None,
            )
            state = self.capture_state(target, task_learning.build_event(args))
            metrics = state["metrics_since_last_review"]
            self.assertIsNone(metrics["rework_rate"])
            self.assertIsNone(metrics["verification_failure_rate"])
            self.assertGreater(metrics["unassessed_signal_values"], 0)
            self.assertEqual(state["trigger"]["level"], "INSUFFICIENT_EVIDENCE")
        finally:
            temp.cleanup()

    def test_fingerprint_tampering_is_detected(self):
        event = task_learning.build_event(self.event_args())
        event["duration_class"] = "long"
        with self.assertRaises(task_learning.LearningError):
            task_learning.validate_event(event)


if __name__ == "__main__":
    unittest.main()
