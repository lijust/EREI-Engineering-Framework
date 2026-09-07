#!/usr/bin/env python3
"""Validate the Framework's machine-readable server/fallback enforcement truth."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


class EnforcementError(RuntimeError):
    pass


def _exact_fields(value: dict, required: set[str], label: str) -> None:
    if not isinstance(value, dict):
        raise EnforcementError(f"{label} must be an object")
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required)
    if missing:
        raise EnforcementError(f"{label} missing fields: {', '.join(missing)}")
    if unknown:
        raise EnforcementError(f"{label} unknown fields: {', '.join(unknown)}")


def _bool(value, label: str) -> bool:
    if type(value) is not bool:
        raise EnforcementError(f"{label} must be boolean")
    return value


def _text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EnforcementError(f"{label} must be a non-empty string")
    return value.strip()


def validate_enforcement(value: dict) -> dict:
    top = {
        "schema_version", "repository", "main_branch", "status",
        "server_enforcement", "fallback", "evidence", "limitations",
    }
    _exact_fields(value, top, "assurance enforcement")
    if value["schema_version"] != 1:
        raise EnforcementError("unsupported assurance enforcement schema_version")
    if _text(value["repository"], "repository") != "lijust/EREI-Engineering-Framework":
        raise EnforcementError("repository mismatch")
    if _text(value["main_branch"], "main_branch") != "main":
        raise EnforcementError("main_branch must be main")
    if value["status"] not in {"candidate_control", "enforced"}:
        raise EnforcementError("invalid enforcement status")

    server_required = {"branch_protection_enabled", "required_status_checks_enforced", "source"}
    server = value["server_enforcement"]
    _exact_fields(server, server_required, "server_enforcement")
    branch_protected = _bool(server["branch_protection_enabled"], "branch_protection_enabled")
    checks_enforced = _bool(server["required_status_checks_enforced"], "required_status_checks_enforced")
    _text(server["source"], "server_enforcement.source")

    fallback_required = {
        "mode", "required_workflow", "release_branch_prefix", "exact_candidate_sha_required",
        "release_assurance_contract_version", "architecture_approval_required",
        "security_approval_required", "exact_target_runtime_evidence_required",
        "complete_prospective_cycle_required", "equivalent_enforcement_verified",
        "stable_promotion_policy",
    }
    fallback = value["fallback"]
    _exact_fields(fallback, fallback_required, "fallback")
    if fallback["mode"] != "controlled_release_v2":
        raise EnforcementError("fallback.mode must be controlled_release_v2")
    if fallback["required_workflow"] != "Framework Assurance Gate":
        raise EnforcementError("fallback.required_workflow mismatch")
    if fallback["release_branch_prefix"] != "release/":
        raise EnforcementError("fallback.release_branch_prefix must be release/")
    for key in (
        "exact_candidate_sha_required", "architecture_approval_required", "security_approval_required",
        "exact_target_runtime_evidence_required", "complete_prospective_cycle_required",
        "equivalent_enforcement_verified",
    ):
        _bool(fallback[key], f"fallback.{key}")
    if fallback["release_assurance_contract_version"] != 2:
        raise EnforcementError("fallback.release_assurance_contract_version must be 2")
    if fallback["stable_promotion_policy"] != "blocked_until_server_or_equivalent_enforcement":
        raise EnforcementError("fallback.stable_promotion_policy mismatch")

    for label in ("evidence", "limitations"):
        items = value[label]
        if not isinstance(items, list) or not items:
            raise EnforcementError(f"{label} must be a non-empty array")
        normalized = [_text(item, f"{label} item") for item in items]
        if len(normalized) != len(set(normalized)):
            raise EnforcementError(f"{label} items must be unique")

    server_equivalent = branch_protected and checks_enforced
    fallback_equivalent = fallback["equivalent_enforcement_verified"]
    stable_enforcement_satisfied = server_equivalent or fallback_equivalent
    if value["status"] == "enforced" and not stable_enforcement_satisfied:
        raise EnforcementError("status=enforced requires server enforcement or verified equivalent fallback")
    return {
        "server_enforcement_satisfied": server_equivalent,
        "fallback_equivalent_verified": fallback_equivalent,
        "stable_enforcement_satisfied": stable_enforcement_satisfied,
    }


def load_and_validate(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EnforcementError(f"unable to load enforcement record: {exc}") from exc
    if not isinstance(value, dict):
        raise EnforcementError("assurance enforcement record must be an object")
    return validate_enforcement(value)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", nargs="?", default="security/ASSURANCE_ENFORCEMENT.json")
    args = parser.parse_args(argv)
    try:
        result = load_and_validate(Path(args.record))
    except EnforcementError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "valid", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
