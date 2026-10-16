#!/usr/bin/env python3
"""Verify a release evidence ZIP against authenticated GitHub Actions artifact metadata.

This validates provenance only at import time. It is NOT a Sigstore attestation,
trusted-workflow approval, Stable authorization, or permanent archival signature.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

REPOSITORY = "lijust/EREI-Engineering-Framework"
WORKFLOW_PATH = ".github/workflows/vnext-exact-target-copilot.yml"
WORKFLOW_NAME = "VNext Exact Target Copilot Evidence"
EXPECTED_FILES = {"exact-target-run.json", "execution-evidence.json", "runtime-identity.json"}
SHA256_DIGEST = re.compile(r"^sha256:([a-f0-9]{64})$")
MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
MAX_FILE_BYTES = 8 * 1024 * 1024


class ActionsProvenanceError(RuntimeError):
    pass


def _api_json(url: str, token: str) -> dict[str, Any]:
    if not url.startswith("https://api.github.com/repos/" + REPOSITORY + "/"):
        raise ActionsProvenanceError("GitHub Actions API URL is outside the official repository")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "EREI-Exact-Target-Provenance-V1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = response.read(1024 * 1024 + 1)
    except (OSError, urllib.error.URLError) as exc:
        raise ActionsProvenanceError("cannot authenticate GitHub Actions evidence provenance") from exc
    if len(payload) > 1024 * 1024:
        raise ActionsProvenanceError("GitHub Actions API response exceeds limit")
    try:
        value = json.loads(payload)
    except (ValueError, UnicodeError) as exc:
        raise ActionsProvenanceError("GitHub Actions API did not return valid JSON") from exc
    if not isinstance(value, dict):
        raise ActionsProvenanceError("GitHub Actions API did not return an object")
    return value


def _validated_zip_bytes(archive: Path) -> tuple[bytes, dict[str, bytes]]:
    try:
        if archive.stat().st_size > MAX_ARCHIVE_BYTES:
            raise ActionsProvenanceError("GitHub Actions evidence archive exceeds maximum size")
        raw = archive.read_bytes()
        with zipfile.ZipFile(io.BytesIO(raw)) as handle:
            infos = handle.infolist()
            if len(infos) != 3 or {item.filename for item in infos} != EXPECTED_FILES:
                raise ActionsProvenanceError("GitHub Actions evidence archive must contain exactly three flat files")
            files = {}
            for item in infos:
                if item.is_dir() or item.file_size > MAX_FILE_BYTES or (item.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ActionsProvenanceError("unsafe file in GitHub Actions evidence archive")
                payload = handle.read(item)
                if len(payload) > MAX_FILE_BYTES:
                    raise ActionsProvenanceError("expanded evidence file exceeds maximum size")
                files[item.filename] = payload
    except ActionsProvenanceError:
        raise
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        raise ActionsProvenanceError("unreadable GitHub Actions evidence archive") from exc
    return raw, files


def verify_official_run_artifact(
    identity: dict[str, Any],
    package_bytes: dict[str, bytes],
    *,
    archive: Path | None,
    token: str | None,
) -> dict[str, Any]:
    """Fail-closed on absent auth, untrusted run, mismatch or tampered package ZIP."""
    if not token or not token.strip():
        raise ActionsProvenanceError("read-only GitHub Actions token is required for import provenance")
    if archive is None:
        raise ActionsProvenanceError("original GitHub Actions artifact ZIP is required for import provenance")
    if identity.get("repository") != REPOSITORY:
        raise ActionsProvenanceError("authenticated repository mismatch")
    run_id, attempt = identity["github_run_id"], identity["github_run_attempt"]
    run = _api_json(
        f"https://api.github.com/repos/{REPOSITORY}/actions/runs/{run_id}", token
    )
    if (
        run.get("id") != run_id
        or run.get("run_attempt") != attempt
        or run.get("event") != "workflow_dispatch"
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
        or run.get("name") != WORKFLOW_NAME
        or run.get("path") != WORKFLOW_PATH
        or run.get("head_sha") != identity["release_carrier_ref"]
        or (run.get("repository") or {}).get("full_name") != REPOSITORY
    ):
        raise ActionsProvenanceError("GitHub Actions run does not authenticate exact controlled release carrier")
    meta = _api_json(
        f"https://api.github.com/repos/{REPOSITORY}/actions/runs/{run_id}/artifacts?per_page=100", token
    )
    expected_name = f"vnext-exact-target-{identity['target_id']}-{run_id}-{attempt}"
    matching = [
        x for x in meta.get("artifacts", []) if isinstance(x, dict)
        and x.get("name") == expected_name and x.get("expired") is False
        and (x.get("workflow_run") or {}).get("id") == run_id
        and (x.get("workflow_run") or {}).get("head_sha") == identity["release_carrier_ref"]
    ]
    if len(matching) != 1 or not isinstance(matching[0].get("id"), int):
        raise ActionsProvenanceError("no unique unexpired artifact from the authenticated controlled run")
    artifact = matching[0]
    match = SHA256_DIGEST.fullmatch(str(artifact.get("digest")))
    if match is None:
        raise ActionsProvenanceError("artifact has no authenticated SHA-256 archive digest")
    raw, extracted = _validated_zip_bytes(Path(archive))
    if hashlib.sha256(raw).hexdigest() != match.group(1):
        raise ActionsProvenanceError("GitHub Actions archive SHA-256 digest mismatch")
    if extracted != package_bytes:
        raise ActionsProvenanceError("extracted release package differs from authenticated artifact ZIP")
    return {"authenticated": True, "repository": REPOSITORY, "run_id": run_id, "attempt": attempt, "artifact_id": artifact["id"], "archive_digest": match.group(1)}
