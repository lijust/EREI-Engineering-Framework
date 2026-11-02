"""J5-02 local real Git, file-topology and fixed-subprocess regression tests.

Tests never run candidate/model-provided source, do not certify OS sandboxing.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools import repair_evidence_contract as j2
from tools import repair_source_binding as j501
from tools import repair_verifier_boundary as boundary


DIFF = (
    "diff --git a/src/example.py b/src/example.py\n"
    "--- a/src/example.py\n"
    "+++ b/src/example.py\n"
    "@@ -1 +1 @@\n"
    "-return 0\n"
    "+return 1\n"
)


class J502VerifierBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.repo = root / "source"
        self.candidate = root / "candidate"
        self.verifier = root / "verifier"
        for directory in (self.repo / "src", self.candidate, self.verifier):
            directory.mkdir(parents=True)
        (self.repo / "src/example.py").write_text("return 0\n", encoding="utf-8")
        self._git("init", "-q")
        self._git("config", "user.name", "core13-test")
        self._git("config", "user.email", "core13-test@example.invalid")
        self._git("add", "src/example.py")
        self._git("-c", "commit.gpgsign=false", "commit", "-qm", "baseline")
        head = self._git("rev-parse", "HEAD").strip()

        # Deliberately private test bytes, never model-facing or in a report.
        self.oracle_bytes = b'{"sealed_expected_result":"private-test-only"}'
        self.profile_bytes = b'{"worker":"reviewed-fixed-only","version":1}'
        self.oracle = self.verifier / "oracle.private.json"
        self.profile = self.verifier / "worker.private.json"
        self.oracle.write_bytes(self.oracle_bytes)
        self.profile.write_bytes(self.profile_bytes)
        self.oracle.chmod(stat.S_IREAD)
        self.profile.chmod(stat.S_IREAD)
        self.task = {
            "contract": j2.TASK_CONTRACT,
            "task_id": "ERT-20261102-ABC12345",
            "base_sha": head,
            "allowed_paths": ["src/example.py"],
            "oracle_sha256": hashlib.sha256(self.oracle_bytes).hexdigest(),
            "worker_profile_sha256": hashlib.sha256(self.profile_bytes).hexdigest(),
            "max_patch_bytes": 65536,
        }
        self.proposal = {
            "contract": j2.PATCH_CONTRACT,
            "task_id": self.task["task_id"],
            "base_sha": head,
            "diff": DIFF,
            "diff_sha256": hashlib.sha256(DIFF.encode()).hexdigest(),
            "changed_paths": ["src/example.py"],
        }
        self.pins = {
            "task_sha256": j501.canonical_task_sha256(self.task),
            "base_sha": head,
            "oracle_sha256": self.task["oracle_sha256"],
            "worker_profile_sha256": self.task["worker_profile_sha256"],
        }

    def _git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.repo,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                check=True, timeout=10)
        return result.stdout.decode("utf-8")

    def _preflight(self, **overrides):
        args = dict(
            source_root=self.repo, task=self.task, proposal=self.proposal,
            trusted_pins=self.pins, candidate_workspace=self.candidate,
            verifier_workspace=self.verifier, oracle_fixture=self.oracle,
            worker_profile_fixture=self.profile,
            candidate_mounts=[self.candidate],
        )
        args.update(overrides)
        return boundary.preflight(**args)

    def _deny(self, reason, **overrides):
        with self.assertRaisesRegex(boundary.BoundaryDenied, reason):
            self._preflight(**overrides)

    def test_01_real_two_fixed_processes_no_ai_execution(self):
        receipt = self._preflight(run_fixed_process_probes=True)
        self.assertTrue(receipt["trusted_fixed_process_pair_exercised"])
        self.assertTrue(receipt["verifier_only_fixtures_digest_matched"])
        self.assertFalse(receipt["worker_isolation_certified"])
        self.assertFalse(receipt["runtime_candidate_code_executed"])
        self.assertFalse(receipt["acceptance_authorized"])
        self.assertEqual(receipt["decision"], "BLOCK_AI_ACCEPTANCE")

    def test_02_no_subprocess_by_default(self):
        with patch.object(boundary, "_fixed_probe") as fixed:
            receipt = self._preflight()
        fixed.assert_not_called()
        self.assertFalse(receipt["trusted_fixed_process_pair_exercised"])

    def test_03_candidate_projection_omits_private_inputs(self):
        view = self._preflight()["candidate_view"]
        encoded = json.dumps(view, sort_keys=True)
        self.assertEqual(set(view), {
            "contract", "task_id", "base_sha", "allowed_paths", "max_patch_bytes"
        })
        for forbidden in (self.task["oracle_sha256"],
                          self.task["worker_profile_sha256"],
                          self.oracle.name, self.profile.name,
                          str(self.verifier), "private-test-only",
                          "sealed_expected_result", "worker_profile"):
            self.assertNotIn(forbidden, encoded)

    def test_04_same_workspace_denied(self):
        self._deny("WORKSPACE_INTERSECTION",
                   verifier_workspace=self.candidate)

    def test_05_nested_verifier_denied(self):
        nested = self.candidate / "verifier"
        nested.mkdir()
        self._deny("WORKSPACE_INTERSECTION", verifier_workspace=nested)

    def test_06_source_inside_candidate_denied(self):
        self._deny("WORKSPACE_INTERSECTION", candidate_workspace=self.repo.parent)

    def test_07_candidate_mount_verifier_rejected(self):
        self._deny("MOUNT_OUTSIDE_CANDIDATE",
                   candidate_mounts=[self.verifier])

    def test_08_candidate_mount_unrelated_path_rejected(self):
        self._deny("MOUNT_OUTSIDE_CANDIDATE",
                   candidate_mounts=[self.repo])

    def test_09_mount_alias_symlink_rejected(self):
        alias = self.candidate / "alias"
        try:
            alias.symlink_to(self.verifier, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("OS forbids symlinks for ordinary user")
        self._deny("CANDIDATE_SYMLINK_DENIED", candidate_mounts=[alias])

    def test_10_candidate_tree_symlink_to_secret_denied(self):
        alias = self.candidate / "oracle-link"
        try:
            alias.symlink_to(self.oracle)
        except (OSError, NotImplementedError):
            self.skipTest("OS forbids symlinks for ordinary user")
        self._deny("CANDIDATE_SYMLINK_DENIED")

    def test_11_hardlink_alias_to_verifier_fixture_denied(self):
        alias = self.candidate / "oracle-hardlink"
        try:
            os.link(self.oracle, alias)
        except (OSError, NotImplementedError):
            self.skipTest("OS cannot create local hardlink in test setup")
        self._deny("FIXTURE_HARDLINK_IN_CANDIDATE")

    def test_12_wrong_pinned_oracle_digest_denied(self):
        oracle = self.task["oracle_sha256"]
        self.task["oracle_sha256"] = "a" * 64
        self.pins["oracle_sha256"] = "a" * 64
        self.pins["task_sha256"] = j501.canonical_task_sha256(self.task)
        self.assertNotEqual(oracle, self.task["oracle_sha256"])
        self._deny("ORACLE_DIGEST_MISMATCH")

    def test_13_wrong_pinned_profile_digest_denied(self):
        self.task["worker_profile_sha256"] = "a" * 64
        self.pins["worker_profile_sha256"] = "a" * 64
        self.pins["task_sha256"] = j501.canonical_task_sha256(self.task)
        self._deny("WORKER_PROFILE_DIGEST_MISMATCH")

    def test_14_modified_oracle_content_detected(self):
        self.oracle.chmod(stat.S_IWRITE | stat.S_IREAD)
        self.oracle.write_bytes(b"modified private test fixture")
        self.oracle.chmod(stat.S_IREAD)
        self._deny("ORACLE_DIGEST_MISMATCH")

    def test_15_writable_oracle_rejected(self):
        self.oracle.chmod(stat.S_IWRITE | stat.S_IREAD)
        self._deny("FIXTURE_NOT_READONLY")

    def test_16_symlinked_oracle_fixture_rejected(self):
        link = self.verifier / "alias-oracle.json"
        try:
            link.symlink_to(self.oracle)
        except (OSError, NotImplementedError):
            self.skipTest("OS forbids symlinks for ordinary user")
        self._deny("FIXTURE_SYMLINK_DENIED", oracle_fixture=link)

    def test_17_verifier_fixture_outside_verifier_denied(self):
        self._deny("FIXTURE_OUTSIDE_VERIFIER", oracle_fixture=self.repo / "src/example.py")

    def test_18_oracle_profile_must_be_distinct(self):
        self._deny("FIXTURES_MUST_BE_DISTINCT", worker_profile_fixture=self.oracle)

    def test_19_swapped_patch_bytes_rejected_by_j2(self):
        proposal = dict(self.proposal, diff=DIFF.replace("+return 1", "+return 2"))
        with self.assertRaises(j2.RepairContractDenied):
            self._preflight(proposal=proposal)

    def test_20_wrong_trusted_task_identity_rejected_by_j501(self):
        pins = dict(self.pins, task_sha256="f" * 64)
        with self.assertRaises(j501.SourceBindingDenied):
            self._preflight(trusted_pins=pins)

    def test_21_dirty_git_source_rejected_by_j501(self):
        (self.repo / "src/example.py").write_text("return 3\n")
        with self.assertRaises(j501.SourceBindingDenied):
            self._preflight()

    def test_22_empty_oracle_fixture_rejected(self):
        self.oracle.chmod(stat.S_IWRITE | stat.S_IREAD)
        self.oracle.write_bytes(b"")
        self.oracle.chmod(stat.S_IREAD)
        self._deny("FIXTURE_SIZE_INVALID")

    def test_23_fake_same_process_pid_rejected(self):
        fake_candidate = {"role": "candidate", "pid": 9001}
        fake_verifier = {
            "role": "verifier", "pid": 9001,
            "oracle_sha256": self.pins["oracle_sha256"],
            "profile_sha256": self.pins["worker_profile_sha256"],
        }
        with patch.object(boundary, "_fixed_probe",
                          side_effect=[fake_candidate, fake_verifier]):
            self._deny("FIXED_PROCESS_SEPARATION_UNVERIFIED",
                       run_fixed_process_probes=True)

    def test_24_forged_fixed_verifier_digest_rejected(self):
        fake_candidate = {"role": "candidate", "pid": 100}
        fake_verifier = {
            "role": "verifier", "pid": 101,
            "oracle_sha256": "f" * 64,
            "profile_sha256": self.pins["worker_profile_sha256"],
        }
        with patch.object(boundary, "_fixed_probe",
                          side_effect=[fake_candidate, fake_verifier]):
            self._deny("FIXED_PROCESS_SEPARATION_UNVERIFIED",
                       run_fixed_process_probes=True)

    def test_25_nonboolean_probe_flag_rejected(self):
        self._deny("PROBE_FLAG_INVALID", run_fixed_process_probes="true")

    def test_26_too_many_mounts_rejected(self):
        self._deny("CANDIDATE_MOUNTS_INVALID", candidate_mounts=[self.candidate] * 33)

    def test_27_candidate_symlink_file_not_mounted_also_denied(self):
        target = self.candidate / "real.txt"
        target.write_text("safe", encoding="utf-8")
        alias = self.candidate / "link.txt"
        try:
            alias.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("OS forbids symlinks for ordinary user")
        self._deny("CANDIDATE_SYMLINK_DENIED", candidate_mounts=[])

    def test_28_private_fixture_not_in_candidate_mounts(self):
        result = self._preflight(candidate_mounts=[])
        self.assertFalse(result["candidate_mounts_verifier_intersection"])
        self.assertTrue(result["candidate_and_verifier_workspaces_disjoint"])


if __name__ == "__main__":
    unittest.main()
