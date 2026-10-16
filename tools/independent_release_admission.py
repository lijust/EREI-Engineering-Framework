#!/usr/bin/env python3
"""Candidate-only independent two-party SSH signature admission for frozen VNext carriers.

IMPORTANT: This checks signatures and exact Git objects. It does NOT establish
server branch protection, independently audited trusted-code execution, authentic
GitHub Actions, equivalent enforcement or Stable V2 eligibility.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from . import release_target
except ImportError:
    import release_target

REPOSITORY = "lijust/EREI-Engineering-Framework"
PURPOSE = "erei-framework-v2-trusted-carrier-admission"
NAMESPACE = "erei-framework-admission@erei.invalid"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
TARGET_ID = re.compile(r"^vnext-rc[1-9][0-9]*$")
PUBLIC_KEY = re.compile(r"^ssh-ed25519 ([A-Za-z0-9+/]+={0,2})$")
ROLES = {
    "release-owner": "release-owner@erei.invalid",
    "independent-security": "independent-security@erei.invalid",
}
FIELDS = {
    "schema_version", "purpose", "repository", "target_id", "target_ref",
    "target_tree", "carrier_ref", "carrier_tree", "scope_sha256",
    "source_assurance", "issued_at", "expires_at",
}
MAX_PACKET_BYTES = 32 * 1024


class AdmissionError(RuntimeError):
    pass


def _git(repo: Path, *args: str) -> bytes:
    # Never accept caller-controlled Git replacement/configuration
    # environment for release-object provenance. Disable replace refs even
    # before probing the repository for unauthorized replacement mechanisms.
    clean_env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    clean_env["GIT_NO_REPLACE_OBJECTS"] = "1"
    # Never let an untrusted partial-clone checkout invoke its configured
    # promisor remote (including ext:: command execution) for missing objects.
    clean_env["GIT_NO_LAZY_FETCH"] = "1"
    clean_env["GIT_ALLOW_PROTOCOL"] = ""
    clean_env["GIT_PROTOCOL_FROM_USER"] = "0"
    # Git commit-graph caches include parent/tree IDs. A writable checkout may
    # contain a checksum-valid but deliberately forged graph, so all provenance
    # reads must resolve the raw Git objects, not cached commit-graph metadata.
    result = subprocess.run(
        ["git", "-C", str(repo), "-c", "core.commitGraph=false", "-c", "protocol.allow=never", "-c", "protocol.ext.allow=never", *args],
        capture_output=True, check=False, env=clean_env,
    )
    if result.returncode:
        raise AdmissionError("unavailable or inconsistent exact Git object")
    return result.stdout


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA40.fullmatch(value):
        raise AdmissionError(f"{label} must be exact lowercase 40-hex commit/tree")
    return value


def _sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise AdmissionError(f"{label} must be lowercase SHA-256")
    return value


def _timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise AdmissionError(f"{label} must be UTC RFC3339 ending in Z")
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AdmissionError(f"{label} is not an RFC3339 timestamp") from exc
    if timestamp.utcoffset() != timedelta(0):
        raise AdmissionError(f"{label} must be UTC")
    return timestamp


def _external_folder(repo: Path, folder: Path, label: str) -> Path:
    root = repo.resolve(strict=True)
    original = folder.absolute()
    if ".." in original.parts:
        raise AdmissionError(f"{label} cannot include parent traversal")
    try:
        resolved = original.resolve(strict=True)
        if not resolved.is_dir():
            raise AdmissionError(f"{label} must be an existing directory")
        if resolved == root or root in resolved.parents:
            raise AdmissionError(f"{label} must be outside the Git worktree")
        # On Windows Path.absolute() and Path.resolve() may legitimately
        # represent the same directory with different canonical casing/aliases.
        # Check the actual filesystem symlink/reparse attributes instead.
        for component in (original, *original.parents):
            attrs = component.lstat()
            if stat.S_ISLNK(attrs.st_mode) or (
                getattr(attrs, "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
            ):
                raise AdmissionError(f"{label} must be a non-symlink directory")
    except OSError as exc:
        raise AdmissionError(f"{label} is unavailable") from exc
    return resolved


def _single_file(path: Path, max_size: int = MAX_PACKET_BYTES) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise AdmissionError(f"missing or linked independent evidence file: {path.name}")
    try:
        if path.stat().st_size < 1 or path.stat().st_size > max_size:
            raise AdmissionError(f"independent evidence file size invalid: {path.name}")
        return path.read_bytes()
    except OSError as exc:
        raise AdmissionError(f"independent evidence file unavailable: {path.name}") from exc


def _envelope(raw: bytes, now: datetime) -> dict[str, Any]:
    try:
        parsed = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise AdmissionError("non-JSON admission envelope") from exc
    if not isinstance(parsed, dict) or set(parsed) != FIELDS:
        raise AdmissionError("admission envelope requires an exact governed field set")
    canonical = (json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    if raw != canonical:
        raise AdmissionError("admission envelope must use canonical UTF-8 JSON bytes")
    if type(parsed["schema_version"]) is not int or parsed["schema_version"] != 1:
        raise AdmissionError("unsupported admission version")
    if parsed["purpose"] != PURPOSE or parsed["repository"] != REPOSITORY:
        raise AdmissionError("admission scope or repository mismatch")
    if not isinstance(parsed["target_id"], str) or not TARGET_ID.fullmatch(parsed["target_id"]):
        raise AdmissionError("invalid release target id")
    for key in ("target_ref", "target_tree", "carrier_ref", "carrier_tree"):
        _sha(parsed[key], key)
    _sha256(parsed["scope_sha256"], "scope_sha256")
    assurance = parsed["source_assurance"]
    if not isinstance(assurance, dict) or set(assurance) != {"workflow", "run_id", "run_attempt", "event", "conclusion"}:
        raise AdmissionError("source_assurance must contain exact run identity")
    if assurance["workflow"] != "Framework Assurance Gate" or assurance["event"] != "push" or assurance["conclusion"] != "success":
        raise AdmissionError("source assurance must describe successful push-side gate")
    if type(assurance["run_id"]) is not int or assurance["run_id"] < 1:
        raise AdmissionError("source assurance run_id must be positive")
    if type(assurance["run_attempt"]) is not int or assurance["run_attempt"] < 1:
        raise AdmissionError("source assurance attempt must be positive")
    issued = _timestamp(parsed["issued_at"], "issued_at")
    expires = _timestamp(parsed["expires_at"], "expires_at")
    if expires <= issued or expires - issued > timedelta(hours=72):
        raise AdmissionError("admission lifetime must be positive and no more than 72 hours")
    if now < issued - timedelta(minutes=5) or now >= expires:
        raise AdmissionError("admission is not currently valid")
    return parsed


def _verify_release_objects(repo: Path, data: dict[str, Any], target: str, carrier: str) -> None:
    root = repo.resolve(strict=True)
    git_root = Path(_git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve(strict=True)
    if git_root != root:
        raise AdmissionError("release checkout must be the actual Git worktree root")
    if _git(root, "for-each-ref", "--format=%(refname)", "refs/replace").strip():
        raise AdmissionError("Git replace refs are forbidden for independently verified release objects")
    graft_raw = _git(root, "rev-parse", "--git-path", "info/grafts").decode().strip()
    graft_path = Path(graft_raw)
    if not graft_path.is_absolute():
        graft_path = root / graft_path
    if graft_path.exists() or graft_path.is_symlink():
        raise AdmissionError("Git graft records are forbidden for independently verified release objects")
    if data["target_ref"] != target or data["carrier_ref"] != carrier:
        raise AdmissionError("admission does not bind expected exact target/carrier")
    if target == carrier:
        raise AdmissionError("release target cannot equal the evidence carrier")
    # A repository supplied by an attacker can hold a counterfeit loose object
    # under the *expected* SHA filename. Revision/tree name comparisons alone
    # trust that corrupt storage. Verify the complete reachable object closure
    # and content hashes using raw Git objects; missing or corrupt blobs fail.
    _git(
        root, "fsck", "--full", "--strict", "--no-reflogs",
        "--no-progress", "--no-dangling", target, carrier,
    )
    for label, revision, recorded_tree in (
        ("target", target, data["target_tree"]),
        ("carrier", carrier, data["carrier_tree"]),
    ):
        if _git(root, "rev-parse", f"{revision}^{{commit}}").decode().strip() != revision:
            raise AdmissionError(f"{label} does not resolve to its exact immutable Git commit")
        if _git(root, "rev-parse", f"{revision}^{{tree}}").decode().strip() != recorded_tree:
            raise AdmissionError(f"{label} tree does not match signed admission")
    parent_line = _git(root, "rev-list", "--parents", "-n", "1", carrier).decode().split()
    if parent_line != [carrier, target]:
        raise AdmissionError("carrier must be one direct single-parent commit above target")
    changes = _git(root, "diff-tree", "--no-commit-id", "--name-status", "-r", carrier).decode().splitlines()
    if changes != ["A\treleases/VNEXT_TARGET.json"]:
        raise AdmissionError("initial trusted carrier may only first-add the frozen target record")
    # Diff path statuses do not distinguish a normal JSON blob from a symlink.
    manifest_entry = _git(root, "ls-tree", carrier, "--", "releases/VNEXT_TARGET.json").decode().strip()
    fields = manifest_entry.split()
    if (len(fields) != 4 or fields[0] != "100644" or fields[1] != "blob"
        or SHA40.fullmatch(fields[2]) is None or fields[3] != "releases/VNEXT_TARGET.json"):
        raise AdmissionError("frozen target manifest must be an ordinary non-executable blob")
    try:
        # json.loads(bytes) silently auto-detects UTF-16/UTF-32. The actual
        # governed release_target loader requires UTF-8, so admit only that.
        manifest_bytes = _git(root, "show", f"{carrier}:releases/VNEXT_TARGET.json")
        frozen = json.loads(manifest_bytes.decode("utf-8"))
        scope = _git(root, "show", f"{target}:releases/VNEXT_RELEASE_SCOPE.json")
        target_capabilities = json.loads(
            _git(root, "show", f"{target}:CAPABILITIES.json").decode("utf-8")
        )
    except (ValueError, UnicodeError) as exc:
        raise AdmissionError("invalid frozen target or release scope") from exc
    # Schema parity is mandatory: validating a subset of fields lets a validly
    # signed packet admit a carrier that the actual release machinery rejects.
    # The authoritative validator and its dependency must be independently
    # pinned together with this verifier on the external trust host.
    try:
        release_target.validate_manifest_shape(frozen)
    except release_target.ReleaseTargetError as exc:
        raise AdmissionError(f"frozen target manifest fails authoritative schema: {exc}") from exc
    stable = target_capabilities.get("stable_release") if isinstance(target_capabilities, dict) else None
    if (
        not isinstance(stable, dict)
        or frozen["stable_baseline"]["baseline"] != stable.get("baseline")
        or frozen["stable_baseline"]["framework_ref"] != stable.get("framework_ref")
        or frozen["framework_ref"] == frozen["stable_baseline"]["framework_ref"]
    ):
        raise AdmissionError("frozen baseline does not match authenticated target CAPABILITIES stable release")
    if (
        frozen.get("target_id") != data["target_id"]
        or frozen.get("framework_ref") != target
        or frozen.get("target_tree") != data["target_tree"]
        or frozen.get("status") != "frozen_candidate"
        or frozen.get("promotion_authorized") is not False
        or frozen.get("source_branch") != "main"
    ):
        raise AdmissionError("carrier frozen target differs from signed immutable admission")
    if hashlib.sha256(scope).hexdigest() != data["scope_sha256"]:
        raise AdmissionError("release scope hash differs from signed target scope")
    expected_assurance = frozen.get("assurance")
    signed_assurance = data["source_assurance"]
    if not isinstance(expected_assurance, dict) or any(
        expected_assurance.get(key) != signed_assurance[key]
        for key in ("workflow", "run_id", "event", "conclusion")
    ):
        raise AdmissionError("frozen target and signed push assurance metadata differ")


def _authorized_key(allowed: bytes, principal: str) -> str:
    try:
        lines = [line.strip() for line in allowed.decode("ascii").splitlines() if line.strip() and not line.startswith("#")]
    except UnicodeError as exc:
        raise AdmissionError("allowed signer keys are not ASCII") from exc
    if len(lines) != 1:
        raise AdmissionError("each role must have exactly one externally pinned authorized key")
    columns = lines[0].split()
    if len(columns) != 3 or columns[0] != principal:
        raise AdmissionError("allowed signer principal must exactly match the independent role")
    if not PUBLIC_KEY.fullmatch(" ".join(columns[1:])):
        raise AdmissionError("only one explicit ssh-ed25519 public key is allowed per role")
    try:
        blob = base64.b64decode(columns[2], validate=True)
    except ValueError as exc:
        raise AdmissionError("malformed signer public key") from exc
    if len(blob) < 40:
        raise AdmissionError("too-short signer public key")
    return columns[1] + " " + columns[2]


def verify_candidate(
    repo_root: Path, packet_dir: Path, trust_dir: Path, *,
    expected_target: str, expected_carrier: str,
    at: datetime | None = None, ssh_keygen: str = "ssh-keygen",
) -> dict[str, Any]:
    """Verify offline signatures only; always return stable_enforcement_satisfied=false."""
    target, carrier = _sha(expected_target, "expected_target"), _sha(expected_carrier, "expected_carrier")
    repo = Path(repo_root).resolve(strict=True)
    packet = _external_folder(repo, Path(packet_dir), "packet_dir")
    trust = _external_folder(repo, Path(trust_dir), "trust_dir")
    if packet == trust or packet in trust.parents or trust in packet.parents:
        raise AdmissionError("trust directory and submitted packet must be independent")
    envelope_bytes = _single_file(packet / "admission.json")
    now = at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise AdmissionError("verification clock must be timezone-aware")
    data = _envelope(envelope_bytes, now.astimezone(timezone.utc))
    _verify_release_objects(repo, data, target, carrier)
    pinned_keys: dict[str, str] = {}
    for role, principal in ROLES.items():
        allowed = trust / f"{role}.allowed_signers"
        key = _authorized_key(_single_file(allowed), principal)
        if key in pinned_keys.values():
            raise AdmissionError("release owner and independent security cannot share one key")
        pinned_keys[role] = key
    for role, principal in ROLES.items():
        executable = shutil.which(ssh_keygen)
        if not executable:
            raise AdmissionError("OpenSSH ssh-keygen -Y verification is unavailable")
        result = subprocess.run(
            [executable, "-Y", "verify", "-f", str(trust / f"{role}.allowed_signers"),
             "-I", principal, "-n", NAMESPACE, "-s", str(packet / f"{role}.sig")],
            input=envelope_bytes, capture_output=True, timeout=20, check=False
        )
        if result.returncode:
            raise AdmissionError(f"detached independent SSH signature invalid for {role}")
    return {
        "status": "verified_offline_signatures_only",
        "target_ref": target, "carrier_ref": carrier,
        "signed_envelope_sha256": hashlib.sha256(envelope_bytes).hexdigest(),
        "verified_roles": list(ROLES),
        "stable_enforcement_satisfied": False,
        "live_actions_run_authenticated": False,
        "trusted_verifier_host_attested": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Candidate-only out-of-band release admission verification")
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--packet-dir", required=True, type=Path)
    parser.add_argument("--trust-dir", required=True, type=Path)
    parser.add_argument("--expected-target", required=True)
    parser.add_argument("--expected-carrier", required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(verify_candidate(
            args.repo_root, args.packet_dir, args.trust_dir,
            expected_target=args.expected_target, expected_carrier=args.expected_carrier,
        ), sort_keys=True))
    except (AdmissionError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
