"""Legacy positional reviews must use the original event ledger order."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

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
            self.project(target, original, [legacy_review(2)], [middle, appended])
            snapshot = task_learning.authoritative_snapshot(target)
            self.assertEqual(snapshot["events"], original + [appended])
            reviewed, _ = task_learning._reviewed_occurrences(snapshot["events"], snapshot["reviews"])
            self.assertEqual(reviewed, {first["task_id"], middle["occurrence_id"]})
            self.assertEqual(snapshot["state"]["metrics_since_last_review"]["verification_escapes"], 1)

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


if __name__ == "__main__":
    unittest.main()

