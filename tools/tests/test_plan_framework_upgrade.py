import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import plan_framework_upgrade as mod


class FrameworkUpgradePlannerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.manifest = {
            "schema_version": 1,
            "framework": {
                "repository": "lijust/EREI-Engineering-Framework",
                "baseline": "project-integration-bootstrap-v1",
                "ref_type": "commit",
                "ref": "fd5942feb925d35a410ae945057bd6a8c4841384",
            },
            "project": {},
            "overlays": ["google-apps-script"],
            "runtime_adapters": [],
        }
        self.current = {"framework": "EREI Engineering Framework", "baseline": "project-integration-bootstrap-v1", "status": "stable"}
        self.target = {"framework": "EREI Engineering Framework", "baseline": "next-stable", "status": "stable"}
        self._write("manifest.json", self.manifest)
        self._write("current.json", self.current)
        self._write("target.json", self.target)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, name, value):
        path = self.root / name
        path.write_text(value if isinstance(value, str) else json.dumps(value), encoding="utf-8")
        return path

    def _args(self, changed, **overrides):
        changed_path = self._write("changed.txt", changed)
        data = dict(
            project_manifest=str(self.root / "manifest.json"),
            framework_repo=None,
            current_ref=None,
            current_baseline=str(self.root / "current.json"),
            target_baseline=str(self.root / "target.json"),
            changed_paths=str(changed_path),
            target_repository="lijust/EREI-Engineering-Framework",
            target_ref_type="commit",
            target_ref="abcdef1234567890",
            allow_nonstable_target=False,
            allow_mutable_target=False,
            output=None,
        )
        data.update(overrides)
        return argparse.Namespace(**data)

    def test_normal_workflow_change_requires_project_review(self):
        plan = mod.build_plan(self._args("workflows/framework-upgrade/WORKFLOW.md\n"))
        self.assertEqual(plan["classification"]["compatibility"], "PROJECT_REVIEW_REQUIRED")
        self.assertEqual(plan["classification"]["risk"], "L2")
        self.assertFalse(plan["approval_eligible"])
        self.assertEqual(plan["input_verification"], "unverified_caller_supplied_inputs")
        self.assertFalse(plan["mutation_performed"])

    def test_all_protected_families_escalate_to_l3(self):
        for path in [
            "constitution/ENGINEERING_CONSTITUTION.md",
            "schemas/runtime-adapter.schema.json",
            "schemas/task-learning-event.schema.json",
            "architecture/EREI_ARCHITECTURE_V1.md",
            "adr/ADR-0005-TASK-LEARNING-AND-REVIEW-TRIGGERS.md",
            "BASELINE.json",
            "CAPABILITIES.json",
            "releases/next.json",
        ]:
            with self.subTest(path=path):
                compatibility, risk, protected, _, _ = mod.classify([path])
                self.assertEqual(compatibility, "ARCHITECTURE_APPROVAL_REQUIRED")
                self.assertEqual(risk, "L3")
                self.assertIn(path, protected)

    def test_unknown_path_escalates_instead_of_failing_open(self):
        plan = mod.build_plan(self._args("new-governance-surface/policy.json\n"))
        self.assertEqual(plan["classification"]["risk"], "L3")
        self.assertEqual(plan["classification"]["unknown_escalated_paths"], ["new-governance-surface/policy.json"])

    def test_mutable_target_blocks_by_default(self):
        with self.assertRaises(mod.PlanError):
            mod.build_plan(self._args("README.md\n", target_ref_type="branch", target_ref="main"))

    def test_nonstable_target_blocks_by_default(self):
        self._write("target.json", {"framework": "EREI Engineering Framework", "baseline": "candidate", "status": "candidate"})
        with self.assertRaises(mod.PlanError):
            mod.build_plan(self._args("README.md\n"))

    def test_repository_change_escalates(self):
        plan = mod.build_plan(self._args("README.md\n", target_repository="other/framework"))
        self.assertEqual(plan["classification"]["compatibility"], "ARCHITECTURE_APPROVAL_REQUIRED")
        self.assertEqual(plan["classification"]["risk"], "L3")
        self.assertTrue(plan["warnings"])

    def test_mismatched_current_baseline_is_rejected(self):
        self._write("current.json", {"framework": "EREI Engineering Framework", "baseline": "unrelated", "status": "stable"})
        with self.assertRaisesRegex(mod.PlanError, "does not match project manifest"):
            mod.build_plan(self._args("README.md\n"))

    def test_verified_mode_derives_git_objects_and_is_approval_eligible(self):
        args = self._args(
            "ignored\n",
            framework_repo=str(self.root),
            current_ref=self.manifest["framework"]["ref"],
            target_ref="b" * 40,
        )
        with mock.patch.object(
            mod,
            "_verified_inputs",
            return_value=(self.current, self.target, ["schemas/runtime-adapter.schema.json"], self.manifest["framework"]["ref"], "b" * 40),
        ):
            plan = mod.build_plan(args)
        self.assertTrue(plan["approval_eligible"])
        self.assertEqual(plan["input_verification"], "verified_git_objects")
        self.assertEqual(plan["target"]["resolved_commit"], "b" * 40)
        self.assertEqual(plan["classification"]["risk"], "L3")


if __name__ == "__main__":
    unittest.main()
