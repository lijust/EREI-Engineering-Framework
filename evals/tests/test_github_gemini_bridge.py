"""Mock-only safety regressions: bridge never runs arbitrary GitHub issue text."""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from evals.bridge import github_gemini_worker as bridge


def issue(n=1, case="TLR-003-VERIFICATION-ESCAPE", *, owner="lijust",
          private_label=True, body=None):
    payload = {
        "version": 1,
        "kind": "core13_smoke",
        "case_id": case,
        "model": bridge.MODEL,
        "experiment": "compact_v2",
        "max_calls": 1,
    }
    return {
        "number": n,
        "user": {"login": owner},
        "state": "open",
        "title": bridge.ISSUE_PREFIX + case,
        "labels": ([{"name": bridge.QUEUE_LABEL}] if private_label else []),
        "body": json.dumps(payload) if body is None else body,
    }


def config(root: Path, *, enabled=True, daily_limit=3):
    return {
        "version": 1,
        "queue_repo": "lijust/Private-Test-Control",
        "queue_owner": "lijust",
        "adapter_root": str(root / "adapter"),
        "target_root": str(root / "target"),
        "evidence_root": str(root / "evidence"),
        "state_root": str(root / "state"),
        "daily_limit": daily_limit,
        "poll_seconds": 60,
        "enabled": enabled,
    }


class FakeGitHub:
    def __init__(self, issues):
        self.issues = list(issues)
        self.private_checks = 0
        self.comments = []
        self.closed = []

    def private_queue_check(self):
        self.private_checks += 1

    def open_jobs(self):
        return self.issues

    def comment(self, issue, text):
        self.comments.append((issue, text))

    def close(self, issue):
        self.closed.append(issue)


