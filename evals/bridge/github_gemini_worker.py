#!/usr/bin/env python3
"""Private GitHub-issue -> Windows-local Gemini Core13 bridge.

Only owner-created allowlisted JSON issues are executable. No remote shell,
workflow dispatch, plugin command, arbitrary prompt, or configurable endpoint.
All raw provider receipts remain on Windows. This bridge is *not* enabled by
opening the public-source PR; it requires a separate owner-local installation.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

QUEUE_LABEL = "erei-gemini-run"
ISSUE_PREFIX = "EREI-GEMINI "
MODEL = "gemini-3.5-flash-lite"
EXPERIMENT = "compact_v2"
BRIDGE_VERSION = 1
# This is the exact separately Codex-reviewed and CI-verified PR105 revision.
# Upgrades require a reviewed code/config change, not a GitHub issue field.
ADAPTER_SHA = "ecfc2818598e4631166bd3dec2774cb8178d0e10"
TARGET_SHA = "31d4e518b9e71a9585df9097e7ca07a7e25af916"
CASES = frozenset({
    "TLR-001-SUCCESS-STILL-LEARNING-DATA",
    "TLR-002-EXPLANATION-NO-EVENT",
    "TLR-003-VERIFICATION-ESCAPE",
    "TLR-004-TWENTY-MATERIAL-TASKS",
    "TLR-005-REPEATED-FEEDBACK",
    "TLR-006-PRIVATE-REASONING",
    "TLR-007-REVIEW-NOT-SELF-MODIFICATION",
    "CCA-001-PRESENCE-IS-NOT-ACTIVATION",
    "CCA-002-EXACT-BOUNDED-ADOPTION",
    "CCA-003-PIN-UPGRADE-DOES-NOT-ACTIVATE",
    "CCA-004-EXPIRED-OR-MISMATCHED",
    "CCA-005-STABLE-NEEDS-NO-CANDIDATE-RECORD",
    "CCA-006-MUTABLE-PIN-BLOCKED",
})
VERDICTS = frozenset({
    "EXPERIMENTAL_MODEL_RESPONSE_SCORED_PASS_UNVERIFIED",
    "EXPERIMENTAL_MODEL_RESPONSE_SCORED_FAIL_UNVERIFIED",
    "EXPERIMENTAL_MODEL_RESPONSE_INVALID_UNVERIFIED",
    "EXPERIMENTAL_MODEL_REQUEST_FAILED_NOT_SCORED",
})
REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SAFE_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_.:-]{1,100}$")


class BridgeError(Exception):
    """Controlled errors only. Never include tokens, raw responses, or prompts."""


def utc_day() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def _strict_object(pairs: list[tuple[str, object]]) -> dict:
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def strict_json(value: str | bytes):
    return json.loads(value, object_pairs_hook=_strict_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def validate_config(raw: dict) -> dict:
    if not isinstance(raw, dict) or set(raw) != {
        "version", "queue_repo", "queue_owner", "adapter_root",
        "target_root", "evidence_root", "state_root",
        "daily_limit", "poll_seconds", "enabled",
    }:
        raise BridgeError("invalid bridge config keys")
    if raw["version"] != 1 or type(raw["enabled"]) is not bool:
        raise BridgeError("invalid bridge config version/status")
    repo = raw["queue_repo"]
    owner = raw["queue_owner"]
    if (not isinstance(repo, str) or not REPO_PATTERN.fullmatch(repo)
            or not isinstance(owner, str) or repo.split("/")[0] != owner
            or owner != "lijust"):
        raise BridgeError("queue repository must be an approved owner's private repository")
    if type(raw["daily_limit"]) is not int or not 1 <= raw["daily_limit"] <= 10:
        raise BridgeError("daily limit must be between 1 and 10")
    if type(raw["poll_seconds"]) is not int or not 30 <= raw["poll_seconds"] <= 3600:
        raise BridgeError("poll seconds must be between 30 and 3600")
    for key in ("adapter_root", "target_root", "evidence_root", "state_root"):
        if not isinstance(raw[key], str) or not Path(raw[key]).is_absolute():
            raise BridgeError("invalid absolute local path")
    paths = [Path(raw[k]).expanduser().resolve() for k in (
        "adapter_root", "target_root", "evidence_root", "state_root",
    )]
    adapter, target, evidence, state = paths
    if adapter == target or evidence in (adapter, target) or state in (adapter, target):
        raise BridgeError("bridge evidence/state cannot equal code checkout")
    if any(root in candidate.parents for root in (adapter, target)
           for candidate in (evidence, state)):
        raise BridgeError("state/evidence cannot live under code checkout")
    if evidence == state or evidence in state.parents or state in evidence.parents:
        raise BridgeError("state and evidence directories must be independent")
    return raw


def exact_git_head(root: Path, expected: str) -> None:
    if not root.is_dir() or root.is_symlink():
        raise BridgeError("missing or symlinked local source worktree")
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            check=True, timeout=10, env={
                k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")
            },
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise BridgeError("source checkout identity unavailable") from None
    if proc.stdout.strip() != expected:
        raise BridgeError("source checkout SHA differs from pinned reviewed code")


def parse_job(issue: dict, owner: str) -> dict | None:
    """Strictly no commands, URLs, custom models, freeform prompts, or scripts."""
    if not isinstance(issue, dict) or "pull_request" in issue:
        return None
    user = issue.get("user")
    labels = issue.get("labels")
    if (not isinstance(user, dict) or user.get("login") != owner
            or not isinstance(labels, list) or not any(
                isinstance(l, dict) and l.get("name") == QUEUE_LABEL for l in labels
            ) or issue.get("state") != "open"):
        return None
    title = issue.get("title")
    if not isinstance(title, str) or not title.startswith(ISSUE_PREFIX):
        return None
    try:
        job = strict_json(issue.get("body", ""))
    except (ValueError, TypeError):
        return None
    if not isinstance(job, dict) or set(job) != {
        "version", "kind", "case_id", "model", "experiment", "max_calls",
    }:
        return None
    if (type(job["version"]) is not int or job["version"] != BRIDGE_VERSION
            or job["kind"] != "core13_smoke"
            or not isinstance(job["case_id"], str) or job["case_id"] not in CASES
            or job["model"] != MODEL
            or job["experiment"] != EXPERIMENT
            or type(job["max_calls"]) is not int or job["max_calls"] != 1
            or title != ISSUE_PREFIX + job["case_id"]):
        return None
    number = issue.get("number")
    if type(number) is not int or number <= 0:
        return None
    return {"number": number, "case_id": job["case_id"]}


class RejectRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise BridgeError("GitHub API redirect denied")


class GitHubClient:
    def __init__(self, repo: str, token: str):
        if not token or any(ch in token for ch in "\r\n\x00") or not token.isascii():
            raise BridgeError("invalid local GitHub token")
        self.repo = repo
        self.token = token

    def request(self, method: str, relative: str, data: dict | None = None):
        if not relative.startswith("/") or relative.startswith("//"):
            raise BridgeError("GitHub API relative path rejected")
        payload = (json.dumps(data, sort_keys=True).encode("utf-8")
                   if data is not None else None)
        req = urllib.request.Request(
            "https://api.github.com" + relative,
            data=payload,
            method=method,
            headers={
                "Authorization": "Bearer " + self.token,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "EREI-Gemini-LocalBridge/1",
                **({"Content-Type": "application/json"} if payload is not None else {}),
            },
        )
        try:
            with urllib.request.build_opener(RejectRedirect()).open(req, timeout=20) as rsp:
                body = rsp.read(2_000_001)
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError, BridgeError):
            # Never render original HTTP exceptions: GitHub authorization and
            # upstream messages can include private tokens or request bodies.
            raise BridgeError("GitHub API request failed") from None
        if len(body) > 2_000_000:
            raise BridgeError("GitHub response too large")
        try:
            return strict_json(body) if body else {}
        except (TypeError, ValueError):
            raise BridgeError("GitHub response format invalid") from None

    def private_queue_check(self) -> None:
        data = self.request("GET", f"/repos/{self.repo}")
        if not isinstance(data, dict) or data.get("private") is not True:
            raise BridgeError("queue repository must be PRIVATE; refuse all requests")
        if data.get("full_name", "").lower() != self.repo.lower():
            raise BridgeError("queue repository identity mismatch")
        if data.get("has_issues") is not True:
            raise BridgeError("queue GitHub issues must be enabled")

    def open_jobs(self) -> list:
        label = urllib.parse.quote(QUEUE_LABEL)
        path = (f"/repos/{self.repo}/issues?state=open&labels={label}"
                "&sort=created&direction=asc&per_page=30")
        issues = self.request("GET", path)
        if not isinstance(issues, list):
            raise BridgeError("GitHub queue list format invalid")
        return issues

    def comment(self, issue: int, text: str) -> None:
        self.request("POST", f"/repos/{self.repo}/issues/{issue}/comments", {"body": text})

    def close(self, issue: int) -> None:
        self.request("PATCH", f"/repos/{self.repo}/issues/{issue}", {"state": "closed"})


def connect_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path), timeout=20, isolation_level=None)
    db.execute("PRAGMA busy_timeout=20000")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
          issue INTEGER PRIMARY KEY,
          case_id TEXT NOT NULL,
          captured_day TEXT NOT NULL,
          state TEXT NOT NULL,
          outcome TEXT,
          comment_sent INTEGER NOT NULL DEFAULT 0,
          closed INTEGER NOT NULL DEFAULT 0
        )""")
    return db


