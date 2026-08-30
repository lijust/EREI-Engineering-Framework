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
                ".erei/PROJECT_PROFILE.md",
                ".erei/ARCHITECTURE.md",
                ".erei/SECURITY_MODEL.md",
                ".erei/DATA_MODEL.md",
                ".erei/PERFORMANCE_BUDGET.md",
                ".erei/PROJECT_RULES.md",
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

    def test_missing_target_fails_without_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "missing"
            result = run_bootstrap(target)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(target.exists())
            self.assertIn("Target does not exist", result.stderr)


if __name__ == "__main__":
    unittest.main()
