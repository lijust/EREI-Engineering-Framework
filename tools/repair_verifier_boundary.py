"""J5-02 topology/data-flow preflight, not a hostile-code security boundary.

Reuses J2 and J5-01. Two temporary *trusted fixed* subprocess probes can
demonstrate distinct working directories and verifier-only fixture reading.
Neither subprocess executes a candidate patch, model text, or unreviewed code.
A shared host OS still gives NO mandatory-access-control confidentiality.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any

from tools import repair_source_binding as j501

MAX_FIXTURE_BYTES = 256 * 1024
MAX_CANDIDATE_ENTRIES = 4096
PROBE_TIMEOUT_SECONDS = 5

# Literal programs are intentionally fixed. No user text is interpolated.
_FIXED_CANDIDATE = (
    "import json,os;"
    "print(json.dumps({'role':'candidate','pid':os.getpid()}))"
)
_FIXED_VERIFIER = (
    "import hashlib,json,os,pathlib,sys;"
    "a=pathlib.Path(sys.argv[1]).read_bytes();"
    "b=pathlib.Path(sys.argv[2]).read_bytes();"
    "print(json.dumps({'role':'verifier','pid':os.getpid(),"
    "'oracle_sha256':hashlib.sha256(a).hexdigest(),"
    "'profile_sha256':hashlib.sha256(b).hexdigest()}))"
)


class BoundaryDenied(ValueError):
    """Fail closed without exposing paths, fixture contents or subprocess logs."""


def _directory(value: Path | str, role: str) -> Path:
    if not isinstance(value, (Path, str)):
        raise BoundaryDenied("DIRECTORY_ARGUMENT_INVALID")
    try:
        path = Path(value).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise BoundaryDenied("DIRECTORY_UNAVAILABLE") from exc
    if not path.is_dir():
        raise BoundaryDenied("WORKSPACE_NOT_DIRECTORY")
    return path


def _inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _disjoint(a: Path, b: Path) -> bool:
    return not _inside(a, b) and not _inside(b, a)


def _fixture(value: Path | str, verifier: Path, verifier_lexical: Path) -> tuple[Path, str, tuple[int, int]]:
    if not isinstance(value, (str, Path)):
        raise BoundaryDenied("FIXTURE_ARGUMENT_INVALID")
    supplied = Path(value)
    if not supplied.is_absolute():
        raise BoundaryDenied("FIXTURE_PATH_MUST_BE_ABSOLUTE")
    # A lexical-in-verifier check is required BEFORE following a symlink:
    # /outside/alias -> /verifier/oracle must not be accepted.
    lexical = Path(os.path.abspath(supplied))
    # Match the caller's *lexical* verifier root. On Windows,
    # Path.resolve() can expand junctions/8.3 aliases: comparing a lexical
    # fixture with only the resolved root would reject valid in-root files.
    if lexical == verifier_lexical or not _inside(lexical, verifier_lexical):
        raise BoundaryDenied("FIXTURE_OUTSIDE_VERIFIER")
    try:
        resolved = lexical.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise BoundaryDenied("FIXTURE_UNAVAILABLE") from exc
    if resolved == verifier or not _inside(resolved, verifier):
        raise BoundaryDenied("FIXTURE_OUTSIDE_VERIFIER")
    # Reject symlinked fixture files and traversed parent links. This also
    # eliminates an easy same-filesystem alias in a prospective mount plan.
    cursor = lexical
    try:
        while cursor != verifier_lexical and _inside(cursor, verifier_lexical):
            if (cursor.is_symlink()
                or (hasattr(cursor, "is_junction") and cursor.is_junction())):
                raise BoundaryDenied("FIXTURE_SYMLINK_DENIED")
            cursor = cursor.parent
        info = lexical.lstat()
        if not stat.S_ISREG(info.st_mode):
            raise BoundaryDenied("FIXTURE_NOT_REGULAR")
        # On Windows a linked directory entry may expose a different file ID
        # in portable stat. Reject any verifier file with multiple hardlinks.
        if info.st_nlink != 1:
            raise BoundaryDenied("FIXTURE_LINK_COUNT_UNSAFE")
        if stat.S_IMODE(info.st_mode) & 0o222:
            raise BoundaryDenied("FIXTURE_NOT_READONLY")
        if info.st_size < 1 or info.st_size > MAX_FIXTURE_BYTES:
            raise BoundaryDenied("FIXTURE_SIZE_INVALID")
        with supplied.open("rb") as stream:
            raw = stream.read(MAX_FIXTURE_BYTES + 1)
        if len(raw) != info.st_size:
            raise BoundaryDenied("FIXTURE_CHANGED_DURING_READ")
    except (OSError, ValueError) as exc:
        if isinstance(exc, BoundaryDenied):
            raise
        raise BoundaryDenied("FIXTURE_READ_FAILED") from exc
    if info.st_ino == 0:
        # Cannot check hardlink intersection on this filesystem.
        raise BoundaryDenied("FIXTURE_FILE_IDENTITY_UNAVAILABLE")
    return resolved, hashlib.sha256(raw).hexdigest(), (info.st_dev, info.st_ino)


def _candidate_tree(candidate: Path, protected_file_ids: set[tuple[int, int]]) -> None:
    # Explicitly forbid symlinks, junction traversal and any hardlink alias
    # to the actual verifier-only fixture files. Not a race-free security scan.
    count = 0
    pending = [candidate]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as iterator:
                for entry in iterator:
                    count += 1
                    if count > MAX_CANDIDATE_ENTRIES:
                        raise BoundaryDenied("CANDIDATE_TREE_SCAN_LIMIT")
                    if entry.is_symlink():
                        raise BoundaryDenied("CANDIDATE_SYMLINK_DENIED")
                    info = entry.stat(follow_symlinks=False)
                    if (info.st_dev, info.st_ino) in protected_file_ids:
                        raise BoundaryDenied("FIXTURE_HARDLINK_IN_CANDIDATE")
                    if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
                        raise BoundaryDenied("CANDIDATE_HARDLINK_DENIED")
                    if stat.S_ISDIR(info.st_mode):
                        # Resolving also detects junction/path redirection.
                        target = Path(entry.path).resolve(strict=True)
                        if not _inside(target, candidate):
                            raise BoundaryDenied("CANDIDATE_TREE_ESCAPE")
                        pending.append(target)
                    elif not stat.S_ISREG(info.st_mode):
                        raise BoundaryDenied("CANDIDATE_UNSUPPORTED_FILE_TYPE")
        except OSError as exc:
            raise BoundaryDenied("CANDIDATE_TREE_UNAVAILABLE") from exc


def _mounts(mounts: Any, candidate: Path) -> None:
    if type(mounts) not in (list, tuple) or len(mounts) > 32:
        raise BoundaryDenied("CANDIDATE_MOUNTS_INVALID")
    for mount in mounts:
        if not isinstance(mount, (Path, str)):
            raise BoundaryDenied("CANDIDATE_MOUNT_PATH_INVALID")
        try:
            path = Path(mount).resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise BoundaryDenied("CANDIDATE_MOUNT_UNAVAILABLE") from exc
        if not _inside(path, candidate):
            raise BoundaryDenied("MOUNT_OUTSIDE_CANDIDATE")
        # Tree scan handles aliases inside candidate; reject any raw symlink.
        if Path(mount).is_symlink():
            raise BoundaryDenied("CANDIDATE_MOUNT_SYMLINK_DENIED")


def candidate_view(task: dict) -> dict:
    """Projection from a J5-01-validated task only. No oracle digest/fixture."""
    return {
        "contract": "erei-repair-candidate-view-v1",
        "task_id": task["task_id"],
        "base_sha": task["base_sha"],
        "allowed_paths": list(task["allowed_paths"]),
        "max_patch_bytes": task["max_patch_bytes"],
    }


def _fixed_probe(role: str, workspace: Path, fixture_paths=()) -> dict:
    if role not in ("candidate", "verifier"):
        raise BoundaryDenied("PROBE_ROLE_INVALID")
    # Explicit minimal environment. No source text, verifier secret or key
    # reaches the candidate process through argv/env/stdin.
    env = {name: os.environ[name] for name in
           ("SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP")
           if name in os.environ}
    command = [sys.executable, "-I", "-S", "-c",
               _FIXED_CANDIDATE if role == "candidate" else _FIXED_VERIFIER]
    if role == "verifier":
        command += [str(item) for item in fixture_paths]
    try:
        result = subprocess.run(command, cwd=workspace, env=env,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, timeout=PROBE_TIMEOUT_SECONDS,
                                check=False)
        if result.returncode != 0 or len(result.stdout) > 4096:
            raise BoundaryDenied("TRUSTED_PROBE_FAILED")
        report = json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, UnicodeError, ValueError,
            TypeError) as exc:
        if isinstance(exc, BoundaryDenied):
            raise
        raise BoundaryDenied("TRUSTED_PROBE_FAILED") from exc
    expected = ({"role", "pid"} if role == "candidate"
                else {"role", "pid", "oracle_sha256", "profile_sha256"})
    if (type(report) is not dict or set(report) != expected
        or report["role"] != role or type(report["pid"]) is not int
        or report["pid"] <= 0):
        raise BoundaryDenied("TRUSTED_PROBE_REPORT_INVALID")
    return report


def preflight(
    source_root: Path | str,
    task: dict,
    proposal: dict,
    trusted_pins: dict,
    *,
    candidate_workspace: Path | str,
    verifier_workspace: Path | str,
    oracle_fixture: Path | str,
    worker_profile_fixture: Path | str,
    candidate_mounts: list[Path | str] | tuple[Path | str, ...] = (),
    run_fixed_process_probes: bool = False,
) -> dict:
    """Validate fixed-only process topology and sealed-input *placement*.

    No execution authority. This is only a prerequisite design/probe, not
    protection against malicious Python running as the same host OS user.
    """
    if type(run_fixed_process_probes) is not bool:
        raise BoundaryDenied("PROBE_FLAG_INVALID")
    source = j501.bind_pinned_source(source_root, task, proposal, trusted_pins)
    if (source.get("decision") != "BLOCK_AI_ACCEPTANCE"
        or source.get("acceptance_authorized") is not False):
        raise BoundaryDenied("J501_AUTHORITY_MISMATCH")
    candidate = _directory(candidate_workspace, "candidate")
    verifier = _directory(verifier_workspace, "verifier")
    original = _directory(source_root, "source")
    if (not _disjoint(candidate, verifier)
        or not _disjoint(candidate, original)
        or not _disjoint(verifier, original)):
        raise BoundaryDenied("WORKSPACE_INTERSECTION")
    verifier_lexical = Path(os.path.abspath(verifier_workspace))
    oracle_path, oracle_sha, oracle_id = _fixture(
        oracle_fixture, verifier, verifier_lexical)
    profile_path, profile_sha, profile_id = _fixture(
        worker_profile_fixture, verifier, verifier_lexical)
    if oracle_path == profile_path or oracle_id == profile_id:
        raise BoundaryDenied("FIXTURES_MUST_BE_DISTINCT")
    if oracle_sha != trusted_pins["oracle_sha256"]:
        raise BoundaryDenied("ORACLE_DIGEST_MISMATCH")
    if profile_sha != trusted_pins["worker_profile_sha256"]:
        raise BoundaryDenied("WORKER_PROFILE_DIGEST_MISMATCH")
    _candidate_tree(candidate, {oracle_id, profile_id})
    _mounts(candidate_mounts, candidate)
    view = candidate_view(task)
    # Never pass a verifier-only path, worker secret, oracle digest or expected
    # results to candidate. Only this deterministic projection is surfaced.
    fixed_pair = False
    if run_fixed_process_probes:
        candidate_observed = _fixed_probe("candidate", candidate)
        verifier_observed = _fixed_probe("verifier", verifier,
                                         (oracle_path, profile_path))
        if (candidate_observed["pid"] == verifier_observed["pid"]
            or verifier_observed["oracle_sha256"] != oracle_sha
            or verifier_observed["profile_sha256"] != profile_sha):
            raise BoundaryDenied("FIXED_PROCESS_SEPARATION_UNVERIFIED")
        fixed_pair = True
    return {
        "status": "J5_02_TOPOLOGY_PREFLIGHT_NOT_ISOLATION_CERTIFIED",
        "task_sha256": source["task_sha256"],
        "patch_sha256": source["patch_sha256"],
        "candidate_view": view,
        "candidate_and_verifier_workspaces_disjoint": True,
        "verifier_only_fixtures_digest_matched": True,
        "candidate_mounts_verifier_intersection": False,
        "trusted_fixed_process_pair_exercised": fixed_pair,
        "runtime_candidate_code_executed": False,
        "trusted_verifier_channel_established": False,
        "independent_model_patch_oracle_established": False,
        "independently_verified": False,
        "acceptance_authorized": False,
        "untrusted_code_execution_authorized": False,
        "worker_isolation_certified": False,
        "model_calls": 0,
        "project_writes": 0,
        "stable_promotable": False,
        "decision": "BLOCK_AI_ACCEPTANCE",
        "learning_effectiveness": "NOT_ESTABLISHED",
    }
