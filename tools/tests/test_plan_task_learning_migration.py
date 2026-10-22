import copy
import contextlib
import io
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import plan_task_learning_migration as migration
from tools import task_learning
from tools.tests.test_task_learning_legacy import legacy_events
from tools.tests.test_task_learning_order import legacy_review, v2_event


class MigrationPlanTests(unittest.TestCase):
    def setup_project(self, root, events, reviews=()):
        learning = root / ".erei" / "learning"
        learning.mkdir(parents=True)
        (root / ".erei" / "framework.json").write_text("{}", encoding="utf-8")
        for name, rows in (("TASK_EVENTS.jsonl", events), ("LEARNING_REVIEWS.jsonl", reviews)):
            (learning / name).write_text("".join(json.dumps(e) + "\n" for e in rows), encoding="utf-8")
        return learning

    def files(self, target):
        return {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob("*") if p.is_file()}

    def test_projection_only_v2_plan_preserves_source_order_and_never_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            first, last = legacy_events()
            middle = v2_event()
            review = legacy_review(2)
            review["closed_at"] = "2026-10-02T10:00:00Z"
            self.setup_project(target, [first, middle, last], [review])
            before = self.files(target)
            report = migration.plan(target)
            self.assertEqual(report["status"], "REVIEW_REQUIRED")
            self.assertFalse(report["apply_supported"])
            self.assertEqual(len(report["proposed_immutable_files"]), 1)
            self.assertEqual(report["legacy_review_memberships"][0]["reviewed_occurrence_ids"], [first["task_id"], middle["occurrence_id"]])
            self.assertEqual(report["derived_summary"]["unreviewed_tasks"], 1)
            self.assertEqual(report["source_files"][1]["git_blob_sha1"], __import__("hashlib").sha1(
                b"blob " + str(len(before[".erei/learning/TASK_EVENTS.jsonl"])).encode() + b"\0" + before[".erei/learning/TASK_EVENTS.jsonl"]
            ).hexdigest())
            self.assertEqual(self.files(target), before)
            # A dry-run must not make otherwise invalid live authority usable.
            with self.assertRaisesRegex(task_learning.LearningError, "without immutable authority"):
                task_learning.validate_ledgers(target)

    def test_historical_anomaly_blocks_all_proposals_without_repair(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            invalid = legacy_events()[0]
            invalid["duration_class"] = "long"
            self.setup_project(target, [invalid, v2_event()], [legacy_review(1)])
            before = self.files(target)
            report = migration.plan(target)
            self.assertEqual(report["status"], "BLOCKED")
            self.assertIn("fingerprint mismatch", report["issues"][0]["error"])
            self.assertEqual(report["proposed_immutable_files"], [])
            self.assertEqual(report["legacy_review_memberships"], [])
            self.assertEqual(len(report["missing_immutable_authority"]), 1)
            self.assertEqual(self.files(target), before)

    def test_invalid_legacy_identity_is_not_grandfathered(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            invalid = legacy_events()[0]
            invalid["task_id"] = "ETASK-20261001T090000Z-NOTHEXID"
            self.setup_project(target, [invalid])
            report = migration.plan(target)
            self.assertEqual(report["status"], "BLOCKED")
            self.assertIn("invalid task_id", report["issues"][0]["error"])

    def test_duplicate_projection_identity_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            event = v2_event()
            self.setup_project(target, [event, copy.deepcopy(event)])
            report = migration.plan(target)
            self.assertEqual(report["status"], "BLOCKED")
            self.assertEqual(report["proposed_immutable_files"], [])
            self.assertIn("duplicate", report["issues"][0]["error"])

    def test_existing_immutable_conflict_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            event = v2_event()
            learning = self.setup_project(target, [event])
            conflict = copy.deepcopy(event)
            conflict["duration_class"] = "long"
            conflict["fingerprint"] = task_learning._fingerprint(conflict)
            task_learning._write_immutable_json(learning / "events" / (event["occurrence_id"] + ".json"), conflict)
            before = self.files(target)
            report = migration.plan(target)
            self.assertEqual(report["status"], "BLOCKED")
            self.assertIn("differs from immutable authority", report["issues"][0]["error"])
            self.assertEqual(self.files(target), before)

    def test_valid_authority_needs_no_import(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            event = v2_event()
            learning = self.setup_project(target, [event])
            task_learning._write_immutable_json(learning / "events" / (event["occurrence_id"] + ".json"), event)
            report = migration.plan(target)
            self.assertEqual(report["status"], "NO_IMPORT_REQUIRED")
            self.assertEqual(report["proposed_immutable_files"], [])

    def test_proposed_digest_matches_existing_writer_bytes_on_this_platform(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            event = v2_event()
            self.setup_project(target, [event])
            report = migration.plan(target)
            proposal = report["proposed_immutable_files"][0]
            # Test fixture only: the planner itself has no write capability.
            destination = target / proposal["path"]
            task_learning._write_immutable_json(destination, event)
            self.assertEqual(proposal["content_sha256"], hashlib.sha256(destination.read_bytes()).hexdigest())

    def test_legacy_cutoff_outside_original_ledger_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            self.setup_project(target, legacy_events(), [legacy_review(3)])
            report = migration.plan(target)
            self.assertEqual(report["status"], "BLOCKED")
            self.assertIn("invalid legacy learning review cutoff", report["issues"][0]["error"])

    def test_missing_historical_mixed_order_is_not_inferred(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            learning = self.setup_project(target, legacy_events(), [legacy_review(1)])
            event = v2_event()
            task_learning._write_immutable_json(learning / "events" / (event["occurrence_id"] + ".json"), event)
            report = migration.plan(target)
            self.assertEqual(report["status"], "BLOCKED")
            self.assertIn("original projection order", report["issues"][0]["error"])

    def test_concurrent_source_change_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            self.setup_project(target, [v2_event()])
            with patch.object(task_learning, "_ledger_generation", side_effect=["first", "changed"]):
                report = migration.plan(target)
            self.assertEqual(report["status"], "BLOCKED")
            self.assertEqual(report["proposed_immutable_files"], [])
            self.assertEqual(report["issues"][0]["kind"], "source_changed")

    def test_noncanonical_projection_order_reports_canonical_review_membership(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            first, second = legacy_events()
            earlier = legacy_review(1)
            later = copy.deepcopy(earlier)
            later["review_id"] = "ELR-20261002T100000Z-BBBBBBBB"
            later["epoch_id"] = "EPOCH-002"
            later["closed_at"] = "2026-10-02T10:00:00Z"
            later["through_event_count"] = 2
            # The source rows are not canonical, but the real loader sorts
            # reviews by ID. The planner must sort both state and the report.
            self.setup_project(target, [first, second], [later, earlier])
            before = self.files(target)
            report = migration.plan(target)
            self.assertEqual(report["status"], "NO_IMPORT_REQUIRED")
            self.assertEqual(report["proposed_immutable_files"], [])
            memberships = report["legacy_review_memberships"]
            self.assertEqual([r["review_id"] for r in memberships],
                             [earlier["review_id"], later["review_id"]])
            self.assertEqual([r["reviewed_occurrence_ids"] for r in memberships],
                             [[first["task_id"]], [second["task_id"]]])
            self.assertEqual(self.files(target), before)

    def test_out_of_order_review_ids_block_instead_of_approving_wrong_epoch(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            first, second = legacy_events()
            initial = legacy_review(1)
            later = copy.deepcopy(initial)
            later["review_id"] = "ELR-20260930T100000Z-BBBBBBBB"
            later["epoch_id"] = "EPOCH-002"
            later["through_event_count"] = 2
            self.setup_project(target, [first, second], [initial, later])
            before = self.files(target)
            report = migration.plan(target)
            # The real ledger loader sorts review IDs, so the epoch sequence
            # fails there. The planner must fail the same way, without writes.
            self.assertEqual(report["status"], "BLOCKED")
            self.assertEqual(report["proposed_immutable_files"], [])
            self.assertTrue(any(
                "epoch sequence mismatch" in issue["error"]
                for issue in report["issues"]
            ))
            self.assertEqual(self.files(target), before)

    def test_apply_flag_does_not_exist(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                migration.main(["--target", ".", "--apply"])
        self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()

