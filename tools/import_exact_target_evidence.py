#!/usr/bin/env python3
"""Validate and atomically import an exact-target evidence package into a frozen release closure."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import types
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

# A governed release evidence commit may contain only the three retained files.
# Stop Python imports from creating untracked tools/__pycache__ in the carrier.
# This must run before importing any local release validation modules.
sys.dont_write_bytecode = True

try:
    from . import exact_target_evidence, exact_target_package_identity, release_target, release_scope, github_actions_artifact_provenance
except ImportError:
    import exact_target_evidence
    import exact_target_package_identity
    import release_target
    import release_scope
    import github_actions_artifact_provenance

OFFICIAL_REPOSITORY = "lijust/EREI-Engineering-Framework"

PACKAGE_FILES = {
    "identity": "runtime-identity.json",
    "manifest": "exact-target-run.json",
    "evidence": "execution-evidence.json",
}


class ExactTargetImportError(RuntimeError):
    pass


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExactTargetImportError(f"unable to load {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ExactTargetImportError(f"{label} must be a JSON object")
    return value


def _digest_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ExactTargetImportError(f"unable to hash {path}: {exc}") from exc


def _git_head(repo_root: Path) -> str:
    process = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise ExactTargetImportError(f"unable to resolve release carrier HEAD: {process.stderr.strip()}")
    value = process.stdout.strip()
    if not exact_target_package_identity.SHA40_RE.fullmatch(value):
        raise ExactTargetImportError("release carrier HEAD must be an exact lowercase 40-character commit")
    return value


def _load_runner(repo_root: Path):
    path = repo_root / "evals" / "runner.py"
    try:
        source = path.read_bytes()
        module = types.ModuleType("erei_import_eval_runner")
        module.__file__ = str(path)
        exec(compile(source, str(path), "exec"), module.__dict__)
    except (OSError, SyntaxError) as exc:
        raise ExactTargetImportError(f"unable to load eval runner: {exc}") from exc
    return module


def _closure_destination(value: Any, *, prefix: str, label: str) -> Path:
    try:
        path = exact_target_package_identity.validate_relative_json_path(
            value, prefix=prefix, label=label
        )
    except exact_target_package_identity.ExactTargetPackageIdentityError as exc:
        raise ExactTargetImportError(str(exc)) from exc
    if not release_target.allowed_closure_path(path.as_posix()):
        raise ExactTargetImportError(f"{label} is outside the frozen release closure allowlist")
    return path


def _stage_binding_root(
    repo_root: Path,
    *,
    manifest_path: Path,
    manifest_bytes: bytes,
    evidence_path: Path,
    evidence_bytes: bytes,
    identity_path: Path,
    identity_bytes: bytes,
) -> tempfile.TemporaryDirectory:
    temp = tempfile.TemporaryDirectory(prefix="erei-exact-target-import-")
    staged = Path(temp.name)
    (staged / "evals").mkdir(parents=True)
    shutil.copy2(repo_root / "evals" / "runner.py", staged / "evals" / "runner.py")
    shutil.copytree(repo_root / "evals" / "cases", staged / "evals" / "cases")
    for relative, payload in (
        (manifest_path, manifest_bytes),
        (evidence_path, evidence_bytes),
        (identity_path, identity_bytes),
    ):
        target = staged / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    return temp


def _identity(data: Any) -> dict[str, Any]:
    try:
        return exact_target_package_identity.validate_runtime_identity(data)
    except exact_target_package_identity.ExactTargetPackageIdentityError as exc:
        raise ExactTargetImportError(str(exc)) from exc


def validate_package(repo_root: Path, package_dir: Path, *, artifact_zip: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    package_dir = package_dir.resolve()
    try:
        target = release_target.load_and_validate_target(repo_root)
        release_target.validate_closure(repo_root, target)
    except release_target.ReleaseTargetError as exc:
        raise ExactTargetImportError(f"invalid or drifted frozen release carrier: {exc}") from exc

    identity_package = package_dir / PACKAGE_FILES["identity"]
    manifest_package = package_dir / PACKAGE_FILES["manifest"]
    evidence_package = package_dir / PACKAGE_FILES["evidence"]
    try:
        identity_bytes = identity_package.read_bytes()
        manifest_bytes = manifest_package.read_bytes()
        evidence_bytes = evidence_package.read_bytes()
        identity = _identity(json.loads(identity_bytes))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExactTargetImportError(f"unable to load exact-target package bytes: {exc}") from exc
    if identity["repository"] != OFFICIAL_REPOSITORY:
        raise ExactTargetImportError("package repository does not match the official release repository")

    if identity["target_id"] != target["target_id"]:
        raise ExactTargetImportError("runtime identity target_id does not match frozen release target")
    if identity["framework_ref"] != target["framework_ref"]:
        raise ExactTargetImportError("runtime identity framework_ref does not match frozen release target")
    if identity["target_tree"] != target["target_tree"]:
        raise ExactTargetImportError("runtime identity target_tree does not match frozen release target")
    if identity["adapter_revision"] != target["framework_ref"]:
        raise ExactTargetImportError("vendored adapter revision must equal the frozen target ref")
    if _git_head(repo_root) != identity["release_carrier_ref"]:
        raise ExactTargetImportError("import must run at the exact release carrier used to execute the runtime evidence")

    if hashlib.sha256(manifest_bytes).hexdigest() != identity["run_manifest_sha256"]:
        raise ExactTargetImportError("run manifest package digest mismatch")
    if hashlib.sha256(evidence_bytes).hexdigest() != identity["execution_evidence_sha256"]:
        raise ExactTargetImportError("execution evidence package digest mismatch")

    try:
        manifest = exact_target_evidence.validate_run_manifest(json.loads(manifest_bytes))
    except (UnicodeError, json.JSONDecodeError, exact_target_evidence.ExactTargetEvidenceError) as exc:
        raise ExactTargetImportError(f"invalid run manifest: {exc}") from exc
    if manifest["run_id"] != identity["run_id"]:
        raise ExactTargetImportError("runtime identity run_id does not match run manifest")
    if manifest["framework_revision"] != target["framework_ref"]:
        raise ExactTargetImportError("run manifest framework_revision does not match frozen target")
    if manifest["adapter"]["id"] != identity["adapter_id"]:
        raise ExactTargetImportError("run manifest adapter id does not match runtime identity")
    if manifest["adapter"]["revision"] != identity["adapter_revision"]:
        raise ExactTargetImportError("run manifest adapter revision does not match runtime identity")
    if manifest["runtime"]["id"] != identity["runtime_id"]:
        raise ExactTargetImportError("run manifest runtime id does not match runtime identity")
    if manifest["runtime"]["version"] != identity["runtime_version"]:
        raise ExactTargetImportError("run manifest runtime version does not match runtime identity")
    if set(manifest["runtime"]["identity_evidence"]) != exact_target_package_identity.expected_runtime_evidence(identity):
        raise ExactTargetImportError("run manifest runtime identity evidence does not match package provenance")

    runner = _load_runner(repo_root)
    try:
        evidence = runner.validate_execution_evidence(json.loads(evidence_bytes))
    except (UnicodeError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        raise ExactTargetImportError(f"invalid execution evidence: {exc}") from exc
    if evidence.get("schema_version") != 2:
        raise ExactTargetImportError("execution evidence must use schema_version 2")
    if evidence.get("framework_revision") != target["framework_ref"]:
        raise ExactTargetImportError("execution evidence framework_revision does not match frozen target")
    try:
        frozen_scope, scope_summary = release_scope.load_target_bound_scope(
            repo_root, target["framework_ref"], closure_ref="HEAD"
        )
    except release_scope.ReleaseScopeError as exc:
        raise ExactTargetImportError(f"invalid target-bound release scope: {exc}") from exc
    if frozen_scope is not None:
        expected = {
            (item["suite_id"], item["case_id"])
            for item in scope_summary["required_eval_case_pairs"]
        }
    else:
        expected = runner._expected_cases(
            [str(repo_root / "evals" / "cases")], minimum_level="exact_target_runtime"
        )
    observed = {(row["suite_id"], row["case_id"]): row for row in evidence["executions"]}
    if set(observed) != expected:
        raise ExactTargetImportError(
            f"exact-target package case set mismatch missing={len(expected - set(observed))} "
            f"unexpected={len(set(observed) - expected)}"
        )

    manifest_destination = _closure_destination(
        identity["run_manifest_path"], prefix="evals/exact-target-runs/", label="run_manifest_path"
    )
    evidence_destination = _closure_destination(
        identity["execution_evidence_path"], prefix="evals/EXECUTION_EVIDENCE.", label="execution_evidence_path"
    )
    identity_destination = _closure_destination(
        identity["runtime_identity_path"], prefix="evals/exact-target-runs/", label="runtime_identity_path"
    )
    try:
        expected_identity_destination = exact_target_package_identity.identity_path_for_manifest(manifest_destination)
    except exact_target_package_identity.ExactTargetPackageIdentityError as exc:
        raise ExactTargetImportError(str(exc)) from exc
    if identity_destination != expected_identity_destination:
        raise ExactTargetImportError("runtime identity destination is not derived from the run manifest path")

    for destination in (manifest_destination, evidence_destination, identity_destination):
        if (repo_root / destination).exists():
            raise ExactTargetImportError(f"release evidence destination already exists: {destination}")

    for key, row in observed.items():
        if row["status"] != "pass":
            raise ExactTargetImportError(f"exact-target case is not PASS: {key[0]}/{key[1]}")
        if row.get("assurance_level") != "exact_target_runtime" or row.get("independent_runtime") is not True:
            raise ExactTargetImportError(f"case lacks exact independent runtime assurance: {key[0]}/{key[1]}")
        path, suite_id, case_id = exact_target_evidence.parse_evidence_ref(row.get("evidence_ref"))
        if path != manifest_destination or (suite_id, case_id) != key:
            raise ExactTargetImportError(f"evidence_ref does not bind imported manifest for {key[0]}/{key[1]}")

    try:
        actions_receipt = github_actions_artifact_provenance.verify_official_run_artifact(
            identity,
            {
                "exact-target-run.json": manifest_bytes,
                "execution-evidence.json": evidence_bytes,
                "runtime-identity.json": identity_bytes,
            },
            archive=artifact_zip,
            token=os.environ.get("EREI_EVIDENCE_GITHUB_TOKEN"),
        )
    except github_actions_artifact_provenance.ActionsProvenanceError as exc:
        raise ExactTargetImportError(f"GitHub Actions artifact provenance not authenticated: {exc}") from exc

    with _stage_binding_root(
        repo_root,
        manifest_path=manifest_destination,
        manifest_bytes=manifest_bytes,
        evidence_path=evidence_destination,
        evidence_bytes=evidence_bytes,
        identity_path=identity_destination,
        identity_bytes=identity_bytes,
    ) as temp_root:
        staged_root = Path(temp_root)
        for key, row in observed.items():
            try:
                exact_target_evidence.validate_binding(staged_root, target["framework_ref"], row)
            except exact_target_evidence.ExactTargetEvidenceError as exc:
                raise ExactTargetImportError(
                    f"reconstructible exact-target binding failed for {key[0]}/{key[1]}: {exc}"
                ) from exc

    return {
        "target": target,
        "identity": identity,
        "manifest_destination": manifest_destination,
        "evidence_destination": evidence_destination,
        "identity_destination": identity_destination,
        "manifest_bytes": manifest_bytes,
        "evidence_bytes": evidence_bytes,
        "identity_bytes": identity_bytes,
        "case_count": len(expected),
        "actions_provenance": actions_receipt,
    }


def _exclusive_write_set(writes: tuple[tuple[Path, Path], ...]) -> None:
    """Reserve every destination exclusively, write all bytes, and rollback the whole set on failure."""
    if not writes:
        raise ExactTargetImportError("evidence import write set must not be empty")
    handles: list[tuple[Any, bytes | Path, Path]] = []
    created: list[Path] = []
    rollback_errors: list[str] = []
    try:
        for _, destination in writes:
            destination.parent.mkdir(parents=True, exist_ok=True)
        for source, destination in writes:
            try:
                handle = destination.open("xb")
            except FileExistsError as exc:
                raise ExactTargetImportError(f"release evidence destination already exists: {destination}") from exc
            handles.append((handle, source, destination))
            created.append(destination)
        for handle, source, _ in handles:
            payload = source if isinstance(source, bytes) else source.read_bytes()
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        for handle, _, _ in handles:
            handle.close()
    except Exception as exc:
        for handle, _, _ in handles:
            try:
                if not handle.closed:
                    handle.close()
            except OSError:
                pass
        for destination in reversed(created):
            try:
                destination.unlink(missing_ok=True)
            except OSError as rollback_exc:
                rollback_errors.append(f"{destination}: {rollback_exc}")
        if rollback_errors:
            raise ExactTargetImportError(
                "evidence import failed and rollback was incomplete: " + "; ".join(rollback_errors)
            ) from exc
        if isinstance(exc, ExactTargetImportError):
            raise
        raise ExactTargetImportError(f"evidence import failed and was rolled back: {exc}") from exc


# Backward-compatible private alias for existing unit tests; implementation supports any non-empty set.
def _exclusive_write_pair(writes: tuple[tuple[Path, Path], ...]) -> None:
    _exclusive_write_set(writes)


def import_package(repo_root: Path, package_dir: Path, *, artifact_zip: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    validated = validate_package(repo_root, package_dir, artifact_zip=artifact_zip)
    writes = (
        (validated["manifest_bytes"], repo_root / validated["manifest_destination"]),
        (validated["evidence_bytes"], repo_root / validated["evidence_destination"]),
        (validated["identity_bytes"], repo_root / validated["identity_destination"]),
    )
    _exclusive_write_set(writes)
    return validated


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--package-dir", required=True)
    parser.add_argument("--actions-artifact-zip", help="Original ZIP downloaded from authenticated GitHub Actions run")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = (
            validate_package(Path(args.repo_root), Path(args.package_dir), artifact_zip=Path(args.actions_artifact_zip) if args.actions_artifact_zip else None)
            if args.validate_only
            else import_package(Path(args.repo_root), Path(args.package_dir), artifact_zip=Path(args.actions_artifact_zip) if args.actions_artifact_zip else None)
        )
    except (
        ExactTargetImportError,
        exact_target_package_identity.ExactTargetPackageIdentityError,
        release_target.ReleaseTargetError,
        OSError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "status": "valid" if args.validate_only else "imported",
        "target_id": result["target"]["target_id"],
        "framework_ref": result["target"]["framework_ref"],
        "run_id": result["identity"]["run_id"],
        "cases": result["case_count"],
        "github_actions_artifact_authenticated": result["actions_provenance"]["authenticated"],
        "run_manifest_path": result["manifest_destination"].as_posix(),
        "execution_evidence_path": result["evidence_destination"].as_posix(),
        "runtime_identity_path": result["identity_destination"].as_posix(),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
