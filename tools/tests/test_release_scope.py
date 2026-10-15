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
                {"path": "evals/cases/task-learning-review.eval.json", "suite_id": "task-learning-review-v1"}
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