def claim(db: sqlite3.Connection, issue: int, case_id: str, limit: int) -> bool:
    """Reserve budget BEFORE any HTTP/model call; never retry after crash."""
    db.execute("BEGIN IMMEDIATE")
    try:
        if db.execute("SELECT 1 FROM jobs WHERE issue=?", (issue,)).fetchone():
            db.execute("COMMIT")
            return False
        used = db.execute("SELECT COUNT(*) FROM jobs WHERE captured_day=?",
                          (utc_day(),)).fetchone()[0]
        if used >= limit:
            db.execute("COMMIT")
            return False
        db.execute("INSERT INTO jobs(issue,case_id,captured_day,state)"
                   " VALUES(?,?,?,?)",
                   (issue, case_id, utc_day(), "CLAIMED"))
        db.execute("COMMIT")
        return True
    except Exception:
        db.execute("ROLLBACK")
        raise


def safe_result(folder: Path) -> str:
    """Only finite enumerated results; raw provider response never leaves disk."""
    fail = folder / "attempt-failed.json"
    verdict = folder / "verdict.json"
    result = {"result": "NOT_SCORED", "reason": "NO_VERDICT"}
    if fail.exists() and not fail.is_symlink():
        try:
            a = strict_json(fail.read_bytes())
            reason = a.get("reason_category")
            if (a.get("status") == "EXPERIMENTAL_MODEL_REQUEST_FAILED_NOT_SCORED"
                    and isinstance(reason, str) and SAFE_KEY_PATTERN.fullmatch(reason)):
                return json.dumps({
                    "result": "NOT_SCORED",
                    "reason": reason,
                    "http_status": (a.get("provider_http_status")
                                    if a.get("provider_http_status") in (400, 401, 403, 404, 429, 500, 502, 503, 504)
                                    else None),
                }, sort_keys=True)
        except (OSError, ValueError, TypeError, AttributeError):
            pass
        return json.dumps(result, sort_keys=True)
    if verdict.exists() and not verdict.is_symlink():
        try:
            v = strict_json(verdict.read_bytes())
            status = v.get("status")
            if status in VERDICTS and v.get("experiment") == (
                    "core13_native_response_json_schema_compact_v2"):
                used = v.get("usage_metadata")
                tokens = used.get("totalTokenCount") if isinstance(used, dict) else None
                return json.dumps({
                    "result": status,
                    "pass": v.get("passed") is True,
                    "total_tokens": tokens if type(tokens) is int and 0 <= tokens <= 1_000_000 else None,
                    "independently_accepted": False,
                    "stable_ready": False,
                }, sort_keys=True)
        except (OSError, ValueError, TypeError):
            pass
    return json.dumps(result, sort_keys=True)


