import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "vnext-exact-target-copilot.yml"


class VNextExactTargetWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.lowered = cls.text.lower()

    def test_workflow_is_manual_only(self):
        self.assertIn("workflow_dispatch:", self.text)
        self.assertNotRegex(self.text, r"(?m)^\s{2}(push|pull_request|schedule):")

    def test_permissions_are_read_only_and_runtime_uses_pat(self):
        self.assertRegex(self.text, r"(?m)^permissions:\s*$")
        self.assertRegex(self.text, r"(?m)^\s{2}contents:\s*read\s*$")
        self.assertNotIn("copilot-requests: write", self.lowered)
        self.assertIn("EREI_COPILOT_EXACT_TARGET_TOKEN", self.text)
        for forbidden in ("issues: write", "pull-requests: write", "actions: write", "checks: write", "statuses: write"):
            self.assertNotIn(forbidden, self.lowered)

    def test_workflow_cannot_mutate_repository_or_promote_release(self):
        for forbidden in (
            "git push", "git commit", "gh pr ", "create-pull-request", "promotion_authorized: true",
            "--yolo", "--allow-all", "--allow-all-tools", "--allow-all-paths",
        ):
            self.assertNotIn(forbidden, self.lowered)

    def test_workflow_requires_exact_release_carrier_and_frozen_target(self):
        self.assertIn("expected_carrier_sha", self.text)
        self.assertIn("python tools/release_target.py --repo-root . --validate-closure", self.text)
        self.assertIn("target_ref=${{ steps.target.outputs.target_ref }}", self.text.lower())
        self.assertIn("target_tree=${{ steps.target.outputs.target_tree }}", self.text.lower())
        self.assertIn("git -C target rev-parse HEAD", self.text)
        self.assertIn("git -C target rev-parse 'HEAD^{tree}'", self.text)

    def test_workflow_executes_exact_target_coverage_without_auto_commit(self):
        self.assertIn("python evals/exact_target_run.py evals/cases", self.text)
        self.assertIn("--minimum-level exact_target_runtime", self.text)
        self.assertIn("--require-complete", self.text)
        self.assertIn("Upload immutable-candidate evidence package", self.text)
        self.assertIn("Behavioral runtime cases: 43", self.text)
        self.assertIn("Harness-only cases sent to Copilot: 0", self.text)

    def test_model_runtime_is_bounded_and_version_pinned(self):
        self.assertIn("--model=gpt-5.4", self.text)
        self.assertIn("copilot_cli_version", self.text)
        self.assertIn('@github/copilot@${COPILOT_CLI_VERSION}', self.text)
        self.assertNotIn("--allow-all", self.lowered)
        self.assertNotIn("--yolo", self.lowered)


if __name__ == "__main__":
    unittest.main()
