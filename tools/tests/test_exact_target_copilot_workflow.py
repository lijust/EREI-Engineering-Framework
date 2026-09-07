import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "vnext-exact-target-copilot.yml"
ADAPTER = ROOT / "evals" / "adapters" / "copilot_cli_exact_target.py"


class ExactTargetCopilotWorkflowTests(unittest.TestCase):
    def test_workflow_is_manual_read_only_and_exact_carrier_bound(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("pull_request:", text)
        self.assertNotIn("schedule:", text)
        self.assertIn("contents: read", text)
        self.assertIn("copilot-requests: write", text)
        self.assertIn("expected_carrier_sha", text)
        self.assertIn("release_target.py --repo-root . --validate-closure", text)
        self.assertIn("ref: ${{ steps.target.outputs.target_ref }}", text)
        self.assertIn("--framework-ref \"$TARGET_REF\"", text)
        self.assertIn("--minimum-level exact_target_runtime", text)
        self.assertIn("actions/upload-artifact@v4", text)

    def test_workflow_contains_no_automatic_repository_mutation_or_broad_copilot_permissions(self):
        text = WORKFLOW.read_text(encoding="utf-8").lower()
        forbidden = (
            "--yolo",
            "--allow-all",
            "--allow-tool",
            "--allow-url",
            "git commit",
            "git push",
            "gh pr create",
            "gh pr merge",
        )
        for marker in forbidden:
            self.assertNotIn(marker, text, marker)

    def test_adapter_exposes_no_effective_model_tools(self):
        text = ADAPTER.read_text(encoding="utf-8")
        self.assertIn('"--available-tools=ask_user"', text)
        self.assertIn('"--no-ask-user"', text)
        self.assertIn('"--no-custom-instructions"', text)
        self.assertIn('"--disable-builtin-mcps"', text)
        self.assertIn('"--no-remote"', text)
        self.assertIn('"--no-remote-export"', text)
        self.assertNotIn('"--allow-all"', text)
        self.assertNotIn('"--yolo"', text)


if __name__ == "__main__":
    unittest.main()
