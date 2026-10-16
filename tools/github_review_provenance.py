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
    purpose = value["purpose"]
    if purpose not in PURPOSES:
        raise ReviewProvenanceError("invalid review_provenance.purpose")
    expected_review_type = "code_review" if purpose == "architecture_approval" else "security_review"
    if value["review_type"] != expected_review_type:
        raise ReviewProvenanceError(
            f"review_provenance.review_type must be {expected_review_type} for {purpose}"
        )
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


def _is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    process = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", ancestor, descendant],
        text=True,
        capture_output=True,
        check=False,
    )
    return process.returncode == 0


def _candidate_review_commits(repo: Path, target_ref: str, closure_ref: str, artifact_path: str) -> list[str]:
    path_changes = [
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
    if not path_changes:
        raise ReviewProvenanceError(f"no post-target change found for reviewed artifact {artifact_path}")

    current_blob = _blob_if_present(repo, closure_ref, artifact_path)
    if current_blob is None:
        raise ReviewProvenanceError(f"reviewed artifact is absent at closure ref: {artifact_path}")

    reachable = [
        item.strip()
        for item in _git(repo, "rev-list", "--reverse", f"{target_ref}..{closure_ref}").splitlines()
        if item.strip()
    ]
    result: list[str] = []
    for commit in reachable:
        if commit == target_ref or commit in result:
            continue
        if not _is_ancestor(repo, target_ref, commit):
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


def _github_paginated_array(
    url: str,
    token: str,
    *,
    max_pages: int = 30,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        separator = "&" if "?" in url else "?"
        batch = _github_json(f"{url}{separator}per_page=100&page={page}", token)
        if not isinstance(batch, list):
            raise ReviewProvenanceError(f"GitHub paginated endpoint did not return an array: {url}")
        result.extend(item for item in batch if isinstance(item, dict))
        if len(batch) < 100:
            return result
    raise ReviewProvenanceError(
        f"GitHub provenance pagination exceeded {max_pages} pages: {url}"
    )


def _clean_codex_summary(
    comments: list[dict[str, Any]],
    reviewed_commit: str,
    reviewer_login: str,
    review_type: str = "code_review",
) -> int | None:
    """Accept only the newest authenticated summary, never an older clean snapshot.

    A later summary for another head, a failed/in-progress review, or an
    unavailable security review supersedes earlier approvals and blocks.
    """
    summaries: list[tuple[str, int, dict[str, Any]]] = []
    for comment in comments:
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
        if not isinstance(state, dict):
            continue
        comment_id = comment.get("id")
        if type(comment_id) is not int:
            continue
        timestamp = comment.get("updated_at") or comment.get("created_at") or ""
        if not isinstance(timestamp, str):
            timestamp = ""
        summaries.append((timestamp, comment_id, state))

    if not summaries:
        return None
    # GitHub returns comments oldest-first, but ordering by last edit is
    # necessary because Codex updates its summary in place.
    _, comment_id, latest = max(summaries, key=lambda item: (item[0], item[1]))
    review = latest.get(review_type)
    if not isinstance(review, dict):
        return None
    if (
        review.get("commit_sha") == reviewed_commit
        and review.get("status") == "completed"
        and review.get("has_any_findings") is False
        and review.get("has_unresolved_findings") is False
    ):
        return comment_id
    return None


def _derived_release_base_ref(repo: Path, closure_ref: str) -> str | None:
    process = subprocess.run(
        ["git", "-C", str(repo), "show", f"{closure_ref}:releases/VNEXT_TARGET.json"],
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        return None
    try:
        value = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise ReviewProvenanceError("invalid VNEXT_TARGET.json while deriving release review branch") from exc
    if not isinstance(value, dict):
        raise ReviewProvenanceError("VNEXT_TARGET.json must be an object")
    target_id = value.get("target_id")
    if not isinstance(target_id, str) or not re.fullmatch(r"vnext-rc[0-9]+", target_id):
        raise ReviewProvenanceError("VNEXT_TARGET.json has invalid target_id for provenance binding")
    return f"release/{target_id}"


def _pr_reviews_artifact(
    files: Any,
    *,
    artifact_path: str,
    expected_blob: str,
) -> bool:
    if not isinstance(files, list):
        return False
    for item in files:
        if not isinstance(item, dict):
            continue
        if item.get("filename") != artifact_path:
            continue
        if item.get("status") == "removed":
            continue
        if item.get("sha") == expected_blob:
            return True
    return False


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
    required_base_ref: str | None = None,
) -> dict[str, Any]:
    validate_descriptor(descriptor, expected_purpose=expected_purpose)
    repo_root = repo_root.resolve()
    token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise ReviewProvenanceError(
            "authenticated GitHub review provenance requires GITHUB_TOKEN or GH_TOKEN"
        )

    candidates = _candidate_review_commits(repo_root, target_ref, closure_ref, artifact_path)
    derived_base_ref = _derived_release_base_ref(repo_root, closure_ref)
    if required_base_ref is None and derived_base_ref is not None:
        required_base_ref = derived_base_ref
    api_base = f"https://api.github.com/repos/{repository}"

    for candidate in candidates:
        pulls = _github_paginated_array(f"{api_base}/commits/{candidate}/pulls", token)
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
            merge_sha = pull.get("merge_commit_sha")
            if not isinstance(merge_sha, str) or not SHA40_RE.fullmatch(merge_sha):
                continue
            # The reviewed merge MUST be inside this specific carrier's
            # ancestry. A different merge/direct replay cannot impersonate it.
            if not _is_ancestor(repo_root, merge_sha, closure_ref):
                continue
            if not _is_ancestor(repo_root, target_ref, candidate):
                continue
            if not _is_ancestor(repo_root, candidate, merge_sha):
                continue
            base_ref = base.get("ref")
            if not isinstance(base_ref, str):
                continue
            if required_base_ref is not None:
                if base_ref != required_base_ref:
                    continue
            elif not base_ref.startswith(required_base_prefix):
                continue

            candidate_blob = _blob_if_present(repo_root, candidate, artifact_path)
            if candidate_blob is None:
                continue
            files = _github_paginated_array(f"{api_base}/pulls/{number}/files", token)
            if not _pr_reviews_artifact(
                files,
                artifact_path=artifact_path,
                expected_blob=candidate_blob,
            ):
                continue

            comments = _github_paginated_array(f"{api_base}/issues/{number}/comments", token)
            summary_comment_id = _clean_codex_summary(
                comments,
                candidate,
                descriptor["reviewer_login"],
                descriptor["review_type"],
            )
            if summary_comment_id is None:
                continue
            return {
                "status": "verified",
                "provider": PROVIDER,
                "purpose": expected_purpose,
                "pull_request_number": number,
                "reviewed_commit": candidate,
                "merge_commit_sha": merge_sha,
                "reviewed_artifact_path": artifact_path,
                "reviewed_artifact_blob": candidate_blob,
                "summary_comment_id": summary_comment_id,
                "base_ref": base_ref,
                "reviewer_login": descriptor["reviewer_login"],
            }

    raise ReviewProvenanceError(
        f"no merged release PR with a clean authenticated Codex review matches {artifact_path}"
    )
