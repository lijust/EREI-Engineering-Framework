#!/usr/bin/env python3
"""Verify immutable Stable release carriers before project adoption.

A Framework target commit is not considered Stable merely because BASELINE.json says
"stable". New Stable releases must be proven by an immutable release carrier that
binds the exact target, frozen closure, exact-target evidence, enforcement and final
approvals. The historical task-learning-review-v1 release is the only V1 grandfather.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from . import release_approval, release_assurance, release_target
except ImportError:
    import release_approval
    import release_assurance
    import release_target

SHA40_RE = re.compile(r"^[a-f0-9]{40}$")
LEGACY_STABLE_REF = "69079018606750312344cb3c648952b9ab72d35b"
LEGACY_STABLE_ID = "task-learning-review-v1"
LEGACY_MANIFEST = "releases/task-learning-review-v1.json"
V2_STABLE_MANIFEST = "releases/vnext-assurance-v2-stable.json"
TARGET_MANIFEST = "releases/VNEXT_TARGET.json"


class StableCarrierError(RuntimeError):
    pass


def _exact_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA40_RE.fullmatch(value):
        raise StableCarrierError(f"{label} must be an exact 40-character commit")
    return value


def _run(repo: Path, *args: str, binary: bool = False) -> str | bytes:
    process = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=not binary,
        check=False,
    )
    if process.returncode != 0:
        stderr = process.stderr if isinstance(process.stderr, str) else process.stderr.decode("utf-8", errors="replace")
        raise StableCarrierError(f"git {' '.join(args)} failed: {stderr.strip()}")
    return process.stdout


def _resolve_exact_commit(repo: Path, revision: str, label: str) -> str:
    revision = _exact_sha(revision, label)
    resolved = str(_run(repo, "rev-parse", "--verify", f"{revision}^{{commit}}")).strip()
    if resolved != revision:
        raise StableCarrierError(f"{label} did not resolve exactly to {revision}")
    return revision


def _assert_ancestor(repo: Path, ancestor: str, descendant: str, label: str) -> None:
    process = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", ancestor, descendant],
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        raise StableCarrierError(f"{label}: {ancestor} must be an ancestor of {descendant}")


def _git_json(repo: Path, revision: str, path: str) -> dict[str, Any]:
    try:
        text = str(_run(repo, "show", f"{revision}:{path}"))
    except StableCarrierError as exc:
        raise StableCarrierError(f"missing {path} at release carrier {revision}") from exc
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise StableCarrierError(f"invalid JSON {path} at {revision}: {exc}") from exc
    if not isinstance(value, dict):
        raise StableCarrierError(f"{path} at {revision} must contain a JSON object")
    return value


def _tree_for(repo: Path, revision: str) -> str:
    value = str(_run(repo, "rev-parse", f"{revision}^{{tree}}")).strip()
    return _exact_sha(value, "target tree")


def _release_manifest_paths(repo: Path, carrier_ref: str) -> list[str]:
    output = str(_run(repo, "ls-tree", "-r", "--name-only", carrier_ref, "releases"))
    return sorted(
        path.strip()
        for path in output.splitlines()
        if path.strip().startswith("releases/")
        and path.strip().endswith(".json")
        and path.strip().count("/") == 1
    )


def _find_stable_manifest(repo: Path, target_ref: str, carrier_ref: str) -> tuple[str, dict[str, Any]]:
    matches: list[tuple[str, dict[str, Any]]] = []
    for path in _release_manifest_paths(repo, carrier_ref):
        value = _git_json(repo, carrier_ref, path)
        if value.get("status") == "stable" and value.get("framework_ref") == target_ref:
            matches.append((path, value))
    if not matches:
        raise StableCarrierError(
            f"release carrier {carrier_ref} has no Stable manifest bound to target {target_ref}"
        )
    if len(matches) != 1:
        raise StableCarrierError(
            f"release carrier {carrier_ref} has multiple Stable manifests bound to target {target_ref}"
        )
    return matches[0]


def _closure_changes(repo: Path, target_ref: str, carrier_ref: str) -> list[tuple[str, str]]:
    output = str(_run(repo, "diff", "--name-status", "--no-renames", f"{target_ref}..{carrier_ref}"))
    rows: list[tuple[str, str]] = []
    for raw in output.splitlines():
        if not raw.strip():
            continue
        parts = raw.split("\t")
        if len(parts) != 2:
            raise StableCarrierError(f"unexpected closure diff row: {raw}")
        rows.append((parts[0], parts[1]))
    return rows


def _blob(repo: Path, revision: str, path: str) -> str:
    return str(_run(repo, "rev-parse", f"{revision}:{path}")).strip()


def _first_write_commit(repo: Path, target_ref: str, carrier_ref: str, path: str) -> str:
    commits = [
        item.strip()
        for item in str(_run(repo, "log", "--reverse", "--format=%H", f"{target_ref}..{carrier_ref}", "--", path)).splitlines()
        if item.strip()
    ]
    if not commits:
        raise StableCarrierError(f"unable to resolve first post-freeze write for {path}")
    return _exact_sha(commits[0], f"first write commit for {path}")


def _assert_first_write_immutable(repo: Path, target_ref: str, carrier_ref: str, path: str) -> str:
    first = _first_write_commit(repo, target_ref, carrier_ref, path)
    try:
        first_blob = _blob(repo, first, path)
        current_blob = _blob(repo, carrier_ref, path)
    except StableCarrierError as exc:
        raise StableCarrierError(f"closure artifact {path} must exist at its first write and at carrier HEAD") from exc
    if first_blob != current_blob:
        raise StableCarrierError(
            f"closure artifact {path} changed after its first post-freeze write; carrier is not immutable"
        )
    return first


def _validate_v2_closure(repo: Path, target_ref: str, carrier_ref: str) -> list[str]:
    changes = _closure_changes(repo, target_ref, carrier_ref)
    for status, path in changes:
        if status not in {"A", "M"}:
            raise StableCarrierError(f"V2 release closure forbids status {status} for {path}")
        if not release_target.allowed_closure_path(path):
            raise StableCarrierError(
                f"V2 release carrier contains behavior/governance drift outside the closure allowlist: {path}"
            )
        _assert_first_write_immutable(repo, target_ref, carrier_ref, path)
    return [path for _, path in changes]


def _safe_materialize(repo: Path, carrier_ref: str, destination: Path) -> None:
    archive_bytes = _run(repo, "archive", "--format=tar", carrier_ref, binary=True)
    assert isinstance(archive_bytes, bytes)
    destination = destination.resolve()
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:") as archive:
        members = archive.getmembers()
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts:
                raise StableCarrierError(f"unsafe path in release carrier archive: {member.name}")
            if member.issym() or member.islnk() or member.isdev():
                raise StableCarrierError(f"unsupported link/device in release carrier archive: {member.name}")
            output = destination.joinpath(*path.parts)
            if member.isdir():
                output.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise StableCarrierError(f"unsupported archive member type: {member.name}")
            output.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise StableCarrierError(f"unable to read archive member: {member.name}")
            output.write_bytes(source.read())


def _validate_legacy(path: str, manifest: dict[str, Any], target_ref: str) -> dict[str, Any]:
    if target_ref != LEGACY_STABLE_REF:
        raise StableCarrierError("Assurance Contract V1 is grandfathered only for the immutable last Stable release")
    if path != LEGACY_MANIFEST:
        raise StableCarrierError("legacy Stable manifest path mismatch")
    if manifest.get("release_id") != LEGACY_STABLE_ID or manifest.get("baseline") != LEGACY_STABLE_ID:
        raise StableCarrierError("legacy Stable identity mismatch")
    if manifest.get("assurance_contract_version") != 1:
        raise StableCarrierError("legacy Stable assurance contract version mismatch")
    try:
        result = release_assurance.validate_manifest(manifest)
    except release_assurance.ReleaseError as exc:
        raise StableCarrierError(f"invalid legacy Stable manifest: {exc}") from exc
    return result


def _validate_approval_ref(
    repo: Path,
    target_ref: str,
    carrier_ref: str,
    value: Any,
    label: str,
    *,
    approval_type: str,
    approval_path: str,
    target_tree: str,
) -> str:
    ref = _resolve_exact_commit(repo, _exact_sha(value, label), label)
    if ref == target_ref:
        raise StableCarrierError(f"{label} must be a post-target immutable approval commit")
    _assert_ancestor(repo, target_ref, ref, label)
    _assert_ancestor(repo, ref, carrier_ref, label)

    first = _assert_first_write_immutable(repo, target_ref, carrier_ref, approval_path)
    if ref != first:
        raise StableCarrierError(
            f"{label} must equal the first commit that writes {approval_path}; expected {first}, got {ref}"
        )
    try:
        record = _git_json(repo, ref, approval_path)
        release_approval.validate_record(
            record,
            expected_type=approval_type,
            expected_target=target_ref,
            expected_tree=target_tree,
            require_approved=True,
        )
    except release_approval.ReleaseApprovalError as exc:
        raise StableCarrierError(f"invalid {approval_type} approval record at {ref}: {exc}") from exc
    if _blob(repo, ref, approval_path) != _blob(repo, carrier_ref, approval_path):
        raise StableCarrierError(f"{approval_type} approval record changed after its bound approval ref")
    return ref


def _validate_v2(
    repo: Path,
    path: str,
    manifest: dict[str, Any],
    target_ref: str,
    carrier_ref: str,
) -> tuple[dict[str, Any], list[str]]:
    if path != V2_STABLE_MANIFEST:
        raise StableCarrierError(f"V2 Stable manifest must be {V2_STABLE_MANIFEST}")
    if type(manifest.get("assurance_contract_version")) is not int or manifest["assurance_contract_version"] < 2:
        raise StableCarrierError("new Stable releases require Assurance Contract V2 or later")

    target_manifest = _git_json(repo, carrier_ref, TARGET_MANIFEST)
    try:
        release_target.validate_manifest_shape(target_manifest)
    except release_target.ReleaseTargetError as exc:
        raise StableCarrierError(f"invalid frozen release target: {exc}") from exc
    if target_manifest["framework_ref"] != target_ref:
        raise StableCarrierError("frozen release target framework_ref does not match requested target")
    target_tree = _tree_for(repo, target_ref)
    if target_manifest["target_tree"] != target_tree:
        raise StableCarrierError("frozen release target tree does not match requested target tree")

    changed_paths = _validate_v2_closure(repo, target_ref, carrier_ref)
    if TARGET_MANIFEST not in changed_paths:
        raise StableCarrierError("V2 Stable carrier must include the immutable frozen release target")
    if V2_STABLE_MANIFEST not in changed_paths:
        raise StableCarrierError("V2 Stable carrier must include the final Stable manifest")

    _validate_approval_ref(
        repo,
        target_ref,
        carrier_ref,
        manifest.get("approval_ref"),
        "approval_ref",
        approval_type="architecture",
        approval_path=release_approval.APPROVAL_PATHS["architecture"],
        target_tree=target_tree,
    )
    _validate_approval_ref(
        repo,
        target_ref,
        carrier_ref,
        manifest.get("security_review_ref"),
        "security_review_ref",
        approval_type="security",
        approval_path=release_approval.APPROVAL_PATHS["security"],
        target_tree=target_tree,
    )

    with tempfile.TemporaryDirectory() as tmp:
        materialized = Path(tmp)
        _safe_materialize(repo, carrier_ref, materialized)
        try:
            result = release_assurance.validate_manifest(manifest, repo_root=materialized)
        except (release_assurance.ReleaseError, OSError) as exc:
            raise StableCarrierError(f"V2 Stable release assurance failed: {exc}") from exc
    if result.get("status") != "stable" or result.get("framework_ref") != target_ref:
        raise StableCarrierError("V2 Stable release assurance did not validate the requested target")
    if result.get("approval_records_validated") != 2:
        raise StableCarrierError("V2 Stable release assurance did not validate both structured approval records")
    return result, changed_paths


def verify_stable_release_carrier(repo: Path, target_ref: str, carrier_ref: str) -> dict[str, Any]:
    repo = repo.resolve()
    if not (repo / ".git").exists():
        raise StableCarrierError(f"Framework repository is not a Git checkout: {repo}")
    target_ref = _resolve_exact_commit(repo, target_ref, "target_ref")
    carrier_ref = _resolve_exact_commit(repo, carrier_ref, "release_carrier_ref")
    _assert_ancestor(repo, target_ref, carrier_ref, "release carrier ancestry")
    path, manifest = _find_stable_manifest(repo, target_ref, carrier_ref)

    version = manifest.get("assurance_contract_version")
    if version == 1:
        assurance = _validate_legacy(path, manifest, target_ref)
        changed_paths: list[str] | None = None
        grandfathered = True
    elif type(version) is int and version >= 2:
        assurance, changed_paths = _validate_v2(repo, path, manifest, target_ref, carrier_ref)
        grandfathered = False
    else:
        raise StableCarrierError("Stable release manifest has unsupported assurance_contract_version")

    return {
        "status": "verified_stable_release_carrier",
        "framework_ref": target_ref,
        "carrier_ref": carrier_ref,
        "manifest_path": path,
        "release_id": manifest["release_id"],
        "baseline": manifest["baseline"],
        "assurance_contract_version": version,
        "grandfathered_v1": grandfathered,
        "closure_changed_paths": changed_paths,
        "release_assurance": assurance,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework-repo", required=True)
    parser.add_argument("--target-ref", required=True)
    parser.add_argument("--release-carrier-ref", required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_stable_release_carrier(
            Path(args.framework_repo), args.target_ref, args.release_carrier_ref
        )
    except StableCarrierError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
