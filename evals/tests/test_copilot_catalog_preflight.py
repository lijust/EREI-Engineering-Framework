"""Static preflight: all external behavioral suites have safely readable artifacts.

No model, token, external API, or Copilot CLI invocation is performed.
"""
import json
import tempfile
import unittest
from pathlib import Path

from evals.adapters import copilot_cli_exact_target as adapter

ROOT = Path(__file__).resolve().parents[2]
SUITES = ROOT / "evals" / "cases"


class CopilotBehavioralCatalogPreflight(unittest.TestCase):
    def test_all_behavioral_suite_artifacts_are_resolvable_without_test_material(self):
        count = 0
        suites = 0
        for path in sorted(SUITES.glob("*.eval.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            if data["assurance_scope"] != "behavioral_runtime":
                continue
            suites += 1
            count += len(data["cases"])
            artifact = data["artifact"]
            with self.subTest(suite=data["suite_id"], artifact=artifact):
                routing = adapter._routing_skill_name(artifact)
                if routing is not None:
                    with tempfile.TemporaryDirectory() as tmp:
                        staged = adapter.stage_routing_skill(ROOT, Path(tmp), artifact)
                        self.assertEqual(staged, routing)
                        self.assertTrue(
                            (Path(tmp) / ".github" / "skills" / routing / "SKILL.md").is_file()
                        )
                else:
                    resolved = adapter.resolve_artifact(ROOT, artifact)
                    self.assertGreater(len(resolved), 0)
                    for name, _ in resolved:
                        self.assertNotIn("/CASES.md", name)
                        self.assertNotIn("/evals/", name)
                        self.assertNotIn("/tests/", name)
        self.assertEqual(suites, 15)
        self.assertEqual(count, 74)
        self.assertEqual(len(adapter.ROUTING_SKILLS), 7)


if __name__ == "__main__":
    unittest.main()
