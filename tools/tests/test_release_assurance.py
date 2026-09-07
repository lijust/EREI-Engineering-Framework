import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import exact_target_evidence, release_assurance


class ReleaseAssuranceTests(unittest.TestCase):
    TARGET_TREE = "e" * 40

    def base(self, **overrides):
        value = {
            "schema_version": 1,
            "assurance_contract_version": 2,
            "release_id": "vnext",
            "baseline": "vnext",
            "status": "candidate",
            "framework_ref": "a" * 40,
            "released_at": "2026-09-07T02:30:00Z",
            "capabilities": {"hardening": "candidate"},
            "notes": "Candidate assurance release.",
            "stable_blockers": ["prospective cycle pending"],
        }
        value.update(overrides)
        return value

    def stable(self, **overrides):
        value = self.base(
            status="stable",
            approval_ref="b" * 40,
            security_review_ref="c" * 40,
            minimum_eval_assurance_level="exact_target_runtime",
            behavioral_eval_evidence="evals/evidence.json",
            prospective_learning_cycle={
                "capture_ref": "capture",
                "review_ref": "review",
                "feedback_ref": "feedback",
                "improvement_ref": "improvement",
                "adoption_ref": "adoption",
                "measured_outcome_ref": "outcome",
            },
        )
        value.pop("stable_blockers", None)
        value.update(overrides)
        return value

    def enforcement(self, *, equivalent=False):
        return {
            "schema_version": 1,
            "repository": "lijust/EREI-Engineering-Framework",
            "main_branch": "main",
            "status": "enforced" if equivalent else "candidate_control",
            "server_enforcement": {
                "branch_protection_enabled": False,
                "required_status_checks_enforced": False,
                "source": "test",
            },
            "fallback": {
                "mode": "controlled_release_v2",
                "required_workflow": "Framework Assurance Gate",
                "release_branch_prefix": "release/",
                "exact_candidate_sha_required": True,
                "release_assurance_contract_version": 2,
                "architecture_approval_required": True,
                "security_approval_required": True,
                "exact_target_runtime_evidence_required": True,
                "complete_prospective_cycle_required": True,
                "equivalent_enforcement_verified": equivalent,
                "stable_promotion_policy": "blocked_until_server_or_equivalent_enforcement",
            },
            "evidence": ["test-evidence"],
            "limitations": ["test limitation"],
        }

    def exact_evidence(self):
        return {
            "schema_version": 2,
            "framework_revision": "a" * 40,
            "produced_at": "2026-09-07T12:00:00Z",
            "executions": [{
                "suite_id": "suite",
                "case_id": "case",
                "status": "pass",
                "adapter_id": "external-adapter",
                "adapter_revision": "d" * 40,
                "assurance_level": "exact_target_runtime",
                "independent_runtime": True,
                "evidence_ref": "exact-target-run:evals/exact-target-runs/run.json#suite/case",
            }],
        }

    def target_manifest(self):
        return {
            "schema_version": 1,
            "target_id": "vnext-rc9",
            "status": "frozen_candidate",
            "framework_ref": "a" * 40,
            "target_tree": self.TARGET_TREE,
            "selected_at": "2026-09-07T12:00:00Z",
            "source_branch": "main",
            "assurance": {
                "workflow": "Framework Assurance Gate",
                "run_id": 1,
                "event": "push",
                "conclusion": "success",
            },
            "stable_baseline": {
                "baseline": "task-learning-review-v1",
                "framework_ref": "f" * 40,
            },
            "promotion_authorized": False,
        }

    def approval(self, approval_type: str):
        suffix = "A1B2C3D4" if approval_type == "architecture" else "E5F6A7B8"
        role = "system-architect" if approval_type == "architecture" else "security-engineer"
        return {
            "schema_version": 1,
            "approval_id": f"EAPP-20260907T123000Z-{suffix}",
            "approval_type": approval_type,
            "target_framework_ref": "a" * 40,
            "target_tree": self.TARGET_TREE,
            "decision": "approved",
            "recorded_at": "2026-09-07T12:30:00Z",
            "reviewer": {"kind": "framework_role", "id": role},
            "evidence": ["test-evidence", "release-target:vnext-rc9"],
            "rationale": f"{approval_type} approval for immutable test target.",
        }

    class FakeRunner:
        ASSURANCE_LEVELS = {"harness_smoke": 0, "reference_contract": 1, "managed_runtime": 2, "exact_target_runtime": 3}

        @staticmethod
        def validate_execution_evidence(data):
            return data

        @staticmethod
        def _expected_cases(paths, minimum_level=None):
            if minimum_level not in {None, "exact_target_runtime"}:
                raise AssertionError(f"unexpected minimum_level={minimum_level}")
            return {("suite", "case")}

        @staticmethod
        def execution_assurance_level(execution, schema_version):
            return execution["assurance_level"]

    def write_stable_root(self, root: Path):
        (root / "security").mkdir(parents=True)
        (root / "evals").mkdir(parents=True)
        (root / "releases" / "approvals").mkdir(parents=True)
        (root / "security" / "ASSURANCE_ENFORCEMENT.json").write_text(
            json.dumps(self.enforcement(equivalent=True)), encoding="utf-8"
        )
        (root / "evals" / "evidence.json").write_text(json.dumps(self.exact_evidence()), encoding="utf-8")
        (root / "releases" / "VNEXT_TARGET.json").write_text(json.dumps(self.target_manifest()), encoding="utf-8")
        (root / "releases" / "approvals" / "architecture.json").write_text(
            json.dumps(self.approval("architecture")), encoding="utf-8"
        )
        (root / "releases" / "approvals" / "security.json").write_text(
            json.dumps(self.approval("security")), encoding="utf-8"
        )

    def test_candidate_requires_explicit_stable_blockers(self):
        value = self.base()
        del value["stable_blockers"]
        with self.assertRaisesRegex(release_assurance.ReleaseError, "stable_blockers"):
            release_assurance.validate_manifest(value)

    def test_candidate_with_blockers_is_valid(self):
        result = release_assurance.validate_manifest(self.base())
        self.assertEqual(result["status"], "candidate")
        self.assertFalse(result["next_stable_gate_applied"])
        self.assertIsNone(result["stable_enforcement_satisfied"])
        self.assertEqual(result["exact_target_bindings_validated"], 0)
        self.assertEqual(result["approval_records_validated"], 0)

    def test_v2_stable_requires_exact_target_runtime_level(self):
        value = self.stable(minimum_eval_assurance_level="reference_contract")
        with self.assertRaisesRegex(release_assurance.ReleaseError, "exact_target_runtime"):
            release_assurance.validate_manifest(value)

    def test_v2_stable_fails_before_eval_when_enforcement_is_not_satisfied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "security").mkdir()
            (root / "security" / "ASSURANCE_ENFORCEMENT.json").write_text(
                json.dumps(self.enforcement(equivalent=False)), encoding="utf-8"
            )
            with self.assertRaisesRegex(release_assurance.ReleaseError, "server branch/status-check enforcement"):
                release_assurance.validate_manifest(self.stable(), repo_root=root)

    def test_v2_stable_reaches_eval_gate_when_equivalent_enforcement_is_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "security").mkdir()
            (root / "security" / "ASSURANCE_ENFORCEMENT.json").write_text(
                json.dumps(self.enforcement(equivalent=True)), encoding="utf-8"
            )
            with self.assertRaises((FileNotFoundError, release_assurance.ReleaseError)):
                release_assurance.validate_manifest(self.stable(), repo_root=root)

    def test_v2_stable_requires_bound_exact_target_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_stable_root(root)
            with mock.patch.object(release_assurance, "_load_runner", return_value=self.FakeRunner), \
                 mock.patch.object(
                     release_assurance.exact_target_evidence,
                     "validate_binding",
                     side_effect=exact_target_evidence.ExactTargetEvidenceError("bad binding"),
                 ):
                with self.assertRaisesRegex(release_assurance.ReleaseError, "exact-target evidence binding failed"):
                    release_assurance.validate_manifest(self.stable(), repo_root=root)

    def test_v2_stable_requires_structured_approved_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_stable_root(root)
            security = self.approval("security")
            security["decision"] = "rejected"
            (root / "releases" / "approvals" / "security.json").write_text(json.dumps(security), encoding="utf-8")
            with mock.patch.object(release_assurance, "_load_runner", return_value=self.FakeRunner):
                with self.assertRaisesRegex(release_assurance.ReleaseError, "security release approval"):
                    release_assurance.validate_manifest(self.stable(), repo_root=root)

    def test_v2_stable_approval_target_tree_must_match_frozen_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_stable_root(root)
            architecture = self.approval("architecture")
            architecture["target_tree"] = "9" * 40
            (root / "releases" / "approvals" / "architecture.json").write_text(json.dumps(architecture), encoding="utf-8")
            with mock.patch.object(release_assurance, "_load_runner", return_value=self.FakeRunner):
                with self.assertRaisesRegex(release_assurance.ReleaseError, "architecture release approval"):
                    release_assurance.validate_manifest(self.stable(), repo_root=root)

    def test_v2_stable_counts_validated_exact_target_bindings_and_approvals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_stable_root(root)
            with mock.patch.object(release_assurance, "_load_runner", return_value=self.FakeRunner), \
                 mock.patch.object(release_assurance.exact_target_evidence, "validate_binding", return_value={}):
                result = release_assurance.validate_manifest(self.stable(), repo_root=root)
            self.assertEqual(result["exact_target_bindings_validated"], 1)
            self.assertEqual(result["approval_records_validated"], 2)


if __name__ == "__main__":
    unittest.main()
