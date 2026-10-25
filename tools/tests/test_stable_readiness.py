import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import release_scope, stable_readiness

from tools.stable_readiness import (
    StableReadinessError,
    _event_target_revision,
    _expected_cases_for_release,
    approval_gate,
    derive_readiness,
)


class StableReadinessTests(unittest.TestCase):
    def test_current_shape_can_close_cycle_without_claiming_stable(self):
        result = derive_readiness(
            cycle_pass=True,
            eval_pass=False,
            enforcement_pass=False,
            approvals_pass=False,
        )
        self.assertFalse(result["ready_for_final_approvals"])
        self.assertFalse(result["stable_ready"])
        self.assertNotIn("prospective_cycle_incomplete", result["blockers"])
        self.assertIn("exact_target_runtime_evidence_incomplete", result["blockers"])
        self.assertIn("release_enforcement_not_satisfied", result["blockers"])

    def test_preapproval_requires_cycle_eval_and_enforcement(self):
        result = derive_readiness(
            cycle_pass=True,
            eval_pass=True,
            enforcement_pass=True,
            approvals_pass=False,
        )
        self.assertTrue(result["ready_for_final_approvals"])
        self.assertFalse(result["stable_ready"])
        self.assertEqual(result["blockers"], ["final_architecture_security_approvals_not_bound"])

    def test_all_four_gates_are_required_for_stable(self):
        result = derive_readiness(
            cycle_pass=True,
            eval_pass=True,
            enforcement_pass=True,
            approvals_pass=True,
        )
        self.assertTrue(result["ready_for_final_approvals"])
        self.assertTrue(result["stable_ready"])
        self.assertEqual(result["blockers"], [])

    def test_missing_cycle_blocks_preapproval(self):
        result = derive_readiness(
            cycle_pass=False,
            eval_pass=True,
            enforcement_pass=True,
            approvals_pass=False,
        )
        self.assertFalse(result["ready_for_final_approvals"])
        self.assertIn("prospective_cycle_incomplete", result["blockers"])

    def test_pull_request_event_resolves_head_sha_not_synthetic_merge_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            path.write_text(json.dumps({
                "pull_request": {
                    "head": {"sha": "a" * 40},
                }
            }), encoding="utf-8")
            self.assertEqual(_event_target_revision(path), "a" * 40)

    def test_non_pull_request_event_has_no_event_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            path.write_text(json.dumps({"ref": "refs/heads/main"}), encoding="utf-8")
            self.assertIsNone(_event_target_revision(path))

    def test_malformed_pull_request_head_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            path.write_text(json.dumps({"pull_request": {"head": {"sha": "main"}}}), encoding="utf-8")
            with self.assertRaises(StableReadinessError):
                _event_target_revision(path)


