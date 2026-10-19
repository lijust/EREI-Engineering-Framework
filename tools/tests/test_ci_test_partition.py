"""Execute the checked-in PowerShell selection without running the full suite.

The fake Python launcher records argv and returns an injected exit status. These
tests prove selection/failure propagation, not GitHub scheduling or test success.
"""
import json
from pathlib import Path
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
    step = source.split("      - name: Run bootstrap unit tests\n", 1)[1]
    step = step.split("      - name:", 1)[0]
    lines = step.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("        run: "):
            value = line.removeprefix("        run: ")
            return textwrap.dedent("\n".join(lines[index + 1:])) if value == "|" else value
    raise AssertionError("Bootstrap test command is missing")


@unittest.skipUnless(POWERSHELL, "Workflow selection requires PowerShell")
class CITestPartitionTests(unittest.TestCase):
    def invoke(self, version, exit_code=0):
        script = bootstrap_test_script().replace("${{ matrix.python-version }}", version)
        launcher = (
            "function py {\n"
            "  ConvertTo-Json -InputObject @($args) -Compress\n"
            f"  $global:LASTEXITCODE = {exit_code}\n"
            "}\n"
        )
        return subprocess.run(
            [POWERSHELL, "-NoProfile", "-NonInteractive", "-Command", launcher + script],
            capture_output=True, text=True, timeout=30, check=False,
        )

    def test_python_311_retains_full_tool_discovery(self):
        result = self.invoke("3.11")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [
            "-3.11", "-m", "unittest", "discover", "-s", "tools/tests",
            "-p", "test_*.py", "-v",
        ])

    def test_python_312_runs_bootstrap_and_activation_smoke_only(self):
        result = self.invoke("3.12")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [
            "-3.12", "-m", "unittest", "tools.tests.test_bootstrap_project",
            "tools.tests.test_capability_activation", "-v",
        ])

    def test_both_selected_commands_propagate_test_failure(self):
        for version in ("3.11", "3.12"):
            with self.subTest(version=version):
                self.assertEqual(self.invoke(version, exit_code=7).returncode, 7)

    def test_unallocated_interpreter_cannot_silently_pass(self):
        result = self.invoke("3.13")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")


class CIFullCoverageSourceTests(unittest.TestCase):
    def test_assurance_retains_unconditional_full_python_312_discovery(self):
        source = ASSURANCE.read_text(encoding="utf-8")
        step = source.split("      - name: Run all Framework tool tests\n", 1)[1]
        step = step.split("      - name:", 1)[0]
        self.assertNotIn("if:", step)
        self.assertIn(
            'run: py "-3.12" -m unittest discover -s tools/tests -p \'test_*.py\' -v',
            step,
        )
        # Every Bootstrap event is also covered by unfiltered Assurance: all
        # PRs and main pushes. PR67's trigger tests independently guard this.
        header = source.split("\nconcurrency:", 1)[0]
        self.assertIn("on:\n  pull_request:\n  push:\n", header)
        self.assertIn("      - main\n", header)
        self.assertNotIn("paths:", header)


if __name__ == "__main__":
    unittest.main()
