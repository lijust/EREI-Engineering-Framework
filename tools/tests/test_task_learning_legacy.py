"""Compatibility fixtures frozen with Stable V1, independent of the V2 builder."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools import task_learning


FIXTURE = Path(__file__).parent / "fixtures" / "task-learning-v1.json"


def legacy_events():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["events"]


class LegacyFingerprintTests(unittest.TestCase):
    def test_frozen_v1_fingerprints_validate_without_rewriting(self):
        for event in legacy_events():
            with self.subTest(task_id=event["task_id"]):
                original = copy.deepcopy(event)
                task_learning.validate_event(event)
                self.assertEqual(event, original)

    def test_v1_semantic_tampering_is_still_rejected(self):
        event = legacy_events()[0]
        event["duration_class"] = "long"
        with self.assertRaisesRegex(task_learning.LearningError, "fingerprint mismatch"):
            task_learning.validate_event(event)

    def test_v1_optional_list_order_remains_part_of_fingerprint(self):
        event = legacy_events()[1]
        event["tags"].reverse()
        with self.assertRaisesRegex(task_learning.LearningError, "fingerprint mismatch"):
            task_learning.validate_event(event)

    def test_real_legacy_shape_loads_without_modifying_source_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            learning = target / ".erei" / "learning"
            learning.mkdir(parents=True)
            (target / ".erei" / "framework.json").write_text("{}", encoding="utf-8")
            source = learning / "TASK_EVENTS.jsonl"
            source.write_text("\n".join(json.dumps(e) for e in legacy_events()) + "\n", encoding="utf-8")
            before = source.read_bytes()
            result = task_learning.validate_ledgers(target)
            self.assertTrue(result["valid"])
            self.assertEqual(result["events"], 2)
            self.assertEqual(source.read_bytes(), before)

    def test_v2_still_binds_new_semantics(self):
        event = legacy_events()[0]
        event.update(
            schema_version=2,
            occurrence_id="EOCC-20261001T090000Z-11111111",
            failure_stage="none",
            signal_assessment={key: "measured" for key in task_learning.SIGNAL_KEYS},
        )
        event["fingerprint"] = task_learning._fingerprint(event)
        task_learning.validate_event(event)
        event["failure_stage"] = "unknown"
        with self.assertRaisesRegex(task_learning.LearningError, "fingerprint mismatch"):
            task_learning.validate_event(event)


if __name__ == "__main__":
    unittest.main()

