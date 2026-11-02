"""J5-03B real, fixed-reviewed RED/GREEN behavior control; never model code."""
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
from tools import repair_verifier_boundary as j502
from tools import repair_fixed_behavior_witness as behavior

DIFF = (
    "diff --git a/src/example.py b/src/example.py\n"
    "--- a/src/example.py\n"
    "+++ b/src/example.py\n"
    "@@ -1 +1 @@\n"
    "-return 0\n"
    "+return 1\n"
)


class J503BFixedBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        home = Path(self.temp.name)
        self.source = home / "source"
        self.candidate = home / "candidate"
        self.verifier = home / "verifier"
        for folder in (self.source / "src", self.candidate, self.verifier):
            folder.mkdir(parents=True)
        (self.source / "src/example.py").write_bytes(b"return 0\n")
        self._git("init", "-q")
        self._git("config", "user.name", "core13-test")
        self._git("config", "user.email", "core13-test@example.invalid")
        self._git("add", "src/example.py")
        self._git("-c", "commit.gpgsign=false", "commit", "-qm", "base")
        base = self._git("rev-parse", "HEAD").strip()
        self.oracle = self.verifier / "behavior-oracle.json"
        self.profile = self.verifier / "worker-profile.json"
        self.profile.write_bytes(b'{"approved":"fixed-only"}')
        self._oracle([1200, 850, 700, 0])
        self.profile.chmod(stat.S_IREAD)
        self.task = {
            "contract": j2.TASK_CONTRACT,
            "task_id": "ERT-20261102-ABC12345",
            "base_sha": base, "allowed_paths": ["src/example.py"],
            "oracle_sha256": hashlib.sha256(self.oracle.read_bytes()).hexdigest(),
            "worker_profile_sha256": hashlib.sha256(self.profile.read_bytes()).hexdigest(),
            "max_patch_bytes": 65536,
        }
        self.proposal = {
            "contract": j2.PATCH_CONTRACT,
            "task_id": self.task["task_id"],
            "base_sha": base,
            "diff": DIFF, "diff_sha256": hashlib.sha256(DIFF.encode()).hexdigest(),
            "changed_paths": ["src/example.py"],
        }
        self.pins = {
            "task_sha256": j501.canonical_task_sha256(self.task),
            "base_sha": base,
            "oracle_sha256": self.task["oracle_sha256"],
            "worker_profile_sha256": self.task["worker_profile_sha256"],
        }

    def _git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.source, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=True, timeout=10,
        ).stdout.decode("utf-8")

    def _oracle(self, expected, *, case=behavior.CASE, contract=behavior.ORACLE_CONTRACT):
        if self.oracle.exists():
            self.oracle.chmod(stat.S_IWRITE | stat.S_IREAD)
        self.oracle.write_bytes(json.dumps(
            {"contract": contract, "case": case, "expected": expected},
            sort_keys=True, separators=(",", ":"),
        ).encode("utf-8"))
        self.oracle.chmod(stat.S_IREAD)

    def _pin_oracle(self):
        self.task["oracle_sha256"] = hashlib.sha256(self.oracle.read_bytes()).hexdigest()
        self.pins["oracle_sha256"] = self.task["oracle_sha256"]
        self.pins["task_sha256"] = j501.canonical_task_sha256(self.task)

    def _run(self, **overrides):
        args = {
            "source_root": self.source, "task": self.task,
            "proposal": self.proposal, "trusted_pins": self.pins,
            "candidate_workspace": self.candidate,
            "verifier_workspace": self.verifier, "oracle_fixture": self.oracle,
            "worker_profile_fixture": self.profile,
            "candidate_mounts": [self.candidate],
        }
        args.update(overrides)
        return behavior.observe_fixed_red_green(**args)

    def _fake_pass(self, *, provenance="caller_reported_unattested"):
        return {
            "contract": j2.RESULT_CONTRACT,
            "task_id": self.task["task_id"], "base_sha": self.task["base_sha"],
            "patch_sha256": self.proposal["diff_sha256"],
            "oracle_sha256": self.task["oracle_sha256"],
            "worker_profile_sha256": self.task["worker_profile_sha256"],
            "outcome": "pass", "checks": [{"id": "functional", "passed": True}],
            "provenance": provenance,
        }

    def test_01_actual_two_fixed_processes_red_fails_green_matches(self):
        report = self._run()
        self.assertEqual(report["status"],
                         "J5_03B_TRUSTED_FIXED_BEHAVIOR_RED_GREEN_OBSERVED")
        self.assertGreater(report["fixed_red_mismatches"], 0)
        self.assertEqual(report["fixed_green_mismatches"], 0)
        self.assertEqual(report["fixed_process_count"], 2)
        self.assertTrue(report["fixed_oracle_control_demonstrated"])
        self.assertTrue(report["disposable_verifier_workspace_cleaned"])
        self.assertFalse(report["acceptance_authorized"])
        self.assertFalse(report["independently_verified"])
        self.assertFalse(report["worker_isolation_certified"])
        self.assertFalse(report["untrusted_code_execution_authorized"])
        self.assertEqual(report["decision"], "BLOCK_AI_ACCEPTANCE")
        self.assertFalse(list(self.verifier.glob("j503b-behavior-*")))

    def test_02_no_sealed_expected_outputs_or_paths_in_receipt(self):
        receipt = json.dumps(self._run(), sort_keys=True)
        for secret in ('"expected"', "behavior-oracle.json",
                       "worker-profile.json", str(self.verifier),
                       '"values"', '"green"', "1,200 SAR"):
            self.assertNotIn(secret, receipt)

    def test_03_fake_pass_cannot_authorize(self):
        report = self._run(reported_result=self._fake_pass())
        self.assertEqual(report["reported_claim_status"],
                         "RESULT_CLAIM_BOUND_NOT_INDEPENDENTLY_VERIFIED")
        self.assertFalse(report["acceptance_authorized"])

    def test_04_forged_independent_provenance_rejected(self):
        with self.assertRaises(j2.RepairContractDenied):
            self._run(reported_result=self._fake_pass(
                provenance="independently_verified"))

    def test_05_wrong_but_pinned_oracle_fails(self):
        self._oracle([1200, 850, 700, 1])
        self._pin_oracle()
        with self.assertRaisesRegex(
            behavior.BehaviorDenied, "REVIEWED_RED_GREEN_ORACLE_CONTROL_FAILED"
        ):
            self._run()

    def test_06_intentionally_faulty_red_fixed_code_rejected_when_fixed(self):
        program = behavior._REVIEWED_FIXED_WORKER.replace(
            "mode=='green'", "mode in ('green','red')"
        )
        with patch.object(behavior, "_REVIEWED_FIXED_WORKER", program):
            with self.assertRaisesRegex(
                behavior.BehaviorDenied, "REVIEWED_RED_GREEN_ORACLE_CONTROL_FAILED"
            ):
                self._run()

    def test_07_green_regression_fails_closed(self):
        program = behavior._REVIEWED_FIXED_WORKER.replace(
            "mode=='green'", "mode=='never'"
        )
        with patch.object(behavior, "_REVIEWED_FIXED_WORKER", program):
            with self.assertRaisesRegex(
                behavior.BehaviorDenied, "REVIEWED_RED_GREEN_ORACLE_CONTROL_FAILED"
            ):
                self._run()

    def test_08_actual_fixed_child_nonzero_exit_denied(self):
        with patch.object(behavior, "_REVIEWED_FIXED_WORKER",
                          "import sys;sys.exit(7)"):
            with self.assertRaisesRegex(
                behavior.BehaviorDenied, "REVIEWED_BEHAVIOR_PROCESS_FAILED"
            ):
                self._run()
        self.assertFalse(list(self.verifier.glob("j503b-behavior-*")))

    def test_09_actual_fixed_child_invalid_json_denied(self):
        with patch.object(behavior, "_REVIEWED_FIXED_WORKER",
                          "print('not json')"):
            with self.assertRaisesRegex(
                behavior.BehaviorDenied, "REVIEWED_BEHAVIOR_PROCESS_UNAVAILABLE"
            ):
                self._run()

    def test_10_dirty_source_rejected_by_j501(self):
        (self.source / "src/example.py").write_bytes(b"changed\n")
        with self.assertRaises(j501.SourceBindingDenied):
            self._run()

    def test_11_new_git_head_rejected_by_j501(self):
        (self.source / "src/example.py").write_bytes(b"new\n")
        self._git("add", "src/example.py")
        self._git("-c", "commit.gpgsign=false", "commit", "-qm", "drift")
        with self.assertRaises(j501.SourceBindingDenied):
            self._run()

    def test_12_swapped_diff_raw_bytes_rejected_by_j2(self):
        changed = dict(self.proposal, diff=DIFF.replace("+return 1", "+return 7"))
        with self.assertRaises(j2.RepairContractDenied):
            self._run(proposal=changed)

    def test_13_oracle_mutation_without_updated_pin_denied(self):
        self._oracle([1200, 850, 700, 77])
        with self.assertRaises(j502.BoundaryDenied):
            self._run()

    def test_14_worker_profile_mutation_denied(self):
        self.profile.chmod(stat.S_IWRITE | stat.S_IREAD)
        self.profile.write_bytes(b"modified")
        self.profile.chmod(stat.S_IREAD)
        with self.assertRaises(j502.BoundaryDenied):
            self._run()

    def test_15_bad_oracle_case_denied(self):
        self._oracle([1200, 850, 700, 0], case="unreviewed")
        self._pin_oracle()
        with self.assertRaisesRegex(
            behavior.BehaviorDenied, "PRIVATE_BEHAVIOR_ORACLE_SCHEMA_INVALID"
        ):
            self._run()

    def test_16_wrong_oracle_type_denied(self):
        self._oracle([1200, "850", 700, 0])
        self._pin_oracle()
        with self.assertRaisesRegex(
            behavior.BehaviorDenied, "PRIVATE_BEHAVIOR_ORACLE_SCHEMA_INVALID"
        ):
            self._run()

    def test_17_oversized_oracle_even_when_pinned_denied(self):
        self.oracle.chmod(stat.S_IWRITE | stat.S_IREAD)
        self.oracle.write_bytes(b"x" * 4097)
        self.oracle.chmod(stat.S_IREAD)
        self._pin_oracle()
        with self.assertRaisesRegex(
            behavior.BehaviorDenied, "PRIVATE_BEHAVIOR_ORACLE_CHANGED"
        ):
            self._run()

    def test_18_candidate_mount_escape_denied(self):
        with self.assertRaisesRegex(
            j502.BoundaryDenied, "MOUNT_OUTSIDE_CANDIDATE"
        ):
            self._run(candidate_mounts=[self.verifier])

    def test_19_bad_worker_mode_denied_before_subprocess(self):
        with self.assertRaisesRegex(
            behavior.BehaviorDenied, "UNREVIEWED_BEHAVIOR_MODE"
        ):
            behavior._run_fixed("candidate_python", self.verifier)

    def test_20_model_code_not_applied_or_run(self):
        report = self._run()
        self.assertFalse(report["model_patch_applied"])
        self.assertFalse(report["candidate_code_executed"])
        self.assertFalse(report["independent_model_patch_oracle_established"])
        self.assertEqual(report["model_calls"], 0)

    def test_21_external_oracle_symlink_alias_rejected(self):
        alias = self.candidate.parent / "oracle-link"
        try:
            alias.symlink_to(self.oracle)
        except (OSError, NotImplementedError):
            self.skipTest("OS forbids symlink")
        with self.assertRaises(j502.BoundaryDenied):
            self._run(oracle_fixture=alias)


if __name__ == "__main__":
    unittest.main()
