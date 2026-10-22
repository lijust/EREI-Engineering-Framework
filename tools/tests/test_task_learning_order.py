"""Legacy positional reviews must use the original event ledger order."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools import task_learning
from tools.tests.test_task_learning_legacy import legacy_events


def v2_event(escape=False, suffix="33333333"):
    event = legacy_events()[0]
    event.update(
        schema_version=2,
        task_id="ETASK-20261002T090000Z-" + suffix,
        occurrence_id="EOCC-20261002T090000Z-" + suffix,
        recorded_at="2026-10-02T09:00:00Z",
        failure_stage="runtime" if escape else "none",
        verification_escape=escape,
        signal_assessment={key: "measured" for key in task_learning.SIGNAL_KEYS},
    )
    event["fingerprint"] = task_learning._fingerprint(event)
    return event


def legacy_review(cutoff):
    return {
        "schema_version": 1,
        "review_id": "ELR-20261001T100000Z-AAAAAAAA",
        "closed_at": "2026-10-01T10:00:00Z",
        "epoch_id": "EPOCH-001",
        "through_event_count": cutoff,
        "trigger": {"level": "LEARNING_HEALTHY", "reasons": []},
        "metrics": {},
        "findings": "Frozen legacy review.",
        "decision": "Preserve original event membership.",
        "evidence": ["audit:legacy-fixture"],
    }


class LegacyOrderTests(unittest.TestCase):
    def project(self, root, events, reviews=(), immutable=()):
        learning = root / ".erei" / "learning"
        learning.mkdir(parents=True)
        (root / ".erei" / "framework.json").write_text("{}", encoding="utf-8")
        for name, records in (("TASK_EVENTS.jsonl", events), ("LEARNING_REVIEWS.jsonl", reviews)):
            (learning / name).write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in records), encoding="utf-8")
        for event in immutable:
            task_learning._write_immutable_json(learning / "events" / (event["occurrence_id"] + ".json"), event)

    def test_v1_cutoff_preserves_append_order_even_with_earlier_timestamp(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            original = legacy_events()  # 09:00 then 08:00: append order is authoritative.
            self.project(target, original, [legacy_review(1)])
            snapshot = task_learning.authoritative_snapshot(target)
            self.assertEqual(snapshot["events"], original)
            self.assertEqual(snapshot["state"]["metrics_since_last_review"]["total_rework_cycles"], 2)

    def test_first_new_v2_escape_cannot_be_consumed_by_full_v1_cutoff(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            original = legacy_events()
            self.project(target, original, [legacy_review(2)])
            new = v2_event(escape=True)
            before = (target / ".erei/learning/LEARNING_REVIEWS.jsonl").read_bytes()
            state, duplicate = task_learning.capture(target, new)
            self.assertFalse(duplicate)
            self.assertEqual(state["reviewed_occurrence_count"], 2)
            self.assertEqual(state["metrics_since_last_review"]["tasks"], 1)
            self.assertEqual(state["metrics_since_last_review"]["verification_escapes"], 1)
            self.assertEqual(state["trigger"]["level"], "IMMEDIATE_REVIEW")
            snapshot = task_learning.authoritative_snapshot(target)
            self.assertEqual(snapshot["events"], original + [new])
            retried, duplicate = task_learning.capture(target, new)
            self.assertTrue(duplicate)
            self.assertEqual(retried["metrics_since_last_review"], state["metrics_since_last_review"])
            self.assertEqual((target / ".erei/learning/LEARNING_REVIEWS.jsonl").read_bytes(), before)

    def test_existing_mixed_projection_positions_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            first, last = legacy_events()
            middle = v2_event()
            appended = v2_event(escape=True, suffix="44444444")
            original = [first, middle, last]
            self.project(target, original + [appended], [legacy_review(2)], [middle, appended])
            snapshot = task_learning.authoritative_snapshot(target)
            self.assertEqual(snapshot["events"], original + [appended])
            reviewed, _ = task_learning._reviewed_occurrences(snapshot["events"], snapshot["reviews"])
            self.assertEqual(reviewed, {first["task_id"], middle["occurrence_id"]})
            self.assertEqual(snapshot["state"]["metrics_since_last_review"]["verification_escapes"], 1)

    def test_late_v1_cutoff_cannot_reclose_an_earlier_v2_review(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            first, last = legacy_events()
            metrics = task_learning._metrics([first])
            early = {
                "schema_version": 2,
                "review_id": "ELR-20261001T090000Z-11111111",
                "closed_at": "2026-10-01T09:00:00Z",
                "epoch_id": "EPOCH-001",
                "reviewed_occurrence_ids": [first["task_id"]],
                "event_digest": task_learning._event_digest([first]),
                "trigger": task_learning._trigger(metrics),
                "metrics": metrics,
                "findings": "Synthetic explicitly reviewed occurrence.",
                "decision": "Protect explicit review membership.",
                "evidence": ["audit:synthetic"],
            }
            later = legacy_review(1)
            later["epoch_id"] = "EPOCH-002"
            self.project(target, [first, last], [early, later])
            # A V2 review must have immutable authority; otherwise loading
            # fails for the unrelated authority rule before testing overlap.
            task_learning._write_immutable_json(
                target / ".erei/learning/reviews" / (early["review_id"] + ".json"),
                early,
            )
            ledger = target / ".erei/learning/TASK_EVENTS.jsonl"
            before = ledger.read_bytes()
            with self.assertRaisesRegex(task_learning.LearningError, "review re-closes occurrences"):
                task_learning.authoritative_snapshot(target)
            self.assertEqual(ledger.read_bytes(), before)

    def test_duplicate_projection_identity_is_rejected_instead_of_shifting_cutoff(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            first = legacy_events()[0]
            self.project(target, [first, copy.deepcopy(first)], [legacy_review(1)])
            with self.assertRaisesRegex(task_learning.LearningError, "duplicate event projection identity"):
                task_learning.authoritative_snapshot(target)

    def test_missing_v2_projection_still_rebuilds_in_deterministic_order(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            earlier = v2_event(suffix="33333333")
            later = v2_event(suffix="44444444")
            self.project(target, [], [], [later, earlier])
            snapshot = task_learning.authoritative_snapshot(target)
            self.assertEqual(snapshot["events"], [earlier, later])
            rebuilt = task_learning.status(target)
            self.assertEqual(rebuilt["total_events"], 2)

    def test_missing_mixed_position_blocks_every_entrypoint_without_ledger_writes(self):
        operations = {
            "snapshot": task_learning.authoritative_snapshot,
            "validate": task_learning.validate_ledgers,
            "status": task_learning.status,
            "capture": lambda target: task_learning.capture(target, v2_event(suffix="55555555")),
            "close_review": lambda target: task_learning.close_review(target, SimpleNamespace(
                evidence=["audit:synthetic"], review_id=None, findings="Review findings",
                decision="Review decision", action=[],
            )),
        }
        for name, operation in operations.items():
            with self.subTest(operation=name), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                first, last = legacy_events()
                last["verification_escape"] = True
                last["fingerprint"] = task_learning._fingerprint(last)
                middle = v2_event()
                self.project(target, [first, middle, last], [legacy_review(2)], [middle])
                original = task_learning.authoritative_snapshot(target)
                self.assertEqual(original["state"]["trigger"]["level"], "IMMEDIATE_REVIEW")
                ledger = target / ".erei/learning/TASK_EVENTS.jsonl"
                ledger.write_text("".join(json.dumps(row) + "\n" for row in [first, last]), encoding="utf-8")
                before = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
                with self.assertRaisesRegex(task_learning.LearningError, "legacy review membership.*recovery required"):
                    operation(target)
                after = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
                self.assertEqual(after, before)

    def test_retry_after_capture_crash_requires_projection_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            self.project(target, legacy_events(), [legacy_review(2)])
            event = v2_event(escape=True)
            ledger = target / ".erei/learning/TASK_EVENTS.jsonl"
            before = ledger.read_bytes()
            with mock.patch.object(task_learning, "_persist_projections", side_effect=OSError("simulated crash")):
                with self.assertRaisesRegex(OSError, "simulated crash"):
                    task_learning.capture(target, event)
            self.assertTrue((target / ".erei/learning/events" / (event["occurrence_id"] + ".json")).is_file())
            with self.assertRaisesRegex(task_learning.LearningError, "legacy review membership.*recovery required"):
                task_learning.capture(target, event)
            self.assertEqual(ledger.read_bytes(), before)

    def test_capture_admission_does_not_cover_other_immutable_only_occurrences(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            self.project(target, legacy_events(), [legacy_review(2)])
            event, other = v2_event(), v2_event(escape=True, suffix="44444444")
            original_write = task_learning._write_immutable_json
            def concurrent_unprojected_write(path, value):
                original_write(path, value)
                original_write(path.parent / (other["occurrence_id"] + ".json"), other)
            ledger = target / ".erei/learning/TASK_EVENTS.jsonl"
            before = ledger.read_bytes()
            with mock.patch.object(task_learning, "_write_immutable_json", side_effect=concurrent_unprojected_write):
                with self.assertRaisesRegex(task_learning.LearningError, "legacy review membership.*recovery required"):
                    task_learning.capture(target, event)
            self.assertEqual(ledger.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()

