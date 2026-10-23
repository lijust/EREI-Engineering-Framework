"""Test the actual hosted Windows PowerShell CI coverage partition without running suites.

This is source/argv regression coverage, not authentication of the GitHub
scheduler, code reviewer, or independent release workflow.
"""
from pathlib import Path
import json
import shutil
import subprocess
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / ".github/workflows/project-bootstrap-tests.yml"
ASSURANCE = ROOT / ".github/workflows/assurance-gate.yml"
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")


def bootstrap_test_script():
    source = BOOTSTRAP.read_text(encoding="utf-8")
    section = source.split("      - name: Run bootstrap unit tests\n", 1)[1]
    section = section.split("      - name:", 1)[0]
    lines = section.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("        run: "):
            value = line.removeprefix("        run: ")
            return textwrap.dedent("\n".join(lines[index + 1:])) if value == "|" else value
    raise AssertionError("Bootstrap unit test step has no run script")


@unittest.skipUnless(POWERSHELL, "PowerShell required to exercise hosted Windows CI")
class CITestPartitionTests(unittest.TestCase):
    def invoke(self, version, exit_code=0):
        script = bootstrap_test_script().replace("${{ matrix.python-version }}", version)
        launcher = (
            "function python {\n"
            "  ConvertTo-Json -InputObject @($args) -Compress\n"
            f"  $global:LASTEXITCODE = {exit_code}\n"
            "}\n"
        )
        return subprocess.run(
            [POWERSHELL, "-NoProfile", "-NonInteractive", "-Command", launcher + script],
            capture_output=True, text=True, timeout=30, check=False,
        )

    def test_python_311_retains_full_suite(self):
        result = self.invoke("3.11")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [
            "-m", "unittest", "discover", "-s", "tools/tests", "-p", "test_*.py", "-v",
        ])

    def test_python_312_runs_focused_bootstrap_and_activation(self):
        result = self.invoke("3.12")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [
            "-m", "unittest", "tools.tests.test_bootstrap_project",
            "tools.tests.test_capability_activation", "-v",
        ])

    def test_failing_python_propagates_nonzero(self):
        for version in ("3.11", "3.12"):
            with self.subTest(version=version):
                self.assertEqual(self.invoke(version, exit_code=7).returncode, 7)

    def test_unknown_matrix_interpreter_fails_closed(self):
        result = self.invoke("3.13")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")


class CIRequiredAssuranceCoverageTests(unittest.TestCase):
    def test_global_required_assurance_keeps_full_312_discovery(self):
        src = ASSURANCE.read_text(encoding="utf-8")
        section = src.split("      - name: Run all Framework tool tests\n", 1)[1]
        section = section.split("      - name:", 1)[0]
        self.assertNotIn("if:", section)
        self.assertIn(
            "run: python -m unittest discover -s tools/tests -p 'test_*.py' -v",
            section,
        )
        hdr = src.split("\nconcurrency:", 1)[0]
        self.assertIn("on:\n  pull_request:\n  push:\n", hdr)
        self.assertIn("      - main\n", hdr)
        self.assertNotIn("paths:", hdr)
        self.assertIn("runs-on: windows-latest", src)
        self.assertNotIn("runs-on: [self-hosted", src)


if __name__ == "__main__":
    unittest.main()
