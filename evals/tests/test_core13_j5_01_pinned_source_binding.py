"""J5-01 real local-Git source inspection; zero patch/application execution."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools import repair_evidence_contract as j2
from tools import repair_source_binding as binding

DIFF = (
    "diff --git a/src/example.py b/src/example.py\n"
    "--- a/src/example.py\n"
    "+++ b/src/example.py\n"
    "@@ -1 +1 @@\n"
    "-return 0\n"
    "+return 1\n"
)


class J501SourceBindingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self._git("init", "-q")
        self._git("config", "user.name", "core13-test")
        self._git("config", "user.email", "core13-test@example.invalid")
        (self.root / "src").mkdir()
        (self.root / "src/example.py").write_text("return 0\n", encoding="utf-8")
        self._git("add", "src/example.py")
        self._git("-c", "commit.gpgsign=false", "commit", "-qm", "baseline")
        head = self._git("rev-parse", "HEAD").strip()
        self.task = {
            "contract": j2.TASK_CONTRACT,
            "task_id": "ERT-20261102-ABC12345",
            "base_sha": head,
            "allowed_paths": ["src/example.py"],
            "oracle_sha256": "b" * 64,
            "worker_profile_sha256": "c" * 64,
            "max_patch_bytes": 65536,
        }
        self.patch = {
            "contract": j2.PATCH_CONTRACT,
            "task_id": self.task["task_id"],
            "base_sha": head,
            "diff": DIFF,
            "diff_sha256": hashlib.sha256(DIFF.encode()).hexdigest(),
            "changed_paths": ["src/example.py"],
        }
        self.pins = {
            "task_sha256": binding.canonical_task_sha256(self.task),
            "base_sha": head,
            "oracle_sha256": self.task["oracle_sha256"],
            "worker_profile_sha256": self.task["worker_profile_sha256"],
        }

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=10).stdout.decode()

    def _bind(self, *, task=None, patch=None, pins=None, report=None):
        return binding.bind_pinned_source(
            self.root, task if task is not None else self.task,
            patch if patch is not None else self.patch,
            pins if pins is not None else self.pins,
            reported_result=report,
        )

    def _denied(self, reason, **kwargs):
        with self.assertRaisesRegex(binding.SourceBindingDenied, reason):
            self._bind(**kwargs)

    def test_01_committed_source_identity_is_observed_without_authority(self):
        outcome = self._bind()
        self.assertEqual(outcome["status"],
                         "J5_01_PINNED_SOURCE_BOUND_NOT_INDEPENDENTLY_VERIFIED")
        self.assertEqual(outcome["sources"][0]["git_mode"], "100644")
        self.assertEqual(outcome["sources"][0]["source_sha256"],
                         hashlib.sha256(b"return 0\n").hexdigest())
        self.assertFalse(outcome["independently_verified"])
        self.assertFalse(outcome["acceptance_authorized"])
        self.assertFalse(outcome["executed"])
        self.assertEqual(outcome["decision"], "BLOCK_AI_ACCEPTANCE")

    def test_02_wrong_task_digest_rejected(self):
        pins = dict(self.pins, task_sha256="0" * 64)
        self._denied("TRUSTED_PINS_MISMATCH", pins=pins)

    def test_03_wrong_base_pin_rejected(self):
        self._denied("TRUSTED_PINS_MISMATCH",
                     pins=dict(self.pins, base_sha="d" * 40))

    def test_04_swapped_oracle_rejected(self):
        self._denied("TRUSTED_PINS_MISMATCH",
                     pins=dict(self.pins, oracle_sha256="d" * 64))

    def test_05_swapped_worker_profile_rejected(self):
        self._denied("TRUSTED_PINS_MISMATCH",
                     pins=dict(self.pins, worker_profile_sha256="d" * 64))

    def test_06_head_drift_rejected(self):
        (self.root / "other.txt").write_text("changed", encoding="ascii")
        self._git("add", "other.txt")
        self._git("-c", "commit.gpgsign=false", "commit", "-qm", "second")
        self._denied("SOURCE_BASE_HEAD_MISMATCH")

    def test_07_dirty_tracked_source_rejected(self):
        (self.root / "src/example.py").write_text("return 100\n")
        self._denied("SOURCE_WORKTREE_DIRTY")

    def test_08_untracked_file_rejected(self):
        (self.root / "src/untracked.py").write_text("x=1\n")
        self._denied("SOURCE_WORKTREE_DIRTY")

    def test_09_git_symlink_mode_rejected_without_os_symlink_privilege(self):
        self._git("rm", "-q", "src/example.py")
        (self.root / "src/example.py").unlink(missing_ok=True)
        # Use Git's index mode to preserve portability on Windows.
        self._git("config", "core.symlinks", "false")
        (self.root / "src/example.py").write_text("sibling.py", encoding="ascii")
        self._git("add", "src/example.py")
        self._git("update-index", "--cacheinfo", "120000,"
                  + self._git("hash-object", "src/example.py").strip()
                  + ",src/example.py")
        self._git("-c", "commit.gpgsign=false", "commit", "-qm", "link")
        self._rebind_latest_base()
        self._denied("SOURCE_MODE_OR_TYPE_PROHIBITED")

    def test_10_executable_source_mode_rejected(self):
        self._git("config", "core.filemode", "false")
        self._git("update-index", "--chmod=+x", "src/example.py")
        self._git("-c", "commit.gpgsign=false", "commit", "-qm", "chmod")
        self._rebind_latest_base()
        self._denied("SOURCE_MODE_OR_TYPE_PROHIBITED")

    def _rebind_latest_base(self):
        head = self._git("rev-parse", "HEAD").strip()
        self.task["base_sha"] = head
        self.patch["base_sha"] = head
        self.pins["base_sha"] = head
        self.pins["task_sha256"] = binding.canonical_task_sha256(self.task)

    def test_11_test_path_disallowed_by_existing_j2_contract(self):
        task = copy.deepcopy(self.task)
        task["allowed_paths"] = ["tests/test_example.py"]
        with self.assertRaises(j2.RepairContractDenied):
            self._bind(task=task)

    def test_12_fake_positive_report_has_zero_authority(self):
        report = {
            "contract": j2.RESULT_CONTRACT,
            "task_id": self.task["task_id"],
            "base_sha": self.task["base_sha"],
            "patch_sha256": self.patch["diff_sha256"],
            "oracle_sha256": self.task["oracle_sha256"],
            "worker_profile_sha256": self.task["worker_profile_sha256"],
            "outcome": "pass",
            "checks": [{"id": "functional", "passed": True}],
            "provenance": "caller_reported_unattested",
        }
        outcome = self._bind(report=report)
        self.assertEqual(outcome["reported_claim_status"],
                         "RESULT_CLAIM_BOUND_NOT_INDEPENDENTLY_VERIFIED")
        self.assertFalse(outcome["trusted_verifier_channel_established"])
        self.assertFalse(outcome["acceptance_authorized"])

    def test_13_forged_independent_provenance_rejected_by_j2(self):
        report = {
            "contract": j2.RESULT_CONTRACT,
            "task_id": self.task["task_id"],
            "base_sha": self.task["base_sha"],
            "patch_sha256": self.patch["diff_sha256"],
            "oracle_sha256": self.task["oracle_sha256"],
            "worker_profile_sha256": self.task["worker_profile_sha256"],
            "outcome": "pass",
            "checks": [{"id": "functional", "passed": True}],
            "provenance": "independently_verified",
        }
        with self.assertRaises(j2.RepairContractDenied):
            self._bind(report=report)

    def test_14_patch_byte_swap_rejected_by_j2(self):
        patch = dict(self.patch, diff=DIFF.replace("+return 1", "+return 2"))
        with self.assertRaises(j2.RepairContractDenied):
            self._bind(patch=patch)

    def test_15_extra_claimed_authority_rejected_by_j2(self):
        patch = dict(self.patch, acceptance_authorized=True)
        with self.assertRaises(j2.RepairContractDenied):
            self._bind(patch=patch)

    def test_16_pins_must_not_accept_untrusted_extra_metadata(self):
        self._denied("TRUSTED_PINS_SCHEMA_INVALID",
                     pins=dict(self.pins, accepted=True))


if __name__ == "__main__":
    unittest.main()
