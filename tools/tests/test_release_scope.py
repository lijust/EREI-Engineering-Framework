from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import release_scope


class ReleaseScopeTests(unittest.TestCase):
    def setup_root(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / "evals" / "cases").mkdir(parents=True)
        (root / "evals" / "runner.py").write_text(
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
                continue
            values = expectation.get("values")
            if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
                errors.append(f"{path}: cases[{index}].expectations[{exp_index}].values invalid")
    return errors
""".strip() + "\n",
            encoding="utf-8",
        )
        registry = {
            "schema_version": 1,
            "development_line": {
                "status": "candidate",
                "capabilities": {
                    "prospective_task_learning": {"status": "candidate", "version": "v2"},
                    "capability_activation_governance": {"status": "candidate", "version": "v1"},
                    "learning_pattern_analysis": {"status": "candidate", "version": "v1"}
                }
            }
        }
        (root / "CAPABILITIES.json").write_text(json.dumps(registry), encoding="utf-8")
        suite = {
            "schema_version": "1.0",
            "suite_id": "task-learning-review-v1",
            "artifact": "task-learning",
            "cases": [
                {"id": "TLR-001", "input": {"prompt": "x"}, "expectations": [{"type": "output_contains_all", "values": ["x"]}]}
            ]
        }
        (root / "evals" / "cases" / "task-learning-review.eval.json").write_text(json.dumps(suite), encoding="utf-8")
        return temp, root

    def scope(self):
        return {
            "schema_version": 1,
            "scope_id": "task-learning-v2-core",
            "status": "approved",
            "release_family": "task-learning-v2-core",
            "target_baseline": "task-learning-review-v2",
            "capabilities": [{"name": "prospective_task_learning", "version": "v2"}],
            "release_control_dependencies": [{"name": "capability_activation_governance", "version": "v1"}],
            "required_eval_suites": [
                {"path": "evals/cases/task-learning-review.eval.json", "suite_id": "task-learning-review-v1", "covers": ["prospective_task_learning", "capability_activation_governance"]}
            ],
            "excluded_candidate_capabilities": ["learning_pattern_analysis"],
            "post_promotion_gates": ["project_framework_pin_upgrade"],
            "rationale": "Promote the bounded V2 core independently from unrelated Candidate operations."
        }

    def test_valid_scope_resolves_exact_cases(self):
        temp, root = self.setup_root()
        try:
            result = release_scope.validate_scope(root, self.scope())
            self.assertEqual(result["status"], "VALID")
            self.assertEqual(result["required_eval_case_count"], 1)
            self.assertEqual(result["required_eval_cases"], ["task-learning-review-v1/TLR-001"])
        finally:
            temp.cleanup()

    def test_unknown_capability_fails_closed(self):
        temp, root = self.setup_root()
        try:
            value = self.scope()
            value["capabilities"] = [{"name": "missing", "version": "v2"}]
            with self.assertRaisesRegex(release_scope.ReleaseScopeError, "unknown capabilities"):
                release_scope.validate_scope(root, value)
        finally:
            temp.cleanup()

    def test_capability_version_mismatch_fails(self):
        temp, root = self.setup_root()
        try:
            value = self.scope()
            value["capabilities"][0]["version"] = "wrong"
            with self.assertRaisesRegex(release_scope.ReleaseScopeError, "version mismatch"):
                release_scope.validate_scope(root, value)
        finally:
            temp.cleanup()

    def test_missing_capability_eval_coverage_fails(self):
        temp, root = self.setup_root()
        try:
            value = self.scope()
            value["required_eval_suites"][0]["covers"] = ["prospective_task_learning"]
            with self.assertRaisesRegex(release_scope.ReleaseScopeError, "lack required eval-suite coverage"):
                release_scope.validate_scope(root, value)
        finally:
            temp.cleanup()

    def test_suite_cannot_cover_excluded_or_unknown_capability(self):
        temp, root = self.setup_root()
        try:
            value = self.scope()
            value["required_eval_suites"][0]["covers"] = ["prospective_task_learning", "learning_pattern_analysis"]
            with self.assertRaisesRegex(release_scope.ReleaseScopeError, "outside release scope"):
                release_scope.validate_scope(root, value)
        finally:
            temp.cleanup()

    def test_stable_manifest_binding_requires_exact_baseline_and_capability_versions(self):
        temp, root = self.setup_root()
        try:
            scope = self.scope()
            manifest = {
                "baseline": "task-learning-review-v2",
                "capabilities": {
                    "prospective_task_learning": "v2",
                    "capability_activation_governance": "v1",
                },
            }
            result = release_scope.validate_stable_manifest_against_scope(manifest, scope)
            self.assertEqual(result["baseline"], "task-learning-review-v2")

            wrong = dict(manifest)
            wrong["baseline"] = "other"
            with self.assertRaisesRegex(release_scope.ReleaseScopeError, "baseline"):
                release_scope.validate_stable_manifest_against_scope(wrong, scope)

            leaked = dict(manifest)
            leaked["capabilities"] = {
                **manifest["capabilities"],
                "learning_pattern_analysis": "v1",
            }
            with self.assertRaisesRegex(release_scope.ReleaseScopeError, "excluded"):
                release_scope.validate_stable_manifest_against_scope(leaked, scope)
        finally:
            temp.cleanup()

    def test_invalid_eval_contract_fails_before_case_pairs_are_accepted(self):
        temp, root = self.setup_root()
        try:
            suite_path = root / "evals" / "cases" / "task-learning-review.eval.json"
            suite = json.loads(suite_path.read_text(encoding="utf-8"))
            del suite["cases"][0]["input"]
            suite_path.write_text(json.dumps(suite), encoding="utf-8")
            with self.assertRaisesRegex(release_scope.ReleaseScopeError, "eval suite contract invalid"):
                release_scope.validate_scope(root, self.scope())
        finally:
            temp.cleanup()

    def test_suite_identity_mismatch_fails(self):
        temp, root = self.setup_root()
        try:
            value = self.scope()
            value["required_eval_suites"][0]["suite_id"] = "wrong"
            with self.assertRaisesRegex(release_scope.ReleaseScopeError, "identity mismatch"):
                release_scope.validate_scope(root, value)
        finally:
            temp.cleanup()

    def test_included_excluded_overlap_fails(self):
        temp, root = self.setup_root()
        try:
            value = self.scope()
            value["excluded_candidate_capabilities"] = ["prospective_task_learning"]
            with self.assertRaisesRegex(release_scope.ReleaseScopeError, "overlap"):
                release_scope.validate_scope(root, value)
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
