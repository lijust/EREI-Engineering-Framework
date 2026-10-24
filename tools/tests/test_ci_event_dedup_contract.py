"""Source-only guard for PR CI de-duplication without losing release evidence.

This checks literal, security-important workflow invariants without adding a
YAML parser dependency. It does not prove GitHub's scheduler or trusted runner.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
ASSURANCE = ROOT / ".github" / "workflows" / "assurance-gate.yml"
BOOTSTRAP = ROOT / ".github" / "workflows" / "project-bootstrap-tests.yml"
GOVERNANCE = ROOT / "governance" / "ASSURANCE_ENFORCEMENT.md"


class CIEvidencePreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assurance = ASSURANCE.read_text(encoding="utf-8")
        cls.bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        cls.governance = GOVERNANCE.read_text(encoding="utf-8")

    def test_public_governance_description_matches_actual_trigger_semantics(self):
        self.assertIn("all pull requests", self.governance)
        self.assertIn("without** an open/synchronized pull request", self.governance)
        self.assertIn("main/release push run", self.governance)
        self.assertIn("75 synthetic cases", self.governance)
        self.assertIn("13 exact-target behavioral cases", self.governance)
        self.assertNotIn("pushes to `main`, `hardening/**`", self.governance)

    def test_assurance_has_pr_trigger_and_required_push_evidence_only(self):
        header = self.assurance.split("\npermissions:", 1)[0]
        # Keep exact main push assurance for externally authenticated source
        # promotion, as well as existing release/** push protection.
        self.assertIn("on:\n  pull_request:\n  push:", header)
        self.assertIn("      - main\n", header)
        self.assertIn("      - 'release/**'\n", header)
        # A hardening branch with an open PR gets the PR run; its earlier
        # duplicate 'push' run was merely consuming scarce Windows slots.
        self.assertNotIn("      - 'hardening/**'\n", header)

    def test_assurance_preserves_security_relevant_steps(self):
        for phrase in (
            "Run all Framework tool tests",
            "Validate truthful assurance enforcement state",
            "Report derived VNext Stable readiness",
            "Validate frozen release-target closure when selected",
            "Validate last Stable release manifest",
            "Validate grandfathered last Stable carrier provenance",
        ):
            self.assertIn(phrase, self.assurance)
        self.assertIn("runs-on: windows-latest", self.assurance)
        self.assertNotIn("runs-on: [self-hosted", self.assurance)
        self.assertIn("persist-credentials: false", self.assurance)

    def test_untrusted_pr_cannot_cancel_authoritative_assurance_push_group(self):
        # Without a push-side concurrency group, PR-origin YAML cannot pick
        # the same group name to cancel an authoritative main/release run.
        self.assertNotIn("concurrency:", self.assurance)
        self.assertNotIn("cancel-in-progress:", self.assurance)
        self.assertIn("no concurrency group", self.assurance)
        self.assertIn("no GitHub Actions concurrency group", self.governance)

    def test_bootstrap_both_interpreter_checks_remain(self):
        self.assertIn("python-version: ['3.11', '3.12']", self.bootstrap)
        self.assertIn("runs-on: windows-latest", self.bootstrap)
        self.assertNotIn("runs-on: [self-hosted", self.bootstrap)
        self.assertIn("persist-credentials: false", self.bootstrap)
        self.assertIn("Run bootstrap unit tests", self.bootstrap)
        self.assertIn("  push:\n    branches: [main]", self.bootstrap)
        self.assertIn("  pull_request:\n    paths:", self.bootstrap)

    def test_bootstrap_main_push_group_is_not_pr_cancelable(self):
        self.assertNotIn("concurrency:", self.bootstrap)
        self.assertNotIn("cancel-in-progress:", self.bootstrap)
        self.assertIn("no concurrency group", self.bootstrap)


if __name__ == "__main__":
    unittest.main()
