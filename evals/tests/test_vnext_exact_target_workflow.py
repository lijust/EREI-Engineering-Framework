import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "vnext-exact-target-copilot.yml"
ACTION_PINS = {
    "actions/checkout": "d23441a48e516b6c34aea4fa41551a30e30af803",
    "actions/setup-python": "ece7cb06caefa5fff74198d8649806c4678c61a1",
    "actions/setup-node": "820762786026740c76f36085b0efc47a31fe5020",
    "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
}


class VNextExactTargetWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.lowered = cls.text.lower()

    def test_workflow_is_manual_only(self):
        self.assertIn("workflow_dispatch:", self.text)
        self.assertIn("if: ${{ false }}", self.text)
        self.assertNotRegex(self.text, r"(?m)^\s{2}(push|pull_request|schedule):")

    def test_permissions_are_read_only_and_runtime_uses_pat(self):
        self.assertRegex(self.text, r"(?m)^permissions:\s*$")
        self.assertRegex(self.text, r"(?m)^\s{2}contents:\s*read\s*$")
        self.assertNotIn("copilot-requests: write", self.lowered)
        self.assertIn("EREI_COPILOT_EXACT_TARGET_TOKEN", self.text)
        for forbidden in ("issues: write", "pull-requests: write", "actions: write", "checks: write", "statuses: write"):
            self.assertNotIn(forbidden, self.lowered)

    def test_external_actions_are_exact_commit_pinned(self):
        uses = re.findall(r"(?m)^\s*uses:\s*([^\s#]+)", self.text)
        self.assertTrue(uses)
        for ref in uses:
            action, separator, revision = ref.partition("@")
            self.assertEqual(separator, "@", ref)
            self.assertRegex(revision, r"^[a-f0-9]{40}$", ref)
            self.assertEqual(revision, ACTION_PINS.get(action), action)
        self.assertNotRegex(self.text, r"uses:\s*actions/[A-Za-z0-9_.-]+@v\d+")

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

    def test_skill_event_transport_is_probed_before_exact_target_execution(self):
        probe_marker = "- name: Verify skill invocation telemetry transport"
        execute_marker = "- name: Execute frozen release-scoped behavioral cases against target"
        self.assertIn(probe_marker, self.text)
        self.assertLess(self.text.index(probe_marker), self.text.index(execute_marker))
        probe = self.text.split(probe_marker, 1)[1].split(execute_marker, 1)[0]
        self.assertIn("--probe-skill-event skills/impact-analysis", probe)
        self.assertIn("EREI_COPILOT_EXACT_TARGET_TOKEN", probe)
        self.assertIn(
            '--runtime-evidence "copilot-skill-event-transport:skill.invoked-v1"',
            self.text,
        )

    def test_workflow_executes_exact_target_coverage_without_auto_commit(self):
        self.assertIn('python evals/exact_target_run.py "${suites[@]}"', self.text)
        self.assertIn("--minimum-level exact_target_runtime", self.text)
        self.assertIn("mapfile -t suites", self.text)
        self.assertIn("required_eval_suites", self.text)
        self.assertIn("PYTHONDONTWRITEBYTECODE", self.text)
        self.assertIn("--require-complete", self.text)
        self.assertIn("Upload immutable-candidate evidence package", self.text)
        self.assertIn("Behavioral runtime cases: frozen release scope (13 currently)", self.text)
        self.assertIn("Harness-only cases sent to Copilot: 0", self.text)

    def test_evidence_package_identity_is_built_and_retained_as_third_file(self):
        self.assertIn("target/tools/build_exact_target_package_identity.py", self.text)
        self.assertIn('--repository "$GITHUB_REPOSITORY"', self.text)
        self.assertIn('--release-carrier-ref "$CARRIER_SHA"', self.text)
        self.assertIn('--requested-cli-integrity "$COPILOT_CLI_INTEGRITY"', self.text)
        self.assertIn('--runtime-identity-path "evals/exact-target-runs/${run_slug}.identity.json"', self.text)
        self.assertIn("evidence-package/runtime-identity.json", self.text)
        self.assertIn("retains all three package files immutably", self.text)
        self.assertIn("digest-bound V2 runtime identity", self.text)

    def test_model_runtime_is_bounded_version_integrity_and_tarball_pinned(self):
        self.assertIn("--model=gpt-5.4", self.text)
        self.assertIn("copilot_cli_version", self.text)
        self.assertIn("copilot_cli_integrity", self.text)
        self.assertIn("{86}==", self.text)
        self.assertIn("dist.integrity", self.text)
        self.assertIn('copilot-package-integrity:${COPILOT_CLI_INTEGRITY}', self.text)
        self.assertIn('npm pack "@github/copilot@${COPILOT_CLI_VERSION}" --json > pack.json', self.text)
        self.assertIn("crypto.createHash('sha512').update(bytes).digest('base64')", self.text)
        self.assertIn('npm install -g "./copilot-package/${{ steps.copilot_package.outputs.tarball }}"', self.text)
        self.assertNotIn('npm install -g "@github/copilot@${COPILOT_CLI_VERSION}"', self.text)
        self.assertNotIn("--allow-all", self.lowered)
        self.assertNotIn("--yolo", self.lowered)


if __name__ == "__main__":
    unittest.main()
