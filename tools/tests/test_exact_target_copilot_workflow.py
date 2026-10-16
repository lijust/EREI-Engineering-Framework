import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "vnext-exact-target-copilot.yml"
ADAPTER = ROOT / "evals" / "adapters" / "copilot_cli_exact_target.py"
ACTION_PINS = {
    "actions/checkout": "d23441a48e516b6c34aea4fa41551a30e30af803",
    "actions/setup-python": "ece7cb06caefa5fff74198d8649806c4678c61a1",
    "actions/setup-node": "820762786026740c76f36085b0efc47a31fe5020",
    "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
}


class ExactTargetCopilotWorkflowTests(unittest.TestCase):
    def test_workflow_is_manual_read_only_and_exact_carrier_bound(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("if: ${{ false }}", text)
        self.assertNotIn("pull_request:", text)
        self.assertNotIn("schedule:", text)
        self.assertIn("contents: read", text)
        self.assertNotIn("copilot-requests: write", text)
        self.assertIn("expected_carrier_sha", text)
        self.assertIn("release_target.py --repo-root . --validate-closure", text)
        self.assertIn("ref: ${{ steps.target.outputs.target_ref }}", text)
        self.assertIn("--framework-ref \"$TARGET_REF\"", text)
        self.assertIn("--minimum-level exact_target_runtime", text)

    def test_all_external_actions_are_pinned_to_exact_commits(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        uses = re.findall(r"(?m)^\s*uses:\s*([^\s#]+)", text)
        self.assertTrue(uses)
        for ref in uses:
            action, separator, revision = ref.partition("@")
            self.assertEqual(separator, "@", ref)
            self.assertRegex(revision, r"^[a-f0-9]{40}$", ref)
            self.assertIn(action, ACTION_PINS, action)
            self.assertEqual(revision, ACTION_PINS[action], action)
        for action, revision in ACTION_PINS.items():
            self.assertIn(f"{action}@{revision}", text)
        self.assertNotRegex(text, r"uses:\s*actions/[A-Za-z0-9_.-]+@v\d+")

    def test_workflow_requires_personal_repo_pat_pinned_cli_and_full_integrity(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("EREI_COPILOT_EXACT_TARGET_TOKEN", text)
        self.assertIn("copilot_cli_version", text)
        self.assertIn("copilot_cli_integrity", text)
        self.assertIn("{86}==", text)
        self.assertIn('npm view "@github/copilot@${COPILOT_CLI_VERSION}" dist.integrity', text)
        self.assertIn('registry_integrity" != "$COPILOT_CLI_INTEGRITY', text)
        self.assertIn('--runtime-evidence "copilot-package-integrity:${COPILOT_CLI_INTEGRITY}"', text)
        self.assertIn('--requested-cli-integrity "$COPILOT_CLI_INTEGRITY"', text)
        execute = text.split("- name: Execute frozen release-scoped behavioral cases against target", 1)[1]
        execute = execute.split("- name: Write evidence package identity", 1)[0]
        self.assertIn("COPILOT_GITHUB_TOKEN", execute)
        self.assertNotRegex(execute, r"(?m)^\s+GITHUB_TOKEN:")

    def test_copilot_install_uses_only_byte_verified_local_tarball(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('npm pack "@github/copilot@${COPILOT_CLI_VERSION}" --json > pack.json', text)
        self.assertIn("crypto.createHash('sha512').update(bytes).digest('base64')", text)
        self.assertIn("downloaded Copilot tarball integrity mismatch", text)
        self.assertIn('npm install -g "./copilot-package/${{ steps.copilot_package.outputs.tarball }}"', text)
        self.assertNotIn('npm install -g "@github/copilot@${COPILOT_CLI_VERSION}"', text)
        self.assertIn("Copilot installation source: byte-verified local npm tarball", text)

    def test_skill_event_transport_probe_precedes_and_binds_evidence_production(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        probe_marker = "- name: Verify skill invocation telemetry transport"
        execute_marker = "- name: Execute frozen release-scoped behavioral cases against target"
        self.assertIn(probe_marker, text)
        self.assertIn(execute_marker, text)
        self.assertLess(text.index(probe_marker), text.index(execute_marker))
        probe = text.split(probe_marker, 1)[1].split(execute_marker, 1)[0]
        self.assertIn("EREI_COPILOT_EXACT_TARGET_TOKEN", probe)
        self.assertIn("--probe-skill-event skills/impact-analysis", probe)
        self.assertIn("--model=gpt-5.4", probe)
        self.assertIn(
            '--runtime-evidence "copilot-skill-event-transport:skill.invoked-v1"',
            text,
        )
        self.assertIn("Skill invocation telemetry: `skill.invoked-v1` transport probe PASS", text)

    def test_workflow_builds_three_file_digest_bound_package(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("target/tools/build_exact_target_package_identity.py", text)
        self.assertIn('--repository "$GITHUB_REPOSITORY"', text)
        self.assertIn('--release-carrier-ref "$CARRIER_SHA"', text)
        self.assertIn('--run-manifest-path "evals/exact-target-runs/${run_slug}.json"', text)
        self.assertIn('--execution-evidence-path "evals/EXECUTION_EVIDENCE.${run_slug}.json"', text)
        self.assertIn('--runtime-identity-path "evals/exact-target-runs/${run_slug}.identity.json"', text)
        self.assertIn("evidence-package/runtime-identity.json", text)
        self.assertIn("retains all three package files immutably", text)
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

    def test_adapter_has_direct_mode_and_authoritative_fail_closed_routing_telemetry(self):
        text = ADAPTER.read_text(encoding="utf-8")
        self.assertIn('available_tools = "skill" if expected_skill is not None else "ask_user"', text)
        self.assertIn('"--no-ask-user"', text)
        self.assertIn('"--no-custom-instructions"', text)
        self.assertIn('"--disable-builtin-mcps"', text)
        self.assertIn('"--no-remote"', text)
        self.assertIn('"--no-remote-export"', text)
        self.assertIn('event_type == "skill.invoked"', text)
        self.assertIn("observed skill tool activity without authoritative skill.invoked telemetry", text)
        self.assertIn("--probe-skill-event", text)
        self.assertNotIn('"--allow-all"', text)
        self.assertNotIn('"--yolo"', text)


if __name__ == "__main__":
    unittest.main()
