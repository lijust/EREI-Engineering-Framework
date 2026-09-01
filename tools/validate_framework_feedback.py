#!/usr/bin/env python3
"""Validate EREI Framework Feedback V1 JSONL using only the Python standard library."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path


FEEDBACK_TYPES = {
    "architecture_gap", "workflow_gap", "skill_gap", "role_gap", "security_gap",
    "data_gap", "verification_gap", "runtime_gap", "performance_gap", "context_gap",
    "integration_gap", "false_positive", "false_negative", "process_friction",
    "missing_pattern", "documentation_gap",
}
SEVERITIES = {"low", "medium", "high", "critical"}
GENERALIZABILITY = {"project_specific", "possible_generic", "likely_generic", "confirmed_multi_project"}
CONFIDENCE = {"low", "medium", "high"}
STATUSES = {"new", "triaged", "candidate", "promoted", "rejected", "archived"}
REQUIRED = {
    "schema_version", "feedback_id", "recorded_at", "project", "framework_ref", "type",
    "severity", "observation", "evidence", "suggestion", "generalizability", "confidence",
    "status", "fingerprint",
}
ALLOWED = REQUIRED | {"source_artifact", "negative_learning", "tags"}
ID_RE = re.compile(r"^EFF-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
FP_RE = re.compile(r"^[a-f0-9]{64}$")


class ValidationError(RuntimeError):
    pass


def _text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{label} must be a non-empty string")
    return value.strip()


def expected_fingerprint(event: dict) -> str:
    project = event.get("project")
    repository = project.get("repository") if isinstance(project, dict) else None
    payload = {
        "project_repository": repository or "",
        "framework_ref": event.get("framework_ref", ""),
        "type": event.get("type", ""),
        "source_artifact": event.get("source_artifact", ""),
        "observation": event.get("observation", ""),
        "suggestion": event.get("suggestion", ""),
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_event(event: dict) -> None:
    if not isinstance(event, dict):
        raise ValidationError("event must be a JSON object")
    missing = sorted(REQUIRED - set(event))
    if missing:
        raise ValidationError("missing required fields: " + ", ".join(missing))
    unknown = sorted(set(event) - ALLOWED)
    if unknown:
        raise ValidationError("unknown fields: " + ", ".join(unknown))
    if event["schema_version"] != 1:
        raise ValidationError("schema_version must be 1")
    if not isinstance(event["feedback_id"], str) or not ID_RE.fullmatch(event["feedback_id"]):
        raise ValidationError("invalid feedback_id")
    recorded_at = _text(event["recorded_at"], "recorded_at")
    try:
        datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError("invalid recorded_at") from exc
    project = event["project"]
    if not isinstance(project, dict) or set(project) - {"repository", "name"}:
        raise ValidationError("project must contain only repository/name")
    _text(project.get("repository"), "project.repository")
    if "name" in project:
        _text(project["name"], "project.name")
    _text(event["framework_ref"], "framework_ref")
    if event["type"] not in FEEDBACK_TYPES:
        raise ValidationError("invalid feedback type")
    if event["severity"] not in SEVERITIES:
        raise ValidationError("invalid severity")
    if event["generalizability"] not in GENERALIZABILITY:
        raise ValidationError("invalid generalizability")
    if event["confidence"] not in CONFIDENCE:
        raise ValidationError("invalid confidence")
    if event["status"] not in STATUSES:
        raise ValidationError("invalid status")
    _text(event["observation"], "observation")
    _text(event["suggestion"], "suggestion")
    if "source_artifact" in event:
        _text(event["source_artifact"], "source_artifact")
    if "negative_learning" in event:
        _text(event["negative_learning"], "negative_learning")
    evidence = event["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise ValidationError("evidence must be a non-empty array")
    normalized_evidence = [_text(item, "evidence item") for item in evidence]
    if len(normalized_evidence) != len(set(normalized_evidence)):
        raise ValidationError("evidence items must be unique")
    if "tags" in event:
        tags = event["tags"]
        if not isinstance(tags, list):
            raise ValidationError("tags must be an array")
        normalized_tags = [_text(item, "tag") for item in tags]
        if len(normalized_tags) != len(set(normalized_tags)):
            raise ValidationError("tags must be unique")
    fingerprint = event["fingerprint"]
    if not isinstance(fingerprint, str) or not FP_RE.fullmatch(fingerprint):
        raise ValidationError("invalid fingerprint format")
    if fingerprint != expected_fingerprint(event):
        raise ValidationError("fingerprint does not match event semantics")


def validate_jsonl(path: Path) -> int:
    if not path.exists():
        raise ValidationError(f"missing feedback ledger: {path}")
    count = 0
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"invalid JSON at line {line_number}: {exc}") from exc
        try:
            validate_event(event)
        except ValidationError as exc:
            raise ValidationError(f"line {line_number}: {exc}") from exc
        count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate EREI Framework Feedback JSONL")
    parser.add_argument("ledger")
    args = parser.parse_args(argv)
    try:
        count = validate_jsonl(Path(args.ledger))
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"valid": True, "events": count}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
