import unittest

from evals.adapters import copilot_cli_exact_target as adapter


class CopilotRoutingPromptBoundaryTests(unittest.TestCase):
    def test_routing_prompt_does_not_name_or_embed_the_staged_skill(self):
        prompt = adapter.build_routing_prompt(
            {"prompt": "Analyze whether this change needs broader impact analysis."},
            {"project": "sample"},
        )
        lowered = prompt.lower()
        self.assertNotIn("impact-analysis", lowered)
        self.assertNotIn("impact policy", lowered)
        self.assertNotIn("skill.md", lowered)
        self.assertNotIn("suite_id", lowered)
        self.assertNotIn("case_id", lowered)
        self.assertNotIn("expectations", lowered)
        self.assertNotIn("tags", lowered)
        self.assertIn("a project skill may be available", lowered)


if __name__ == "__main__":
    unittest.main()
