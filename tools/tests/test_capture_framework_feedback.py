from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tools.capture_framework_feedback import FeedbackError, build_event, capture


class FeedbackCaptureTests(unittest.TestCase):
    def args(self, **overrides):
        values = dict(
            project_repository="example/project",
            project_name="Example Project",
            framework_ref="a" * 40,
            feedback_id=None,
            type="workflow_gap",
            severity="medium",
            source_artifact="workflows/bug-fix",
            observation="A required concurrency check was missing.",
            evidence=["evidence/BUG-001.md"],
            suggestion="Add a concurrency trigger to bug-fix workflow.",
            negative_learning="Do not assume local success proves concurrency safety.",
            generalizability="likely_generic",
            confidence="high",
            sensitivity_class=None,
            redaction_state=None,
            export_eligibility=None,
            tag=["concurrency", "regression"],
        )
        values.update(overrides)
        return argparse.Namespace(**values)

    def project(self):
        temp = tempfile.TemporaryDirectory()
        target = Path(temp.name)
        (target / ".erei").mkdir()
        (target / ".erei" / "framework.json").write_text("{}", encoding="utf-8")
        return temp, target

    def test_build_event_defaults_local_only(self):
        now = datetime(2026, 9, 2, 0, 0, 0, tzinfo=timezone.utc)
        event = build_event(self.args(), now=now)
        self.assertRegex(event["feedback_id"], r"^EFF-20260902T000000Z-[A-F0-9]{8}$")
        self.assertEqual(event["recorded_at"], "2026-09-02T00:00:00Z")
        self.assertEqual(event["status"], "new")
        self.assertEqual(event["sensitivity_class"], "internal")
        self.assertEqual(event["redaction_state"], "pending")
        self.assertEqual(event["export_eligibility"], "local_only")
        self.assertEqual(len(event["fingerprint"]), 64)

    def test_missing_evidence_is_rejected(self):
        with self.assertRaises(FeedbackError):
            build_event(self.args(evidence=[]))

    def test_secret_like_content_is_rejected_before_capture(self):
        with self.assertRaisesRegex(FeedbackError, "credential/secret"):
            build_event(self.args(observation="password=do-not-store-this-value"))

    def test_email_content_defaults_confidential(self):
        event = build_event(self.args(observation="Contact test@example.com about the observation."))
        self.assertEqual(event["sensitivity_class"], "confidential")
        self.assertEqual(event["export_eligibility"], "local_only")

    def test_sensitive_export_requires_approved_redaction(self):
        with self.assertRaisesRegex(FeedbackError, "approved redaction"):
            build_event(
                self.args(
                    sensitivity_class="confidential",
                    redaction_state="pending",
                    export_eligibility="eligible",
                )
            )

    def test_capture_requires_erei_integrated_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FeedbackError):
                capture(Path(tmp), build_event(self.args()))

    def test_capture_writes_immutable_event_projection_and_markdown(self):
        temp, target = self.project()
        try:
            event = build_event(self.args())
            jsonl, markdown, idempotent = capture(target, event)
            self.assertFalse(idempotent)
            self.assertTrue(jsonl.exists())
            self.assertTrue(markdown.exists())
            immutable = target / ".erei" / "feedback" / "events" / f"{event['feedback_id']}.json"
            self.assertTrue(immutable.exists())
            rows = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["feedback_id"], event["feedback_id"])
            md = markdown.read_text(encoding="utf-8")
            self.assertIn(event["feedback_id"], md)
            self.assertIn("rendered as data", md)
        finally:
            temp.cleanup()

    def test_capture_appends_multiple_events_without_loss(self):
        temp, target = self.project()
        try:
            first = build_event(self.args(observation="First observation"))
            second = build_event(self.args(observation="Second observation"))
            capture(target, first)
            jsonl, _, _ = capture(target, second)
            rows = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(rows), 2)
        finally:
            temp.cleanup()

    def test_same_feedback_id_retry_is_idempotent(self):
        temp, target = self.project()
        try:
            event = build_event(self.args())
            _, _, first = capture(target, event)
            _, _, second = capture(target, event)
            self.assertFalse(first)
            self.assertTrue(second)
        finally:
            temp.cleanup()

    def test_same_feedback_id_conflict_is_rejected(self):
        temp, target = self.project()
        try:
            now = datetime(2026, 9, 2, 0, 0, 0, tzinfo=timezone.utc)
            event = build_event(self.args(feedback_id="EFF-20260902T000000Z-ABCDEF12"), now=now)
            capture(target, event)
            conflict = build_event(
                self.args(
                    feedback_id="EFF-20260902T000000Z-ABCDEF12",
                    observation="Different semantics",
                ),
                now=now,
            )
            with self.assertRaisesRegex(FeedbackError, "conflicting content"):
                capture(target, conflict)
        finally:
            temp.cleanup()

    def test_invalid_existing_record_blocks_before_new_write(self):
        temp, target = self.project()
        try:
            first = build_event(self.args())
            jsonl, _, _ = capture(target, first)
            immutable = target / ".erei" / "feedback" / "events" / f"{first['feedback_id']}.json"
            broken = json.loads(immutable.read_text(encoding="utf-8"))
            broken["recorded_at"] = "2026-09-02"
            immutable.write_text(json.dumps(broken), encoding="utf-8")
            before = jsonl.read_text(encoding="utf-8")
            new_event = build_event(self.args(observation="Should not commit"))
            with self.assertRaises(FeedbackError):
                capture(target, new_event)
            self.assertEqual(jsonl.read_text(encoding="utf-8"), before)
            self.assertFalse((target / ".erei" / "feedback" / "events" / f"{new_event['feedback_id']}.json").exists())
        finally:
            temp.cleanup()

    def test_fingerprint_is_stable_for_same_content(self):
        now = datetime(2026, 9, 2, 0, 0, 0, tzinfo=timezone.utc)
        a = build_event(self.args(), now=now)
        b = build_event(self.args(), now=now)
        self.assertNotEqual(a["feedback_id"], b["feedback_id"])
        self.assertEqual(a["fingerprint"], b["fingerprint"])


if __name__ == "__main__":
    unittest.main()
