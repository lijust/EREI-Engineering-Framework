#!/usr/bin/env python3
"""Verify authenticated GitHub/Codex review provenance for release-control artifacts."""
from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

CODEX_REVIEWER = "chatgpt-codex-connector[bot]"
PROVIDER = "github_codex_review"
SUMMARY_RE = re.compile(r"<!-- codex-review-state:v1\s+(\{.*?\})\s+-->", re.DOTALL)
PURPOSES = {"enforcement_equivalence", "architecture_approval", "security_approval"}
SHA40_RE = re.compile(r"^[a-f0-9]{40}$")


class ReviewProvenanceError(RuntimeError):
    pass


def validate_descriptor(value: Any, *, expected_purpose: str | None = None) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReviewProvenanceError("review_provenance must be an object")
    fields = {"provider", "reviewer_login", "review_type", "purpose"}
    if set(value) != fields:
        raise ReviewProvenanceError(
            f"review_provenance fields mismatch missing={sorted(fields-set(value))} "
            f"unknown={sorted(set(value)-fields)}"
        )
    if value["provider"] != PROVIDER:
        raise ReviewProvenanceError("review_provenance.provider must be github_codex_review")
    if value["reviewer_login"] != CODEX_REVIEWER:
        raise ReviewProvenanceError("review_provenance.reviewer_login must be the configured Codex bot")
    if value["review_type"] != "code_review":
        raise ReviewProvenanceError("review_provenance.review_type must be code_review")
    purpose = value["purpose"]
    if purpose not in PURPOSES:
        raise ReviewProvenanceError("invalid review_provenance.purpose")
    if expected_purpose is not None and purpose != expected_purpose:
        raise ReviewProvenanceError(
            f"review_provenance purpose mismatch: expected {expected_purpose}, got {purpose}"
        )
    return value


def _git(repo: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise ReviewProvenanceError(f"git {' '.join(args)} failed: {process.stderr.strip()}")
    return process.stdout.strip()


def _blob_if_present(repo: Path, revision: str, path: str) -> str | None:
    process = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", f"{revision}:{path}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        return None
    value = process.stdout.strip()
    if not SHA40_RE.fullmatch(value):
        raise ReviewProvenanceError(f"invalid blob identity for {revision}:{path}")
    return value


def _candidate_review_commits(repo: Path, target_ref: str, closure_ref: str, artifact_path: str) -> list[str]:
    commits = [
        item.strip()
        for item in _git(
            repo,
            "log",
            "--reverse",
            "--format=%H",
            f"{target_ref}..{closure_ref}",
            "--",
            artifact_path,
        ).splitlines()
        if item.strip()
    ]
    if not commits:
        raise ReviewProvenanceError(f"no post-target change found for reviewed artifact {artifact_path}")
    first = commits[0]
    parent_line = _git(repo, "rev-list", "--parents", "-n", "1", first).split()
    candidates = [first, *parent_line[1:]]
    current_blob = _blob_if_present(repo, closure_ref, artifact_path)
    if current_blob is None:
        raise ReviewProvenanceError(f"reviewed artifact is absent at closure ref: {artifact_path}")
    result: list[str] = []
    for commit in candidates:
        if commit == target_ref or commit in result:
            continue
        if _blob_if_present(repo, commit, artifact_path) == current_blob:
            result.append(commit)
    if not result:
        raise ReviewProvenanceError(
            f"unable to identify a reviewed source commit carrying closure blob for {artifact_path}"
        )
    return result


def _github_json(url: str, token: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "erei-release-provenance",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        raise ReviewProvenanceError(f"GitHub provenance query failed for {url}: {exc}") from exc


def _clean_codex_summary(comments: list[dict[str, Any]], reviewed_commit: str, reviewer_login: str) -> int | None:
    for comment in reversed(comments):
        user = comment.get("user")
        if not isinstance(user, dict) or user.get("login") != reviewer_login:
            continue
        body = comment.get("body")
        if not isinstance(body, str):
            continue
        match = SUMMARY_RE.search(body)
        if not match:
            continue
        try:
            state = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        review = state.get("code_review")
        if not isinstance(review, dict):
            continue
        if (
            review.get("commit_sha") == reviewed_commit
            and review.get("status") == "completed"
            and review.get("has_any_findings") is False
            and review.get("has_unresolved_findings") is False
        ):
            comment_id = comment.get("id")
            return comment_id if isinstance(comment_id, int) else 0
    return None


def verify_artifact_review(
    repo_root: Path,
    *,
    repository: str,
    target_ref: str,
    closure_ref: str,
    artifact_path: str,
    descriptor: dict[str, Any],
    expected_purpose: str,
    token: str | None = None,
    required_base_prefix: str = "release/",
) -> dict[str, Any]:
    validate_descriptor(descriptor, expected_purpose=expected_purpose)
    repo_root = repo_root.resolve()
    token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise ReviewProvenanceError(
            "authenticated GitHub review provenance requires GITHUB_TOKEN or GH_TOKEN"
        )

    candidates = _candidate_review_commits(repo_root, target_ref, closure_ref, artifact_path)
    api_base = f"https://api.github.com/repos/{repository}"

    for candidate in candidates:
        pulls = _github_json(f"{api_base}/commits/{candidate}/pulls", token)
        if not isinstance(pulls, list):
            continue
        for pull in pulls:
            if not isinstance(pull, dict):
                continue
            number = pull.get("number")
            head = pull.get("head")
            base = pull.get("base")
            if not isinstance(number, int) or not isinstance(head, dict) or not isinstance(base, dict):
                continue
            if head.get("sha") != candidate:
                continue
            if pull.get("merged_at") is None:
                continue
            base_ref = base.get("ref")
            if not isinstance(base_ref, str) or not base_ref.startswith(required_base_prefix):
                continue
            comments = _github_json(f"{api_base}/issues/{number}/comments?per_page=100", token)
            if not isinstance(comments, list):
                continue
            summary_comment_id = _clean_codex_summary(
                comments,
                candidate,
                descriptor["reviewer_login"],
            )
            if summary_comment_id is None:
                continue
            return {
                "status": "verified",
                "provider": PROVIDER,
                "purpose": expected_purpose,
                "pull_request_number": number,
                "reviewed_commit": candidate,
                "summary_comment_id": summary_comment_id,
                "base_ref": base_ref,
                "reviewer_login": descriptor["reviewer_login"],
            }

    raise ReviewProvenanceError(
        f"no merged release PR with a clean authenticated Codex review matches {artifact_path}"
    )
