#!/usr/bin/env python3
"""Build strict runtime-identity metadata for an exact-target evidence artifact package."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    from .import_exact_target_evidence import ExactTargetImportError, validate_runtime_identity
except ImportError:
    from import_exact_target_evidence import ExactTargetImportError, validate_runtime_identity


def _load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExactTargetImportError(f"unable to load run manifest {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ExactTargetImportError("run manifest must be an object")
    return value


def _digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ExactTargetImportError(f"unable to hash package file {path}: {exc}") from exc


def build_identity(
    *,
    package_dir: Path,
    repository: str,
    target_id: str,
    framework_ref: str,
    target_tree: str,
    release_carrier_ref: str,
    adapter_id: str,
    adapter_revision: str,
    runtime_id: str,
    runtime_version: str,
    requested_cli_version: str,
    model: str,
    github_run_id: int,
    github_run_attempt: int,
    run_manifest_path: str,
    execution_evidence_path: str,
) -> dict:
    package_dir = package_dir.resolve()
    manifest_file = package_dir / "exact-target-run.json"
    evidence_file = package_dir / "execution-evidence.json"
    manifest = _load(manifest_file)
    payload = {
        "schema_version": 2,
        "repository": repository,
        "target_id": target_id,
        "framework_ref": framework_ref,
        "target_tree": target_tree,
        "release_carrier_ref": release_carrier_ref,
        "adapter_id": adapter_id,
        "adapter_revision": adapter_revision,
        "runtime_id": runtime_id,
        "runtime_version": runtime_version,
        "requested_cli_version": requested_cli_version,
        "model": model,
        "github_run_id": github_run_id,
        "github_run_attempt": github_run_attempt,
        "run_id": manifest.get("run_id"),
        "run_manifest_path": run_manifest_path,
        "execution_evidence_path": execution_evidence_path,
        "run_manifest_sha256": _digest(manifest_file),
        "execution_evidence_sha256": _digest(evidence_file),
    }
    return validate_runtime_identity(payload)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--target-id", required=True)
    parser.add_argument("--framework-ref", required=True)
    parser.add_argument("--target-tree", required=True)
    parser.add_argument("--release-carrier-ref", required=True)
    parser.add_argument("--adapter-id", required=True)
    parser.add_argument("--adapter-revision", required=True)
    parser.add_argument("--runtime-id", required=True)
    parser.add_argument("--runtime-version", required=True)
    parser.add_argument("--requested-cli-version", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--github-run-id", required=True, type=int)
    parser.add_argument("--github-run-attempt", required=True, type=int)
    parser.add_argument("--run-manifest-path", required=True)
    parser.add_argument("--execution-evidence-path", required=True)
    parser.add_argument("--output", default="runtime-identity.json")
    args = parser.parse_args(argv)
    try:
        payload = build_identity(
            package_dir=Path(args.package_dir),
            repository=args.repository,
            target_id=args.target_id,
            framework_ref=args.framework_ref,
            target_tree=args.target_tree,
            release_carrier_ref=args.release_carrier_ref,
            adapter_id=args.adapter_id,
            adapter_revision=args.adapter_revision,
            runtime_id=args.runtime_id,
            runtime_version=args.runtime_version,
            requested_cli_version=args.requested_cli_version,
            model=args.model,
            github_run_id=args.github_run_id,
            github_run_attempt=args.github_run_attempt,
            run_manifest_path=args.run_manifest_path,
            execution_evidence_path=args.execution_evidence_path,
        )
        output = Path(args.output)
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (ExactTargetImportError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "written", "output": str(output), "run_id": payload["run_id"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
