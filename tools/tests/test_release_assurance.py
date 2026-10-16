import json
import tempfile
from contextlib import contextmanager
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
            baseline="task-learning-review-v2",
            capabilities={
                "prospective_task_learning": "v2",
                "capability_activation_governance": "v1",
            },
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
            "schema_version": 2,
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
                "equivalence_target_ref": "a" * 40 if equivalent else None,
                "review_provenance": ({
                    "provider": "github_codex_review",
                    "reviewer_login": "chatgpt-codex-connector[bot]",
                    "review_type": "security_review",
                    "purpose": "enforcement_equivalence",
                } if equivalent else None),
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
            "schema_version": 2,
            "approval_id": f"EAPP-20260907T123000Z-{suffix}",
            "approval_type": approval_type,
            "target_framework_ref": "a" * 40,
            "target_tree": self.TARGET_TREE,
            "decision": "approved",
            "recorded_at": "2026-09-07T12:30:00Z",
            "reviewer": {"kind": "framework_role", "id": role},
            "review_provenance": {
                "provider": "github_codex_review",
                "reviewer_login": "chatgpt-codex-connector[bot]",
                "review_type": "code_review" if approval_type == "architecture" else "security_review",
                "purpose": f"{approval_type}_approval",
            },
            "evidence": ["test-evidence", "release-target:vnext-rc9"],
            "rationale": f"{approval_type} approval for immutable test target.",
        }

    class FakeRunner:
        ASSURANCE_LEVELS = {"harness_smoke": 0, "reference_contract": 1, "managed_runtime": 2, "exact_target_runtime": 3}

        @staticmethod
        def validate_execution_evidence(data):
            return data

        @staticmethod
        def _expected_cases(paths):
            return {("suite", "case")}

        @staticmethod
        def execution_assurance_level(execution, schema_version):
            return execution["assurance_level"]

    def frozen_scope(self):
        return {
            "schema_version": 1,
            "scope_id": "task-learning-v2-core",
            "status": "approved",
            "release_family": "task-learning-v2-core",
            "target_baseline": "task-learning-review-v2",
            "capabilities": [{"name": "prospective_task_learning", "version": "v2"}],
            "release_control_dependencies": [{"name": "capability_activation_governance", "version": "v1"}],
            "required_eval_suites": [{
                "path": "evals/cases/scope.eval.json",
                "suite_id": "suite",
                "covers": ["prospective_task_learning", "capability_activation_governance"],
            }],
            "excluded_candidate_capabilities": [],
            "post_promotion_gates": ["project_framework_pin_upgrade"],
            "rationale": "Test frozen release scope for V2 Stable assurance validation.",
        }

    def frozen_scope_summary(self):
        return {
            "status": "VALID",
            "scope_id": "task-learning-v2-core",
            "release_family": "task-learning-v2-core",
            "target_baseline": "task-learning-review-v2",
            "capabilities": [{"name": "prospective_task_learning", "version": "v2"}],
            "release_control_dependencies": [{"name": "capability_activation_governance", "version": "v1"}],
            "excluded_candidate_capabilities": [],
            "required_eval_suite_count": 1,
            "required_eval_case_count": 1,
            "covered_capabilities": ["capability_activation_governance", "prospective_task_learning"],
            "required_eval_paths": ["evals/cases/scope.eval.json"],
            "required_eval_cases": ["suite/case"],
            "required_eval_case_pairs": [{"suite_id": "suite", "case_id": "case"}],
        }

    def scope_patch(self):
        return mock.patch.object(
            release_assurance.release_scope,
            "load_target_bound_scope",
            return_value=(self.frozen_scope(), self.frozen_scope_summary()),
        )

    @contextmanager
    def stable_patches(self):
        with self.scope_patch(), \
             mock.patch.object(
                 release_assurance.assurance_enforcement,
                 "verify_authenticated_equivalence",
                 return_value={"status": "verified", "stable_enforcement_satisfied": True},
             ), \
             mock.patch.object(
                 release_assurance.github_review_provenance,
                 "verify_artifact_review",
                 return_value={"status": "verified"},
             ), \
             mock.patch.object(
                 release_assurance.github_actions_artifact_provenance,
                 "verify_retained_release_provenance",
                 return_value={"authenticated": True},
             ):
            yield

    def write_scope_root(self, root: Path):
        (root / "evals" / "cases").mkdir(parents=True, exist_ok=True)
        (root / "releases").mkdir(parents=True, exist_ok=True)
        (root / "CAPABILITIES.json").write_text(json.dumps({
            "schema_version": 1,
            "development_line": {
                "status": "candidate",
                "capabilities": {
                    "prospective_task_learning": {"status": "candidate", "version": "v2"},
                    "capability_activation_governance": {"status": "candidate", "version": "v1"},
                },
            },
        }), encoding="utf-8")
        (root / "evals" / "cases" / "scope.eval.json").write_text(json.dumps({
            "schema_version": "1.0",
            "suite_id": "suite",
            "artifact": "task-learning",
            "assurance_scope": "behavioral_runtime",
            "cases": [{
                "id": "case",
                "input": {"prompt": "test"},
                "expectations": [{"type": "output_contains_all", "values": ["test"]}],
            }],
        }), encoding="utf-8")
        (root / "releases" / "VNEXT_RELEASE_SCOPE.json").write_text(json.dumps({
            "schema_version": 1,
            "scope_id": "task-learning-v2-core",
            "status": "approved",
            "release_family": "task-learning-v2-core",
            "target_baseline": "task-learning-review-v2",
            "capabilities": [{"name": "prospective_task_learning", "version": "v2"}],
            "release_control_dependencies": [{"name": "capability_activation_governance", "version": "v1"}],
            "required_eval_suites": [{
                "path": "evals/cases/scope.eval.json",
                "suite_id": "suite",
                "covers": ["prospective_task_learning", "capability_activation_governance"],
            }],
            "excluded_candidate_capabilities": [],
            "post_promotion_gates": ["project_framework_pin_upgrade"],
            "rationale": "Test frozen release scope for V2 Stable assurance validation.",
        }), encoding="utf-8")

    def write_stable_root(self, root: Path):
        self.write_scope_root(root)
        (root / "security").mkdir(parents=True, exist_ok=True)
        (root / "evals").mkdir(parents=True, exist_ok=True)
        (root / "releases" / "approvals").mkdir(parents=True, exist_ok=True)
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
            self.write_scope_root(root)
            (root / "security").mkdir(exist_ok=True)
            (root / "security" / "ASSURANCE_ENFORCEMENT.json").write_text(
                json.dumps(self.enforcement(equivalent=False)), encoding="utf-8"
            )
            with self.stable_patches(), \
                 self.assertRaisesRegex(release_assurance.ReleaseError, "server branch/status-check enforcement"):
                release_assurance.validate_manifest(self.stable(), repo_root=root)

    def test_v2_stable_reaches_eval_gate_when_equivalent_enforcement_is_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_scope_root(root)
            (root / "security").mkdir(exist_ok=True)
            (root / "security" / "ASSURANCE_ENFORCEMENT.json").write_text(
                json.dumps(self.enforcement(equivalent=True)), encoding="utf-8"
            )
            with self.stable_patches(), \
                 self.assertRaises((FileNotFoundError, release_assurance.ReleaseError)):
                release_assurance.validate_manifest(self.stable(), repo_root=root)

    def test_v2_stable_baseline_must_match_frozen_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_stable_root(root)
            with self.stable_patches(), \
                 mock.patch.object(release_assurance, "_load_runner", return_value=self.FakeRunner):
                with self.assertRaisesRegex(release_assurance.ReleaseError, "baseline"):
                    release_assurance.validate_manifest(
                        self.stable(baseline="wrong-baseline"),
                        repo_root=root,
                    )

    def test_v2_stable_capabilities_must_match_frozen_scope_exactly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_stable_root(root)
            capabilities = {
                "prospective_task_learning": "v2",
                "capability_activation_governance": "v1",
                "learning_to_development": "candidate-v1",
            }
            with self.stable_patches(), \
                 mock.patch.object(release_assurance, "_load_runner", return_value=self.FakeRunner):
                with self.assertRaisesRegex(release_assurance.ReleaseError, "capabilities"):
                    release_assurance.validate_manifest(
                        self.stable(capabilities=capabilities),
                        repo_root=root,
                    )

    def test_v2_stable_scope_loader_is_bound_to_manifest_framework_ref(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_scope_root(root)
            with mock.patch.object(
                release_assurance.release_scope,
                "load_target_bound_scope",
                side_effect=release_assurance.release_scope.ReleaseScopeError("scope drift"),
            ) as loader:
                with self.assertRaisesRegex(release_assurance.ReleaseError, "target-bound release scope"):
                    release_assurance.validate_manifest(self.stable(), repo_root=root)
            loader.assert_called_once_with(root, "a" * 40, closure_ref="HEAD")

    def test_v2_stable_requires_bound_exact_target_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_stable_root(root)
            with self.stable_patches(), \
                 mock.patch.object(release_assurance, "_load_runner", return_value=self.FakeRunner), \
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
            with self.stable_patches(), \
                 mock.patch.object(release_assurance, "_load_runner", return_value=self.FakeRunner):
                with self.assertRaisesRegex(release_assurance.ReleaseError, "security release approval"):
                    release_assurance.validate_manifest(self.stable(), repo_root=root)

    def test_v2_stable_approval_target_tree_must_match_frozen_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_stable_root(root)
            architecture = self.approval("architecture")
            architecture["target_tree"] = "9" * 40
            (root / "releases" / "approvals" / "architecture.json").write_text(json.dumps(architecture), encoding="utf-8")
            with self.stable_patches(), \
                 mock.patch.object(release_assurance, "_load_runner", return_value=self.FakeRunner):
                with self.assertRaisesRegex(release_assurance.ReleaseError, "architecture release approval"):
                    release_assurance.validate_manifest(self.stable(), repo_root=root)

    def test_v2_stable_rejects_missing_authenticated_actions_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_stable_root(root)
            with self.stable_patches(), \
                 mock.patch.object(release_assurance, "_load_runner", return_value=self.FakeRunner), \
                 mock.patch.object(release_assurance.exact_target_evidence, "validate_binding", return_value={}), \
                 mock.patch.object(
                     release_assurance.github_actions_artifact_provenance,
                     "verify_retained_release_provenance",
                     side_effect=release_assurance.github_actions_artifact_provenance.ActionsProvenanceError("artifact expired or missing"),
                 ):
                with self.assertRaisesRegex(release_assurance.ReleaseError, "Actions provenance verification failed"):
                    release_assurance.validate_manifest(self.stable(), repo_root=root)

    def test_v2_stable_counts_validated_exact_target_bindings_and_approvals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_stable_root(root)
            with self.stable_patches(), \
                 mock.patch.object(release_assurance, "_load_runner", return_value=self.FakeRunner), \
                 mock.patch.object(release_assurance.exact_target_evidence, "validate_binding", return_value={}):
                result = release_assurance.validate_manifest(self.stable(), repo_root=root)
            self.assertEqual(result["exact_target_bindings_validated"], 1)
            self.assertEqual(result["approval_records_validated"], 2)
            self.assertEqual(result["release_scope_id"], "task-learning-v2-core")


if __name__ == "__main__":
    unittest.main()
