#!/usr/bin/env python3
"""Validate an exact-target Actions evidence package before writing it into a frozen release closure."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from . import exact_target_evidence, release_target
except ImportError:
    import exact_target_evidence
    import release_target

SHA40_RE = re.compile(r"^[a-f0-9]{40}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
RUN_ID_RE = re.compile(r"^ETR-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-.][0-9A-Za-z.-]+)?$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
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


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExactTargetImportError(f"{label} must be a non-empty string")
    return value.strip()


def _sha40(value: Any, label: str) -> str:
    text = _text(value, label)
    if not SHA40_RE.fullmatch(text):
        raise ExactTargetImportError(f"{label} must be an exact lowercase 40-character commit")
    return text


def _sha256(value: Any, label: str) -> str:
    text = _text(value, label)
    if not SHA256_RE.fullmatch(text):
        raise ExactTargetImportError(f"{label} must be a lowercase SHA-256 digest")
    return text


def _int(value: Any, label: str) -> int:
    if type(value) is not int or value < 1:
        raise ExactTargetImportError(f"{label} must be an integer >= 1")
    return value


def _exact_fields(value: dict[str, Any], fields: set[str], label: str) -> None:
    if set(value) != fields:
        raise ExactTargetImportError(
            f"{label} fields mismatch missing={sorted(fields - set(value))} unknown={sorted(set(value) - fields)}"
        )


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
    return _sha40(process.stdout.strip(), "release carrier HEAD")


def _load_runner(repo_root: Path):
    path = repo_root / "evals" / "runner.py"
    spec = importlib.util.spec_from_file_location("erei_import_eval_runner", path)
    if spec is None or spec.loader is None:
        raise ExactTargetImportError("unable to load eval runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _destination(value: Any, *, prefix: str, label: str) -> Path:
    text = _text(value, label)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts or not text.startswith(prefix) or path.suffix != ".json":
        raise ExactTargetImportError(f"{label} must be a relative JSON path under {prefix}")
    if not release_target.allowed_closure_path(path.as_posix()):
        raise ExactTargetImportError(f"{label} is outside the frozen release closure allowlist")
    return path


def validate_runtime_identity(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ExactTargetImportError("runtime identity must be an object")
    fields = {
        "schema_version", "repository", "target_id", "framework_ref", "target_tree", "release_carrier_ref",
        "adapter_id", "adapter_revision", "runtime_id", "runtime_version", "requested_cli_version",
        "model", "github_run_id", "github_run_attempt", "run_id", "run_manifest_path",
        "execution_evidence_path", "run_manifest_sha256", "execution_evidence_sha256",
    }
    _exact_fields(data, fields, "runtime identity")
    if data["schema_version"] != 2:
        raise ExactTargetImportError("runtime identity schema_version must be 2")
    repository = _text(data["repository"], "repository")
    if not REPOSITORY_RE.fullmatch(repository):
        raise ExactTargetImportError("repository must use owner/name format")
    _text(data["target_id"], "target_id")
    _sha40(data["framework_ref"], "framework_ref")
    _sha40(data["target_tree"], "target_tree")
    _sha40(data["release_carrier_ref"], "release_carrier_ref")
    _text(data["adapter_id"], "adapter_id")
    _sha40(data["adapter_revision"], "adapter_revision")
    _text(data["runtime_id"], "runtime_id")
    runtime_version = _text(data["runtime_version"], "runtime_version")
    version = _text(data["requested_cli_version"], "requested_cli_version")
    if not SEMVER_RE.fullmatch(version):
        raise ExactTargetImportError("requested_cli_version must be an exact semantic version")
    if version not in runtime_version:
        raise ExactTargetImportError("runtime_version must contain the requested CLI version")
    _text(data["model"], "model")
    _int(data["github_run_id"], "github_run_id")
    _int(data["github_run_attempt"], "github_run_attempt")
    if not isinstance(data["run_id"], str) or not RUN_ID_RE.fullmatch(data["run_id"]):
        raise ExactTargetImportError("run_id must match ETR-YYYYMMDDTHHMMSSZ-XXXXXXXX")
    _destination(data["run_manifest_path"], prefix="evals/exact-target-runs/", label="run_manifest_path")
    _destination(data["execution_evidence_path"], prefix="evals/EXECUTION_EVIDENCE.", label="execution_evidence_path")
    _sha256(data["run_manifest_sha256"], "run_manifest_sha256")
    _sha256(data["execution_evidence_sha256"], "execution_evidence_sha256")
    return data


def _stage_binding_root(repo_root: Path, manifest_path: Path, manifest_bytes: bytes) -> tempfile.TemporaryDirectory:
    temp = tempfile.TemporaryDirectory(prefix="erei-exact-target-import-")
    staged = Path(temp.name)
    (staged / "evals").mkdir(parents=True)
    shutil.copy2(repo_root / "evals" / "runner.py", staged / "evals" / "runner.py")
    shutil.copytree(repo_root / "evals" / "cases", staged / "evals" / "cases")
    target = staged / manifest_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(manifest_bytes)
    return temp


def validate_package(repo_root: Path, package_dir: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    package_dir = package_dir.resolve()
    target = release_target.load_and_validate_target(repo_root)
    release_target.validate_closure(repo_root, target)

    identity_path = package_dir / PACKAGE_FILES["identity"]
    manifest_package = package_dir / PACKAGE_FILES["manifest"]
    evidence_package = package_dir / PACKAGE_FILES["evidence"]
    identity = validate_runtime_identity(_load_json(identity_path, "runtime identity"))

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

    if _digest_file(manifest_package) != identity["run_manifest_sha256"]:
        raise ExactTargetImportError("run manifest package digest mismatch")
    if _digest_file(evidence_package) != identity["execution_evidence_sha256"]:
        raise ExactTargetImportError("execution evidence package digest mismatch")

    manifest = exact_target_evidence.validate_run_manifest(_load_json(manifest_package, "run manifest"))
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
    expected_runtime_evidence = {
        f"github-actions:{identity['repository']}/run/{identity['github_run_id']}/attempt/{identity['github_run_attempt']}",
        f"release-carrier:{identity['release_carrier_ref']}",
        f"copilot-model:{identity['model']}",
    }
    if set(manifest["runtime"]["identity_evidence"]) != expected_runtime_evidence:
        raise ExactTargetImportError("run manifest runtime identity evidence does not match package provenance")

    runner = _load_runner(repo_root)
    evidence = runner.validate_execution_evidence(_load_json(evidence_package, "execution evidence"))
    if evidence.get("schema_version") != 2:
        raise ExactTargetImportError("execution evidence must use schema_version 2")
    if evidence.get("framework_revision") != target["framework_ref"]:
        raise ExactTargetImportError("execution evidence framework_revision does not match frozen target")
    expected = runner._expected_cases(
        [str(repo_root / "evals" / "cases")], minimum_level="exact_target_runtime"
    )
    observed = {(row["suite_id"], row["case_id"]): row for row in evidence["executions"]}
    if set(observed) != expected:
        raise ExactTargetImportError(
            f"exact-target package case set mismatch missing={len(expected - set(observed))} unexpected={len(set(observed) - expected)}"
        )

    manifest_destination = _destination(
        identity["run_manifest_path"], prefix="evals/exact-target-runs/", label="run_manifest_path"
    )
    evidence_destination = _destination(
        identity["execution_evidence_path"], prefix="evals/EXECUTION_EVIDENCE.", label="execution_evidence_path"
    )
    for destination in (manifest_destination, evidence_destination):
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

    manifest_bytes = manifest_package.read_bytes()
    with _stage_binding_root(repo_root, manifest_destination, manifest_bytes) as temp_root:
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
        "manifest_source": manifest_package,
        "evidence_source": evidence_package,
        "case_count": len(expected),
    }


def _exclusive_write_pair(writes: tuple[tuple[Path, Path], ...]) -> None:
    """Reserve all destinations exclusively, then write both; rollback on handled failures."""
    handles: list[tuple[Any, Path, Path]] = []
    created: list[Path] = []
    rollback_errors: list[str] = []
    try:
        for _, destination in writes:
            destination.parent.mkdir(parents=True, exist_ok=True)
        for source, destination in writes:
            try:
                handle = destination.open("xb")
            except FileExistsError as exc:
                raise ExactTargetImportError(
                    f"release evidence destination already exists: {destination}"
                ) from exc
            handles.append((handle, source, destination))
            created.append(destination)
        for handle, source, _ in handles:
            payload = source.read_bytes()
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
        raise ExactTargetImportError(f"evidence import write failed and was rolled back: {exc}") from exc


def import_package(repo_root: Path, package_dir: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    validated = validate_package(repo_root, package_dir)
    writes = (
        (validated["manifest_source"], repo_root / validated["manifest_destination"]),
        (validated["evidence_source"], repo_root / validated["evidence_destination"]),
    )
    _exclusive_write_pair(writes)
    return validated


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--package-dir", required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = (
            validate_package(Path(args.repo_root), Path(args.package_dir))
            if args.validate_only
            else import_package(Path(args.repo_root), Path(args.package_dir))
        )
    except (ExactTargetImportError, release_target.ReleaseTargetError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "status": "valid" if args.validate_only else "imported",
        "target_id": result["target"]["target_id"],
        "framework_ref": result["target"]["framework_ref"],
        "run_id": result["identity"]["run_id"],
        "cases": result["case_count"],
        "run_manifest_path": result["manifest_destination"].as_posix(),
        "execution_evidence_path": result["evidence_destination"].as_posix(),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