class AuthenticatedEvidenceReadinessTests(unittest.TestCase):
    class FakeRunner:
        ASSURANCE_LEVELS = {
            "harness_smoke": 0, "reference_contract": 1,
            "managed_runtime": 2, "exact_target_runtime": 3,
        }

        @staticmethod
        def validate_execution_evidence(data):
            return data

        @staticmethod
        def execution_assurance_level(row, version):
            return row["assurance_level"]

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "evals").mkdir()
        self.path = self.root / "evals" / "EXECUTION_EVIDENCE.test.json"
        self.expected = {("suite", "case")}
        self.ref = "a" * 40
        self.path.write_text(json.dumps({
            "schema_version": 2,
            "framework_revision": self.ref,
            "executions": [{
                "suite_id": "suite", "case_id": "case",
                "assurance_level": "exact_target_runtime",
                "independent_runtime": True,
                "status": "pass",
                "evidence_ref": "exact-target-run:evals/exact-target-runs/copilot-test.json#suite/case",
            }],
        }), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_unavailable_actions_artifact_blocks_preapprovals(self):
        with mock.patch.object(stable_readiness.exact_target_evidence, "validate_binding", return_value={}), \
             mock.patch.object(
                 stable_readiness.github_actions_artifact_provenance,
                 "verify_retained_release_provenance",
                 side_effect=stable_readiness.github_actions_artifact_provenance.ActionsProvenanceError("expired ZIP"),
             ):
            result = stable_readiness._evaluate_evidence_file(
                self.root, self.FakeRunner, self.expected, self.path, self.ref
            )
        self.assertFalse(result["complete"])
        self.assertFalse(result["actions_source_authenticated"])
        self.assertEqual(result["binding_error_count"], 1)
        self.assertIn("expired ZIP", result["binding_errors"][0])

    def test_authenticated_exact_artifact_allows_readiness_evidence_pass(self):
        with mock.patch.object(stable_readiness.exact_target_evidence, "validate_binding", return_value={}), \
             mock.patch.object(
                 stable_readiness.github_actions_artifact_provenance,
                 "verify_retained_release_provenance",
                 return_value={"authenticated": True},
             ) as verify:
            result = stable_readiness._evaluate_evidence_file(
                self.root, self.FakeRunner, self.expected, self.path, self.ref
            )
        self.assertTrue(result["complete"])
        self.assertTrue(result["actions_source_authenticated"])
        self.assertEqual(result["binding_error_count"], 0)
        self.assertEqual(verify.call_args.args[1], Path("evals/exact-target-runs/copilot-test.json"))

    def test_false_provenance_receipt_is_not_a_pass(self):
        with mock.patch.object(stable_readiness.exact_target_evidence, "validate_binding", return_value={}), \
             mock.patch.object(
                 stable_readiness.github_actions_artifact_provenance,
                 "verify_retained_release_provenance",
                 return_value={"authenticated": False},
             ):
            result = stable_readiness._evaluate_evidence_file(
                self.root, self.FakeRunner, self.expected, self.path, self.ref
            )
        self.assertFalse(result["complete"])
        self.assertEqual(result["binding_error_count"], 1)


class ReleaseScopeReadinessTests(unittest.TestCase):
    class Runner:
        @staticmethod
        def _expected_cases(paths, minimum_level="harness_smoke"):
            result = set()
            for raw in paths:
                path = Path(raw)
                candidates = sorted(path.rglob("*.eval.json")) if path.is_dir() else [path]
                for candidate in candidates:
                    value = json.loads(candidate.read_text(encoding="utf-8"))
                    for case in value["cases"]:
                        result.add((value["suite_id"], case["id"]))
            return result

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "EREI Test")
        (self.repo / "evals" / "cases").mkdir(parents=True)
        (self.repo / "evals" / "runner.py").write_text(
            """
def validate_suite(data, path):
    errors = []
    if not isinstance(data, dict):
        return [f"{path}: root must be object"]
    if not isinstance(data.get("suite_id"), str) or not data.get("suite_id"):
        errors.append(f"{path}: suite_id must be non-empty")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append(f"{path}: cases must be non-empty")
        return errors
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"{path}: cases[{index}] must be object")
            continue
        if not isinstance(case.get("id"), str) or not case.get("id"):
            errors.append(f"{path}: cases[{index}].id missing")
        if not isinstance(case.get("input"), dict):
            errors.append(f"{path}: cases[{index}].input must be object")
        expectations = case.get("expectations")
        if not isinstance(expectations, list) or not expectations:
            errors.append(f"{path}: cases[{index}].expectations must be non-empty")
            continue
        for exp_index, expectation in enumerate(expectations):
            if not isinstance(expectation, dict) or expectation.get("type") != "output_contains_all":
                errors.append(f"{path}: cases[{index}].expectations[{exp_index}] unsupported")
    return errors
""".strip() + "\n",
            encoding="utf-8",
        )
        (self.repo / "releases").mkdir()
        registry = {
            "schema_version": 1,
            "development_line": {
                "status": "candidate",
                "capabilities": {
                    "prospective_task_learning": {"status": "candidate", "version": "v2"},
                    "capability_activation_governance": {"status": "candidate", "version": "v1"},
                    "learning_pattern_analysis": {"status": "candidate", "version": "v1"},
                },
            },
        }
        self.write("CAPABILITIES.json", registry)
        self.write("evals/cases/task-learning-review.eval.json", {
            "schema_version": "1.0",
            "suite_id": "task-learning-review-v1",
            "artifact": "task-learning",
            "assurance_scope": "behavioral_runtime",
            "cases": [
                {"id": "TLR-001", "input": {"prompt": "x"}, "expectations": [{"type": "output_contains_all", "values": ["x"]}]},
                {"id": "TLR-002", "input": {"prompt": "y"}, "expectations": [{"type": "output_contains_all", "values": ["y"]}]},
            ],
        })
        self.write("evals/cases/candidate-capability-activation.eval.json", {
            "schema_version": "1.0",
            "suite_id": "candidate-capability-activation-v1",
            "artifact": "capability-activation",
            "assurance_scope": "behavioral_runtime",
            "cases": [
                {"id": "CCA-001", "input": {"prompt": "a"}, "expectations": [{"type": "output_contains_all", "values": ["a"]}]},
            ],
        })
        self.write("evals/cases/unrelated.eval.json", {
            "schema_version": "1.0",
            "suite_id": "unrelated-v1",
            "artifact": "other",
            "assurance_scope": "behavioral_runtime",
            "cases": [
                {"id": "OTH-001", "input": {"prompt": "z"}, "expectations": [{"type": "output_contains_all", "values": ["z"]}]},
            ],
        })
        self.write("releases/VNEXT_RELEASE_SCOPE.json", {
            "schema_version": 1,
            "scope_id": "task-learning-v2-core",
            "status": "approved",
            "release_family": "task-learning-v2-core",
            "target_baseline": "task-learning-review-v2",
            "capabilities": [{"name": "prospective_task_learning", "version": "v2"}],
            "release_control_dependencies": [{"name": "capability_activation_governance", "version": "v1"}],
            "required_eval_suites": [
                {
                    "path": "evals/cases/task-learning-review.eval.json",
                    "suite_id": "task-learning-review-v1",
                    "covers": ["prospective_task_learning"],
                },
                {
                    "path": "evals/cases/candidate-capability-activation.eval.json",
                    "suite_id": "candidate-capability-activation-v1",
                    "covers": ["capability_activation_governance"],
                },
            ],
            "excluded_candidate_capabilities": ["learning_pattern_analysis"],
            "post_promotion_gates": ["project_framework_pin_upgrade"],
            "rationale": "Bound the Stable release to Task Learning V2 Core without unrelated Candidate evals.",
        })
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "target")
        self.target = self.git("rev-parse", "HEAD")

    def tearDown(self):
        if hasattr(self, "review_patcher"):
            self.review_patcher.stop()
        self.tmp.cleanup()

    def git(self, *args):
        process = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        if process.returncode != 0:
            self.fail(f"git {' '.join(args)} failed: {process.stderr}")
        return process.stdout.strip()

    def write(self, path, value):
        full = self.repo / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def test_frozen_scope_selects_only_declared_eval_suite(self):
        expected, meta = _expected_cases_for_release(self.repo, self.Runner(), self.target)
        self.assertEqual(expected, {
            ("task-learning-review-v1", "TLR-001"),
            ("task-learning-review-v1", "TLR-002"),
            ("candidate-capability-activation-v1", "CCA-001"),
        })
        self.assertEqual(meta["mode"], "frozen_release_scope")
        self.assertEqual(meta["required_eval_case_count"], 3)

    def test_scope_drift_after_target_fails_closed(self):
        value = json.loads((self.repo / "releases/VNEXT_RELEASE_SCOPE.json").read_text(encoding="utf-8"))
        value["rationale"] = "Changed after freeze and therefore must require a new release candidate target."
        self.write("releases/VNEXT_RELEASE_SCOPE.json", value)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "scope drift")
        with self.assertRaisesRegex(StableReadinessError, "drifted after target freeze"):
            _expected_cases_for_release(self.repo, self.Runner(), self.target)

    def test_scope_deleted_after_target_fails_closed_instead_of_legacy_fallback(self):
        (self.repo / "releases/VNEXT_RELEASE_SCOPE.json").unlink()
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "delete frozen scope")
        with self.assertRaisesRegex(StableReadinessError, "scope presence changed after target freeze"):
            _expected_cases_for_release(self.repo, self.Runner(), self.target)

    def test_uncommitted_scope_edit_cannot_reduce_expected_cases(self):
        scope_path = self.repo / "releases/VNEXT_RELEASE_SCOPE.json"
        value = json.loads(scope_path.read_text(encoding="utf-8"))
        value["required_eval_suites"] = [value["required_eval_suites"][0]]
        scope_path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        expected, meta = _expected_cases_for_release(self.repo, self.Runner(), self.target)
        self.assertEqual(expected, {
            ("task-learning-review-v1", "TLR-001"),
            ("task-learning-review-v1", "TLR-002"),
            ("candidate-capability-activation-v1", "CCA-001"),
        })
        self.assertEqual(meta["required_eval_case_count"], 3)

    def test_required_eval_suite_drift_after_target_fails_closed(self):
        value = json.loads((self.repo / "evals/cases/task-learning-review.eval.json").read_text(encoding="utf-8"))
        value["cases"].append({
            "id": "TLR-003",
            "input": {"prompt": "later"},
            "expectations": [{"type": "output_contains_all", "values": ["later"]}],
        })
        self.write("evals/cases/task-learning-review.eval.json", value)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "suite drift")
        with self.assertRaisesRegex(StableReadinessError, "drifted after target freeze"):
            _expected_cases_for_release(self.repo, self.Runner(), self.target)

    def test_no_scope_preserves_legacy_all_evals_behavior(self):
        (self.repo / "releases/VNEXT_RELEASE_SCOPE.json").unlink()
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "no scope")
        expected, meta = _expected_cases_for_release(self.repo, self.Runner(), self.git("rev-parse", "HEAD"))
        self.assertIn(("task-learning-review-v1", "TLR-001"), expected)
        self.assertIn(("unrelated-v1", "OTH-001"), expected)
        self.assertEqual(meta["mode"], "all_published_evals")


class StructuredApprovalReadinessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "user.name", "EREI Test")
        self._write("README.md", "target\n")
        self.target = self._commit("target")
        self.target_tree = self._git("rev-parse", f"{self.target}^{{tree}}")
        self.review_patcher = mock.patch(
            "tools.stable_readiness.github_review_provenance.verify_artifact_review",
            return_value={"status": "verified"},
        )
        self.review_patcher.start()

    def tearDown(self):
        self.review_patcher.stop()
        self.tmp.cleanup()

    def _git(self, *args):
        process = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        if process.returncode != 0:
            self.fail(f"git {' '.join(args)} failed: {process.stderr}")
        return process.stdout.strip()

    def _write(self, path, value):
        full = self.repo / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(value if isinstance(value, str) else json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def _commit(self, message):
        self._git("add", "-A")
        self._git("commit", "-q", "-m", message)
        return self._git("rev-parse", "HEAD")

    def _approval(self, approval_type, *, decision="approved", rationale_suffix=""):
        architecture = approval_type == "architecture"
        return {
            "schema_version": 2,
            "approval_id": "EAPP-20260907T130000Z-A1B2C3D4" if architecture else "EAPP-20260907T130100Z-E5F6A7B8",
            "approval_type": approval_type,
            "target_framework_ref": self.target,
            "target_tree": self.target_tree,
            "decision": decision,
            "recorded_at": "2026-09-07T13:00:00Z" if architecture else "2026-09-07T13:01:00Z",
            "reviewer": {
                "kind": "framework_role",
                "id": "system-architect" if architecture else "security-engineer",
            },
            "review_provenance": {
                "provider": "github_codex_review",
                "reviewer_login": "chatgpt-codex-connector[bot]",
                "review_type": "code_review" if approval_type == "architecture" else "security_review",
                "purpose": f"{approval_type}_approval",
            },
            "evidence": ["github-actions:123", "release-target:vnext-rc1"],
            "rationale": f"Reviewed immutable target for {approval_type} Stable promotion{rationale_suffix}.",
        }

    def _build(self, *, rejected_security=False, wrong_arch_ref=False, rewrite_architecture=False):
        self._write("releases/approvals/architecture.json", self._approval("architecture"))
        architecture_ref = self._commit("architecture approval")
        if rewrite_architecture:
            self._write(
                "releases/approvals/architecture.json",
                self._approval("architecture", rationale_suffix=" after rewrite"),
            )
            self._commit("rewrite architecture approval")
        self._write(
            "releases/approvals/security.json",
            self._approval("security", decision="rejected" if rejected_security else "approved"),
        )
        security_ref = self._commit("security approval")
        stable = {
            "schema_version": 1,
            "assurance_contract_version": 2,
            "release_id": "vnext-assurance-v2",
            "baseline": "vnext-assurance-v2",
            "status": "stable",
            "framework_ref": self.target,
            "released_at": "2026-09-07T13:02:00Z",
            "capabilities": {"assurance": "stable-v2"},
            "notes": "structured approval readiness test",
            "approval_ref": security_ref if wrong_arch_ref else architecture_ref,
            "security_review_ref": security_ref,
        }
        self._write("releases/vnext-assurance-v2-stable.json", stable)
        self._commit("stable manifest")
        return architecture_ref, security_ref

    def test_history_binding_with_synthetic_approval_authority(self):
        architecture_ref, security_ref = self._build()
        # Isolate immutable history checks; this is not positive authority proof.
        with mock.patch.object(stable_readiness.release_approval, "verify_approval_authority"):
            result = approval_gate(self.repo, self.target, True)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["validated_records"], 2)
        self.assertEqual(result["approvals"]["architecture"]["bound_ref"], architecture_ref)
        self.assertEqual(result["approvals"]["security"]["bound_ref"], security_ref)

    def test_authenticated_reviews_do_not_pass_readiness_authority(self):
        self._build()
        result = approval_gate(self.repo, self.target, True)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("independent principals", result["reason"])

    def test_readiness_propagates_missing_independent_authority(self):
        self._build()
        with mock.patch.object(
            stable_readiness.release_approval, "verify_approval_authority",
            side_effect=stable_readiness.release_approval.ReleaseApprovalError("independent authority unavailable"),
        ) as authority:
            result = approval_gate(self.repo, self.target, True)
        authority.assert_called_once()
        self.assertEqual(len(authority.call_args.args[0]), 2)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("independent authority unavailable", result["reason"])

    def test_target_bound_scope_drift_blocks_approval_gate(self):
        self._build()
        with mock.patch(
            "tools.stable_readiness.release_scope.load_target_bound_scope",
            side_effect=release_scope.ReleaseScopeError("scope drift"),
        ):
            result = approval_gate(self.repo, self.target, True)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("target-bound release scope", result["reason"])

    def test_rejected_security_record_blocks(self):
        self._build(rejected_security=True)
        result = approval_gate(self.repo, self.target, True)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("security approval invalid", result["reason"])

    def test_sha_shaped_but_wrong_approval_ref_blocks(self):
        self._build(wrong_arch_ref=True)
        result = approval_gate(self.repo, self.target, True)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("must equal first post-target write", result["reason"])

    def test_rewritten_approval_record_blocks(self):
        self._build(rewrite_architecture=True)
        result = approval_gate(self.repo, self.target, True)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("changed after its bound approval ref", result["reason"])

    def test_no_manifest_remains_pending_only_after_preapproval(self):
        self.assertEqual(approval_gate(self.repo, self.target, True)["status"], "pending")
        self.assertEqual(approval_gate(self.repo, self.target, False)["status"], "deferred")


if __name__ == "__main__":
    unittest.main()
