#!/usr/bin/env python3
"""Export only explicitly eligible, redaction-approved Framework feedback observations."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from capture_framework_feedback import _contains_secret
from validate_framework_feedback import ValidationError, validate_event


class ExportError(RuntimeError):
    pass


def _walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)


def load_eligible(path: Path) -> tuple[list[dict], int]:
    eligible: list[dict] = []
    total = 0
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        total += 1
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ExportError(f"invalid JSON at line {number}: {exc}") from exc
        try:
            validate_event(event)
        except ValidationError as exc:
            raise ExportError(f"line {number}: {exc}") from exc
        if event.get("schema_version") != 2:
            continue
        if event.get("export_eligibility") != "eligible":
            continue
        if event.get("redaction_state") not in {"not_required", "approved"}:
            raise ExportError(f"eligible event has unresolved redaction state: {event['feedback_id']}")
        if event.get("sensitivity_class") in {"confidential", "restricted"} and event.get("redaction_state") != "approved":
            raise ExportError(f"sensitive event requires explicit approved redaction before export: {event['feedback_id']}")
        if any(_contains_secret(text) for text in _walk_strings(event)):
            raise ExportError(f"possible secret detected at export boundary: {event['feedback_id']}")
        eligible.append(event)
    return eligible, total


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        events, total = load_eligible(Path(args.ledger))
        output = Path(args.output)
        temp = output.with_suffix(output.suffix + ".tmp")
        temp.write_text("".join(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n" for event in events), encoding="utf-8")
        temp.replace(output)
    except (ExportError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "exported", "source_events": total, "exported_events": len(events), "output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
