#!/usr/bin/env python3
"""Resolve project activation for Stable vs Candidate Framework capabilities."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

SHA40_RE = re.compile(r"^[a-f0-9]{40}$")
RFC3339_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)
MAX_TRIAL = timedelta(days=30)
ADOPTION_PATH = Path(".erei/candidate-capabilities.json")
FRAMEWORK_REPOSITORY = "lijust/EREI-Engineering-Framework"


class ActivationError(RuntimeError):
    pass


def _load_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ActivationError(f"missing {label}: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ActivationError(f"invalid JSON in {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ActivationError(f"{label} must be a JSON object: {path}")
    return value


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise ActivationError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def _head(root: Path) -> str:
    value = _git(root, "rev-parse", "HEAD")
    if not SHA40_RE.fullmatch(value):
        raise ActivationError("Framework HEAD is not an exact commit")
    return value


def _resolve_project_ref(root: Path, manifest: dict) -> tuple[str, str]:
    framework = manifest.get("framework")
    if not isinstance(framework, dict):
        raise ActivationError("project manifest missing framework object")
    repository = framework.get("repository")
    if repository != FRAMEWORK_REPOSITORY:
        raise ActivationError(
            f"project Framework repository {repository!r} does not match {FRAMEWORK_REPOSITORY!r}"
        )
    ref_type = framework.get("ref_type")
    ref = framework.get("ref")
    if ref_type not in {"commit", "tag", "branch"} or not isinstance(ref, str) or not ref:
        raise ActivationError("project manifest has invalid framework ref")
    if ref_type == "commit":
        if not SHA40_RE.fullmatch(ref):
            raise ActivationError("project commit pin is not an exact SHA")
        return ref_type, ref
    resolved = _git(root, "rev-parse", "--verify", f"{ref}^{{commit}}")
    if not SHA40_RE.fullmatch(resolved):
        raise ActivationError("project Framework ref did not resolve to an exact commit")
    return ref_type, resolved


def _time(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not RFC3339_RE.fullmatch(value):
        raise ActivationError(f"{label} must be RFC3339 with timezone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ActivationError(f"{label} is invalid") from exc
    if parsed.tzinfo is None:
        raise ActivationError(f"{label} must include timezone")
    return parsed


def _validate_adoptions(value: dict) -> None:
    if type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise ActivationError("candidate adoption schema_version must be integer 1")
    framework_ref = value.get("framework_ref")
    if not isinstance(framework_ref, str) or not SHA40_RE.fullmatch(framework_ref):
        raise ActivationError("candidate adoption framework_ref must be an exact commit")
    adoptions = value.get("adoptions")
    if not isinstance(adoptions, list):
        raise ActivationError("candidate adoptions must be an array")
    seen: set[str] = set()
    allowed = {
        "capability", "version", "adopted_at", "expires_at",
        "approved_by_role", "evidence", "notes",
    }
    required = {
        "capability", "version", "adopted_at", "expires_at",
        "approved_by_role", "evidence",
    }
    for index, adoption in enumerate(adoptions):
        if not isinstance(adoption, dict):
            raise ActivationError(f"adoptions[{index}] must be an object")
        missing = required - set(adoption)
        unknown = set(adoption) - allowed
        if missing:
            raise ActivationError(f"adoptions[{index}] missing fields: {', '.join(sorted(missing))}")
        if unknown:
            raise ActivationError(f"adoptions[{index}] unknown fields: {', '.join(sorted(unknown))}")
        capability = adoption["capability"]
        if not isinstance(capability, str) or not capability.strip():
            raise ActivationError(f"adoptions[{index}].capability must be non-empty")
        if capability in seen:
            raise ActivationError(f"duplicate capability adoption: {capability}")
        seen.add(capability)
        if not isinstance(adoption["version"], str) or not adoption["version"].strip():
            raise ActivationError(f"adoptions[{index}].version must be non-empty")
        if not isinstance(adoption["approved_by_role"], str) or not adoption["approved_by_role"].strip():
            raise ActivationError(f"adoptions[{index}].approved_by_role must be non-empty")
        evidence = adoption["evidence"]
        if (
            not isinstance(evidence, list)
            or not evidence
            or any(not isinstance(item, str) or not item.strip() for item in evidence)
            or len(evidence) != len(set(evidence))
        ):
            raise ActivationError(f"adoptions[{index}].evidence must be non-empty unique strings")
        adopted = _time(adoption["adopted_at"], f"adoptions[{index}].adopted_at")
        expires = _time(adoption["expires_at"], f"adoptions[{index}].expires_at")
        if expires <= adopted:
            raise ActivationError(f"adoptions[{index}] expires_at must be after adopted_at")
        if expires - adopted > MAX_TRIAL:
            raise ActivationError(f"adoptions[{index}] trial may not exceed 30 days")
        if "notes" in adoption and not isinstance(adoption["notes"], str):
            raise ActivationError(f"adoptions[{index}].notes must be a string")


def resolve(framework_root: Path, project_root: Path, capability: str, now: datetime) -> dict:
    framework_root = framework_root.resolve()
    project_root = project_root.resolve()
    head = _head(framework_root)
    manifest = _load_object(project_root / ".erei" / "framework.json", "project Framework manifest")
    ref_type, project_ref = _resolve_project_ref(framework_root, manifest)
    if project_ref != head:
        raise ActivationError(
            f"Framework checkout HEAD {head} does not match project pin {project_ref}; "
            "resolve the pinned Framework revision before capability activation"
        )

    registry = _load_object(framework_root / "CAPABILITIES.json", "capability registry")
    development = registry.get("development_line")
    capabilities = development.get("capabilities") if isinstance(development, dict) else None
    if not isinstance(capabilities, dict) or capability not in capabilities:
        raise ActivationError(f"unknown capability: {capability}")
    entry = capabilities[capability]
    if not isinstance(entry, dict):
        raise ActivationError(f"capability registry entry is invalid: {capability}")
    status = entry.get("status")
    version = entry.get("version")

    if status == "stable":
        return {
            "status": "ACTIVE_STABLE",
            "active": True,
            "capability": capability,
            "version": version,
            "framework_ref": head,
            "activation_source": "capability_registry_stable",
        }
    if status == "deprecated":
        return {
            "status": "INACTIVE_DEPRECATED",
            "active": False,
            "capability": capability,
            "version": version,
            "framework_ref": head,
            "activation_source": "capability_registry_deprecated",
        }
    if status not in {"candidate", "experimental"}:
        raise ActivationError(f"unsupported capability status for {capability}: {status}")

    adoption_path = project_root / ADOPTION_PATH
    if not adoption_path.exists():
        return {
            "status": "INACTIVE_CANDIDATE",
            "active": False,
            "capability": capability,
            "version": version,
            "framework_ref": head,
            "activation_source": "no_project_candidate_adoption",
        }

    adoptions = _load_object(adoption_path, "candidate capability adoptions")
    _validate_adoptions(adoptions)
    if ref_type != "commit":
        raise ActivationError("Candidate capability trials require an exact commit project pin")
    if adoptions["framework_ref"] != head:
        raise ActivationError("candidate adoption framework_ref does not match the exact project Framework pin")

    match = next((item for item in adoptions["adoptions"] if item["capability"] == capability), None)
    if match is None:
        return {
            "status": "INACTIVE_CANDIDATE",
            "active": False,
            "capability": capability,
            "version": version,
            "framework_ref": head,
            "activation_source": "capability_not_adopted",
        }
    if match["version"] != version:
        raise ActivationError(
            f"candidate adoption version {match['version']} does not match registry version {version}"
        )
    adopted = _time(match["adopted_at"], "adopted_at")
    expires = _time(match["expires_at"], "expires_at")
    if now < adopted:
        raise ActivationError("candidate adoption is future-dated")
    if now >= expires:
        return {
            "status": "INACTIVE_CANDIDATE_EXPIRED",
            "active": False,
            "capability": capability,
            "version": version,
            "framework_ref": head,
            "activation_source": "expired_project_candidate_adoption",
            "expires_at": match["expires_at"],
        }
    return {
        "status": "ACTIVE_CANDIDATE_TRIAL",
        "active": True,
        "capability": capability,
        "version": version,
        "framework_ref": head,
        "activation_source": "bounded_project_candidate_adoption",
        "approved_by_role": match["approved_by_role"],
        "evidence": match["evidence"],
        "expires_at": match["expires_at"],
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework-root", required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--capability", required=True)
    parser.add_argument("--now")
    parser.add_argument("--require-active", action="store_true")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        now = _time(args.now, "--now") if args.now else datetime.now(timezone.utc)
        result = resolve(Path(args.framework_root), Path(args.project_root), args.capability, now)
    except (ActivationError, OSError) as exc:
        print(json.dumps({"status": "BLOCKED", "active": False, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    if args.require_active and not result["active"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
