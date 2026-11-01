"""J2 P0 contract checks: local-only, no model, no patch execution."""
from __future__ import annotations

import copy
import hashlib
import unittest

from tools import repair_evidence_contract as c

DIFF = (
    "diff --git a/src/example.py b/src/example.py\n"
    "--- a/src/example.py\n"
    "+++ b/src/example.py\n"
    "@@ -1 +1 @@\n"
    "-return 0\n"
    "+return 1\n"
)


def task():
    return {
        "contract": c.TASK_CONTRACT,
        "task_id": "ERT-20261101-AB12CD34",
        "base_sha": "a" * 40,
        "allowed_paths": ["src/example.py"],
        "oracle_sha256": "b" * 64,
        "worker_profile_sha256": "c" * 64,
        "max_patch_bytes": 65536,
    }


def patch(diff=DIFF, changed_paths=None):
    return {
        "contract": c.PATCH_CONTRACT,
        "task_id": "ERT-20261101-AB12CD34",
        "base_sha": "a" * 40,
        "diff": diff,
        "diff_sha256": hashlib.sha256(diff.encode("utf-8")).hexdigest(),
        "changed_paths": ["src/example.py"] if changed_paths is None else changed_paths,
    }


def result(outcome="pass", checks=None):
    return {
        "contract": c.RESULT_CONTRACT,
        "task_id": "ERT-20261101-AB12CD34",
        "base_sha": "a" * 40,
        "patch_sha256": patch()["diff_sha256"],
        "oracle_sha256": "b" * 64,
        "worker_profile_sha256": "c" * 64,
        "outcome": outcome,
        "checks": ([{"id": "functional", "passed": True}]
                   if checks is None else checks),
        "provenance": "caller_reported_unattested",
    }


