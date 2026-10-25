"""Opt-in, synthetic rollback drill; never accepts a consumer project path.

Run with --v1-tool pointing to the exact Git-exported Stable V1 source.
This is an integration test, not a migration or rollback command.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import task_learning as v2

V1_COMMIT = "69079018606750312344cb3c648952b9ab72d35b"
V1_TOOL_SHA256 = "336037ea356c91d780f61684889b7c92c5d2bde21a8fff2591fec95e559be8f2"
# Fixture metadata only. Actual V2 source identity is emitted in the report.
TRIAL_REF = None  # explicitly bound to the real Git checkout by --target-ref
v1 = None



def require_exact_clean_checkout(target_ref: str) -> str:
    """Tie synthetic data drill to immutable real checkout identity, not a label."""
    if not isinstance(target_ref, str) or not re.fullmatch(r"[a-f0-9]{40}", target_ref):
        raise ValueError("--target-ref must be an exact lowercase 40-hex commit")

    def checked_git(*args: str) -> str:
        try:
            result = subprocess.run(
                ["git", *args], cwd=ROOT, capture_output=True, text=True,
                timeout=15, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValueError("cannot verify the exact Git checkout") from exc
        if result.returncode:
            raise ValueError("cannot verify exact Git checkout: " + result.stderr.strip())
        return result.stdout.strip()

    root = Path(checked_git("rev-parse", "--show-toplevel")).resolve()
    if root != ROOT.resolve():
        raise ValueError("rollback drill must run at the verified checkout root")
    head = checked_git("rev-parse", "HEAD")
    if head != target_ref:
        raise ValueError("rollback drill target does not match checked-out Git HEAD")
    if checked_git("status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("rollback drill source checkout is dirty")
    return head


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


def synthetic_input_digest(baseline: dict[str, bytes],
                           trial: dict[str, bytes]) -> str:
    """Digest exact synthetic INPUT file names and bytes before test mutations.

    The trial ref is intentionally included, so each reviewed source SHA has
    its own fixture identity. This hash is evidence, NOT admission authority.
    """
    manifest = {
        "schema_version": 1,
        "inputs": {
            name: {
                path: {
                    "sha256": hashlib.sha256(blob).hexdigest(),
                    "length_bytes": len(blob),
                }
                for path, blob in sorted(snapshot.items())
            }
            for name, snapshot in (
                ("baseline-v1", baseline),
                ("trial-v2", trial),
            )
        },
    }
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
    fixture_digests: set[str] = set()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="erei-rollback-drill-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        # A generated projection/state uses the current clock unless injected.
        # Freeze it ONLY in this ephemeral synthetic unit-test fixture so that
        # the input bytes have a stable, reviewable SHA256 across all 4 cases.
        fixed_clock = datetime(2026, 10, 1, 14, 0, tzinfo=timezone.utc)
        for module in (v1, v2):
            clock_patch = patch.object(module, "_utc_now", return_value=fixed_clock)
            clock_patch.start()
            self.addCleanup(clock_patch.stop)
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
        self.fixture_sha256 = synthetic_input_digest(
            self.baseline_bytes, files(self.trial)
        )
        self.__class__.fixture_digests.add(self.fixture_sha256)

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

    def test_checkout_ref_preflight_denies_unbound_target(self):
        self.assertEqual(require_exact_clean_checkout(TRIAL_REF), TRIAL_REF)
        for invalid in ("main", "F" * 40, "0" * 39, "f" * 40):
            with self.subTest(ref=invalid), self.assertRaises(ValueError):
                require_exact_clean_checkout(invalid)

    def test_verified_v1_loader_rejects_modified_source(self):
        self.assertRegex(self.fixture_sha256, r"^[a-f0-9]{64}$")
        self.assertEqual(
            self.fixture_sha256,
            synthetic_input_digest(self.baseline_bytes, files(self.trial)),
        )
        self.assertNotEqual(
            self.fixture_sha256,
            synthetic_input_digest(self.baseline_bytes, {
                **files(self.trial), ".erei/framework.json": b"tampered trial pin"
            }),
        )
        with self.assertRaisesRegex(ValueError, "frozen Stable source"):
            load_v1(b"raise RuntimeError('untrusted source must not execute')")


def main():
    global v1, TRIAL_REF
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v1-tool", type=Path, required=True)
    parser.add_argument("--target-ref", required=True, help="Exact 40-hex Git HEAD of isolated drill checkout")
    args = parser.parse_args()
    try:
        TRIAL_REF = require_exact_clean_checkout(args.target_ref)
        v1 = load_v1(args.v1_tool.read_bytes())
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    RollbackDrill.fixture_digests.clear()
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(RollbackDrill)
    )
    fixture_consistent = result.testsRun == 4 and len(RollbackDrill.fixture_digests) == 1
    fixture_sha = next(iter(RollbackDrill.fixture_digests)) if fixture_consistent else None
    print(json.dumps({
        "evidence_kind": "LOCAL_SYNTHETIC_ROLLBACK_DRILL",
        "v1_commit": V1_COMMIT,
        "v1_tool_sha256": V1_TOOL_SHA256,
        "isolated_checkout_ref": TRIAL_REF,
        "checkout_identity_verified": True,
        "synthetic_input_sha256": fixture_sha,
        "fixture_consistent_across_cases": fixture_consistent,
        "fixture_approved_by_independent_reviewer": False,
        "v2_source_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in ("tools/task_learning.py", "tools/validation_contract.py",
                         "tools/tests/drill_task_learning_rollback.py")
        },
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "passed": result.wasSuccessful() and fixture_consistent,
        "live_adoption": False,
        "internal_release_qualified": False,
    }, indent=2))
    return 0 if result.wasSuccessful() and fixture_consistent else 1


if __name__ == "__main__":
    raise SystemExit(main())
