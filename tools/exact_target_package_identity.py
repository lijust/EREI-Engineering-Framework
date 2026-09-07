#!/usr/bin/env python3
"""Strict contract for durable exact-target runtime evidence package identity."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

SHA40_RE = re.compile(r"^[a-f0-9]{40}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
RUN_ID_RE = re.compile(r"^ETR-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-.][0-9A-Za-z.-]+)?$")
SRI_SHA512_RE = re.compile(r"^sha512-[A-Za-z0-9+/]+={0,2}$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class ExactTargetPackageIdentityError(RuntimeError):
    pass


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExactTargetPackageIdentityError(f"{label} must be a non-empty string")
    return value.strip()


def _pattern(value: Any, pattern: re.Pattern[str], label: str, message: str) -> str:
    text = _text(value, label)
    if not pattern.fullmatch(text):
        raise ExactTargetPackageIdentityError(message)
    return text


def _int(value: Any, label: str) -> int:
    if type(value) is not int or value < 1:
        raise ExactTargetPackageIdentityError(f"{label} must be an integer >= 1")
    return value


def _relative_json_path(value: Any, *, prefix: str, label: str) -> Path:
    text = _text(value, label)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts or not text.startswith(prefix) or path.suffix != ".json":
        raise ExactTargetPackageIdentityError(f"{label} must be a relative JSON path under {prefix}")
    return path


def identity_path_for_manifest(manifest_path: Path | str) -> Path:
    path = Path(manifest_path)
    raw = path.as_posix()
    if path.is_absolute() or ".." in path.parts or not raw.startswith("evals/exact-target-runs/") or path.suffix != ".json":
        raise ExactTargetPackageIdentityError(
            "run manifest path must be a relative JSON path under evals/exact-target-runs/"
        )
    if path.name.endswith(".identity.json"):
        raise ExactTargetPackageIdentityError("run manifest path cannot use the reserved .identity.json suffix")
    return path.with_name(path.stem + ".identity.json")


def expected_runtime_evidence(identity: dict[str, Any]) -> set[str]:
    return {
        f"github-actions:{identity['repository']}/run/{identity['github_run_id']}/attempt/{identity['github_run_attempt']}",
        f"release-carrier:{identity['release_carrier_ref']}",
        f"copilot-model:{identity['model']}",
        f"copilot-package-integrity:{identity['requested_cli_integrity']}",
    }


def validate_runtime_identity(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ExactTargetPackageIdentityError("runtime identity must be an object")
    fields = {
        "schema_version", "repository", "target_id", "framework_ref", "target_tree", "release_carrier_ref",
        "adapter_id", "adapter_revision", "runtime_id", "runtime_version", "requested_cli_version",
        "requested_cli_integrity", "model", "github_run_id", "github_run_attempt", "run_id",
        "run_manifest_path", "execution_evidence_path", "runtime_identity_path",
        "run_manifest_sha256", "execution_evidence_sha256",
    }
    if set(data) != fields:
        raise ExactTargetPackageIdentityError(
            f"runtime identity fields mismatch missing={sorted(fields - set(data))} unknown={sorted(set(data) - fields)}"
        )
    if data["schema_version"] != 2:
        raise ExactTargetPackageIdentityError("runtime identity schema_version must be 2")
    _pattern(data["repository"], REPOSITORY_RE, "repository", "repository must use owner/name format")
    _text(data["target_id"], "target_id")
    _pattern(data["framework_ref"], SHA40_RE, "framework_ref", "framework_ref must be an exact lowercase 40-character commit")
    _pattern(data["target_tree"], SHA40_RE, "target_tree", "target_tree must be an exact lowercase 40-character commit")
    _pattern(data["release_carrier_ref"], SHA40_RE, "release_carrier_ref", "release_carrier_ref must be an exact lowercase 40-character commit")
    _text(data["adapter_id"], "adapter_id")
    _pattern(data["adapter_revision"], SHA40_RE, "adapter_revision", "adapter_revision must be an exact lowercase 40-character commit")
    _text(data["runtime_id"], "runtime_id")
    runtime_version = _text(data["runtime_version"], "runtime_version")
    version = _pattern(
        data["requested_cli_version"], SEMVER_RE, "requested_cli_version",
        "requested_cli_version must be an exact semantic version",
    )
    if version not in runtime_version:
        raise ExactTargetPackageIdentityError("runtime_version must contain the requested CLI version")
    _pattern(
        data["requested_cli_integrity"], SRI_SHA512_RE, "requested_cli_integrity",
        "requested_cli_integrity must be an npm sha512 SRI value",
    )
    _text(data["model"], "model")
    _int(data["github_run_id"], "github_run_id")
    _int(data["github_run_attempt"], "github_run_attempt")
    _pattern(data["run_id"], RUN_ID_RE, "run_id", "run_id must match ETR-YYYYMMDDTHHMMSSZ-XXXXXXXX")

    manifest_path = _relative_json_path(
        data["run_manifest_path"], prefix="evals/exact-target-runs/", label="run_manifest_path"
    )
    if manifest_path.name.endswith(".identity.json"):
        raise ExactTargetPackageIdentityError("run_manifest_path cannot use the reserved .identity.json suffix")
    evidence_path = _relative_json_path(
        data["execution_evidence_path"], prefix="evals/EXECUTION_EVIDENCE.", label="execution_evidence_path"
    )
    identity_path = _relative_json_path(
        data["runtime_identity_path"], prefix="evals/exact-target-runs/", label="runtime_identity_path"
    )
    expected_identity_path = identity_path_for_manifest(manifest_path)
    if identity_path != expected_identity_path:
        raise ExactTargetPackageIdentityError(
            f"runtime_identity_path must equal {expected_identity_path.as_posix()} for the run manifest"
        )
    if len({manifest_path.as_posix(), evidence_path.as_posix(), identity_path.as_posix()}) != 3:
        raise ExactTargetPackageIdentityError("runtime evidence destination paths must be distinct")

    _pattern(data["run_manifest_sha256"], SHA256_RE, "run_manifest_sha256", "run_manifest_sha256 must be a lowercase SHA-256 digest")
    _pattern(data["execution_evidence_sha256"], SHA256_RE, "execution_evidence_sha256", "execution_evidence_sha256 must be a lowercase SHA-256 digest")
    return data
