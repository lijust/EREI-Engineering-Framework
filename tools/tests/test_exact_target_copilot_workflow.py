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
        self.assertNotIn("copilot-requests: write", text)
        self.assertIn("expected_carrier_sha", text)
        self.assertIn("release_target.py --repo-root . --validate-closure", text)
        self.assertIn("ref: ${{ steps.target.outputs.target_ref }}", text)
        self.assertIn("--framework-ref \"$TARGET_REF\"", text)
        self.assertIn("--minimum-level exact_target_runtime", text)
        self.assertIn("actions/upload-artifact@v4", text)

    def test_workflow_requires_personal_repo_pat_and_pinned_cli_version(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("EREI_COPILOT_EXACT_TARGET_TOKEN", text)
        self.assertIn("copilot_cli_version", text)
        self.assertIn('npm install -g "@github/copilot@${COPILOT_CLI_VERSION}"', text)
        self.assertNotIn("npm install -g @github/copilot\n", text)
        execute = text.split("- name: Execute 43 behavioral cases against frozen target", 1)[1]
        execute = execute.split("- name: Write evidence package identity", 1)[0]
        self.assertIn("COPILOT_GITHUB_TOKEN", execute)
        self.assertNotIn("GITHUB_TOKEN:", execute)

    def test_workflow_builds_digest_bound_package_identity_from_frozen_target_tooling(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("target/tools/build_exact_target_package_identity.py", text)
        self.assertIn('--repository "$GITHUB_REPOSITORY"', text)
        self.assertIn('--release-carrier-ref "$CARRIER_SHA"', text)
        self.assertIn('--run-manifest-path "evals/exact-target-runs/${run_slug}.json"', text)
        self.assertIn('--execution-evidence-path "evals/EXECUTION_EVIDENCE.${run_slug}.json"', text)
        self.assertIn("evidence-package/runtime-identity.json", text)
        self.assertIn("Evidence package: digest-bound V2 runtime identity", text)

    def test_workflow_contains_no_automatic_repository_mutation_or_broad_copilot_permissions(self):
        text = WORKFLOW.read_text(encoding="utf-8").lower()
        forbidden = (
            "copilot-requests: write",
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

    def test_adapter_has_separate_direct_and_observed_routing_modes(self):
        text = ADAPTER.read_text(encoding="utf-8")
        self.assertIn('available_tools = "skill" if routing_mode else "ask_user"', text)
        self.assertIn('"--no-ask-user"', text)
        self.assertIn('"--no-custom-instructions"', text)
        self.assertIn('"--disable-builtin-mcps"', text)
        self.assertIn('"--no-remote"', text)
        self.assertIn('"--no-remote-export"', text)
        self.assertIn('event_type == "skill.invoked"', text)
        self.assertNotIn('"--allow-all"', text)
        self.assertNotIn('"--yolo"', text)


if __name__ == "__main__":
    unittest.main()
