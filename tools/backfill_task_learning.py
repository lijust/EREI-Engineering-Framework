#!/usr/bin/env python3
"""Capture retrospective EREI task-learning evidence without mixing it with prospective events.

The tool is Python-standard-library-only. It appends to
`.erei/learning/RETROSPECTIVE_TASK_EVENTS.jsonl`, validates semantic fingerprints,
and never changes Framework Core, the project Framework pin, source code or runtime.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

QUALITY = {"confirmed", "reconstructed", "inferred"}
OUTCOMES = {"verified_success", "success_with_deferred", "blocked", "failed", "canceled", "unknown"}
RISKS = {"L0", "L1", "L2", "L3", "L4", "UNKNOWN"}
SIGNALS = {
    "rework_cycles", "verification_failures", "verification_escape", "manual_workaround",
    "context_gap", "unexpected_scope_growth", "security_or_data_critical_event",
    "framework_feedback_candidate",
}


class BackfillError(RuntimeError):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _stamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _event_id(now: datetime) -> str:
    return f"EHIST-{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8].upper()}"


def _fingerprint(event: dict) -> str:
    semantic = {
        "observed_at": event["observed_at"],
        "project_repository": event["project"]["repository"],
        "framework_ref_when_executed": event["framework_ref_when_executed"],
        "task_label": event["task_label"],
        "workflow": event.get("workflow", ""),
        "risk": event.get("risk", "UNKNOWN"),
        "source_refs": sorted(event["source_refs"]),
        "outcome_class": event["outcome_class"],
        "signals": sorted(event.get("signals", []), key=lambda item: (item["name"], json.dumps(item["value"], sort_keys=True))),
    }
    canonical = json.dumps(semantic, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_event(event: dict) -> None:
    required = {
        "schema_version", "historical_event_id", "recorded_at", "observed_at", "project",
        "framework_ref_when_executed", "capture_mode", "evidence_quality", "task_label",
        "source_refs", "outcome_class", "signals", "fingerprint",
    }
    missing = sorted(required - set(event))
    if missing:
        raise BackfillError("historical event missing fields: " + ", ".join(missing))
    if event["schema_version"] != 1 or event["capture_mode"] != "retrospective":
        raise BackfillError("unsupported retrospective task event version/mode")
    if event["evidence_quality"] not in QUALITY:
        raise BackfillError("invalid evidence_quality")
    if event["outcome_class"] not in OUTCOMES:
        raise BackfillError("invalid outcome_class")
    if event.get("risk", "UNKNOWN") not in RISKS:
        raise BackfillError("invalid risk")
    if not isinstance(event["source_refs"], list) or not event["source_refs"]:
        raise BackfillError("source_refs must be a non-empty list")
    if not isinstance(event["signals"], list):
        raise BackfillError("signals must be a list")
    for signal in event["signals"]:
        if signal.get("name") not in SIGNALS:
            raise BackfillError(f"invalid signal name: {signal.get('name')}")
        if signal.get("quality") not in QUALITY:
            raise BackfillError("invalid signal quality")
        refs = signal.get("source_refs")
        if not isinstance(refs, list) or not refs:
            raise BackfillError("signal source_refs must be non-empty")
    if event["fingerprint"] != _fingerprint(event):
        raise BackfillError(f"historical event fingerprint mismatch: {event.get('historical_event_id', 'UNKNOWN')}")


@contextmanager
def _lock(directory: Path, timeout_seconds: float = 5.0):
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = directory / ".retrospective-learning.lock"
    deadline = time.monotonic() + timeout_seconds
    fd = None
    while fd is None:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(fd, f"pid={os.getpid()}\n".encode("utf-8"))
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise BackfillError(f"retrospective ledger is busy: {lock_path}")
            time.sleep(0.05)
    try:
        yield
    finally:
        if fd is not None:
            os.close(fd)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    values: list[dict] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise BackfillError(f"invalid JSONL at {path}:{number}: {exc}") from exc
        if not isinstance(item, dict):
            raise BackfillError(f"record at {path}:{number} is not an object")
        validate_event(item)
        values.append(item)
    return values


def _write_jsonl(path: Path, events: list[dict]) -> None:
    temp = path.with_suffix(".jsonl.tmp")
    temp.write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in events), encoding="utf-8")
    os.replace(temp, path)


def normalize_imported(raw: dict, *, recorded_at: datetime | None = None) -> dict:
    now = recorded_at or _utc_now()
    event = dict(raw)
    event.setdefault("schema_version", 1)
    event.setdefault("historical_event_id", _event_id(now))
    event.setdefault("recorded_at", _stamp(now))
    event["capture_mode"] = "retrospective"
    event.setdefault("signals", [])
    event["source_refs"] = sorted(set(event.get("source_refs", [])))
    for signal in event["signals"]:
        signal["source_refs"] = sorted(set(signal.get("source_refs", [])))
    event["fingerprint"] = _fingerprint(event)
    validate_event(event)
    return event


def import_events(target: Path, source: Path) -> tuple[int, Path]:
    if not (target / ".erei" / "framework.json").exists():
        raise BackfillError("target is not an EREI-integrated project: missing .erei/framework.json")
    raw = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise BackfillError("source JSON must contain a list of historical task events")
    incoming = [normalize_imported(item) for item in raw]
    learning_dir = target / ".erei" / "learning"
    ledger = learning_dir / "RETROSPECTIVE_TASK_EVENTS.jsonl"
    with _lock(learning_dir):
        existing = _read_jsonl(ledger)
        known = {item["fingerprint"] for item in existing}
        additions: list[dict] = []
        for item in incoming:
            fingerprint = item["fingerprint"]
            if fingerprint in known:
                continue
            additions.append(item)
            known.add(fingerprint)
        _write_jsonl(ledger, existing + additions)
    return len(additions), ledger


def validate_ledger(target: Path) -> tuple[int, Path]:
    ledger = target / ".erei" / "learning" / "RETROSPECTIVE_TASK_EVENTS.jsonl"
    events = _read_jsonl(ledger)
    return len(events), ledger


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill retrospective EREI task-learning evidence.")
    sub = parser.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import-json")
    imp.add_argument("--target", required=True)
    imp.add_argument("--source", required=True)
    val = sub.add_parser("validate")
    val.add_argument("--target", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        target = Path(args.target).resolve()
        if args.command == "import-json":
            added, ledger = import_events(target, Path(args.source).resolve())
            print(json.dumps({"status": "imported", "added": added, "ledger": str(ledger)}, sort_keys=True))
        else:
            count, ledger = validate_ledger(target)
            print(json.dumps({"status": "valid", "events": count, "ledger": str(ledger)}, sort_keys=True))
        return 0
    except (BackfillError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
