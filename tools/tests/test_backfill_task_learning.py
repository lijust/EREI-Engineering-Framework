from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import backfill_task_learning as backfill


class RetrospectiveTaskLearningTests(unittest.TestCase):
    def _target(self, root: Path) -> Path:
        target = root / "project"
        (target / ".erei").mkdir(parents=True)
        (target / ".erei" / "framework.json").write_text("{}", encoding="utf-8")
        return target

    def _raw(self) -> dict:
        return {
            "observed_at": "2026-09-06T14:29:25Z",
            "project": {"repository": "lijust/EREI-App-Google"},
            "framework_ref_when_executed": "f" * 40,
            "evidence_quality": "reconstructed",
            "task_label": "Implementation: add PostgreSQL SearchSnapshotRepository adapter V1",
            "workflow": "feature-development",
            "risk": "L2",
            "source_refs": ["github-pr:48", "ci-run:34039214971"],
            "outcome_class": "verified_success",
            "signals": [
                {
                    "name": "verification_failures",
                    "value": 2,
                    "quality": "confirmed",
                    "source_refs": ["github-pr:48"]
                }
            ]
        }

    def test_normalize_marks_retrospective_and_validates(self) -> None:
        event = backfill.normalize_imported(self._raw())
        self.assertEqual(event["capture_mode"], "retrospective")
        self.assertEqual(len(event["fingerprint"]), 64)
        backfill.validate_event(event)

    def test_import_deduplicates_by_semantic_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = self._target(root)
            source = root / "events.json"
            source.write_text(json.dumps([self._raw(), self._raw()]), encoding="utf-8")
            added, ledger = backfill.import_events(target, source)
            self.assertEqual(added, 1)
            self.assertEqual(len(backfill._read_jsonl(ledger)), 1)

    def test_missing_project_integration_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "project"
            target.mkdir()
            source = root / "events.json"
            source.write_text(json.dumps([self._raw()]), encoding="utf-8")
            with self.assertRaises(backfill.BackfillError):
                backfill.import_events(target, source)

    def test_signal_requires_source_evidence(self) -> None:
        raw = self._raw()
        raw["signals"][0]["source_refs"] = []
        with self.assertRaises(backfill.BackfillError):
            backfill.normalize_imported(raw)

    def test_tampered_ledger_fingerprint_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = self._target(root)
            source = root / "events.json"
            source.write_text(json.dumps([self._raw()]), encoding="utf-8")
            _, ledger = backfill.import_events(target, source)
            event = json.loads(ledger.read_text(encoding="utf-8"))
            event["task_label"] = "tampered"
            ledger.write_text(json.dumps(event) + "\n", encoding="utf-8")
            with self.assertRaises(backfill.BackfillError):
                backfill.validate_ledger(target)


if __name__ == "__main__":
    unittest.main()
