#!/usr/bin/env python3
"""Strict machine-readable Architecture/Security release-approval validation."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SHA40_RE = re.compile(r"^[a-f0-9]{40}$")
APPROVAL_ID_RE = re.compile(r"^EAPP-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
APPROVAL_PATHS = {
    "architecture": "releases/approvals/architecture.json",
    "security": "releases/approvals/security.json",
}


class ReleaseApprovalError(RuntimeError):
    pass


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReleaseApprovalError(f"{label} must be a non-empty string")
    return value.strip()


def _sha(value: Any, label: str) -> str:
    text = _text(value, label)
    if not SHA40_RE.fullmatch(text):
        raise ReleaseApprovalError(f"{label} must be an exact 40-character commit/tree")
    return text


def _datetime(value: Any, label: str) -> str:
    text = _text(value, label)
    if "T" not in text or not (text.endswith("Z") or re.search(r"[+-][0-9]{2}:[0-9]{2}$", text)):
        raise ReleaseApprovalError(f"{label} must be RFC3339 date-time with timezone")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReleaseApprovalError(f"invalid {label}") from exc
    if parsed.tzinfo is None:
        raise ReleaseApprovalError(f"{label} must include timezone")
    return text


def _unique_texts(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ReleaseApprovalError(f"{label} must be a non-empty array")
    normalized = [_text(item, f"{label} item") for item in value]
    if len(normalized) != len(set(normalized)):
        raise ReleaseApprovalError(f"{label} must contain unique items")
    return normalized


def validate_record(
    value: Any,
    *,
    expected_type: str | None = None,
    expected_target: str | None = None,
    expected_tree: str | None = None,
    require_approved: bool = False,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReleaseApprovalError("release approval must be an object")
    fields = {
        "schema_version", "approval_id", "approval_type", "target_framework_ref", "target_tree",
        "decision", "recorded_at", "reviewer", "evidence", "rationale",
    }
    missing = sorted(fields - set(value))
    unknown = sorted(set(value) - fields)
    if missing:
        raise ReleaseApprovalError("release approval missing fields: " + ", ".join(missing))
    if unknown:
        raise ReleaseApprovalError("release approval unknown fields: " + ", ".join(unknown))
    if value["schema_version"] != 1:
        raise ReleaseApprovalError("unsupported release approval schema_version")
    if not isinstance(value["approval_id"], str) or not APPROVAL_ID_RE.fullmatch(value["approval_id"]):
        raise ReleaseApprovalError("invalid approval_id")
    if value["approval_type"] not in APPROVAL_PATHS:
        raise ReleaseApprovalError("invalid approval_type")
    target = _sha(value["target_framework_ref"], "target_framework_ref")
    tree = _sha(value["target_tree"], "target_tree")
    if value["decision"] not in {"approved", "rejected"}:
        raise ReleaseApprovalError("invalid decision")
    _datetime(value["recorded_at"], "recorded_at")
    reviewer = value["reviewer"]
    if not isinstance(reviewer, dict) or set(reviewer) != {"kind", "id"}:
        raise ReleaseApprovalError("reviewer must contain exactly kind/id")
    if reviewer["kind"] not in {"github_user", "framework_role", "external_reviewer"}:
        raise ReleaseApprovalError("invalid reviewer.kind")
    _text(reviewer["id"], "reviewer.id")
    _unique_texts(value["evidence"], "evidence")
    _text(value["rationale"], "rationale")

    if expected_type is not None and value["approval_type"] != expected_type:
        raise ReleaseApprovalError(
            f"approval_type mismatch: expected {expected_type}, got {value['approval_type']}"
        )
    if expected_target is not None and target != _sha(expected_target, "expected_target"):
        raise ReleaseApprovalError("target_framework_ref does not match expected target")
    if expected_tree is not None and tree != _sha(expected_tree, "expected_tree"):
        raise ReleaseApprovalError("target_tree does not match expected target tree")
    if require_approved and value["decision"] != "approved":
        raise ReleaseApprovalError("release approval decision is not approved")
    return value


def load_and_validate(
    path: Path,
    *,
    expected_type: str | None = None,
    expected_target: str | None = None,
    expected_tree: str | None = None,
    require_approved: bool = False,
) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseApprovalError(f"unable to load release approval {path}: {exc}") from exc
    return validate_record(
        value,
        expected_type=expected_type,
        expected_target=expected_target,
        expected_tree=expected_tree,
        require_approved=require_approved,
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("record")
    parser.add_argument("--type", choices=sorted(APPROVAL_PATHS))
    parser.add_argument("--target-ref")
    parser.add_argument("--target-tree")
    parser.add_argument("--require-approved", action="store_true")
    args = parser.parse_args(argv)
    try:
        value = load_and_validate(
            Path(args.record),
            expected_type=args.type,
            expected_target=args.target_ref,
            expected_tree=args.target_tree,
            require_approved=args.require_approved,
        )
    except ReleaseApprovalError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "status": "valid",
        "approval_id": value["approval_id"],
        "approval_type": value["approval_type"],
        "decision": value["decision"],
        "target_framework_ref": value["target_framework_ref"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
