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
            type="workflow_gap",
            severity="medium",
            source_artifact="workflows/bug-fix",
            observation="A required concurrency check was missing.",
            evidence=["evidence/BUG-001.md"],
            suggestion="Add a concurrency trigger to bug-fix workflow.",
            negative_learning="Do not assume local success proves concurrency safety.",
            generalizability="likely_generic",
            confidence="high",
            tag=["concurrency", "regression"],
        )
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_build_event_is_evidence_backed_and_fingerprinted(self):
        now = datetime(2026, 9, 2, 0, 0, 0, tzinfo=timezone.utc)
        event = build_event(self.args(), now=now)
        self.assertRegex(event["feedback_id"], r"^EFF-20260902T000000Z-[A-F0-9]{8}$")
        self.assertEqual(event["recorded_at"], "2026-09-02T00:00:00Z")
        self.assertEqual(event["status"], "new")
        self.assertEqual(len(event["fingerprint"]), 64)
        self.assertEqual(event["evidence"], ["evidence/BUG-001.md"])

    def test_missing_evidence_is_rejected(self):
        with self.assertRaises(FeedbackError):
            build_event(self.args(evidence=[]))

    def test_capture_requires_erei_integrated_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FeedbackError):
                capture(Path(tmp), build_event(self.args()))

    def test_capture_writes_jsonl_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / ".erei").mkdir()
            (target / ".erei" / "framework.json").write_text("{}", encoding="utf-8")
            event = build_event(self.args())
            jsonl, markdown = capture(target, event)
            self.assertTrue(jsonl.exists())
            self.assertTrue(markdown.exists())
            rows = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["feedback_id"], event["feedback_id"])
            md = markdown.read_text(encoding="utf-8")
            self.assertIn(event["feedback_id"], md)
            self.assertIn("Suggested Framework improvement", md)

    def test_capture_appends_multiple_events_without_loss(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / ".erei").mkdir()
            (target / ".erei" / "framework.json").write_text("{}", encoding="utf-8")
            first = build_event(self.args(observation="First observation"))
            second = build_event(self.args(observation="Second observation"))
            capture(target, first)
            jsonl, _ = capture(target, second)
            rows = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["observation"], "First observation")
            self.assertEqual(rows[1]["observation"], "Second observation")

    def test_fingerprint_is_stable_for_same_semantics(self):
        now = datetime(2026, 9, 2, 0, 0, 0, tzinfo=timezone.utc)
        a = build_event(self.args(), now=now)
        b = build_event(self.args(), now=now)
        self.assertNotEqual(a["feedback_id"], b["feedback_id"])
        self.assertEqual(a["fingerprint"], b["fingerprint"])


if __name__ == "__main__":
    unittest.main()
