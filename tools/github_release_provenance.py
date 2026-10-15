#!/usr/bin/env python3
"""Verify GitHub-authenticated provenance for V2 release-control decisions."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

POLICY_PATH = Path("security/RELEASE_REVIEW_POLICY.json")
REPOSITORY = "lijust/EREI-Engineering-Framework"
SHA40_RE = re.compile(r"^[a-f0-9]{40}$")
CODEX_MARKER_RE = re.compile(r"<!-- codex-review-state:v1 (\{.*?\}) -->", re.DOTALL)
REVIEWED_COMMIT_RE = re.compile(r"Reviewed commit:\*\*\s*`?([a-f0-9]{7,40})`?", re.IGNORECASE)


class GitHubProvenanceError(RuntimeError):
    pass


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GitHubProvenanceError(f"{label} must be a non-empty string")
    return value.strip()


def _sha40(value: Any, label: str) -> str:
    text = _text(value, label)
    if not SHA40_RE.fullmatch(text):
        raise GitHubProvenanceError(f"{label} must be an exact 40-character SHA")
    return text


def _positive_int(value: Any, label: str) -> int:
    if type(value) is not int or value < 1:
        raise GitHubProvenanceError(f"{label} must be an integer >= 1")
    return value


def load_policy(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GitHubProvenanceError(f"unable to load release review policy: {exc}") from exc
    required = {
        "schema_version", "repository", "release_branch_prefix",
        "codex_reviewer_login", "architecture_approver_login",
        "require_verified_merge_commit",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise GitHubProvenanceError("release review policy fields mismatch")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise GitHubProvenanceError("release review policy schema_version must be integer 1")
    if value["repository"] != REPOSITORY:
        raise GitHubProvenanceError("release review policy repository mismatch")
    if value["release_branch_prefix"] != "release/":
        raise GitHubProvenanceError("release review policy branch prefix mismatch")
    _text(value["codex_reviewer_login"], "codex_reviewer_login")
    _text(value["architecture_approver_login"], "architecture_approver_login")
    if value["require_verified_merge_commit"] is not True:
        raise GitHubProvenanceError("release review policy must require verified merge commits")
    return value


def validate_provenance_shape(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GitHubProvenanceError("provenance must be an object")
    required = {"kind", "pr_number", "actor_login"}
    if set(value) != required:
        raise GitHubProvenanceError("provenance must contain exactly kind/pr_number/actor_login")
    if value["kind"] not in {"github_codex_clean_review", "github_owner_approval_comment"}:
        raise GitHubProvenanceError("unsupported provenance.kind")
    _positive_int(value["pr_number"], "provenance.pr_number")
    _text(value["actor_login"], "provenance.actor_login")
    return value


def architecture_approval_comment(approval_id: str, target_ref: str, head_sha: str) -> str:
    return (
        "EREI FINAL ARCHITECTURE APPROVAL\n"
        f"approval_id={_text(approval_id, 'approval_id')}\n"
        f"target_ref={_sha40(target_ref, 'target_ref')}\n"
        f"head_sha={_sha40(head_sha, 'head_sha')}"
    )


def _api_json(repository: str, path: str, token: str) -> Any:
    url = f"https://api.github.com/repos/{repository}/{path.lstrip('/')}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "erei-release-provenance-v1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        raise GitHubProvenanceError(f"GitHub API request failed for {path}: {exc}") from exc


def _git_blob_sha(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def _content_blob(repository: str, path: str, ref: str, token: str) -> tuple[str, bytes]:
    encoded_path = urllib.parse.quote(path, safe="/")
    data = _api_json(repository, f"contents/{encoded_path}?ref={urllib.parse.quote(ref, safe='')}", token)
    if not isinstance(data, dict) or data.get("type") != "file":
        raise GitHubProvenanceError(f"review PR does not contain required file: {path}")
    raw = data.get("content")
    if not isinstance(raw, str):
        raise GitHubProvenanceError(f"GitHub content payload missing for {path}")
    try:
        content = base64.b64decode(raw.replace("\n", ""), validate=True)
    except Exception as exc:
        raise GitHubProvenanceError(f"invalid GitHub base64 content for {path}") from exc
    sha = data.get("sha")
    if not isinstance(sha, str) or sha != _git_blob_sha(content):
        raise GitHubProvenanceError(f"GitHub blob identity mismatch for {path}")
    return sha, content


def _require_clean_codex_review(repository: str, pr_number: int, head_sha: str, actor: str, token: str) -> dict[str, Any]:
    comments = _api_json(repository, f"issues/{pr_number}/comments?per_page=100", token)
    if not isinstance(comments, list):
        raise GitHubProvenanceError("GitHub comments response must be an array")
    clean_summary = None
    for comment in comments:
        if not isinstance(comment, dict) or comment.get("user", {}).get("login") != actor:
            continue
        body = comment.get("body")
        if not isinstance(body, str):
            continue
        match = CODEX_MARKER_RE.search(body)
        if not match:
            continue
        try:
            state = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        review = state.get("code_review") if isinstance(state, dict) else None
        if not isinstance(review, dict):
            continue
        if (
            review.get("commit_sha") == head_sha
            and review.get("status") == "completed"
            and review.get("has_any_findings") is False
            and review.get("has_unresolved_findings") is False
        ):
            clean_summary = {"comment_id": comment.get("id"), "state": review}
    if clean_summary is None:
        raise GitHubProvenanceError("no clean Codex review summary is bound to the exact PR head")

    reviews = _api_json(repository, f"pulls/{pr_number}/reviews?per_page=100", token)
    if not isinstance(reviews, list):
        raise GitHubProvenanceError("GitHub reviews response must be an array")
    receipt = None
    for review in reviews:
        if not isinstance(review, dict) or review.get("user", {}).get("login") != actor:
            continue
        body = review.get("body")
        if not isinstance(body, str):
            continue
        match = REVIEWED_COMMIT_RE.search(body)
        if match and head_sha.startswith(match.group(1)):
            receipt = {"review_id": review.get("id"), "state": review.get("state")}
    if receipt is None:
        raise GitHubProvenanceError("no Codex review receipt is bound to the exact PR head")
    return {**clean_summary, **receipt}


def verify_reviewed_file(
    repo_root: Path,
    record_path: str,
    provenance: dict[str, Any],
    *,
    policy: dict[str, Any],
    target_ref: str,
    approval_id: str | None = None,
    require_merged: bool = True,
    token: str | None = None,
) -> dict[str, Any]:
    provenance = validate_provenance_shape(provenance)
    token = token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise GitHubProvenanceError("authenticated GitHub provenance requires GH_TOKEN/GITHUB_TOKEN")

    repository = policy["repository"]
    pr_number = provenance["pr_number"]
    pr = _api_json(repository, f"pulls/{pr_number}", token)
    if not isinstance(pr, dict):
        raise GitHubProvenanceError("GitHub PR response must be an object")
    head_sha = _sha40(pr.get("head", {}).get("sha"), "review PR head.sha")
    base_ref = _text(pr.get("base", {}).get("ref"), "review PR base.ref")
    if not base_ref.startswith(policy["release_branch_prefix"]):
        raise GitHubProvenanceError("release provenance PR must target a release/* branch")

    local_path = repo_root / record_path
    try:
        local_bytes = local_path.read_bytes()
    except OSError as exc:
        raise GitHubProvenanceError(f"unable to read release record {record_path}: {exc}") from exc
    _, reviewed_bytes = _content_blob(repository, record_path, head_sha, token)
    if reviewed_bytes != local_bytes:
        raise GitHubProvenanceError("release record differs from the exact GitHub-reviewed PR head")

    kind = provenance["kind"]
    actor = provenance["actor_login"]
    details: dict[str, Any]
    if kind == "github_codex_clean_review":
        if actor != policy["codex_reviewer_login"]:
            raise GitHubProvenanceError("Codex provenance actor does not match frozen review policy")
        details = _require_clean_codex_review(repository, pr_number, head_sha, actor, token)
    else:
        if actor != policy["architecture_approver_login"]:
            raise GitHubProvenanceError("architecture approver does not match frozen review policy")
        if approval_id is None:
            raise GitHubProvenanceError("architecture approval provenance requires approval_id")
        expected = architecture_approval_comment(approval_id, target_ref, head_sha)
        comments = _api_json(repository, f"issues/{pr_number}/comments?per_page=100", token)
        found = next(
            (
                item for item in comments
                if isinstance(item, dict)
                and item.get("user", {}).get("login") == actor
                and isinstance(item.get("body"), str)
                and item["body"].strip() == expected
            ),
            None,
        )
        if found is None:
            raise GitHubProvenanceError("exact authenticated architecture approval comment not found")
        details = {"comment_id": found.get("id")}

    merge_sha = pr.get("merge_commit_sha")
    if require_merged:
        if pr.get("merged") is not True or not isinstance(merge_sha, str) or not SHA40_RE.fullmatch(merge_sha):
            raise GitHubProvenanceError("review provenance PR is not merged")
        commit = _api_json(repository, f"commits/{merge_sha}", token)
        verification = commit.get("commit", {}).get("verification") if isinstance(commit, dict) else None
        if (
            policy["require_verified_merge_commit"]
            and (not isinstance(verification, dict) or verification.get("verified") is not True)
        ):
            raise GitHubProvenanceError("review provenance merge commit is not GitHub-verified")
    return {
        "status": "authenticated",
        "repository": repository,
        "pr_number": pr_number,
        "head_sha": head_sha,
        "merge_commit_sha": merge_sha,
        "actor_login": actor,
        **details,
    }
