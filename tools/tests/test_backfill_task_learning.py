from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import backfill_task_learning as backfill

PRODUCER = "c76fb80297ac624246e60e178bcf985a2d35ab1d"
SOURCE_REV = "48efb10da57bb8e6a9adc1325074b7fabb1945b5"


class RetrospectiveTaskLearningTests(unittest.TestCase):
    def _target(self, root: Path) -> Path:
        target = root / "project"
        (target / ".erei").mkdir(parents=True)
        (target / ".erei" / "framework.json").write_text("{}", encoding="utf-8")
        return target

    def _raw(self) -> dict:
        return {
            "schema_version": 2,
            "historical_event_id": "EHIST-20260907T010000Z-A1B2C3D4",
            "occurrence_id": "erei-app-google:pr48:search-snapshot-adapter-v1",
            "recorded_at": "2026-09-07T01:00:00Z",
            "observed_at": "2026-09-06T14:29:25Z",
            "project": {"repository": "lijust/EREI-App-Google"},
            "framework_ref_when_executed": "f" * 40,
            "evidence_quality": "reconstructed",
            "task_label": "Implementation: add PostgreSQL SearchSnapshotRepository adapter V1",
            "workflow": "feature-development",
            "risk": "L2",
            "source_refs": ["ESRC-PR48"],
            "outcome_class": "verified_success",
            "signals": [
                {
                    "name": "verification_failures",
                    "value": 2,
                    "quality": "confirmed",
                    "source_refs": ["ESRC-PR48"],
                }
            ],
        }

    def _provenance(self) -> list[dict]:
        return [
            {
                "schema_version": 1,
                "source_id": "ESRC-PR48",
                "kind": "github_pr",
                "repository": "lijust/EREI-App-Google",
                "revision": SOURCE_REV,
                "locator": "pull/48",
                "event_time": None,
                "event_time_meaning": "unknown",
                "reconstruction_time": "2026-09-07T01:00:00Z",
            }
        ]

    def _write_inputs(self, root: Path, events=None, provenance=None):
        source = root / "events.json"
        source.write_text(json.dumps(events if events is not None else [self._raw()]), encoding="utf-8")
        prov = root / "provenance.json"
        prov.write_text(json.dumps(provenance if provenance is not None else self._provenance()), encoding="utf-8")
        return source, prov

    def test_normalize_v2_has_stable_occurrence_and_producer(self):
        event = backfill.normalize_v2(self._raw(), producer_repository="lijust/EREI-Engineering-Framework", producer_ref=PRODUCER)
        self.assertEqual(event["capture_mode"], "retrospective")
        self.assertEqual(event["occurrence_id"], self._raw()["occurrence_id"])
        self.assertEqual(event["producer"]["ref"], PRODUCER)
        self.assertEqual(event["canonicalization_version"], 2)
        self.assertEqual(len(event["fingerprint"]), 64)
        backfill.validate_event(event)

    def test_import_is_idempotent_by_occurrence_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = self._target(root)
            source, prov = self._write_inputs(root, events=[self._raw(), self._raw()])
            added, sources = backfill.import_events(
                target, source, prov,
                producer_repository="lijust/EREI-Engineering-Framework",
                producer_ref=PRODUCER,
            )
            self.assertEqual(added, 1)
            self.assertEqual(sources, 1)
            added_again, sources_again = backfill.import_events(
                target, source, prov,
                producer_repository="lijust/EREI-Engineering-Framework",
                producer_ref=PRODUCER,
            )
            self.assertEqual((added_again, sources_again), (0, 0))

    def test_same_occurrence_with_enriched_content_requires_amendment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = self._target(root)
            source, prov = self._write_inputs(root)
            backfill.import_events(target, source, prov, producer_repository="lijust/EREI-Engineering-Framework", producer_ref=PRODUCER)
            enriched = self._raw()
            enriched["evidence_quality"] = "confirmed"
            source.write_text(json.dumps([enriched]), encoding="utf-8")
            with self.assertRaisesRegex(backfill.BackfillError, "use an amendment"):
                backfill.import_events(target, source, prov, producer_repository="lijust/EREI-Engineering-Framework", producer_ref=PRODUCER)

    def test_amendment_preserves_occurrence_and_is_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = self._target(root)
            source, prov = self._write_inputs(root)
            backfill.import_events(target, source, prov, producer_repository="lijust/EREI-Engineering-Framework", producer_ref=PRODUCER)
            amendment_source = root / "amendments.json"
            amendment_source.write_text(json.dumps([{
                "amendment_id": "EAMD-20260907T020000Z-ABCDEF12",
                "recorded_at": "2026-09-07T02:00:00Z",
                "occurrence_id": self._raw()["occurrence_id"],
                "reason": "Evidence quality improved after exact revision review.",
                "changes": {"evidence_quality": "confirmed"},
            }]), encoding="utf-8")
            added, _ = backfill.import_amendments(
                target, amendment_source, None,
                producer_repository="lijust/EREI-Engineering-Framework",
                producer_ref=PRODUCER,
            )
            self.assertEqual(added, 1)
            result = backfill.validate_ledger(target)
            self.assertEqual(result["amendments"], 1)
            self.assertEqual(result["v2_events"], 1)

    def test_missing_frozen_provenance_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = self._target(root)
            source, prov = self._write_inputs(root, provenance=[])
            with self.assertRaisesRegex(backfill.BackfillError, "missing provenance"):
                backfill.import_events(target, source, prov, producer_repository="lijust/EREI-Engineering-Framework", producer_ref=PRODUCER)

    def test_invalid_date_unknown_field_and_object_signal_fail(self):
        raw = self._raw()
        raw["observed_at"] = "2026-99-99"
        raw["unexpected"] = True
        raw["signals"][0]["value"] = {"bad": "type"}
        with self.assertRaises(backfill.BackfillError):
            backfill.normalize_v2(raw, producer_repository="lijust/EREI-Engineering-Framework", producer_ref=PRODUCER)

    def test_boolean_is_not_accepted_as_count_signal(self):
        raw = self._raw()
        raw["signals"][0]["value"] = True
        with self.assertRaises(backfill.BackfillError):
            backfill.normalize_v2(raw, producer_repository="lijust/EREI-Engineering-Framework", producer_ref=PRODUCER)

    def test_tampered_immutable_event_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = self._target(root)
            source, prov = self._write_inputs(root)
            backfill.import_events(target, source, prov, producer_repository="lijust/EREI-Engineering-Framework", producer_ref=PRODUCER)
            event_path = next((target / ".erei" / "learning" / "retrospective-events").glob("*.json"))
            event = json.loads(event_path.read_text(encoding="utf-8"))
            event["task_label"] = "tampered"
            event_path.write_text(json.dumps(event), encoding="utf-8")
            with self.assertRaises(backfill.BackfillError):
                backfill.validate_ledger(target)


if __name__ == "__main__":
    unittest.main()
