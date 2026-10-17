#!/usr/bin/env python3
"""Out-of-band GitHub Actions source/assurance metadata verifier (Candidate).

Does not grant runtime credentials, pin an external authority, or prove that
unprotected GitHub main cannot be bypassed. It NEVER returns Stable enforcement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPOSITORY = "lijust/EREI-Engineering-Framework"
API_ROOT = f"https://api.github.com/repos/{REPOSITORY}"
WORKFLOW_PATH = ".github/workflows/assurance-gate.yml"
RUN_NAME = "Framework Assurance Gate"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
MAX_API_BYTES = 1024 * 1024
MAX_POLICY_BYTES = 16 * 1024


class ActionsSourceError(RuntimeError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ActionsSourceError("GitHub Actions metadata redirect is forbidden")


def _request_json(url: str, token: str) -> dict[str, Any]:
    if not isinstance(token, str) or not token.strip():
        raise ActionsSourceError("independent read-only GitHub API token is required")
    if not url.startswith(API_ROOT + "/"):
        raise ActionsSourceError("GitHub Actions API endpoint outside official repository")
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "EREI-Out-of-band-Assurance-Source-v1",
    })
    try:
        with urllib.request.build_opener(_NoRedirect).open(request, timeout=15) as response:
            payload = response.read(MAX_API_BYTES + 1)
    except ActionsSourceError:
        raise
    except (OSError, urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise ActionsSourceError("authenticated GitHub Actions metadata request failed") from exc
    if len(payload) > MAX_API_BYTES:
        raise ActionsSourceError("GitHub API response exceeds allowed size")
    try:
        result = json.loads(payload)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ActionsSourceError("invalid GitHub API JSON") from exc
    if not isinstance(result, dict):
        raise ActionsSourceError("GitHub API response must be an object")
    return result


def _git_blob(repo: Path, ref: str, path: str) -> bytes:
    if not SHA40.fullmatch(ref):
        raise ActionsSourceError("target must be exact Git commit SHA")
    if path != WORKFLOW_PATH:
        raise ActionsSourceError("workflow path not in independent trusted policy")
    root = repo.resolve(strict=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_NO_LAZY_FETCH"] = "1"
    env["GIT_ALLOW_PROTOCOL"] = ""
    env["GIT_PROTOCOL_FROM_USER"] = "0"
    argv = ["git", "-C", str(root), "-c", "core.commitGraph=false", "-c", "protocol.allow=never", "-c", "protocol.ext.allow=never"]
    def git(*args: str) -> bytes:
        cp = subprocess.run([*argv, *args], env=env, capture_output=True, check=False, timeout=15)
        if cp.returncode:
            raise ActionsSourceError("cannot verify raw Git target/workflow object")
        return cp.stdout
    top = Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve(strict=True)
    if top != root:
        raise ActionsSourceError("expected independently verified Git checkout root")
    if git("rev-parse", f"{ref}^{{commit}}").decode().strip() != ref:
        raise ActionsSourceError("target ref does not resolve to exact raw commit")
    if git("for-each-ref", "--format=%(refname)", "refs/replace").strip():
        raise ActionsSourceError("Git replacement refs are forbidden")
    graft = Path(git("rev-parse", "--git-path", "info/grafts").decode().strip())
    if not graft.is_absolute():
        graft = root / graft
    if graft.exists() or graft.is_symlink():
        raise ActionsSourceError("Git grafts are forbidden")
    return git("show", f"{ref}:{path}")


def _policy(repo_root: Path, trust_file: Path, expected_sha256: str) -> dict[str, Any]:
    if not SHA256.fullmatch(expected_sha256):
        raise ActionsSourceError("external policy pin must be exact SHA256")
    root = repo_root.resolve(strict=True)
    source = trust_file.absolute()
    if ".." in source.parts:
        raise ActionsSourceError("trusted policy path cannot contain parent traversal")
    try:
        resolved = source.resolve(strict=True)
        if root == resolved or root in resolved.parents:
            raise ActionsSourceError(
                "trusted policy must be independently stored outside mutable Git checkout"
            )
        # Path.absolute and Path.resolve can legitimately differ on Windows
        # due to OS canonical casing/drive aliases. Reject actual symlinks and
        # junctions/reparse points in every path component instead of testing
        # raw pathname-string equality.
        for candidate in (source, *source.parents):
            record = candidate.lstat()
            if stat.S_ISLNK(record.st_mode) or (
                getattr(record, "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            ):
                raise ActionsSourceError(
                    "trusted policy file must not be a symlink or indirect path"
                )
        if not resolved.is_file():
            raise ActionsSourceError("trusted policy file must be a regular file")
        if resolved.stat().st_size > MAX_POLICY_BYTES:
            raise ActionsSourceError("trusted policy file exceeds size limit")
        raw = resolved.read_bytes()
    except (OSError, ValueError) as exc:
        raise ActionsSourceError("trusted policy path is unavailable") from exc
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ActionsSourceError("trusted policy does not match externally pinned hash")
    try:
        p = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ActionsSourceError("trusted policy JSON invalid") from exc
    expected = {"schema_version", "repository", "workflow_path", "workflow_sha256",
                "workflow_id", "required_job", "head_branch"}
    if not isinstance(p, dict) or set(p) != expected:
        raise ActionsSourceError("trusted policy field set mismatch")
    if type(p["schema_version"]) is not int or p["schema_version"] != 1:
        raise ActionsSourceError("unsupported trusted policy version")
    if p["repository"] != REPOSITORY or p["workflow_path"] != WORKFLOW_PATH:
        raise ActionsSourceError("trusted policy repository/workflow mismatch")
    if p["required_job"] != "assurance" or p["head_branch"] != "main":
        raise ActionsSourceError("trusted workflow/job/branch must match independent policy")
    if type(p["workflow_id"]) is not int or p["workflow_id"] < 1:
        raise ActionsSourceError("trusted GitHub workflow ID invalid")
    if not isinstance(p["workflow_sha256"], str) or not SHA256.fullmatch(p["workflow_sha256"]):
        raise ActionsSourceError("trusted workflow blob digest invalid")
    return p


def verify_source(
    repo_root: Path, policy_file: Path, expected_policy_sha256: str,
    *, target_ref: str, run_id: int, run_attempt: int, token: str,
) -> dict[str, Any]:
    """Authenticate run+job and externally pinned workflow source; never promote."""
    if not isinstance(target_ref, str) or not SHA40.fullmatch(target_ref):
        raise ActionsSourceError("target must be exact 40-hex Git commit")
    if type(run_id) is not int or run_id <= 0 or type(run_attempt) is not int or run_attempt <= 0:
        raise ActionsSourceError("run ID and attempt must be positive integers")
    policy = _policy(Path(repo_root), Path(policy_file), expected_policy_sha256)
    source = _git_blob(Path(repo_root), target_ref, policy["workflow_path"])
    if hashlib.sha256(source).hexdigest() != policy["workflow_sha256"]:
        raise ActionsSourceError("target assurance workflow source not externally pinned")
    run = _request_json(f"{API_ROOT}/actions/runs/{run_id}", token)
    # GitHub may legitimately return nested nulls; adversarial JSON can
    # contain truthy scalars here. Never allow an AttributeError to escape
    # the fail-closed ActionsSourceError contract.
    if (
        not isinstance(run.get("repository"), dict)
        or not isinstance(run.get("head_repository"), dict)
        or not isinstance(run.get("path"), str)
    ):
        raise ActionsSourceError("official Actions repository metadata malformed")
    if (
        run.get("id") != run_id or run.get("run_attempt") != run_attempt
        or run.get("workflow_id") != policy["workflow_id"]
        or run.get("name") != RUN_NAME
        # GitHub REST may report a ref-qualified path, e.g. workflow.yml@main.
        # Do not accept any other suffix, ref or pull-request variant.
        or run.get("path") not in {WORKFLOW_PATH, WORKFLOW_PATH + "@main"}
        or run.get("event") != "push" or run.get("head_branch") != "main"
        or run.get("head_sha") != target_ref or run.get("status") != "completed"
        or run.get("conclusion") != "success"
        or (run.get("repository") or {}).get("full_name") != REPOSITORY
        or (run.get("head_repository") or {}).get("full_name") != REPOSITORY
    ):
        raise ActionsSourceError("official Actions run metadata does not bind trusted workflow and target")
    jobs = _request_json(
        f"{API_ROOT}/actions/runs/{run_id}/attempts/{run_attempt}/jobs?per_page=100", token
    )
    rows = jobs.get("jobs")
    if type(jobs.get("total_count")) is not int or not isinstance(rows, list):
        raise ActionsSourceError("Actions job list malformed")
    if jobs["total_count"] != len(rows) or len(rows) != 1:
        raise ActionsSourceError("Actions job listing is incomplete or unexpected")
    job = rows[0]
    if not isinstance(job, dict) or (
        job.get("name") != policy["required_job"]
        or job.get("run_id") != run_id
        # The per-attempt URL binds the attempt; GitHub's documented job
        # representation does not always include a run_attempt field.
        or ("run_attempt" in job and job["run_attempt"] != run_attempt)
        or job.get("head_sha") != target_ref
        or job.get("status") != "completed" or job.get("conclusion") != "success"
    ):
        raise ActionsSourceError("required exact-attempt assurance job was not authenticated")
    return {
        "status": "authenticated_actions_source_metadata_only",
        "target_ref": target_ref, "run_id": run_id, "run_attempt": run_attempt,
        "policy_sha256": expected_policy_sha256, "workflow_sha256": policy["workflow_sha256"],
        "required_job": policy["required_job"],
        "stable_enforcement_satisfied": False,
        "trusted_externally_enforced_consumption": False,
        "self_hosted_runner_execution_attested": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Candidate-only external Actions source check")
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--policy-file", required=True, type=Path)
    parser.add_argument("--expected-policy-sha256", required=True)
    parser.add_argument("--target-ref", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--run-attempt", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        report = verify_source(
            args.repo_root, args.policy_file, args.expected_policy_sha256,
            target_ref=args.target_ref, run_id=args.run_id, run_attempt=args.run_attempt,
            token=os.environ.get("EREI_INDEPENDENT_GITHUB_READ_TOKEN", ""),
        )
        print(json.dumps(report, sort_keys=True))
    except (ActionsSourceError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
