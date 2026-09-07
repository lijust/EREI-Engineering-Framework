#!/usr/bin/env python3
"""Strict validator for the current prospective learning-cycle progress record."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SHA40_RE = re.compile(r"^[a-f0-9]{40}$")
CYCLE_ID_RE = re.compile(r"^PLC-[0-9]{8}-[A-Z0-9-]+$")
STEP_ORDER = ("capture", "review", "feedback", "improvement", "adoption", "measured_outcome")


class CycleStatusError(RuntimeError):
    pass


def _text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CycleStatusError(f"{label} must be a non-empty string")
    return value.strip()


def _sha(value, label: str) -> str:
    text = _text(value, label)
    if not SHA40_RE.fullmatch(text):
        raise CycleStatusError(f"{label} must be an exact 40-character commit")
    return text


def _datetime(value, label: str) -> str:
    text = _text(value, label)
    if "T" not in text or not (text.endswith("Z") or re.search(r"[+-][0-9]{2}:[0-9]{2}$", text)):
        raise CycleStatusError(f"{label} must be RFC3339 date-time with timezone")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CycleStatusError(f"invalid {label}") from exc
    if parsed.tzinfo is None:
        raise CycleStatusError(f"{label} must include timezone")
    return text


def _unique_texts(value, label: str, minimum: int = 0) -> list[str]:
    if not isinstance(value, list) or len(value) < minimum:
        raise CycleStatusError(f"{label} must contain at least {minimum} item(s)")
    result = [_text(item, f"{label} item") for item in value]
    if len(result) != len(set(result)):
        raise CycleStatusError(f"{label} must be unique")
    return result


def validate_step(name: str, step: object) -> str:
    if not isinstance(step, dict):
        raise CycleStatusError(f"steps.{name} must be an object")
    allowed = {"status", "repository", "ref", "evidence", "reason"}
    unknown = sorted(set(step) - allowed)
    if unknown:
        raise CycleStatusError(f"steps.{name} unknown fields: " + ", ".join(unknown))
    if "status" not in step:
        raise CycleStatusError(f"steps.{name}.status is required")
    status = step["status"]
    if status not in {"completed", "pending"}:
        raise CycleStatusError(f"invalid steps.{name}.status")
    if status == "completed":
        required = {"status", "repository", "ref", "evidence"}
        missing = sorted(required - set(step))
        if missing:
            raise CycleStatusError(f"completed steps.{name} missing fields: " + ", ".join(missing))
        if "reason" in step:
            raise CycleStatusError(f"completed steps.{name} must not contain reason")
        _text(step["repository"], f"steps.{name}.repository")
        _sha(step["ref"], f"steps.{name}.ref")
        _unique_texts(step["evidence"], f"steps.{name}.evidence", 1)
    else:
        if set(step) != {"status", "reason"}:
            raise CycleStatusError(f"pending steps.{name} must contain exactly status/reason")
        _text(step["reason"], f"steps.{name}.reason")
    return status


def validate(data: object) -> dict:
    if not isinstance(data, dict):
        raise CycleStatusError("cycle status must be an object")
    required = {
        "schema_version", "cycle_id", "updated_at", "status", "stable_framework_ref",
        "framework_candidate_ref", "source_project", "steps", "blockers",
    }
    missing = sorted(required - set(data))
    unknown = sorted(set(data) - required)
    if missing:
        raise CycleStatusError("cycle status missing fields: " + ", ".join(missing))
    if unknown:
        raise CycleStatusError("cycle status unknown fields: " + ", ".join(unknown))
    if data["schema_version"] != 1:
        raise CycleStatusError("unsupported schema_version")
    if not isinstance(data["cycle_id"], str) or not CYCLE_ID_RE.fullmatch(data["cycle_id"]):
        raise CycleStatusError("invalid cycle_id")
    _datetime(data["updated_at"], "updated_at")
    if data["status"] not in {"awaiting_measured_outcome", "complete", "blocked"}:
        raise CycleStatusError("invalid cycle status")
    stable_ref = _sha(data["stable_framework_ref"], "stable_framework_ref")
    candidate_ref = _sha(data["framework_candidate_ref"], "framework_candidate_ref")
    if stable_ref == candidate_ref:
        raise CycleStatusError("framework_candidate_ref must differ from stable_framework_ref")
    source = data["source_project"]
    if not isinstance(source, dict) or set(source) != {"repository"}:
        raise CycleStatusError("source_project must contain exactly repository")
    _text(source["repository"], "source_project.repository")
    steps = data["steps"]
    if not isinstance(steps, dict) or set(steps) != set(STEP_ORDER):
        raise CycleStatusError("steps must contain exactly capture/review/feedback/improvement/adoption/measured_outcome")
    statuses = [validate_step(name, steps[name]) for name in STEP_ORDER]
    seen_pending = False
    for name, status in zip(STEP_ORDER, statuses):
        if status == "pending":
            seen_pending = True
        elif seen_pending:
            raise CycleStatusError(f"completed step {name} cannot follow a pending earlier step")
    blockers = _unique_texts(data["blockers"], "blockers")
    if data["status"] == "complete":
        if any(status != "completed" for status in statuses):
            raise CycleStatusError("complete cycle requires all six steps completed")
        if blockers:
            raise CycleStatusError("complete cycle must not contain blockers")
    elif data["status"] == "awaiting_measured_outcome":
        if statuses[:5] != ["completed"] * 5 or statuses[5] != "pending":
            raise CycleStatusError("awaiting_measured_outcome requires first five steps completed and measured_outcome pending")
        if "measured_post_adoption_outcome_pending" not in blockers:
            raise CycleStatusError("awaiting_measured_outcome requires measured_post_adoption_outcome_pending blocker")
    elif not blockers:
        raise CycleStatusError("blocked cycle requires at least one blocker")
    return {
        "cycle_id": data["cycle_id"],
        "status": data["status"],
        "completed_steps": sum(status == "completed" for status in statuses),
        "pending_steps": sum(status == "pending" for status in statuses),
        "blockers": blockers,
    }


def load_and_validate(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CycleStatusError(f"invalid JSON: {exc}") from exc
    return validate(data)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("status_file")
    args = parser.parse_args(argv)
    try:
        result = load_and_validate(Path(args.status_file))
    except (CycleStatusError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "valid", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
