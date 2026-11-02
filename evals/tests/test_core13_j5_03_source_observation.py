"""J5-03 trusted-source offline real Git + trusted Python observer tests.

Tests are fixed-only and do not execute any proposed diff/model source.
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
from tools import repair_verifier_boundary as j502
from tools import repair_independent_evidence as evidence


DIFF = (
    "diff --git a/src/example.py b/src/example.py\n"
    "--- a/src/example.py\n"
    "+++ b/src/example.py\n"
    "@@ -1 +1 @@\n"
    "-return 0\n"
    "+return 1\n"
)
SOURCE = b"def property_value():\n    return 0\n"


class J503SourceEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        home = Path(self.temp.name)
        self.source = home / "source"
        self.candidate = home / "candidate"
        self.verifier = home / "verifier"
        for folder in (self.source / "src", self.candidate, self.verifier):
            folder.mkdir(parents=True)
        (self.source / "src/example.py").write_bytes(SOURCE)
        self._git("init", "-q")
        self._git("config", "user.name", "core13-test")
        self._git("config", "user.email", "core13-test@example.invalid")
        self._git("add", "src/example.py")
        self._git("-c", "commit.gpgsign=false", "commit", "-qm", "base")
        base_sha = self._git("rev-parse", "HEAD").strip()
        self.oracle = self.verifier / "private-oracle.json"
        self.profile = self.verifier / "private-profile.json"
        self.profile.write_bytes(b'{"profile":"trusted-only"}')
        self.expected = {
            "source_sha256": hashlib.sha256(SOURCE).hexdigest(),
            "source_bytes": len(SOURCE),
            "line_count": 2, "function_count": 1,
            "class_count": 0, "syntax_valid": True,
        }
        self._oracle(self.expected)
        self.profile.chmod(stat.S_IREAD)
        self.task = {
            "contract": j2.TASK_CONTRACT,
            "task_id": "ERT-20261102-ABC12345",
            "base_sha": base_sha,
            "allowed_paths": ["src/example.py"],
            "oracle_sha256": hashlib.sha256(self.oracle.read_bytes()).hexdigest(),
            "worker_profile_sha256": hashlib.sha256(self.profile.read_bytes()).hexdigest(),
            "max_patch_bytes": 65536,
        }
        self.proposal = {
            "contract": j2.PATCH_CONTRACT,
            "task_id": self.task["task_id"],
            "base_sha": base_sha,
            "diff": DIFF,
            "diff_sha256": hashlib.sha256(DIFF.encode()).hexdigest(),
            "changed_paths": ["src/example.py"],
        }
        self.pins = {
            "task_sha256": j501.canonical_task_sha256(self.task),
            "base_sha": base_sha,
            "oracle_sha256": self.task["oracle_sha256"],
            "worker_profile_sha256": self.task["worker_profile_sha256"],
        }

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.source,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=10, check=True).stdout.decode()

    def _oracle(self, expected):
        self.oracle.chmod(stat.S_IWRITE | stat.S_IREAD) if self.oracle.exists() else None
        payload = {"contract": evidence.ORACLE_CONTRACT,
                   "case": evidence.CASE, "expected": expected}
        self.oracle.write_bytes(json.dumps(payload, sort_keys=True,
                           separators=(",", ":")).encode("utf-8"))
        self.oracle.chmod(stat.S_IREAD)

    def _pin_oracle(self):
        self.task["oracle_sha256"] = hashlib.sha256(self.oracle.read_bytes()).hexdigest()
        self.pins["oracle_sha256"] = self.task["oracle_sha256"]
        self.pins["task_sha256"] = j501.canonical_task_sha256(self.task)

    def _run(self, **overrides):
        kw = {
            "source_root": self.source,
            "task": self.task, "proposal": self.proposal,
            "trusted_pins": self.pins,
            "candidate_workspace": self.candidate,
            "verifier_workspace": self.verifier,
            "oracle_fixture": self.oracle,
            "worker_profile_fixture": self.profile,
            "candidate_mounts": [self.candidate],
        }
        kw.update(overrides)
        return evidence.observe_fixed_source(**kw)

    def test_01_real_fixed_python_inspector_records_source(self):
        report = self._run()
        self.assertEqual(report["status"], "J5_03_FIXED_SOURCE_OBSERVATION_MATCH")
        self.assertEqual(report["provenance"],
                         "TRUSTED_FIXED_INSPECTOR_PROCESS_OBSERVED")
        self.assertTrue(report["fixed_oracle_matched"])
        self.assertEqual(len(report["fixed_checks"]), 6)
        self.assertTrue(all(c["passed"] for c in report["fixed_checks"]))
        self.assertEqual(report["source_sha256"], hashlib.sha256(SOURCE).hexdigest())
        self.assertEqual(report["patch_sha256"], self.proposal["diff_sha256"])
        self.assertEqual(report["fixed_process_exit_code"], 0)
        self.assertTrue(report["disposable_verifier_workspace_cleaned"])
        self.assertFalse(report["model_patch_applied"])
        self.assertFalse(report["independently_verified"])
        self.assertFalse(report["trusted_verifier_channel_established"])
        self.assertFalse(report["acceptance_authorized"])
        self.assertEqual(report["decision"], "BLOCK_AI_ACCEPTANCE")
        self.assertFalse(list(self.verifier.glob("j503-trusted-*")))

    def test_02_private_oracle_and_expected_absent_from_receipt(self):
        report = json.dumps(self._run(), sort_keys=True)
        for value in ('"expected"', "private-oracle.json",
                      str(self.verifier), "property_value", "trusted-only"):
            self.assertNotIn(value, report)

    def test_03_wrong_expectation_reports_mismatch_not_approval(self):
        wrong = dict(self.expected, function_count=2)
        self._oracle(wrong)
        self._pin_oracle()
        report = self._run()
        self.assertEqual(report["status"], "J5_03_FIXED_SOURCE_OBSERVATION_MISMATCH")
        self.assertFalse(report["fixed_oracle_matched"])
        self.assertFalse(report["acceptance_authorized"])
        self.assertFalse(report["independently_verified"])

    def test_04_fake_candidate_pass_does_not_change_observation(self):
        report = {
            "contract": j2.RESULT_CONTRACT,
            "task_id": self.task["task_id"],
            "base_sha": self.task["base_sha"],
            "patch_sha256": self.proposal["diff_sha256"],
            "oracle_sha256": self.task["oracle_sha256"],
            "worker_profile_sha256": self.task["worker_profile_sha256"],
            "outcome": "pass", "checks": [{"id": "functional", "passed": True}],
            "provenance": "caller_reported_unattested",
        }
        outcome = self._run(reported_result=report)
        self.assertEqual(outcome["reported_claim_status"],
                         "RESULT_CLAIM_BOUND_NOT_INDEPENDENTLY_VERIFIED")
        self.assertTrue(outcome["fixed_oracle_matched"])
        self.assertFalse(outcome["acceptance_authorized"])

    def test_05_fake_candidate_pass_cannot_turn_failure_into_match(self):
        wrong = dict(self.expected, function_count=20)
        self._oracle(wrong)
        self._pin_oracle()
        claim = {
            "contract": j2.RESULT_CONTRACT,
            "task_id": self.task["task_id"], "base_sha": self.task["base_sha"],
            "patch_sha256": self.proposal["diff_sha256"],
            "oracle_sha256": self.task["oracle_sha256"],
            "worker_profile_sha256": self.task["worker_profile_sha256"],
            "outcome": "pass", "checks": [{"id": "functional", "passed": True}],
            "provenance": "caller_reported_unattested",
        }
        observed = self._run(reported_result=claim)
        self.assertFalse(observed["fixed_oracle_matched"])

    def test_06_forged_independent_provenance_is_rejected_by_j2(self):
        claim = {
            "contract": j2.RESULT_CONTRACT,
            "task_id": self.task["task_id"], "base_sha": self.task["base_sha"],
            "patch_sha256": self.proposal["diff_sha256"],
            "oracle_sha256": self.task["oracle_sha256"],
            "worker_profile_sha256": self.task["worker_profile_sha256"],
            "outcome": "pass", "checks": [{"id": "functional", "passed": True}],
            "provenance": "independently_verified",
        }
        with self.assertRaises(j2.RepairContractDenied):
            self._run(reported_result=claim)

    def test_07_patch_changed_without_digest_rejected_by_j2(self):
        modified = dict(self.proposal, diff=DIFF.replace("+return 1", "+return 9"))
        with self.assertRaises(j2.RepairContractDenied):
            self._run(proposal=modified)

    def test_08_wrong_base_commit_rejected_by_j501(self):
        (self.source / "src/example.py").write_bytes(SOURCE + b"\n")
        self._git("add", "src/example.py")
        self._git("-c", "commit.gpgsign=false", "commit", "-qm", "new")
        with self.assertRaises(j501.SourceBindingDenied):
            self._run()

    def test_09_dirty_source_rejected(self):
        (self.source / "src/example.py").write_text("def x(): pass\n")
        with self.assertRaises(j501.SourceBindingDenied):
            self._run()

    def test_10_oracle_content_mutation_rejected(self):
        self._oracle(dict(self.expected, line_count=9))
        with self.assertRaises(j502.BoundaryDenied):
            self._run()

    def test_11_worker_profile_mutation_rejected(self):
        self.profile.chmod(stat.S_IWRITE | stat.S_IREAD)
        self.profile.write_bytes(b"not pinned")
        self.profile.chmod(stat.S_IREAD)
        with self.assertRaises(j502.BoundaryDenied):
            self._run()

    def test_12_different_source_declared_rejected(self):
        task = dict(self.task, allowed_paths=["src/nonexistent.py"])
        pins = dict(self.pins, task_sha256=j501.canonical_task_sha256(task))
        # J2 is authoritative and rejects a diff targeting a path
        # outside the newly declared task scope before Git lookup.
        with self.assertRaises(j2.RepairContractDenied):
            self._run(task=task, trusted_pins=pins)

    def test_13_multiple_allowed_sources_not_supported_by_fixed_probe(self):
        (self.source / "src/other.py").write_text("pass\n")
        self._git("add", "src/other.py")
        self._git("-c", "commit.gpgsign=false", "commit", "-qm", "two")
        head = self._git("rev-parse", "HEAD").strip()
        self.task["base_sha"] = head
        self.task["allowed_paths"] = ["src/example.py", "src/other.py"]
        self.proposal["base_sha"] = head
        self.pins["base_sha"] = head
        self.pins["task_sha256"] = j501.canonical_task_sha256(self.task)
        with self.assertRaisesRegex(evidence.EvidenceDenied,
                                    "FIXED_CASE_REQUIRES_EXACTLY_ONE_SOURCE"):
            self._run()

    def test_14_untrusted_but_hash_correct_wrong_patch_not_executed(self):
        # J2 permits a diff with no semantic improvement as a valid envelope.
        diff = DIFF.replace("+return 1", "+return 0")
        p = dict(self.proposal, diff=diff,
                 diff_sha256=hashlib.sha256(diff.encode()).hexdigest())
        receipt = self._run(proposal=p)
        self.assertTrue(receipt["fixed_oracle_matched"])
        self.assertFalse(receipt["model_patch_applied"])
        self.assertFalse(receipt["acceptance_authorized"])

    def test_15_real_fixed_inspector_exit_failure_fails_closed(self):
        # Literal test-only script, never candidate patch content.
        with patch.object(evidence, "_INSPECTOR", "import sys;sys.exit(7)"):
            with self.assertRaisesRegex(evidence.EvidenceDenied,
                                        "FIXED_INSPECTOR_RUNTIME_FAILED"):
                self._run()
        self.assertFalse(list(self.verifier.glob("j503-trusted-*")))

    def test_16_real_fixed_inspector_invalid_trace_fails_closed(self):
        with patch.object(evidence, "_INSPECTOR", "print('not json')"):
            with self.assertRaisesRegex(evidence.EvidenceDenied,
                                        "EVIDENCE_JSON_INVALID"):
                self._run()
        self.assertFalse(list(self.verifier.glob("j503-trusted-*")))

    def test_17_probe_source_hash_spoof_rejected(self):
        fake = json.dumps({
            "contract": evidence.TRACE_CONTRACT,
            **dict(self.expected, source_sha256="f" * 64),
        })
        with patch.object(evidence, "_INSPECTOR", "print(" + repr(fake) + ")"):
            with self.assertRaisesRegex(evidence.EvidenceDenied,
                                        "FIXED_INSPECTOR_SOURCE_IDENTITY_MISMATCH"):
                self._run()

    def test_18_bad_oracle_schema_rejected(self):
        self.oracle.chmod(stat.S_IWRITE | stat.S_IREAD)
        self.oracle.write_bytes(b'{"contract":"wrong","case":"baseline_python_ast","expected":{}}')
        self.oracle.chmod(stat.S_IREAD)
        self._pin_oracle()
        with self.assertRaisesRegex(evidence.EvidenceDenied,
                                    "EVIDENCE_SCHEMA_INVALID"):
            self._run()

    def test_19_large_oracle_json_denied_even_if_pinned(self):
        self.oracle.chmod(stat.S_IWRITE | stat.S_IREAD)
        self.oracle.write_bytes(b"x" * 5000)
        self.oracle.chmod(stat.S_IREAD)
        self._pin_oracle()
        with self.assertRaisesRegex(evidence.EvidenceDenied,
                                    "ORACLE_CHANGED_OR_OVERSIZE"):
            self._run()

    def test_20_test_does_not_run_candidate_source_or_patch(self):
        report = self._run()
        self.assertFalse(report["candidate_code_executed"])
        self.assertFalse(report["untrusted_code_execution_authorized"])
        self.assertFalse(report["worker_isolation_certified"])


if __name__ == "__main__":
    unittest.main()
