"""Opt-in private, verified source-export preparation for public calibration.

Use on an authenticated, trusted local machine. Requires GitHub CLI ('gh')
read permission for EREI-3.2 and EREI-App-Google. Never use this in public
GitHub Actions, or commit private source files to the Framework repository.
The subprocess's private output and errors never reach program stdout/stderr.
No mutation, model calls, deployment or production writes.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import quote


CATALOG = Path(__file__).with_name("calibration-packages.json")
FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_PRIVATE_REPOS = frozenset({
    "lijust/EREI-App-Google", "lijust/EREI-3.2",
})
COMMIT_RE = re.compile(r"[a-f0-9]{40}\Z")
GIT_BLOB_RE = COMMIT_RE


def safe_path(value: str) -> Path:
    posix = PurePosixPath(value)
    if (not isinstance(value, str) or not value or "\\" in value
            or ":" in value or posix.is_absolute()
            or ".." in posix.parts or str(posix) != value):
        raise ValueError("Unsafe pinned source path")
    return Path(*posix.parts)


def verified_file_specifications(catalog: dict, task: str | None) -> dict[tuple[str, str], dict]:
    if catalog.get("execution_authorized") is not False:
        raise ValueError("Public-only catalog must have execution_authorized=false")
    packages = catalog["packages"]
    selected = [item for item in packages if task is None or item["task_id"] == task]
    if not selected or len({p["task_id"] for p in selected}) != len(selected):
        raise ValueError("Unknown or duplicate public calibration task")
    wanted: dict[tuple[str, str], dict] = {}
    for package in selected:
        if package.get("state") != "PUBLIC_CALIBRATION_ONLY":
            raise ValueError("Nonpublic calibration package")
        src = package["source"]
        repo, commit = src["repository"], src["commit"]
        if repo not in ALLOWED_PRIVATE_REPOS or not COMMIT_RE.fullmatch(commit):
            raise ValueError("Unapproved or unpinned source repository")
        directory = str(safe_path(src["export_directory"]))
        if directory not in ("app", "py"):
            raise ValueError("Unexpected export directory")
        for file in package["files"]:
            filename = str(safe_path(file["path"]))
            blob = file["git_blob"]
            if not isinstance(blob, str) or not GIT_BLOB_RE.fullmatch(blob):
                raise ValueError("Malformed pinned source blob")
            key = (directory, filename)
            expected = {"repo": repo, "commit": commit, "path": filename,
                        "sha": blob}
            if key in wanted and wanted[key] != expected:
                raise ValueError("Conflicting original pinned source identity")
            wanted[key] = expected
    return wanted


def fetch_original_bytes(spec: dict, gh: str) -> bytes:
    # GitHub Contents API returns JSON with base64; no unauthenticated raw URLs.
    endpoint = (f"repos/{spec['repo']}/contents/"
                + quote(spec["path"], safe="/") + "?ref=" + spec["commit"])
    result = subprocess.run(
        [gh, "api", "-H", "Accept: application/vnd.github+json", endpoint],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=False, timeout=35, check=False,
    )
    if result.returncode:
        # Do not print 'gh' stderr: it might contain secrets or private content.
        raise RuntimeError("Private GitHub source fetch failed")
    body = json.loads(result.stdout)
    if (not isinstance(body, dict) or body.get("type") != "file"
            or body.get("encoding") != "base64"
            or body.get("sha") != spec["sha"]):
        raise ValueError("Pinned original source response mismatch")
    encoded = body.get("content")
    if not isinstance(encoded, str):
        raise ValueError("Missing original source bytes")
    try:
        data = base64.b64decode("".join(encoded.split()), validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Invalid pinned source response encoding") from exc
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\\0" + data).hexdigest()
    if blob != spec["sha"]:
        raise ValueError("Downloaded original bytes fail Git blob identity check")
    return data


def prepare(destination: Path, task: str | None, gh: str = "gh") -> dict:
    if not destination.is_absolute():
        raise ValueError("Source export destination must be an absolute path")
    resolved = destination.resolve()
    if resolved.is_relative_to(FRAMEWORK_ROOT):
        raise ValueError("Private export destination must be outside public Framework checkout")
    if destination.exists():
        raise ValueError("Private source export destination already exists")
    if not destination.parent.is_dir():
        raise ValueError("Create the private export destination parent first")
    raw_catalog = CATALOG.read_bytes()
    catalog = json.loads(raw_catalog)
    selected = verified_file_specifications(catalog, task)
    stage = Path(tempfile.mkdtemp(prefix=".erei-private-source-", dir=destination.parent))
    try:
        try:
            stage.chmod(0o700)
        except OSError:
            pass  # Windows ACL inherits parent; parent must be trusted.
        for (directory, filename), spec in sorted(selected.items()):
            data = fetch_original_bytes(spec, gh)
            target = stage / directory / safe_path(filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        # Verify all source contents are exactly the expected pins a second time
        # before publishing this private directory atomically.
        for (directory, filename), spec in selected.items():
            payload = (stage / directory / safe_path(filename)).read_bytes()
            blob = hashlib.sha1(
                b"blob " + str(len(payload)).encode() + b"\\0" + payload
            ).hexdigest()
            if blob != spec["sha"]:
                raise ValueError("Staged export verification failed")
        stage.rename(destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return {
        "kind": "PRIVATE_ORIGINAL_SOURCES_PREPARED",
        "file_count": len(selected),
        "task": task or "ALL",
        "catalog_sha256": hashlib.sha256(raw_catalog).hexdigest(),
        "private_bytes_printed": False,
        "model_executions": 0,
        "independent_review": "NOT_PERFORMED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, type=Path,
                        help="Absolute NEW directory outside public checkout; trusted local filesystem")
    parser.add_argument("--task", help="Optional task ID, e.g. PY-04")
    args = parser.parse_args()
    try:
        report = prepare(args.destination, args.task)
    except Exception as exc:
        # Exception text and gh stderr are deliberately suppressed.
        print(json.dumps({"status": "FAIL_CLOSED",
                          "error_type": type(exc).__name__,
                          "private_bytes_printed": False,
                          "model_executions": 0}), file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
