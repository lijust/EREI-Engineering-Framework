from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path

from tools.capture_framework_feedback import build_event
from tools.validate_framework_feedback import ValidationError, validate_event, validate_jsonl


class FeedbackValidationTests(unittest.TestCase):
    def args(self):
        return argparse.Namespace(
            project_repository="example/project",
            project_name="Example Project",
            framework_ref="a" * 40,
            type="verification_gap",
            severity="high",
            source_artifact="skills/verification-before-completion",
            observation="A deterministic gate was skipped by the documented path.",
            evidence=["evidence/REG-001.md"],
            suggestion="Require the deterministic gate before completion.",
            negative_learning=None,
            generalizability="likely_generic",
            confidence="high",
            tag=["verification"],
        )

    def test_valid_event_passes(self):
        validate_event(build_event(self.args()))

    def test_tampered_semantics_break_fingerprint(self):
        event = build_event(self.args())
        event["suggestion"] = "Different suggestion"
        with self.assertRaisesRegex(ValidationError, "fingerprint"):
            validate_event(event)

    def test_unknown_field_fails(self):
        event = build_event(self.args())
        event["auto_promote"] = True
        with self.assertRaisesRegex(ValidationError, "unknown fields"):
            validate_event(event)

    def test_jsonl_validates_multiple_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            first = build_event(self.args())
            second_args = self.args()
            second_args.observation = "Another verified limitation."
            second = build_event(second_args)
            path.write_text(
                json.dumps(first, ensure_ascii=False, sort_keys=True) + "\n" +
                json.dumps(second, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(validate_jsonl(path), 2)

    def test_corrupt_jsonl_fails_with_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            event = build_event(self.args())
            path.write_text(json.dumps(event) + "\n{bad json}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValidationError, "line 2"):
                validate_jsonl(path)


if __name__ == "__main__":
    unittest.main()
