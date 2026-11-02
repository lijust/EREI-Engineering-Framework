"""J5-01: read-only Git source binding built on the Framework J2 contract.

NOT an execution permit, independent verifier, sealed oracle, or acceptance
authority. Trusted pins MUST arrive from an operator-controlled channel, not
from the patch author. No patch is applied and no candidate code is executed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

from tools import repair_evidence_contract as j2

PIN_KEYS = frozenset({
    "task_sha256", "base_sha", "oracle_sha256", "worker_profile_sha256",
})
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
MAX_SOURCE_BYTES = 1024 * 1024


class SourceBindingDenied(ValueError):
    """A pinned source/identity prerequisite is not satisfied."""


def canonical_task_sha256(task: Any) -> str:
    """Digest canonical J2 task encoding; this digest is NOT an attestation."""
    try:
        raw = json.dumps(task, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise SourceBindingDenied("TASK_ENCODING_INVALID") from exc
    return hashlib.sha256(raw).hexdigest()


def _git(root: Path, *args: str) -> bytes:
    """Read-only Git operations; no shell and no Git hooks of our own."""
    try:
        return subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "--no-optional-locks",
             *args], cwd=root, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            check=True, timeout=10,
        ).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise SourceBindingDenied("SOURCE_GIT_READ_FAILED") from exc


def _read_source(root: Path, base_sha: str, name: str) -> dict[str, str]:
    # J2 validated 'name' as a canonical, exact, allowlisted ASCII path.
    listing = _git(root, "ls-tree", "-z", "--full-tree", base_sha, "--", name)
    entries = [e for e in listing.split(b"\x00") if e]
    if len(entries) != 1:
        raise SourceBindingDenied("SOURCE_NOT_EXACTLY_ONE_TRACKED_FILE")
    metadata, sep, actual = entries[0].partition(b"\t")
    if not sep or actual != name.encode("ascii"):
        raise SourceBindingDenied("SOURCE_PATH_MISMATCH")
    fields = metadata.split()
    # Explicitly exclude 120000 symlinks, 160000 submodules, 100755 scripts.
    if len(fields) != 3 or fields[0] != b"100644" or fields[1] != b"blob":
        raise SourceBindingDenied("SOURCE_MODE_OR_TYPE_PROHIBITED")
    oid = fields[2].decode("ascii")
    if SHA40.fullmatch(oid) is None:
        raise SourceBindingDenied("SOURCE_BLOB_ID_INVALID")
    raw_size = _git(root, "cat-file", "-s", oid).strip()
    try:
        size = int(raw_size)
    except ValueError as exc:
        raise SourceBindingDenied("SOURCE_BLOB_SIZE_INVALID") from exc
    if not 1 <= size <= MAX_SOURCE_BYTES:
        raise SourceBindingDenied("SOURCE_BLOB_SIZE_OUT_OF_BOUNDS")
    raw = _git(root, "cat-file", "blob", oid)
    if len(raw) != size:
        raise SourceBindingDenied("SOURCE_BLOB_READ_INCOMPLETE")
    return {"path": name, "git_mode": "100644", "git_blob_sha": oid,
            "source_sha256": hashlib.sha256(raw).hexdigest()}


def bind_pinned_source(
    root: Path | str,
    task: dict,
    proposal: dict,
    trusted_pins: dict,
    *,
    reported_result: dict | None = None,
) -> dict:
    """Fail closed on base/path/mode/content/patch/claimed-report drift.

    'trusted_pins' is an external operator/verifier input, not model output.
    Comparing digest strings does not prove that it came from that authority.
    """
    envelope = j2.validate_patch(task, proposal)  # Only J2 owns schema rules.
    if type(trusted_pins) is not dict or set(trusted_pins) != PIN_KEYS:
        raise SourceBindingDenied("TRUSTED_PINS_SCHEMA_INVALID")
    if any(type(value) is not str or SHA256.fullmatch(value) is None
           for name, value in trusted_pins.items() if name != "base_sha"):
        raise SourceBindingDenied("TRUSTED_PIN_DIGEST_INVALID")
    if (type(trusted_pins["base_sha"]) is not str
        or SHA40.fullmatch(trusted_pins["base_sha"]) is None):
        raise SourceBindingDenied("TRUSTED_BASE_INVALID")
    if (trusted_pins["task_sha256"] != canonical_task_sha256(task)
        or trusted_pins["base_sha"] != task["base_sha"]
        or trusted_pins["oracle_sha256"] != task["oracle_sha256"]
        or trusted_pins["worker_profile_sha256"] != task["worker_profile_sha256"]):
        raise SourceBindingDenied("TRUSTED_PINS_MISMATCH")

    try:
        root = Path(root).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise SourceBindingDenied("SOURCE_ROOT_MISSING") from exc
    if not root.is_dir():
        raise SourceBindingDenied("SOURCE_ROOT_NOT_DIRECTORY")
    if _git(root, "rev-parse", "--is-inside-work-tree").strip() != b"true":
        raise SourceBindingDenied("SOURCE_NOT_GIT_WORKTREE")
    top = _git(root, "rev-parse", "--show-toplevel").strip()
    if Path(top.decode("utf-8")).resolve() != root:
        raise SourceBindingDenied("SOURCE_ROOT_MISMATCH")
    head = _git(root, "rev-parse", "--verify", "HEAD^{commit}").strip()
    if head.decode("ascii") != task["base_sha"]:
        raise SourceBindingDenied("SOURCE_BASE_HEAD_MISMATCH")
    # Exact checkout must be clean, including untracked files. Ignored paths
    # are not used as source; verifier workspace isolation is a later J5 gate.
    if _git(root, "status", "--porcelain=v1", "-z",
            "--untracked-files=all"):
        raise SourceBindingDenied("SOURCE_WORKTREE_DIRTY")
    sources = [_read_source(root, task["base_sha"], name)
               for name in task["allowed_paths"]]
    claim_status = "NO_CANDIDATE_REPORT"
    if reported_result is not None:
        claim = j2.bind_reported_result(task, proposal, reported_result)
        if claim.get("acceptance_authorized") is not False:
            raise SourceBindingDenied("UNTRUSTED_CLAIM_HAS_AUTHORITY")
        claim_status = claim["status"]
    return {
        "status": "J5_01_PINNED_SOURCE_BOUND_NOT_INDEPENDENTLY_VERIFIED",
        "base_sha": task["base_sha"],
        "task_sha256": trusted_pins["task_sha256"],
        "patch_sha256": envelope["patch_sha256"],
        "oracle_sha256": task["oracle_sha256"],
        "worker_profile_sha256": task["worker_profile_sha256"],
        "sources": sources,
        "reported_claim_status": claim_status,
        "trusted_verifier_channel_established": False,
        "independently_verified": False,
        "acceptance_authorized": False,
        "untrusted_code_execution_authorized": False,
        "worker_isolation_certified": False,
        "executed": False,
        "project_writes": 0,
        "model_calls": 0,
        "stable_promotable": False,
        "decision": "BLOCK_AI_ACCEPTANCE",
        "learning_effectiveness": "NOT_ESTABLISHED",
    }
