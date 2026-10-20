"""Opt-in, synthetic rollback drill; never accepts a consumer project path.

Run with --v1-tool pointing to the exact Git-exported Stable V1 source.
This is an integration test, not a migration or rollback command.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import types
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import task_learning as v2

V1_COMMIT = "69079018606750312344cb3c648952b9ab72d35b"
V1_TOOL_SHA256 = "336037ea356c91d780f61684889b7c92c5d2bde21a8fff2591fec95e559be8f2"
# Fixture metadata only. Actual V2 source identity is emitted in the report.
TRIAL_REF = "9ca0fd14ca2e4a60def23f9e7df11c827a961135"
v1 = None


def load_v1(source: bytes):
    if hashlib.sha256(source).hexdigest() != V1_TOOL_SHA256:
        raise ValueError("V1 tool bytes do not match the frozen Stable source")
    module = types.ModuleType("rollback_drill_v1")
    # Execute the verified bytes, without a second file read.
    exec(compile(source, "frozen_v1_task_learning.py", "exec"), module.__dict__)
    return module


def files(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*") if path.is_file()
    }


def event(module, number, *, escape=False):
    stamp = f"20261001T09000{number}Z"
    args = module.parse_args([
        "capture", "--target", "unused-fixture-path",
        "--project-repository", "example/rollback-fixture",
        "--framework-ref", V1_COMMIT if module is v1 else TRIAL_REF,
        "--task-id", f"ETASK-{stamp}-{number:08X}",
        "--workflow", "bug-fix", "--risk", "L1",
        "--terminal-state", "COMPLETE_VERIFIED",
        "--outcome-class", "verified_success",
        "--rework-cycles", "0", "--verification-failures", "0",
    ])
    if module is v2:
        args.occurrence_id = f"EOCC-{stamp}-{number:08X}"
        args.failure_stage = "runtime" if escape else "none"
    args.verification_escape = escape
    # Deliberately reverse the two V1 timestamps: append order defines membership.
    now = datetime(2026, 10, 1, 10 - number if number <= 2 else 11, number, tzinfo=timezone.utc)
    return module.build_event(args, now=now)


def review_args(number):
    return argparse.Namespace(
        review_id=f"ELR-20261001T12000{number}Z-{number:08X}",
        findings="Synthetic rollback fixture only.",
        decision="Preserve membership and retain all trial evidence.",
        evidence=["fixture:rollback-drill"], action=[],
    )


class RollbackDrill(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="erei-rollback-drill-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.baseline = self.root / "baseline-v1"
        (self.baseline / ".erei").mkdir(parents=True)
        (self.baseline / ".erei/framework.json").write_text(json.dumps({
            "repository": "lijust/EREI-Engineering-Framework",
            "ref_type": "commit", "ref": V1_COMMIT,
        }) + "\n", encoding="utf-8")
        self.old_events = [event(v1, 1), event(v1, 2)]
        for item in self.old_events:
            v1.capture(self.baseline, item)
        self.old_review, _ = v1.close_review(
            self.baseline, review_args(1),
            now=datetime(2026, 10, 1, 12, tzinfo=timezone.utc),
        )
        self.baseline_bytes = files(self.baseline)
        self.trial = self.root / "trial-v2"
        shutil.copytree(self.baseline, self.trial)
        pin = self.trial / ".erei/framework.json"
        value = json.loads(pin.read_text(encoding="utf-8"))
        value["ref"] = TRIAL_REF
        pin.write_text(json.dumps(value) + "\n", encoding="utf-8")
        self.reviewed_new = event(v2, 3)
        v2.capture(self.trial, self.reviewed_new)
        self.new_review, _ = v2.close_review(
            self.trial, review_args(2),
            now=datetime(2026, 10, 1, 13, tzinfo=timezone.utc),
        )
        self.pending_escape = event(v2, 4, escape=True)
        v2.capture(self.trial, self.pending_escape)

    def test_pin_only_rollback_rejects_v2_without_status_writes(self):
        pin = self.trial / ".erei/framework.json"
        pin.write_bytes(self.baseline_bytes[".erei/framework.json"])
        before = files(self.trial)
        for reader in (v1.validate_ledgers, v1.status):
            with self.subTest(reader=reader.__name__):
                with self.assertRaisesRegex(v1.LearningError, "unsupported task event schema_version"):
                    reader(self.trial)
                self.assertEqual(files(self.trial), before)

    def test_fresh_restore_preserves_baseline_and_full_trial_archive(self):
        trial_bytes = files(self.trial)
        archive = self.root / "retained-v2"
        shutil.copytree(self.trial, archive)
        self.assertEqual(files(archive), trial_bytes)
        restored = self.root / "restored-v1"
        shutil.copytree(self.baseline, restored)
        self.assertEqual(files(restored), self.baseline_bytes)
        result = v1.validate_ledgers(restored)
        self.assertEqual((result["events"], result["reviews"], result["epoch_id"]), (2, 1, "EPOCH-002"))
        v1.status(restored)
        for name in ("TASK_EVENTS.jsonl", "LEARNING_REVIEWS.jsonl"):
            key = ".erei/learning/" + name
            self.assertEqual(files(restored)[key], self.baseline_bytes[key])
        self.assertEqual(files(restored)[".erei/framework.json"], self.baseline_bytes[".erei/framework.json"])

        retained = v2.authoritative_snapshot(archive)
        self.assertEqual(retained["events"], self.old_events + [self.reviewed_new, self.pending_escape])
        self.assertEqual(retained["reviews"], [self.old_review, self.new_review])
        historical_ids, _ = v2._reviewed_occurrences(retained["events"], [self.old_review])
        self.assertEqual(historical_ids, {item["task_id"] for item in self.old_events})
        self.assertEqual(self.new_review["reviewed_occurrence_ids"], [self.reviewed_new["occurrence_id"]])
        state = retained["state"]
        self.assertEqual(state["metrics_since_last_review"]["tasks"], 1)
        self.assertEqual(state["metrics_since_last_review"]["verification_escapes"], 1)
        self.assertEqual(state["trigger"]["level"], "IMMEDIATE_REVIEW")
        self.assertEqual(files(archive), trial_bytes)
        self.assertEqual(files(self.baseline), self.baseline_bytes)

        # New V1 work is a separate history; never merge ledgers or renumber epochs.
        resumed_event = event(v1, 5)
        v1.capture(restored, resumed_event)
        self.assertEqual(v1.validate_ledgers(restored)["events"], 3)
        self.assertEqual(files(archive), trial_bytes)
        self.assertEqual(files(self.trial), trial_bytes)
        self.assertNotIn(resumed_event["task_id"], {item["task_id"] for item in retained["events"]})

    def test_verified_v1_loader_rejects_modified_source(self):
        with self.assertRaisesRegex(ValueError, "frozen Stable source"):
            load_v1(b"raise RuntimeError('untrusted source must not execute')")


def main():
    global v1
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v1-tool", type=Path, required=True)
    args = parser.parse_args()
    try:
        v1 = load_v1(args.v1_tool.read_bytes())
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(RollbackDrill)
    )
    print(json.dumps({
        "evidence_kind": "LOCAL_SYNTHETIC_ROLLBACK_DRILL",
        "v1_commit": V1_COMMIT,
        "v1_tool_sha256": V1_TOOL_SHA256,
        "v2_source_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in ("tools/task_learning.py", "tools/validation_contract.py",
                         "tools/tests/drill_task_learning_rollback.py")
        },
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "passed": result.wasSuccessful(),
        "live_adoption": False,
        "internal_release_qualified": False,
    }, indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
