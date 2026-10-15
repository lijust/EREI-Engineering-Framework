#!/usr/bin/env python3
"""Resolve Framework capability activation for one integrated project.

Candidate presence in the Framework tree is never activation. Candidate use requires
an exact commit-pinned project plus a bounded project-local adoption record.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "CAPABILITIES.json"
MANIFEST_PATH = Path(".erei") / "framework.json"
ADOPTION_PATH = Path(".erei") / "CANDIDATE_CAPABILITIES.json"

SHA1_RE = re.compile(r"^[a-f0-9]{40}$")
ADOPTION_ID_RE = re.compile(r"^CAD-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
CAPABILITY_RE = re.compile(r"^[a-z0-9][a-z0-9_]*$")
RFC3339_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)
MAX_CANDIDATE_TRIAL = timedelta(days=30)
RISK_LEVELS = {"L2", "L3", "L4"}
ACTIVE_STATUSES = {"ACTIVE_STABLE", "ACTIVE_CANDIDATE"}


class ActivationError(RuntimeError):
    pass


def _read_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ActivationError(f"missing {label}: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ActivationError(f"invalid JSON in {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ActivationError(f"{label} must contain a JSON object")
    return value


def _exact_fields(value: dict, required: set[str], allowed: set[str], label: str) -> None:
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - allowed)
    if missing:
        raise ActivationError(f"{label} missing fields: " + ", ".join(missing))
    if unknown:
        raise ActivationError(f"{label} unknown fields: " + ", ".join(unknown))


def _text(value: Any, label: str, minimum: int = 1) -> str:
    if not isinstance(value, str) or len(value.strip()) < minimum:
        raise ActivationError(f"{label} must be a non-empty string")
    return value.strip()


def _time(value: Any, label: str) -> datetime:
    text = _text(value, label)
    if not RFC3339_RE.fullmatch(text):
        raise ActivationError(f"{label} must be RFC3339 with timezone")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ActivationError(f"{label} is not a valid date-time") from exc
    if parsed.tzinfo is None:
        raise ActivationError(f"{label} must include timezone")
    return parsed.astimezone(timezone.utc)


def _validate_manifest(value: dict) -> dict:
    required = {"schema_version", "framework", "project", "overlays", "runtime_adapters"}
    _exact_fields(value, required, required, "project framework manifest")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ActivationError("project framework schema_version must be integer 1")
    framework = value["framework"]
    if not isinstance(framework, dict):
        raise ActivationError("framework must be an object")
    fw_required = {"repository", "baseline", "ref_type", "ref"}
    _exact_fields(framework, fw_required, fw_required, "framework")
    _text(framework["repository"], "framework.repository", 3)
    _text(framework["baseline"], "framework.baseline")
    if framework["ref_type"] not in {"commit", "tag", "branch"}:
        raise ActivationError("invalid framework.ref_type")
    _text(framework["ref"], "framework.ref")
    if not isinstance(value["project"], dict):
        raise ActivationError("project must be an object")
    if not isinstance(value["overlays"], list) or not isinstance(value["runtime_adapters"], list):
        raise ActivationError("overlays/runtime_adapters must be arrays")
    return framework


def _validate_registry(value: dict) -> dict:
    if type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise ActivationError("capability registry schema_version must be integer 1")
    development = value.get("development_line")
    if not isinstance(development, dict):
        raise ActivationError("capability registry development_line is missing")
    capabilities = development.get("capabilities")
    if not isinstance(capabilities, dict):
        raise ActivationError("capability registry capabilities are missing")
    return capabilities


def _validate_adoptions(value: dict) -> list[dict]:
    required = {"schema_version", "framework_ref", "adoptions"}
    _exact_fields(value, required, required, "candidate capability adoption document")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ActivationError("candidate adoption schema_version must be integer 1")
    framework_ref = _text(value["framework_ref"], "candidate adoption framework_ref")
    if not isinstance(value["adoptions"], list):
        raise ActivationError("candidate adoptions must be an array")
    if value["adoptions"] and not SHA1_RE.fullmatch(framework_ref):
        raise ActivationError("non-empty candidate adoption requires a 40-character commit SHA")

    required_item = {"adoption_id","capability","version","approved_at","expires_at","approved_by_role","risk","purpose","evidence"}
    seen: set[str] = set()
    normalized: list[dict] = []
    for index, item in enumerate(value["adoptions"]):
        if not isinstance(item, dict):
            raise ActivationError(f"adoptions[{index}] must be an object")
        _exact_fields(item, required_item, required_item, f"adoptions[{index}]")
        if not isinstance(item["adoption_id"], str) or not ADOPTION_ID_RE.fullmatch(item["adoption_id"]):
            raise ActivationError(f"invalid adoptions[{index}].adoption_id")
        capability = item["capability"]
        if not isinstance(capability, str) or not CAPABILITY_RE.fullmatch(capability):
            raise ActivationError(f"invalid adoptions[{index}].capability")
        if capability in seen:
            raise ActivationError(f"duplicate candidate adoption for capability: {capability}")
        seen.add(capability)
        _text(item["version"], f"adoptions[{index}].version")
        approved = _time(item["approved_at"], f"adoptions[{index}].approved_at")
        expires = _time(item["expires_at"], f"adoptions[{index}].expires_at")
        if expires <= approved:
            raise ActivationError(f"adoptions[{index}] expiry must be after approval")
        if expires - approved > MAX_CANDIDATE_TRIAL:
            raise ActivationError(f"adoptions[{index}] exceeds the 30-day candidate trial boundary")
        _text(item["approved_by_role"], f"adoptions[{index}].approved_by_role", 3)
        if item["risk"] not in RISK_LEVELS:
            raise ActivationError(f"invalid adoptions[{index}].risk")
        _text(item["purpose"], f"adoptions[{index}].purpose", 20)
        evidence = item["evidence"]
        if (
            not isinstance(evidence, list)
            or not evidence
            or any(not isinstance(entry, str) or not entry.strip() for entry in evidence)
            or len(evidence) != len(set(evidence))
        ):
            raise ActivationError(f"adoptions[{index}].evidence must be a non-empty unique string list")
        normalized.append({**item, "_approved": approved, "_expires": expires})
    return normalized


def detect_loaded_framework_ref(root: Path = ROOT) -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ActivationError("cannot resolve loaded Framework checkout commit") from exc
    value = proc.stdout.strip().lower()
    if not SHA1_RE.fullmatch(value):
        raise ActivationError("loaded Framework checkout is not an exact commit SHA")
    return value


def resolve_activation(
    manifest: dict,
    registry: dict,
    capability: str,
    *,
    adoption_document: dict | None,
    loaded_framework_ref: str | None,
    now: datetime | None = None,
) -> dict:
    framework = _validate_manifest(manifest)
    capabilities = _validate_registry(registry)
    if capability not in capabilities:
        return {"status": "BLOCK_UNKNOWN_CAPABILITY", "capability": capability}

    record = capabilities[capability]
    if not isinstance(record, dict):
        return {"status": "BLOCK_INVALID_CAPABILITY_REGISTRY", "capability": capability}
    status = record.get("status")
    version = record.get("version")
    if status not in {"stable", "candidate"} or not isinstance(version, str) or not version:
        return {"status": "BLOCK_INVALID_CAPABILITY_REGISTRY", "capability": capability}

    if status == "stable":
        return {
            "status": "ACTIVE_STABLE",
            "capability": capability,
            "version": version,
            "framework_ref": framework["ref"],
        }

    if framework["ref_type"] != "commit" or not SHA1_RE.fullmatch(framework["ref"]):
        return {"status": "BLOCK_NON_COMMIT_PROJECT_PIN", "capability": capability, "version": version}

    project_ref = framework["ref"].lower()
    if loaded_framework_ref is None or not SHA1_RE.fullmatch(loaded_framework_ref.lower()):
        return {"status": "BLOCK_FRAMEWORK_CHECKOUT_UNRESOLVED", "capability": capability, "version": version}
    loaded_ref = loaded_framework_ref.lower()
    if loaded_ref != project_ref:
        return {
            "status": "BLOCK_FRAMEWORK_REF_MISMATCH",
            "capability": capability,
            "version": version,
            "project_ref": project_ref,
            "loaded_framework_ref": loaded_ref,
        }

    if adoption_document is None:
        return {
            "status": "DORMANT_CANDIDATE",
            "capability": capability,
            "version": version,
            "framework_ref": project_ref,
            "reason": "no project-local candidate adoption record",
        }

    try:
        adoptions = _validate_adoptions(adoption_document)
    except ActivationError as exc:
        return {
            "status": "BLOCK_INVALID_CANDIDATE_ADOPTION",
            "capability": capability,
            "version": version,
            "error": str(exc),
        }

    if adoption_document["framework_ref"].lower() != project_ref:
        return {
            "status": "BLOCK_FRAMEWORK_REF_MISMATCH",
            "capability": capability,
            "version": version,
            "project_ref": project_ref,
            "adoption_framework_ref": adoption_document["framework_ref"].lower(),
        }

    matching = [item for item in adoptions if item["capability"] == capability]
    if not matching:
        return {
            "status": "DORMANT_CANDIDATE",
            "capability": capability,
            "version": version,
            "framework_ref": project_ref,
            "reason": "capability has no explicit adoption record",
        }

    adoption = matching[0]
    if adoption["version"] != version:
        return {
            "status": "BLOCK_CANDIDATE_VERSION_MISMATCH",
            "capability": capability,
            "expected_version": version,
            "adopted_version": adoption["version"],
        }

    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if current < adoption["_approved"]:
        return {
            "status": "BLOCK_INVALID_CANDIDATE_ADOPTION",
            "capability": capability,
            "version": version,
            "error": "candidate adoption approval is future-dated",
        }
    if current >= adoption["_expires"]:
        return {
            "status": "BLOCK_EXPIRED_CANDIDATE_ADOPTION",
            "capability": capability,
            "version": version,
            "adoption_id": adoption["adoption_id"],
            "expires_at": adoption["expires_at"],
        }

    return {
        "status": "ACTIVE_CANDIDATE",
        "capability": capability,
        "version": version,
        "framework_ref": project_ref,
        "adoption_id": adoption["adoption_id"],
        "risk": adoption["risk"],
        "expires_at": adoption["expires_at"],
        "evidence": adoption["evidence"],
    }


def resolve_target(target: Path, capability: str) -> dict:
    manifest = _read_json(target / MANIFEST_PATH, "project Framework manifest")
    registry = _read_json(REGISTRY_PATH, "Framework capability registry")
    adoption_path = target / ADOPTION_PATH
    adoption = _read_json(adoption_path, "candidate capability adoption document") if adoption_path.exists() else None
    return resolve_activation(
        manifest,
        registry,
        capability,
        adoption_document=adoption,
        loaded_framework_ref=detect_loaded_framework_ref(),
    )


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve EREI Framework capability activation.")
    parser.add_argument("--target", required=True)
    parser.add_argument("--capability", required=True)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        result = resolve_target(Path(args.target).resolve(), args.capability)
    except (ActivationError, OSError) as exc:
        result = {"status": "BLOCK_ACTIVATION_RESOLUTION_ERROR", "error": str(exc)}
        print(json.dumps(result, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] in ACTIVE_STATUSES else 3


if __name__ == "__main__":
    raise SystemExit(main())
