"""Positive/negative retention contracts for hosted T14 synthetic rollback CI."""
import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools import t14_capture_evidence as capture

ROOT = Path(__file__).resolve().parents[2]
TARGET = "a" * 40


def valid_report():
    return {
        "evidence_kind": "LOCAL_SYNTHETIC_ROLLBACK_DRILL",
        "v1_commit": capture.V1_COMMIT,
        "v1_tool_sha256": capture.V1_SHA256,
        "isolated_checkout_ref": TARGET,
        "checkout_identity_verified": True,
        "v2_source_sha256": {
            key: hashlib.sha256((ROOT / key).read_bytes()).hexdigest()
            for key in (
                "tools/task_learning.py", "tools/validation_contract.py",
                "tools/tests/drill_task_learning_rollback.py",
            )
        },
        "tests_run": 4, "failures": 0, "errors": 0, "passed": True,
        "live_adoption": False, "internal_release_qualified": False,
    }


def subprocess_command(stdout: bytes, stderr: bytes, code: int):
    script = (
        "import sys;"
        "sys.stdout.buffer.write(" + repr(stdout) + ");"
        "sys.stderr.buffer.write(" + repr(stderr) + ");"
        "sys.exit(" + str(code) + ")"
    )
    return [sys.executable, "-c", script]


class T14EvidenceCaptureTests(unittest.TestCase):
    def invoke(self, stdout, stderr=b"", code=0):
        with tempfile.TemporaryDirectory() as temp:
            evidence_dir = Path(temp) / "evidence"
            accepted = capture.capture(
                subprocess_command(stdout, stderr, code), evidence_dir, TARGET
            )
            evidence = {p.name: p.read_bytes() for p in evidence_dir.iterdir()}
        return accepted, evidence

    def test_success_preserves_full_report_and_stderr_and_explicit_boundary(self):
        report = json.dumps(valid_report()).encode("utf-8")
        accepted, evidence = self.invoke(report, b"four synthetic tests\n")
        self.assertTrue(accepted)
        self.assertEqual(evidence["drill-report.stdout.json"], report)
        self.assertEqual(evidence["drill-stderr.txt"], b"four synthetic tests\n")
        self.assertEqual(evidence["drill-exit-code.txt"], b"0\n")
        verdict = json.loads(evidence["capture-verdict.json"])
        self.assertTrue(verdict["accepted"])
        self.assertFalse(verdict["live_adoption"])
        self.assertFalse(verdict["internal_release_qualified"])
        self.assertFalse(verdict["independent_security_approval"])

    def test_failing_drill_preserves_even_partially_valid_json(self):
        report = valid_report()
        report.update({"passed": False, "failures": 1})
        output = json.dumps(report).encode("utf-8")
        accepted, evidence = self.invoke(output, b"traceback on stderr\n", 7)
        self.assertFalse(accepted)
        self.assertEqual(evidence["drill-report.stdout.json"], output)
        self.assertEqual(evidence["drill-stderr.txt"], b"traceback on stderr\n")
        self.assertEqual(evidence["drill-exit-code.txt"], b"7\n")
        self.assertFalse(json.loads(evidence["capture-verdict.json"])["accepted"])

    def test_non_json_failure_still_preserves_stderr_and_status(self):
        accepted, evidence = self.invoke(b"", b"broken before JSON\n", 9)
        self.assertFalse(accepted)
        self.assertEqual(evidence["drill-report.stdout.json"], b"")
        self.assertEqual(evidence["drill-stderr.txt"], b"broken before JSON\n")
        self.assertEqual(evidence["drill-exit-code.txt"], b"9\n")
        self.assertIn(b"nonzero", evidence["capture-verdict.json"])

    def test_success_exit_with_untrusted_metadata_is_denied_and_retained(self):
        for change in ({"isolated_checkout_ref": "b" * 40},
                       {"internal_release_qualified": True},
                       {"tests_run": 3}, {"passed": False}):
            with self.subTest(change=change):
                report = valid_report()
                report.update(change)
                accepted, evidence = self.invoke(json.dumps(report).encode())
                self.assertFalse(accepted)
                self.assertFalse(json.loads(evidence["capture-verdict.json"])["accepted"])
                self.assertEqual(evidence["drill-exit-code.txt"], b"0\n")

    def test_spawn_failure_produces_failure_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "evidence"
            self.assertFalse(capture.capture(
                [str(Path(temp) / "no-such-executable")], root, TARGET
            ))
            self.assertEqual((root / "drill-exit-code.txt").read_text(), "127\n")
            self.assertTrue((root / "drill-stderr.txt").read_bytes())
            self.assertFalse(json.loads((root / "capture-verdict.json").read_text())["accepted"])

    def test_refuse_artifacts_inside_checkout(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            capture.capture(subprocess_command(b"{}", b"", 0), ROOT / "unsafe", TARGET)

    def test_workflow_uploads_per_interpreter_even_after_failure(self):
        source = (ROOT / ".github/workflows/t14-isolated-rollback-drill.yml").read_text(encoding="utf-8")
        self.assertIn("tools/t14_capture_evidence.py", source)
        self.assertIn("actions/upload-artifact@v4", source)
        self.assertIn("always()", source)
        self.assertIn("retention-days: 14", source)
        self.assertIn("if-no-files-found: error", source)
        self.assertIn("github.run_attempt", source)
        self.assertIn("matrix.python-version", source)
        self.assertIn("persist-credentials: false", source)
        self.assertIn("runs-on: windows-latest", source)


if __name__ == "__main__":
    unittest.main()