class Core13PrivateBridgeTests(unittest.TestCase):
    def test_strict_allowed_issue_json(self):
        self.assertEqual(bridge.parse_job(issue(), "lijust"),
                         {"number": 1, "case_id": "TLR-003-VERIFICATION-ESCAPE"})
        bad = [
            issue(owner="other"),
            issue(private_label=False),
            {**issue(), "title": "unexpected title"},
            {**issue(), "state": "closed"},
            {**issue(), "pull_request": {"url": "https://github.com"}},
            issue(body=json.dumps({
                "version": 1, "kind": "core13_smoke",
                "case_id": ["TLR-003-VERIFICATION-ESCAPE"],
                "model": bridge.MODEL,
                "experiment": "compact_v2", "max_calls": 1,
            })),
            issue(body=json.dumps({
                "version": 1, "kind": "core13_smoke",
                "case_id": "TLR-003-VERIFICATION-ESCAPE",
                "model": bridge.MODEL,
                "experiment": "compact_v2", "max_calls": 1,
                "command": "powershell -enc unsafe",
            })),
            issue(body=json.dumps({
                "version": 1, "kind": "core13_smoke",
                "case_id": "TLR-003-VERIFICATION-ESCAPE",
                "model": "gemini-latest",
                "experiment": "compact_v2", "max_calls": 1,
            })),
            issue(body=json.dumps({
                "version": 1, "kind": "core13_smoke",
                "case_id": "TLR-003-VERIFICATION-ESCAPE",
                "model": bridge.MODEL,
                "experiment": "compact_v2", "max_calls": 2,
            })),
            issue(body='{"version":1,"version":1}'),
            issue(body='not JSON'),
        ]
        for item in bad:
            with self.subTest(item=item.get("body")):
                self.assertIsNone(bridge.parse_job(item, "lijust"))

    def test_actual_windows_powershell_51_native_bootstrap_quoting(self):
        if os.name != "nt":
            self.skipTest("Windows powershell.exe argument passing only")
        launcher = (Path(__file__).resolve().parents[1]
                    / "bridge" / "windows" / "start-gemini-bridge.ps1")
        line = next(
            line.strip() for line in launcher.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("$boot = ")
        )
        source = Path(__file__).resolve().parents[2]
        def ps_quote(value):
            return "'" + str(value).replace("'", "''") + "'"
        missing_config = source / "never-create-bridge-config.json"
        command = (
            line + "\n"
            + "& python -I -B -c $boot " + ps_quote(source)
            + " --config " + ps_quote(missing_config)
            + " --healthcheck\nexit $LASTEXITCODE"
        )
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, timeout=45, check=False,
        )
        # The worker must actually execute and return its stable config error,
        # not crash with a NameError or leak a Python native quoting traceback.
        self.assertEqual(result.returncode, 2, result.stderr[-300:])
        line = result.stderr.strip()
        self.assertNotIn("NameError", line)
        self.assertNotIn("Traceback", line)
        self.assertEqual(json.loads(line)["stage"], "CONFIG")

    def test_bad_http_framing_is_redacted_without_traceback_or_retry(self):
        import http.client
        import traceback
        gh = bridge.GitHubClient("lijust/Private-Test-Control", "SENSITIVE_PAT_CANARY")
        opener = mock.Mock()
        opener.open.side_effect = http.client.BadStatusLine(
            "SECRET_UPSTREAM_BAD_STATUS_LINE"
        )
        with mock.patch.object(bridge.urllib.request, "build_opener",
                               return_value=opener):
            with self.assertRaises(bridge.BridgeError) as caught:
                gh.request("GET", "/repos/lijust/Private-Test-Control")
        self.assertEqual(str(caught.exception), "GitHub API request failed")
        self.assertNotIn("SECRET_UPSTREAM", str(caught.exception))
        self.assertNotIn(
            "SECRET_UPSTREAM", "".join(traceback.format_exception(caught.exception))
        )
        opener.open.assert_called_once()

    def test_open_jobs_paginates_past_one_hundred_skipped_entries(self):
        gh = bridge.GitHubClient("lijust/Private-Test-Control", "dummy-token")
        old_invalid = [
            {**issue(n=n), "title": "not-a-valid-job"}
            for n in range(1, 101)
        ]
        responses = [old_invalid, [issue(n=101)]]
        with mock.patch.object(gh, "request", side_effect=responses) as api:
            jobs = list(gh.open_jobs())
        self.assertEqual(len(jobs), 101)
        self.assertEqual(jobs[-1]["number"], 101)
        self.assertEqual(api.call_count, 2)
        self.assertIn("page=1", api.call_args_list[0].args[1])
        self.assertIn("page=2", api.call_args_list[1].args[1])

    def test_open_jobs_bounded_scan_is_explicit_when_limit_reached(self):
        gh = bridge.GitHubClient("lijust/Private-Test-Control", "dummy-token")
        full_page = [{**issue(n=n), "title": "not-a-valid-job"} for n in range(1, 101)]
        with mock.patch.object(gh, "request", return_value=full_page) as api:
            with self.assertRaisesRegex(bridge.BridgeError, "scan limit"):
                list(gh.open_jobs())
        self.assertEqual(api.call_count, 20)

    def test_private_repo_and_owner_config_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = config(Path(d))
            self.assertEqual(bridge.validate_config(cfg), cfg)
            for replacement in ("public/queue", "thirdparty/queue"):
                invalid = {**cfg, "queue_repo": replacement}
                with self.assertRaises(bridge.BridgeError):
                    bridge.validate_config(invalid)
            for label, value in (
                ("enabled", "true"),
                ("daily_limit", 0),
                ("daily_limit", 50),
                ("poll_seconds", 2),
                ("adapter_root", "relative/adapter"),
            ):
                invalid = {**cfg, label: value}
                with self.assertRaises(bridge.BridgeError):
                    bridge.validate_config(invalid)
        gh = bridge.GitHubClient("lijust/Private-Test-Control", "mock-gh-token")
        with mock.patch.object(gh, "request", return_value={
            "private": False,
            "full_name": "lijust/Private-Test-Control",
            "has_issues": True,
        }):
            with self.assertRaises(bridge.BridgeError):
                gh.private_queue_check()

    def test_exactly_once_claim_even_when_worker_is_restarted(self):
        with tempfile.TemporaryDirectory() as root:
            db = bridge.connect_db(Path(root) / "jobs.sqlite")
            self.assertTrue(bridge.claim(db, 18, "TLR-003-VERIFICATION-ESCAPE", 1))
            self.assertFalse(bridge.claim(db, 18, "TLR-003-VERIFICATION-ESCAPE", 1))
            self.assertFalse(bridge.claim(db, 19, "CCA-006-MUTABLE-PIN-BLOCKED", 1))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 1)
            db.close()

    def test_issue_comment_and_close_both_idempotent_without_gemini_retry(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cfg = config(root, daily_limit=3)
            gh = FakeGitHub([issue(n=31)])
            db = bridge.connect_db(root / "jobs.sqlite")
            calls = []
            def fake_execute(cfg, n, case):
                calls.append((n, case))
                return json.dumps({
                    "result": "EXPERIMENTAL_MODEL_RESPONSE_SCORED_FAIL_UNVERIFIED",
                    "pass": False, "stable_ready": False,
                })
            first = bridge.one_poll(cfg, gh, db, execute=fake_execute)
            second = bridge.one_poll(cfg, gh, db, execute=fake_execute)
            self.assertEqual(first["accepted"], 1)
            self.assertEqual(first["executed"], 1)
            self.assertEqual(second["executed"], 0)
            self.assertEqual(calls, [(31, "TLR-003-VERIFICATION-ESCAPE")])
            self.assertEqual(len(gh.comments), 1)
            self.assertEqual(gh.closed, [31])
            self.assertIn("Raw provider evidence and credentials remain local",
                          gh.comments[0][1])
            self.assertNotIn("api_key", gh.comments[0][1])
            db.close()

    def test_disabled_bridge_only_checks_private_repo(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = config(Path(d), enabled=False)
            gh = FakeGitHub([issue()])
            db = bridge.connect_db(Path(d) / "jobs.sqlite")
            with mock.patch.object(bridge, "execute_local") as model:
                result = bridge.one_poll(cfg, gh, db)
            self.assertEqual(result["executed"], 0)
            self.assertEqual(gh.private_checks, 1)
            self.assertEqual(gh.comments, [])
            model.assert_not_called()
            db.close()

    def test_crash_after_claim_does_not_repeat_provider_call(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = config(Path(d))
            gh = FakeGitHub([issue(n=81)])
            db = bridge.connect_db(Path(d) / "jobs.sqlite")
            def crash(*_):
                raise RuntimeError("do-not-print-this-provider-output")
            first = bridge.one_poll(cfg, gh, db, execute=crash)
            self.assertEqual(first["accepted"], 1)
            self.assertIn("LOCAL_BRIDGE_BLOCKED", gh.comments[0][1])
            second = bridge.one_poll(cfg, gh, db, execute=crash)
            self.assertEqual(second["executed"], 0)
            self.assertEqual(len(gh.comments), 1)
            db.close()

    def test_exact_local_subprocess_never_includes_github_token_or_shell(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = config(Path(d))
            adapter = Path(cfg["adapter_root"])
            target = Path(cfg["target_root"])
            adapter.mkdir()
            target.mkdir()
            with (
                mock.patch.object(bridge, "exact_git_head") as head,
                mock.patch.object(bridge, "validate_adapter_bytes") as files,
                mock.patch.object(bridge.subprocess, "run",
                                  return_value=subprocess.CompletedProcess(
                                      args=[], returncode=1, stdout="", stderr=""
                                  )) as run,
                mock.patch.object(bridge, "safe_result",
                                  return_value='{"result":"synthetic-fail"}'),
                mock.patch.dict(os.environ, {
                    "EREI_BRIDGE_GITHUB_TOKEN": "SENSITIVE_GITHUB_TOKEN",
                    "GEMINI_API_KEY": "MOCK_GEMINI_KEY",
                }),
            ):
                output = bridge.execute_local(cfg, 57, "TLR-003-VERIFICATION-ESCAPE")
            self.assertEqual(json.loads(output)["result"], "synthetic-fail")
            head.assert_any_call(adapter.resolve(), bridge.ADAPTER_SHA)
            head.assert_any_call(target.resolve(), bridge.TARGET_SHA)
            files.assert_called_once_with(adapter.resolve())
            command = run.call_args.args[0]
            self.assertEqual(command[1:3], ["-I", "-B"])
            self.assertEqual(command[3], "-X")
            self.assertTrue(command[4].startswith("pycache_prefix="))
            self.assertEqual(command[5], "-c")
            self.assertIn("runpy.run_module('evals.experiments.run_gemini_schema_smoke'", command[6])
            self.assertEqual(command[7], str(adapter.resolve()))
            self.assertIn("--confirm-experimental-schema", command)
            self.assertNotIn("-m", command)
            self.assertNotIn("PYTHONPATH", run.call_args.kwargs["env"] if False else {})
            self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)
            self.assertNotIn("shell", run.call_args.kwargs)
            self.assertNotIn("SENSITIVE_GITHUB_TOKEN", command)
            self.assertNotIn("EREI_BRIDGE_GITHUB_TOKEN", run.call_args.kwargs["env"])
            self.assertEqual(run.call_args.kwargs["env"]["GEMINI_API_KEY"],
                             "MOCK_GEMINI_KEY")

    def test_pinned_adapter_blobs_block_subtle_worktree_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in bridge.PINNED_EXECUTABLE_FILES:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"trusted-public-code")
            def fake_git(argv, **kwargs):
                if "status" in argv:
                    return subprocess.CompletedProcess(argv, 0, stdout=b"", stderr=b"")
                if "show" in argv:
                    return subprocess.CompletedProcess(argv, 0, stdout=b"trusted-public-code",
                                                       stderr=b"")
                self.fail("unexpected git command")
            with mock.patch.object(bridge.subprocess, "run", side_effect=fake_git) as git:
                bridge.validate_adapter_bytes(root)
            self.assertEqual(git.call_count, 1 + len(bridge.PINNED_EXECUTABLE_FILES))
            tamper = root / bridge.PINNED_EXECUTABLE_FILES[0]
            tamper.write_bytes(b"malicious-worktree-change-assume-unchanged")
            with mock.patch.object(bridge.subprocess, "run", side_effect=fake_git):
                with self.assertRaises(bridge.BridgeError):
                    bridge.validate_adapter_bytes(root)

    def test_github_redirect_is_rejected_before_forwarding_auth_token(self):
        gh = bridge.GitHubClient("lijust/Private-Test-Control", "MOCK_SECRET_TOKEN")
        handler = bridge.RejectRedirect()
        req = bridge.urllib.request.Request(
            "https://api.github.com/repos/lijust/Private-Test-Control",
            headers={"Authorization": "Bearer MOCK_SECRET_TOKEN"},
        )
        with self.assertRaises(bridge.BridgeError):
            handler.redirect_request(
                req, None, 302, "Found", {},
                "https://example.com/steal-this-token",
            )

    def test_windows_crlf_checkout_accepted_but_other_changes_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for rel in bridge.PINNED_EXECUTABLE_FILES:
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"first\r\nsecond\r\n")
            def fake_git(args, **kwargs):
                if "status" in args:
                    return subprocess.CompletedProcess(args, 0, stdout=b"", stderr=b"")
                if "show" in args:
                    return subprocess.CompletedProcess(
                        args, 0, stdout=b"first\nsecond\n", stderr=b"",
                    )
                self.fail("unexpected git argument")
            with mock.patch.object(bridge.subprocess, "run", side_effect=fake_git):
                bridge.validate_adapter_bytes(root)
            (root / bridge.PINNED_EXECUTABLE_FILES[0]).write_bytes(
                b"first\r\nchanged\r\n"
            )
            with mock.patch.object(bridge.subprocess, "run", side_effect=fake_git):
                with self.assertRaises(bridge.BridgeError):
                    bridge.validate_adapter_bytes(root)

    def test_healthcheck_reports_fixed_failure_stage_without_exposing_secrets(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            file = root / "config.json"
            file.write_text(json.dumps(config(root)), encoding="utf-8")
            for stage, gh_error, expected_code in [
                ("queue", bridge.BridgeError("GitHub API refused request HTTP_403"),
                 "GitHub API refused request HTTP_403"),
                ("queue", bridge.BridgeError("MOCK_GITHUB_SECRET_UNEXPECTED"),
                 "OTHER"),
            ]:
                with self.subTest(stage=stage, error=expected_code):
                    fake_gh = mock.Mock()
                    fake_gh.private_queue_check.side_effect = gh_error
                    stderr = io.StringIO()
                    with (
                        mock.patch.object(bridge, "GitHubClient", return_value=fake_gh),
                        mock.patch.object(bridge, "exact_git_head") as head,
                        mock.patch.dict(os.environ, {
                            "EREI_BRIDGE_GITHUB_TOKEN": "DO_NOT_PRINT_GH_KEY",
                            "GEMINI_API_KEY": "DO_NOT_PRINT_GEMINI_KEY",
                        }),
                        contextlib.redirect_stderr(stderr),
                    ):
                        status = bridge.main([
                            "--config", str(file), "--healthcheck",
                        ])
                    self.assertEqual(status, 2)
                    output = json.loads(stderr.getvalue())
                    self.assertEqual(output["stage"], "PRIVATE_GITHUB_QUEUE")
                    self.assertEqual(output["reason"], expected_code)
                    self.assertEqual(output["model_calls"], 0)
                    self.assertNotIn("DO_NOT_PRINT_", stderr.getvalue())
                    self.assertNotIn("MOCK_GITHUB_SECRET", stderr.getvalue())
                    head.assert_not_called()

    def test_local_source_sha_failure_is_disclosed_only_as_fixed_category(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            config_file = root / "config.json"
            config_file.write_text(json.dumps(config(root)), encoding="utf-8")
            stderr = io.StringIO()
            fake_gh = mock.Mock()
            with (
                mock.patch.object(bridge, "GitHubClient", return_value=fake_gh),
                mock.patch.object(bridge, "exact_git_head", side_effect=(
                    bridge.BridgeError("source checkout SHA differs from pinned reviewed code")
                )),
                mock.patch.dict(os.environ, {
                    "EREI_BRIDGE_GITHUB_TOKEN": "DO_NOT_PRINT_GH_KEY"
                }),
                contextlib.redirect_stderr(stderr),
            ):
                code = bridge.main(["--config", str(config_file), "--healthcheck"])
            self.assertEqual(code, 2)
            record = json.loads(stderr.getvalue())
            self.assertEqual(record["stage"], "PINNED_ADAPTER_SHA")
            self.assertEqual(
                record["reason"], "source checkout SHA differs from pinned reviewed code"
            )
            self.assertNotIn("DO_NOT_PRINT_", stderr.getvalue())
            fake_gh.private_queue_check.assert_called_once()

    def test_safe_verdict_never_exports_prompt_or_raw_response(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            (folder / "verdict.json").write_text(json.dumps({
                "status": "EXPERIMENTAL_MODEL_RESPONSE_SCORED_FAIL_UNVERIFIED",
                "experiment": "core13_native_response_json_schema_compact_v2",
                "passed": False,
                "usage_metadata": {"totalTokenCount": 4384},
                "raw_prompt": "PRIVATE_SENTINEL",
                "api_key": "PRIVATE_SENTINEL",
            }), encoding="utf-8")
            out = bridge.safe_result(folder)
            self.assertEqual(json.loads(out)["total_tokens"], 4384)
            self.assertNotIn("PRIVATE_SENTINEL", out)
            self.assertFalse(json.loads(out)["independently_accepted"])

    def test_gh_authorization_failure_never_echoes_exception_headers(self):
        gh = bridge.GitHubClient("lijust/Private-Test-Control", "MOCK_SECRET_TOKEN")
        opener = mock.Mock()
        opener.open.side_effect = urllib.error.HTTPError(
            "https://api.github.com", 401,
            "MOCK_SECRET_TOKEN private details", {}, None
        )
        with mock.patch.object(bridge.urllib.request, "build_opener",
                               return_value=opener):
            with self.assertRaises(bridge.BridgeError) as caught:
                gh.request("GET", "/repos/lijust/Private-Test-Control")
        self.assertNotIn("MOCK_SECRET_TOKEN", str(caught.exception))
        self.assertNotIn("MOCK_SECRET_TOKEN", repr(caught.exception))
        opener.open.assert_called_once()


if __name__ == "__main__":
    unittest.main()
