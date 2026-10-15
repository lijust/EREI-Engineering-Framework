from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "bootstrap_project.py"
PIN = "a" * 40


def run_bootstrap(target: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--target",
        str(target),
        "--project-name",
        "Demo Project",
        "--project-repository",
        "example/demo",
        "--project-lifecycle",
        "brownfield",
        "--framework-ref",
        PIN,
        "--framework-baseline",
        "eval-harness-v1",
        "--overlay",
        "google-apps-script",
        "--runtime-adapter",
        "chatgpt-codex",
        *extra,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=10)


class BootstrapProjectTests(unittest.TestCase):
    def test_creates_expected_skeleton_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            result = run_bootstrap(target)
            self.assertEqual(result.returncode, 0, result.stderr)

            expected = [
                "AGENTS.md",
                ".erei/framework.json",
                ".erei/CANDIDATE_CAPABILITIES.json",
                ".erei/PROJECT_PROFILE.md",
                ".erei/ARCHITECTURE.md",
                ".erei/SECURITY_MODEL.md",
                ".erei/DATA_MODEL.md",
                ".erei/PERFORMANCE_BUDGET.md",
                ".erei/PROJECT_RULES.md",
                ".erei/feedback/README.md",
                ".erei/feedback/FRAMEWORK_FEEDBACK.md",
                ".erei/learning/README.md",
                ".erei/learning/LEARNING_SUMMARY.md",
                ".erei/learning/development-outputs/README.md",
                "adr/ADR_TEMPLATE.md",
            ]
            for rel in expected:
                self.assertTrue((target / rel).exists(), rel)

            manifest = json.loads((target / ".erei/framework.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["framework"]["repository"], "lijust/EREI-Engineering-Framework")
            self.assertEqual(manifest["framework"]["baseline"], "eval-harness-v1")
            self.assertEqual(manifest["framework"]["ref_type"], "commit")
            self.assertEqual(manifest["framework"]["ref"], PIN)
            self.assertEqual(manifest["overlays"], ["google-apps-script"])
            self.assertEqual(manifest["runtime_adapters"], ["chatgpt-codex"])
            candidate_adoptions = json.loads(
                (target / ".erei/CANDIDATE_CAPABILITIES.json").read_text(encoding="utf-8")
            )
            self.assertEqual(candidate_adoptions["framework_ref"], PIN)
            self.assertEqual(candidate_adoptions["adoptions"], [])
            feedback_md = (target / ".erei/feedback/FRAMEWORK_FEEDBACK.md").read_text(encoding="utf-8")
            self.assertIn("No feedback events recorded yet", feedback_md)
            self.assertFalse((target / ".erei/feedback/FRAMEWORK_FEEDBACK.jsonl").exists())
            learning_md = (target / ".erei/learning/LEARNING_SUMMARY.md").read_text(encoding="utf-8")
            self.assertIn("No Task Learning Events recorded yet", learning_md)
            self.assertFalse((target / ".erei/learning/TASK_EVENTS.jsonl").exists())
            development_readme = (target / ".erei/learning/development-outputs/README.md").read_text(encoding="utf-8")
            self.assertIn("Learning Development Outputs", development_readme)

    def test_branch_experiment_bootstrap_keeps_candidate_adoptions_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            result = run_bootstrap(
                target,
                "--framework-ref-type",
                "branch",
                "--framework-ref",
                "candidate-branch",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            candidate = json.loads(
                (target / ".erei/CANDIDATE_CAPABILITIES.json").read_text(encoding="utf-8")
            )
            self.assertEqual(candidate["framework_ref"], "candidate-branch")
            self.assertEqual(candidate["adoptions"], [])

    def test_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            result = run_bootstrap(target, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((target / "AGENTS.md").exists())
            self.assertIn("DRY-RUN CREATE", result.stdout)

    def test_existing_file_blocks_all_writes_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            existing = target / "AGENTS.md"
            existing.write_text("keep-me", encoding="utf-8")

            result = run_bootstrap(target)
            self.assertEqual(result.returncode, 3)
            self.assertEqual(existing.read_text(encoding="utf-8"), "keep-me")
            self.assertFalse((target / ".erei/framework.json").exists())
            self.assertIn("CONFLICT", result.stderr)

    def test_dry_run_reports_conflict_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            existing = target / "AGENTS.md"
            existing.write_text("keep-me", encoding="utf-8")

            result = run_bootstrap(target, "--dry-run")
            self.assertEqual(result.returncode, 3)
            self.assertEqual(existing.read_text(encoding="utf-8"), "keep-me")
            self.assertFalse((target / ".erei/framework.json").exists())
            self.assertIn("DRY-RUN CONFLICT", result.stderr)

    def test_force_replaces_existing_integration_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            agents = target / "AGENTS.md"
            agents.write_text("old", encoding="utf-8")

            result = run_bootstrap(target, "--force")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotEqual(agents.read_text(encoding="utf-8"), "old")
            self.assertIn("Demo Project", agents.read_text(encoding="utf-8"))

    def test_force_preserves_existing_candidate_adoption_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            first = run_bootstrap(target)
            self.assertEqual(first.returncode, 0, first.stderr)
            path = target / ".erei/CANDIDATE_CAPABILITIES.json"
            protected = {
                "schema_version": 1,
                "framework_ref": PIN,
                "adoptions": [{
                    "adoption_id": "CAD-20261015T200000Z-A1B2C3D4",
                    "capability": "candidate_capability",
                    "version": "v1",
                    "approved_at": "2026-10-15T20:00:00Z",
                    "expires_at": "2026-10-20T20:00:00Z",
                    "approved_by_role": "chief-engineer",
                    "risk": "L2",
                    "purpose": "Preserve explicit project Candidate adoption authority.",
                    "evidence": ["approval:test"],
                }],
            }
            path.write_text(json.dumps(protected), encoding="utf-8")
            forced = run_bootstrap(target, "--force")
            self.assertEqual(forced.returncode, 0, forced.stderr)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), protected)
            self.assertIn("PRESERVE PROJECT AUTHORITY", forced.stdout)

    def test_missing_target_fails_without_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "missing"
            result = run_bootstrap(target)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(target.exists())
            self.assertIn("Target does not exist", result.stderr)


if __name__ == "__main__":
    unittest.main()
