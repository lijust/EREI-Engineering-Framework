import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "plan_framework_upgrade.py"
spec = importlib.util.spec_from_file_location("plan_framework_upgrade", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


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
                "ref": "fd5942feb925d35a410ae945057bd6a8c4841384"
            },
            "project": {},
            "overlays": ["google-apps-script"],
            "runtime_adapters": []
        }
        self.current = {"framework": "EREI Engineering Framework", "baseline": "project-integration-bootstrap-v1", "status": "stable"}
        self.target = {"framework": "EREI Engineering Framework", "baseline": "next-stable", "status": "stable"}
        self._write("manifest.json", self.manifest)
        self._write("current.json", self.current)
        self._write("target.json", self.target)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, name, value):
        p = self.root / name
        if isinstance(value, str):
            p.write_text(value, encoding="utf-8")
        else:
            p.write_text(json.dumps(value), encoding="utf-8")
        return p

    def _args(self, changed, **overrides):
        changed_path = self._write("changed.txt", changed)
        data = dict(
            project_manifest=str(self.root / "manifest.json"),
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
        self.assertFalse(plan["mutation_performed"])

    def test_constitution_change_requires_architecture_approval(self):
        plan = mod.build_plan(self._args("constitution/ENGINEERING_CONSTITUTION.md\n"))
        self.assertEqual(plan["classification"]["compatibility"], "ARCHITECTURE_APPROVAL_REQUIRED")
        self.assertEqual(plan["classification"]["risk"], "L3")
        self.assertIn("explicit-architecture-approval", plan["required_gates"])

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


if __name__ == "__main__":
    unittest.main()
