"""Public unit tests for local-only, private GitHub-source export preparation.

Every response is synthetic. No GitHub authentication, API calls, or private
consumer code execution occur inside hosted public CI.
"""
from __future__ import annotations

import base64
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


MODULE = Path(__file__).resolve().parents[1] / "benchmarks/prepare_private_exports.py"
spec = importlib.util.spec_from_file_location("private_exports", MODULE)
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class PrivateExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = self.root / "public-catalog.json"
        self.data = b"source = 'immutable private test fixture'\n"
        self.git_blob = hashlib.sha1(
            b"blob " + str(len(self.data)).encode() + b"\0" + self.data
        ).hexdigest()
        self.entry = {
            "task_id": "PY-04", "state": "PUBLIC_CALIBRATION_ONLY",
            "source": {
                "repository": "lijust/EREI-3.2",
                "commit": "87d730ddc3547f863de2a6895e91f9b83e9c6e72",
                "export_directory": "py",
            },
            "files": [{"path": "core/pinned_fixture.py", "git_blob": self.git_blob}],
        }
        self.write_catalog([self.entry])

    def write_catalog(self, packages):
        self.catalog.write_text(json.dumps({
            "execution_authorized": False, "packages": packages,
        }), encoding="utf-8")

    def mock_response(self, payload=None, git_blob=None):
        return subprocess.CompletedProcess(
            [], 0,
            stdout=json.dumps({
                "type": "file", "encoding": "base64",
                "sha": git_blob or self.git_blob,
                "content": base64.b64encode(self.data if payload is None else payload).decode(),
            }).encode(),
            stderr=b"NEVER PRINT PRIVATE REPOSITORY INTERNALS",
        )

    def test_full_local_export_verifies_pin_and_is_atomic_and_private(self):
        dest = self.root / "isolated-private-exports"
        with (patch.object(exporter, "CATALOG", self.catalog),
              patch.object(exporter.subprocess, "run",
                           return_value=self.mock_response()) as runner):
            report = exporter.prepare(dest, "PY-04")
        self.assertEqual((dest / "py/core/pinned_fixture.py").read_bytes(), self.data)
        self.assertEqual(report["file_count"], 1)
        self.assertEqual(report["task"], "PY-04")
        self.assertFalse(report["private_bytes_printed"])
        self.assertEqual(report["model_executions"], 0)
        self.assertEqual(report["independent_review"], "NOT_PERFORMED")
        self.assertEqual(list(self.root.glob(".erei-private-source-*")), [])
        cmd = runner.call_args.args[0]
        self.assertEqual(cmd[1:4], ["api", "-H", "Accept: application/vnd.github+json"])
        self.assertIn("refs", repr(cmd) + " refs")  # use immutable ref below
        self.assertIn(self.entry["source"]["commit"], cmd[-1])
        self.assertNotIn("shell=True", str(runner.call_args))
        self.assertIs(runner.call_args.kwargs["shell"], False)
        self.assertEqual(runner.call_args.kwargs["timeout"], 35)

    def test_tampered_private_download_is_never_published(self):
        destination = self.root / "never-publish"
        bad = self.mock_response(payload=b"tampered source bytes")
        with (patch.object(exporter, "CATALOG", self.catalog),
              patch.object(exporter.subprocess, "run", return_value=bad),
              self.assertRaisesRegex(ValueError, "fail Git blob")):
            exporter.prepare(destination, None)
        self.assertFalse(destination.exists())
        self.assertEqual(list(self.root.glob(".erei-private-source-*")), [])

    def test_gh_failure_message_is_not_forwarded_through_entrypoint(self):
        bad = subprocess.CompletedProcess(
            [], 1, stdout=b"", stderr=b"GH_TOKEN=PRIVATE-DO-NOT-LEAK")
        stdout, stderr = io.StringIO(), io.StringIO()
        with (patch.object(exporter, "CATALOG", self.catalog),
              patch.object(exporter.subprocess, "run", return_value=bad),
              patch.object(sys, "argv", ["prepare_private_exports.py",
                                       "--destination", str(self.root / "reject")]),
              contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr)):
            self.assertEqual(exporter.main(), 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertNotIn("PRIVATE-DO-NOT-LEAK", stderr.getvalue())
        self.assertEqual(json.loads(stderr.getvalue())["status"], "FAIL_CLOSED")
        self.assertFalse((self.root / "reject").exists())
        self.assertEqual(list(self.root.glob(".erei-private-source-*")), [])

    def test_disallow_checkout_relative_existing_and_unpinned_sources(self):
        with self.assertRaisesRegex(ValueError, "absolute path"):
            exporter.prepare(Path("relative-export"), None)
        with self.assertRaisesRegex(ValueError, "outside public Framework"):
            exporter.prepare(exporter.FRAMEWORK_ROOT / "private", None)
        with self.assertRaisesRegex(ValueError, "already exists"):
            exporter.prepare(self.root, None)
        with patch.object(exporter, "CATALOG", self.catalog):
            with self.assertRaisesRegex(ValueError, "Unknown or duplicate"):
                exporter.prepare(self.root / "nope", "PY-DOES-NOT-EXIST")
            for modified in (
                {**self.entry, "source": {**self.entry["source"],
                                         "repository": "third-party/unapproved"}},
                {**self.entry, "source": {**self.entry["source"],
                                         "commit": "main"}},
                {**self.entry, "files": [{"path": "../escape",
                                          "git_blob": self.git_blob}]},
            ):
                self.write_catalog([modified])
                with self.assertRaises(ValueError):
                    exporter.prepare(self.root / "reject", "PY-04")
                self.assertFalse((self.root / "reject").exists())

    def test_conflicting_same_export_path_across_recipes_fails_closed(self):
        conflict = {
            **self.entry, "task_id": "PY-05",
            "files": [{"path": "core/pinned_fixture.py", "git_blob": "a" * 40}],
        }
        self.write_catalog([self.entry, conflict])
        with patch.object(exporter, "CATALOG", self.catalog):
            with self.assertRaisesRegex(ValueError, "Conflicting"):
                exporter.prepare(self.root / "not-created", None)
        self.assertFalse((self.root / "not-created").exists())


if __name__ == "__main__":
    unittest.main()