class RepairEvidenceContractTests(unittest.TestCase):
    def test_01_valid_envelope_never_authorizes_execution(self):
        report = c.validate_patch(task(), patch())
        self.assertEqual(report["status"], "PATCH_ENVELOPE_VALIDATED_NOT_AUTHORIZED")
        self.assertFalse(report["executed"])
        self.assertFalse(report["acceptance_authorized"])
        self.assertEqual(report["project_writes"], 0)

    def test_02_wrong_base_is_denied(self):
        item = patch()
        item["base_sha"] = "b" * 40
        with self.assertRaisesRegex(c.RepairContractDenied, "BASE_MISMATCH"):
            c.validate_patch(task(), item)

    def test_03_wrong_task_is_denied(self):
        item = patch()
        item["task_id"] = "ERT-20261101-XYZ12345"
        with self.assertRaises(c.RepairContractDenied):
            c.validate_patch(task(), item)

    def test_04_wrong_diff_digest_is_denied(self):
        item = patch()
        item["diff_sha256"] = "d" * 64
        with self.assertRaisesRegex(c.RepairContractDenied, "DIGEST_MISMATCH"):
            c.validate_patch(task(), item)

    def test_05_path_traversal_is_denied(self):
        modified = task()
        modified["allowed_paths"] = ["src/../example.py"]
        with self.assertRaisesRegex(c.RepairContractDenied, "PATH_PROHIBITED"):
            c.validate_patch(modified, patch())

    def test_06_tests_are_not_patchable(self):
        modified = task()
        modified["allowed_paths"] = ["tests/test_example.py"]
        with self.assertRaisesRegex(c.RepairContractDenied, "PATH_PROHIBITED"):
            c.validate_patch(modified, patch())

    def test_07_unapproved_source_path_is_denied(self):
        modified = task()
        modified["allowed_paths"] = ["src/other.py"]
        with self.assertRaisesRegex(c.RepairContractDenied, "OUTSIDE_APPROVED_SCOPE"):
            c.validate_patch(modified, patch())

    def test_08_renamed_file_is_denied(self):
        evil = DIFF.replace("diff --git a/src/example.py b/src/example.py",
                            "diff --git a/src/example.py b/src/other.py")
        with self.assertRaisesRegex(c.RepairContractDenied, "HEADER_INVALID"):
            c.validate_patch(task(), patch(evil))

    def test_09_patch_size_budget_enforced(self):
        modified = task()
        modified["max_patch_bytes"] = 12
        with self.assertRaisesRegex(c.RepairContractDenied, "PATCH_SIZE_LIMIT"):
            c.validate_patch(modified, patch())

    def test_10_forged_claimed_path_denied(self):
        modified = patch(changed_paths=["src/example.py", "src/second.py"])
        with self.assertRaisesRegex(c.RepairContractDenied, "CHANGED_PATHS_MISMATCH"):
            c.validate_patch(task(), modified)

    def test_11_report_must_bind_exact_patch(self):
        modified = result()
        modified["patch_sha256"] = "d" * 64
        with self.assertRaisesRegex(c.RepairContractDenied, "IDENTITY_MISMATCH"):
            c.bind_reported_result(task(), patch(), modified)

    def test_12_report_must_bind_exact_oracle(self):
        modified = result()
        modified["oracle_sha256"] = "d" * 64
        with self.assertRaisesRegex(c.RepairContractDenied, "IDENTITY_MISMATCH"):
            c.bind_reported_result(task(), patch(), modified)

    def test_13_report_must_bind_exact_worker_profile(self):
        modified = result()
        modified["worker_profile_sha256"] = "d" * 64
        with self.assertRaisesRegex(c.RepairContractDenied, "IDENTITY_MISMATCH"):
            c.bind_reported_result(task(), patch(), modified)

    def test_14_untrusted_pass_is_never_accepted(self):
        report = c.bind_reported_result(task(), patch(), result())
        self.assertEqual(report["candidate_decision"], "REVIEW_REQUIRED")
        self.assertEqual(report["status"], "RESULT_CLAIM_BOUND_NOT_INDEPENDENTLY_VERIFIED")
        self.assertFalse(report["trusted_verifier_channel_established"])
        self.assertFalse(report["acceptance_authorized"])
        self.assertFalse(report["independently_verified"])
        self.assertEqual(report["learning_effectiveness"], "NOT_ESTABLISHED")

    def test_15_contradictory_pass_is_denied(self):
        modified = result(checks=[{"id": "functional", "passed": False}])
        with self.assertRaisesRegex(c.RepairContractDenied, "CONTRADICTION"):
            c.bind_reported_result(task(), patch(), modified)

    def test_16_false_attestation_claim_is_denied(self):
        modified = result()
        modified["provenance"] = "independently_verified"
        with self.assertRaisesRegex(c.RepairContractDenied, "NOT_ATTESTED"):
            c.bind_reported_result(task(), patch(), modified)

    def test_17_failed_report_is_not_positive_acceptance(self):
        modified = result("fail", [{"id": "functional", "passed": False}])
        report = c.bind_reported_result(task(), patch(), modified)
        self.assertEqual(report["candidate_decision"], "REJECTED_CLAIM")
        self.assertFalse(report["acceptance_authorized"])

    def test_18_blocked_report_is_not_positive_acceptance(self):
        modified = result("blocked", [])
        report = c.bind_reported_result(task(), patch(), modified)
        self.assertEqual(report["candidate_decision"], "BLOCKED_CLAIM")
        self.assertFalse(report["stable_promotable"])

    def test_19_duplicate_check_denied(self):
        modified = result(checks=[
            {"id": "functional", "passed": True},
            {"id": "functional", "passed": True},
        ])
        with self.assertRaisesRegex(c.RepairContractDenied, "CHECK_INVALID"):
            c.bind_reported_result(task(), patch(), modified)

    def test_20_extra_proposer_authority_field_denied(self):
        modified = patch()
        modified["executed"] = True
        with self.assertRaisesRegex(c.RepairContractDenied, "SCHEMA_INVALID"):
            c.validate_patch(task(), modified)

    def test_21_diff_metadata_cannot_change_mode(self):
        evil = DIFF.replace("--- a/src/example.py", "new file mode 100755\n--- a/src/example.py")
        with self.assertRaises(c.RepairContractDenied):
            c.validate_patch(task(), patch(evil))

    def test_23_nonstring_outcome_fails_closed(self):
        modified = result()
        modified["outcome"] = {"pass": True}
        with self.assertRaisesRegex(c.RepairContractDenied, "OUTCOME_INVALID"):
            c.bind_reported_result(task(), patch(), modified)

    def test_24_untrusted_result_cannot_add_acceptance_field(self):
        modified = result()
        modified["acceptance_authorized"] = True
        with self.assertRaisesRegex(c.RepairContractDenied, "SCHEMA_INVALID"):
            c.bind_reported_result(task(), patch(), modified)

    def test_22_diff_is_not_semantic_correctness(self):
        # Semantically useless code is still a syntactically valid envelope.
        # Such a result MUST NOT be upgraded to accepted code by this tool.
        evil = DIFF.replace("+return 1", "+return 0")
        report = c.validate_patch(task(), patch(evil))
        self.assertFalse(report["independently_verified"])
        self.assertFalse(report["acceptance_authorized"])


if __name__ == "__main__":
    unittest.main()
