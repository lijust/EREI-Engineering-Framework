#!/usr/bin/env python3
"""Strict validation for EREI Framework Feedback ledgers."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from validation_contract import ContractValidationError, validate_feedback_event_shape


class ValidationError(RuntimeError):
    pass


def expected_fingerprint(event: dict) -> str:
    project = event.get("project")
    repository = project.get("repository") if isinstance(project, dict) else None
    if event.get("schema_version") == 1:
        payload = {
            "project_repository": repository or "",
            "framework_ref": event.get("framework_ref", ""),
            "type": event.get("type", ""),
            "source_artifact": event.get("source_artifact", ""),
            "observation": event.get("observation", ""),
            "suggestion": event.get("suggestion", ""),
        }
    else:
        payload = {
            "project": event.get("project"),
            "framework_ref": event.get("framework_ref", ""),
            "type": event.get("type", ""),
            "severity": event.get("severity", ""),
            "source_artifact": event.get("source_artifact", ""),
            "observation": event.get("observation", ""),
            "evidence": event.get("evidence", []),
            "suggestion": event.get("suggestion", ""),
            "negative_learning": event.get("negative_learning", ""),
            "generalizability": event.get("generalizability", ""),
            "confidence": event.get("confidence", ""),
            "status": event.get("status", ""),
            "sensitivity_class": event.get("sensitivity_class", ""),
            "redaction_state": event.get("redaction_state", ""),
            "export_eligibility": event.get("export_eligibility", ""),
            "tags": event.get("tags", []),
        }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_event(event: dict) -> None:
    try:
        validate_feedback_event_shape(event)
    except ContractValidationError as exc:
        raise ValidationError(str(exc)) from exc
    if event.get("schema_version") == 2 and event.get("status") != "new":
        raise ValidationError("V2 project-local feedback is immutable observation data; central decisions own later status")
    if event["fingerprint"] != expected_fingerprint(event):
        raise ValidationError("fingerprint does not match event content")


def validate_records(events: list[dict]) -> None:
    seen_ids: set[str] = set()
    for index, event in enumerate(events, start=1):
        try:
            validate_event(event)
        except ValidationError as exc:
            raise ValidationError(f"record {index}: {exc}") from exc
        feedback_id = event["feedback_id"]
        if feedback_id in seen_ids:
            raise ValidationError(f"duplicate feedback_id: {feedback_id}")
        seen_ids.add(feedback_id)


def validate_jsonl(path: Path) -> int:
    if not path.exists():
        raise ValidationError(f"missing feedback ledger: {path}")
    events: list[dict] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"invalid JSON at line {line_number}: {exc}") from exc
        if not isinstance(event, dict):
            raise ValidationError(f"line {line_number}: event must be an object")
        events.append(event)
    validate_records(events)
    return len(events)


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