def execute_local(config: dict, issue: int, case_id: str) -> str:
    """Exactly ONE reviewed command, fixed args; subprocess without shell."""
    adapter = Path(config["adapter_root"]).resolve()
    target = Path(config["target_root"]).resolve()
    exact_git_head(adapter, ADAPTER_SHA)
    exact_git_head(target, TARGET_SHA)
    folder = Path(config["evidence_root"]).resolve() / f"github-issue-{issue:07d}"
    if folder.exists():
        # If a job has an existing evidence path, never overwrite or re-run it.
        raise BridgeError("immutable issue receipt already exists")
    env = dict(os.environ)
    env.pop("EREI_BRIDGE_GITHUB_TOKEN", None)
    # Gemini token remains in local child process only; never in argv.
    cmd = [
        sys.executable, "-m", "evals.experiments.run_gemini_schema_smoke",
        "--model", MODEL, "--target-root", str(target),
        "--case-id", case_id, "--output-dir", str(folder),
        "--timeout", "90", "--live", "--confirm-free-tier",
        "--confirm-experimental-schema",
    ]
    try:
        proc = subprocess.run(
            cmd, cwd=str(adapter), env=env, capture_output=True,
            text=True, stdin=subprocess.DEVNULL, timeout=150, check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return json.dumps({"result": "NOT_SCORED", "reason": "LOCAL_PROCESS_ERROR"})
    # Never forward child stdout/stderr (may include model/provider text).
    status = safe_result(folder)
    if proc.returncode not in (0, 1, 2):
        return json.dumps({"result": "NOT_SCORED", "reason": "UNEXPECTED_EXIT"})
    return status


def publish_unposted(db: sqlite3.Connection, gh: GitHubClient) -> None:
    rows = db.execute(
        "SELECT issue, outcome, comment_sent, closed FROM jobs "
        "WHERE state='FINISHED' AND (comment_sent=0 OR closed=0) "
        "ORDER BY issue LIMIT 30"
    ).fetchall()
    for issue, outcome, commented, closed in rows:
        if not commented:
            gh.comment(issue, "EREI Gemini Bridge result (synthetic/public, unverified):\n\n"
                       + "```json\n" + outcome + "\n```\n\n"
                       "Raw provider evidence and credentials remain local.")
            db.execute("UPDATE jobs SET comment_sent=1 WHERE issue=?", (issue,))
        if not closed:
            gh.close(issue)
            db.execute("UPDATE jobs SET closed=1 WHERE issue=?", (issue,))


def one_poll(config: dict, gh: GitHubClient, db: sqlite3.Connection, *,
             execute=execute_local) -> dict:
    gh.private_queue_check()  # Fail closed if queue becomes public.
    publish_unposted(db, gh)
    totals = {"queued": 0, "accepted": 0, "executed": 0, "skipped": 0}
    if not config["enabled"]:
        return totals
    for issue in gh.open_jobs():
        totals["queued"] += 1
        job = parse_job(issue, config["queue_owner"])
        if not job:
            totals["skipped"] += 1
            continue
        n = job["number"]
        if not claim(db, n, job["case_id"], config["daily_limit"]):
            continue
        totals["accepted"] += 1
        try:
            outcome = execute(config, n, job["case_id"])
        except Exception:
            outcome = json.dumps({
                "result": "NOT_SCORED", "reason": "LOCAL_BRIDGE_BLOCKED"
            }, sort_keys=True)
        # No local retry even if the worker crashes after CLAIMED.
        db.execute("UPDATE jobs SET state='FINISHED', outcome=? WHERE issue=?",
                   (outcome, n))
        totals["executed"] += 1
        publish_unposted(db, gh)
    return totals


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--once", action="store_true",
                        help="single poll; cannot bypass real job authorization")
    parser.add_argument("--healthcheck", action="store_true",
                        help="read-only repo/privacy/source checks, no model call")
    args = parser.parse_args(argv)
    try:
        config = validate_config(strict_json(args.config.read_bytes()))
        token = os.environ.get("EREI_BRIDGE_GITHUB_TOKEN", "")
        if not os.environ.get("GEMINI_API_KEY") and not args.healthcheck:
            raise BridgeError("Gemini key unavailable on local machine")
        gh = GitHubClient(config["queue_repo"], token)
        gh.private_queue_check()
        exact_git_head(Path(config["adapter_root"]), ADAPTER_SHA)
        exact_git_head(Path(config["target_root"]), TARGET_SHA)
        if args.healthcheck:
            print(json.dumps({
                "status": "PRIVATE_QUEUE_AND_PINNED_SOURCE_VERIFIED",
                "enabled": config["enabled"], "model_calls": 0,
                "queue_private": True,
            }))
            return 0
        db = connect_db(Path(config["state_root"]) / "requests.sqlite3")
        if args.once:
            print(json.dumps({"status": "ONE_POLL_COMPLETE", **one_poll(config, gh, db)}))
            return 0
        while True:
            try:
                one_poll(config, gh, db)
            except BridgeError:
                # Generic operational issues never print tokens or raw data.
                print("EREI_BRIDGE_POLL_BLOCKED", file=sys.stderr)
            time.sleep(config["poll_seconds"])
    except (BridgeError, OSError, ValueError, sqlite3.Error):
        print("EREI_BRIDGE_CONFIGURATION_OR_CONNECTION_BLOCKED", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
