import argparse
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
            feedback_id=[],
            feedback_fingerprint=[],
            tag=[],
        )
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_twenty_material_tasks_recommend_review(self):
        temp, target = self.make_project()
        try:
            for _ in range(20):
                state = task_learning.capture(target, task_learning.build_event(self.event_args()))
            self.assertEqual(state["trigger"]["level"], "REVIEW_RECOMMENDED")
        finally:
            temp.cleanup()

    def test_forty_material_tasks_make_review_due(self):
        temp, target = self.make_project()
        try:
            for _ in range(40):
                state = task_learning.capture(target, task_learning.build_event(self.event_args()))
            self.assertEqual(state["trigger"]["level"], "REVIEW_DUE")
        finally:
            temp.cleanup()

    def test_verification_escape_requires_immediate_review(self):
        temp, target = self.make_project()
        try:
            state = task_learning.capture(
                target,
                task_learning.build_event(self.event_args(verification_escape=True)),
            )
            self.assertEqual(state["trigger"]["level"], "IMMEDIATE_REVIEW")
        finally:
            temp.cleanup()

    def test_same_feedback_pattern_three_times_makes_review_due(self):
        temp, target = self.make_project()
        try:
            for _ in range(3):
                state = task_learning.capture(
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

    def test_review_close_starts_new_epoch(self):
        temp, target = self.make_project()
        try:
            task_learning.capture(target, task_learning.build_event(self.event_args()))
            review_args = argparse.Namespace(
                review_id=None,
                findings="Reviewed current task-learning evidence.",
                decision="No Framework change yet.",
                evidence=["docs/evidence/learning-review.md"],
                action=[],
            )
            review, state = task_learning.close_review(target, review_args)
            self.assertEqual(review["epoch_id"], "EPOCH-001")
            self.assertEqual(state["epoch_id"], "EPOCH-002")
            self.assertEqual(state["metrics_since_last_review"]["tasks"], 0)
        finally:
            temp.cleanup()

    def test_fingerprint_tampering_is_detected(self):
        event = task_learning.build_event(self.event_args())
        event["rework_cycles"] = 9
        with self.assertRaises(task_learning.LearningError):
            task_learning.validate_event(event)


if __name__ == "__main__":
    unittest.main()
