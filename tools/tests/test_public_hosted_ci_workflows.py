"""Ensure public PRs use ephemeral GitHub-hosted Windows instead of persistent personal runners."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_PR_WORKFLOWS = (
    "assurance-gate.yml",
    "framework-evals.yml",
    "project-bootstrap-tests.yml",
    "runtime-adapter-tests.yml",
)


class PublicHostedCIWorkflowTests(unittest.TestCase):
    def test_pr_ci_never_uses_persistent_windows(self):
        for filename in PUBLIC_PR_WORKFLOWS:
            with self.subTest(workflow=filename):
                body = (ROOT / ".github/workflows" / filename).read_text(encoding="utf-8")
                self.assertIn("  pull_request:", body)
                self.assertIn("runs-on: windows-latest", body)
                self.assertNotIn("runs-on: [self-hosted", body)
                self.assertNotIn("pull_request_target:", body)
                self.assertIn("actions/setup-python@v5", body)
                self.assertIn("persist-credentials: false", body)
                self.assertIn("permissions:\n  contents: read", body)
                self.assertNotIn("secrets.", body)
                self.assertNotIn('py "-3.12"', body)

    def test_preflight_is_hosted(self):
        body = (ROOT / ".github/workflows/self-hosted-runner-preflight.yml").read_text(encoding="utf-8")
        self.assertIn("runs-on: windows-latest", body)
        self.assertNotIn("runs-on: [self-hosted", body)
        self.assertIn("actions/setup-python@v5", body)
        self.assertNotIn("  pull_request:", body)

    def test_python_matrices_and_assurance_adapter(self):
        for filename in ("project-bootstrap-tests.yml", "runtime-adapter-tests.yml"):
            body = (ROOT / ".github/workflows" / filename).read_text(encoding="utf-8")
            self.assertIn("python-version: ${{ matrix.python-version }}", body)
            self.assertIn("3.11", body)
            self.assertIn("3.12", body)
            self.assertIn("python -m unittest", body)
        assurance = (ROOT / ".github/workflows/assurance-gate.yml").read_text(encoding="utf-8")
        self.assertIn("python-version: '3.12'", assurance)
        self.assertIn('python evals/fixtures/reference_oracle_adapter.py', assurance)
        self.assertIn('evals/runner.py coverage', assurance)


if __name__ == "__main__":
    unittest.main()
