#!/usr/bin/env python3
"""Retrospective Task Learning V2: stable occurrence identity, frozen provenance and amendments.

Legacy V1 records remain readable and immutable. New imports use V2 occurrence identity;
evidence enrichment/correction is represented as an explicit amendment rather than a
new occurrence or silent overwrite. JSONL files are generated projections of immutable
V2 record files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from validation_contract import ContractValidationError, validate_retrospective_event_shape

QUALITY = {"confirmed", "reconstructed", "inferred"}
OUTCOMES = {"verified_success", "success_with_deferred", "blocked", "failed", "canceled", "unknown"}
RISKS = {"L0", "L1", "L2", "L3", "L4", "UNKNOWN"}
COUNT_SIGNALS = {"rework_cycles", "verification_failures"}
BOOLEAN_SIGNALS = {
    "verification_escape", "manual_workaround", "context_gap", "unexpected_scope_growth",
    "security_or_data_critical_event", "framework_feedback_candidate",
}
SIGNALS = COUNT_SIGNALS | BOOLEAN_SIGNALS
SOURCE_ID_RE = re.compile(r"^ESRC-[A-Z0-9][A-Z0-9._-]{2,127}$")
HIST_ID_RE = re.compile(r"^EHIST-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
AMEND_ID_RE = re.compile(r"^EAMD-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
SHA40_RE = re.compile(r"^[a-f0-9]{40}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
CANONICALIZATION_VERSION = 2


class BackfillError(RuntimeError):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _stamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _event_id(now: datetime) -> str:
    return f"EHIST-{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8].upper()}"


def _amendment_id(now: datetime) -> str:
    return f"EAMD-{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8].upper()}"


def _text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BackfillError(f"{label} must be a non-empty string")
    return value.strip()


def _datetime(value, label: str, *, nullable: bool = False):
    if value is None and nullable:
        return None
    text = _text(value, label)
    if "T" not in text or not (text.endswith("Z") or re.search(r"[+-][0-9]{2}:[0-9]{2}$", text)):
        raise BackfillError(f"{label} must be an RFC3339 date-time with timezone")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BackfillError(f"invalid {label}") from exc
    if parsed.tzinfo is None:
        raise BackfillError(f"{label} must include timezone")
    return text


def _exact_fields(value: dict, required: set[str], allowed: set[str], label: str) -> None:
    missing = sorted(required - set(value))
    if missing:
        raise BackfillError(f"{label} missing fields: " + ", ".join(missing))
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise BackfillError(f"{label} unknown fields: " + ", ".join(unknown))


def _unique_texts(value, label: str, *, minimum: int = 0, pattern=None) -> list[str]:
    if not isinstance(value, list) or len(value) < minimum:
        raise BackfillError(f"{label} must be a list with at least {minimum} item(s)")
    result = []
    for item in value:
        text = _text(item, f"{label} item")
        if pattern is not None and not pattern.fullmatch(text):
            raise BackfillError(f"invalid {label} item: {text}")
        result.append(text)
    if len(result) != len(set(result)):
        raise BackfillError(f"{label} items must be unique")
    return result


def _canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _canonical_signals(signals: list[dict]) -> list[dict]:
    return sorted(
        signals,
        key=lambda item: (
            item["name"],
            _canonical_json(item["value"]),
            item["quality"],
            _canonical_json(sorted(item["source_refs"])),
        ),
    )


def _fingerprint_v1(event: dict) -> str:
    semantic = {
        "observed_at": event["observed_at"],
        "project_repository": event["project"]["repository"],
        "framework_ref_when_executed": event["framework_ref_when_executed"],
        "task_label": event["task_label"],
        "workflow": event.get("workflow", ""),
        "risk": event.get("risk", "UNKNOWN"),
        "source_refs": sorted(event["source_refs"]),
        "outcome_class": event["outcome_class"],
        "signals": sorted(event.get("signals", []), key=lambda item: (item["name"], _canonical_json(item["value"]))),
    }
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _fingerprint_v2(event: dict) -> str:
    semantic = {
        "occurrence_id": event["occurrence_id"],
        "observed_at": event["observed_at"],
        "project": event["project"],
        "framework_ref_when_executed": event["framework_ref_when_executed"],
        "evidence_quality": event["evidence_quality"],
        "task_label": event["task_label"],
        "workflow": event.get("workflow", ""),
        "risk": event.get("risk", "UNKNOWN"),
        "source_refs": sorted(event["source_refs"]),
        "outcome_class": event["outcome_class"],
        "signals": _canonical_signals(event.get("signals", [])),
        "notes": event.get("notes", ""),
        "producer": event["producer"],
        "canonicalization_version": event["canonicalization_version"],
    }
    return hashlib.sha256(_canonical_json(semantic).encode("utf-8")).hexdigest()


def _validate_signal(signal: dict, label: str, *, v2: bool) -> None:
    if not isinstance(signal, dict):
        raise BackfillError(f"{label} must be an object")
    _exact_fields(signal, {"name", "value", "quality", "source_refs"}, {"name", "value", "quality", "source_refs"}, label)
    name = signal["name"]
    if name not in SIGNALS:
        raise BackfillError(f"invalid signal name: {name}")
    if signal["quality"] not in QUALITY:
        raise BackfillError(f"invalid {label}.quality")
    if name in COUNT_SIGNALS:
        if type(signal["value"]) is not int or signal["value"] < 0:
            raise BackfillError(f"{label}.value must be a non-negative integer")
    elif type(signal["value"]) is not bool:
        raise BackfillError(f"{label}.value must be boolean")
    _unique_texts(signal["source_refs"], f"{label}.source_refs", minimum=1, pattern=SOURCE_ID_RE if v2 else None)


def validate_v1(event: dict) -> None:
    required = {
        "schema_version", "historical_event_id", "recorded_at", "observed_at", "project",
        "framework_ref_when_executed", "capture_mode", "evidence_quality", "task_label",
        "source_refs", "outcome_class", "signals", "fingerprint",
    }
    allowed = required | {"workflow", "risk", "notes"}
    _exact_fields(event, required, allowed, "legacy historical event")
    if event["schema_version"] != 1 or event["capture_mode"] != "retrospective":
        raise BackfillError("unsupported legacy retrospective event version/mode")
    if not isinstance(event["historical_event_id"], str) or not HIST_ID_RE.fullmatch(event["historical_event_id"]):
        raise BackfillError("invalid historical_event_id")
    _datetime(event["recorded_at"], "recorded_at")
    _datetime(event["observed_at"], "observed_at")
    project = event["project"]
    if not isinstance(project, dict):
        raise BackfillError("project must be an object")
    _exact_fields(project, {"repository"}, {"repository", "name"}, "project")
    _text(project["repository"], "project.repository")
    if "name" in project:
        _text(project["name"], "project.name")
    _text(event["framework_ref_when_executed"], "framework_ref_when_executed")
    if event["evidence_quality"] not in QUALITY:
        raise BackfillError("invalid evidence_quality")
    _text(event["task_label"], "task_label")
    if "workflow" in event:
        _text(event["workflow"], "workflow")
    if event.get("risk", "UNKNOWN") not in RISKS:
        raise BackfillError("invalid risk")
    _unique_texts(event["source_refs"], "source_refs", minimum=1)
    if event["outcome_class"] not in OUTCOMES:
        raise BackfillError("invalid outcome_class")
    if not isinstance(event["signals"], list):
        raise BackfillError("signals must be a list")
    for index, signal in enumerate(event["signals"]):
        _validate_signal(signal, f"signals[{index}]", v2=False)
    if "notes" in event:
        _text(event["notes"], "notes")
    if not isinstance(event["fingerprint"], str) or not SHA256_RE.fullmatch(event["fingerprint"]):
        raise BackfillError("invalid fingerprint")
    if event["fingerprint"] != _fingerprint_v1(event):
        raise BackfillError(f"historical event fingerprint mismatch: {event['historical_event_id']}")


def validate_v2(event: dict) -> None:
    try:
        validate_retrospective_event_shape(event)
    except ContractValidationError as exc:
        raise BackfillError(str(exc)) from exc
    if event["canonicalization_version"] != CANONICALIZATION_VERSION:
        raise BackfillError("unsupported canonicalization_version")
    if not SHA40_RE.fullmatch(event["producer"]["ref"]):
        raise BackfillError("producer.ref must be an exact 40-character commit")
    if event["producer"]["canonicalization_version"] != CANONICALIZATION_VERSION:
        raise BackfillError("producer canonicalization version mismatch")
    if event["fingerprint"] != _fingerprint_v2(event):
        raise BackfillError(f"historical event fingerprint mismatch: {event['historical_event_id']}")


def validate_event(event: dict) -> None:
    if not isinstance(event, dict):
        raise BackfillError("historical event must be an object")
    if event.get("schema_version") == 1:
        validate_v1(event)
    elif event.get("schema_version") == 2:
        validate_v2(event)
    else:
        raise BackfillError("unsupported retrospective schema_version")


def validate_source_record(record: dict) -> None:
    if not isinstance(record, dict):
        raise BackfillError("source provenance record must be an object")
    required = {
        "schema_version", "source_id", "kind", "repository", "revision", "locator",
        "event_time", "event_time_meaning", "reconstruction_time",
    }
    allowed = required | {"artifact_path", "artifact_digest", "ci_run_id", "ci_attempt", "notes"}
    _exact_fields(record, required, allowed, "source provenance")
    if record["schema_version"] != 1:
        raise BackfillError("unsupported source provenance schema_version")
    if not isinstance(record["source_id"], str) or not SOURCE_ID_RE.fullmatch(record["source_id"]):
        raise BackfillError("invalid source_id")
    if record["kind"] not in {"github_pr", "github_commit", "ci_run", "artifact", "runtime_episode", "other"}:
        raise BackfillError("invalid source provenance kind")
    _text(record["repository"], "source repository")
    if not isinstance(record["revision"], str) or not SHA40_RE.fullmatch(record["revision"]):
        raise BackfillError("source revision must be an exact 40-character commit")
    _text(record["locator"], "source locator")
    if "artifact_path" in record:
        _text(record["artifact_path"], "artifact_path")
    if "artifact_digest" in record and (not isinstance(record["artifact_digest"], str) or not SHA256_RE.fullmatch(record["artifact_digest"])):
        raise BackfillError("artifact_digest must be sha256")
    for key in ("ci_run_id", "ci_attempt"):
        if key in record and (type(record[key]) is not int or record[key] < 1):
            raise BackfillError(f"{key} must be a positive integer")
    _datetime(record["event_time"], "event_time", nullable=True)
    if record["event_time_meaning"] not in {"exact_event", "task_completion", "observation", "unknown"}:
        raise BackfillError("invalid event_time_meaning")
    if record["event_time"] is None and record["event_time_meaning"] != "unknown":
        raise BackfillError("null event_time requires event_time_meaning=unknown")
    _datetime(record["reconstruction_time"], "reconstruction_time")
    if "notes" in record:
        _text(record["notes"], "source notes")


def _load_provenance_source(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise BackfillError("provenance JSON must contain a list")
    seen: set[str] = set()
    for record in raw:
        validate_source_record(record)
        if record["source_id"] in seen:
            raise BackfillError(f"duplicate source_id in provenance input: {record['source_id']}")
        seen.add(record["source_id"])
    return raw


def validate_amendment(amendment: dict) -> None:
    if not isinstance(amendment, dict):
        raise BackfillError("amendment must be an object")
    required = {"schema_version", "amendment_id", "recorded_at", "occurrence_id", "reason", "changes", "producer"}
    _exact_fields(amendment, required, required, "amendment")
    if amendment["schema_version"] != 1:
        raise BackfillError("unsupported amendment schema_version")
    if not isinstance(amendment["amendment_id"], str) or not AMEND_ID_RE.fullmatch(amendment["amendment_id"]):
        raise BackfillError("invalid amendment_id")
    _datetime(amendment["recorded_at"], "amendment.recorded_at")
    _text(amendment["occurrence_id"], "amendment.occurrence_id")
    _text(amendment["reason"], "amendment.reason")
    changes = amendment["changes"]
    if not isinstance(changes, dict) or not changes:
        raise BackfillError("amendment.changes must be a non-empty object")
    allowed_changes = {"observed_at", "evidence_quality", "source_refs", "outcome_class", "signals", "notes"}
    unknown = sorted(set(changes) - allowed_changes)
    if unknown:
        raise BackfillError("unsupported amendment changes: " + ", ".join(unknown))
    if "observed_at" in changes:
        _datetime(changes["observed_at"], "changes.observed_at")
    if "evidence_quality" in changes and changes["evidence_quality"] not in QUALITY:
        raise BackfillError("invalid amendment evidence_quality")
    if "source_refs" in changes:
        _unique_texts(changes["source_refs"], "changes.source_refs", minimum=1, pattern=SOURCE_ID_RE)
    if "outcome_class" in changes and changes["outcome_class"] not in OUTCOMES:
        raise BackfillError("invalid amendment outcome_class")
    if "signals" in changes:
        if not isinstance(changes["signals"], list):
            raise BackfillError("changes.signals must be a list")
        for index, signal in enumerate(changes["signals"]):
            _validate_signal(signal, f"changes.signals[{index}]", v2=True)
    if "notes" in changes:
        _text(changes["notes"], "changes.notes")
    producer = amendment["producer"]
    if not isinstance(producer, dict):
        raise BackfillError("amendment producer must be an object")
    _exact_fields(producer, {"repository", "ref"}, {"repository", "ref"}, "amendment producer")
    _text(producer["repository"], "producer.repository")
    if not isinstance(producer["ref"], str) or not SHA40_RE.fullmatch(producer["ref"]):
        raise BackfillError("amendment producer.ref must be exact 40-character commit")


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


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BackfillError(f"invalid JSON at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BackfillError(f"record at {path} is not an object")
    return value


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    values = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise BackfillError(f"invalid JSONL at {path}:{number}: {exc}") from exc
        if not isinstance(item, dict):
            raise BackfillError(f"record at {path}:{number} is not an object")
        values.append(item)
    return values


def _write_jsonl(path: Path, values: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in values), encoding="utf-8")
    os.replace(temp, path)


def _write_immutable(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = _read_json(path)
        if existing == value:
            return
        raise BackfillError(f"immutable record conflicts: {path}")
    temp = path.with_name(path.name + f".{uuid4().hex}.tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def _paths(target: Path) -> dict[str, Path]:
    learning = target / ".erei" / "learning"
    return {
        "root": learning,
        "legacy": learning / "RETROSPECTIVE_TASK_EVENTS.jsonl",
        "events": learning / "retrospective-events",
        "amendments": learning / "retrospective-amendments",
        "sources": learning / "retrospective-sources",
        "event_projection": learning / "RETROSPECTIVE_TASK_EVENTS_V2.jsonl",
        "amendment_projection": learning / "RETROSPECTIVE_TASK_AMENDMENTS.jsonl",
        "source_projection": learning / "RETROSPECTIVE_SOURCE_PROVENANCE.jsonl",
    }


def _load_v2_events(paths: dict[str, Path]) -> list[dict]:
    records = [_read_json(path) for path in sorted(paths["events"].glob("*.json"))] if paths["events"].exists() else []
    by_occurrence: dict[str, dict] = {}
    seen_ids: set[str] = set()
    for event in records:
        validate_v2(event)
        occurrence = event["occurrence_id"]
        if occurrence in by_occurrence and by_occurrence[occurrence] != event:
            raise BackfillError(f"conflicting occurrence_id: {occurrence}")
        if event["historical_event_id"] in seen_ids:
            raise BackfillError(f"duplicate historical_event_id: {event['historical_event_id']}")
        seen_ids.add(event["historical_event_id"])
        by_occurrence[occurrence] = event
    return sorted(by_occurrence.values(), key=lambda item: item["occurrence_id"])


def _load_sources(paths: dict[str, Path]) -> list[dict]:
    records = [_read_json(path) for path in sorted(paths["sources"].glob("*.json"))] if paths["sources"].exists() else []
    by_id: dict[str, dict] = {}
    for record in records:
        validate_source_record(record)
        source_id = record["source_id"]
        if source_id in by_id and by_id[source_id] != record:
            raise BackfillError(f"conflicting source_id: {source_id}")
        by_id[source_id] = record
    return sorted(by_id.values(), key=lambda item: item["source_id"])


def _load_amendments(paths: dict[str, Path]) -> list[dict]:
    records = [_read_json(path) for path in sorted(paths["amendments"].glob("*.json"))] if paths["amendments"].exists() else []
    by_id: dict[str, dict] = {}
    for record in records:
        validate_amendment(record)
        amendment_id = record["amendment_id"]
        if amendment_id in by_id and by_id[amendment_id] != record:
            raise BackfillError(f"conflicting amendment_id: {amendment_id}")
        by_id[amendment_id] = record
    return sorted(by_id.values(), key=lambda item: (item["recorded_at"], item["amendment_id"]))


def _validate_references(events: list[dict], amendments: list[dict], sources: list[dict]) -> None:
    source_ids = {item["source_id"] for item in sources}
    occurrences = {item["occurrence_id"] for item in events}
    for event in events:
        missing = sorted(set(event["source_refs"]) - source_ids)
        for signal in event["signals"]:
            missing.extend(sorted(set(signal["source_refs"]) - source_ids))
        if missing:
            raise BackfillError(f"occurrence {event['occurrence_id']} references missing provenance: {sorted(set(missing))}")
    for amendment in amendments:
        if amendment["occurrence_id"] not in occurrences:
            raise BackfillError(f"amendment references unknown occurrence: {amendment['occurrence_id']}")
        changes = amendment["changes"]
        refs = list(changes.get("source_refs", []))
        for signal in changes.get("signals", []):
            refs.extend(signal["source_refs"])
        missing = sorted(set(refs) - source_ids)
        if missing:
            raise BackfillError(f"amendment {amendment['amendment_id']} references missing provenance: {missing}")


def _apply_amendments(event: dict, amendments: list[dict]) -> dict:
    effective = json.loads(json.dumps(event))
    for amendment in amendments:
        if amendment["occurrence_id"] != event["occurrence_id"]:
            continue
        for key, value in amendment["changes"].items():
            effective[key] = value
    return effective


def normalize_v2(raw: dict, *, producer_repository: str, producer_ref: str, recorded_at: datetime | None = None) -> dict:
    now = recorded_at or _utc_now()
    if not isinstance(raw, dict):
        raise BackfillError("historical source item must be an object")
    if raw.get("schema_version") not in (None, 2):
        raise BackfillError("new import accepts V2 source items only; preserve V1 through the legacy ledger")
    occurrence_id = _text(raw.get("occurrence_id"), "occurrence_id")
    event = dict(raw)
    event["schema_version"] = 2
    event.setdefault("historical_event_id", _event_id(now))
    event.setdefault("recorded_at", _stamp(now))
    event["capture_mode"] = "retrospective"
    event["occurrence_id"] = occurrence_id
    event.setdefault("signals", [])
    event["source_refs"] = sorted(set(event.get("source_refs", [])))
    for signal in event["signals"]:
        signal["source_refs"] = sorted(set(signal.get("source_refs", [])))
    event["producer"] = {
        "repository": _text(producer_repository, "producer repository"),
        "ref": _text(producer_ref, "producer ref"),
        "schema_version": 2,
        "canonicalization_version": CANONICALIZATION_VERSION,
    }
    event["canonicalization_version"] = CANONICALIZATION_VERSION
    event["fingerprint"] = _fingerprint_v2(event)
    validate_v2(event)
    return event


def normalize_amendment(raw: dict, *, producer_repository: str, producer_ref: str, recorded_at: datetime | None = None) -> dict:
    now = recorded_at or _utc_now()
    if not isinstance(raw, dict):
        raise BackfillError("amendment source item must be an object")
    amendment = dict(raw)
    amendment["schema_version"] = 1
    amendment.setdefault("amendment_id", _amendment_id(now))
    amendment.setdefault("recorded_at", _stamp(now))
    amendment["producer"] = {
        "repository": _text(producer_repository, "producer repository"),
        "ref": _text(producer_ref, "producer ref"),
    }
    validate_amendment(amendment)
    return amendment


def import_events(target: Path, source: Path, provenance: Path, *, producer_repository: str, producer_ref: str) -> tuple[int, int]:
    if not (target / ".erei" / "framework.json").exists():
        raise BackfillError("target is not an EREI-integrated project: missing .erei/framework.json")
    raw = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise BackfillError("source JSON must contain a list of historical task events")
    incoming = [normalize_v2(item, producer_repository=producer_repository, producer_ref=producer_ref) for item in raw]
    incoming_sources = _load_provenance_source(provenance)
    paths = _paths(target)
    with _lock(paths["root"]):
        existing_events = _load_v2_events(paths)
        existing_sources = _load_sources(paths)
        existing_amendments = _load_amendments(paths)
        event_by_occurrence = {item["occurrence_id"]: item for item in existing_events}
        source_by_id = {item["source_id"]: item for item in existing_sources}
        event_additions = []
        source_additions = []
        for record in incoming_sources:
            source_id = record["source_id"]
            if source_id in source_by_id:
                if source_by_id[source_id] != record:
                    raise BackfillError(f"source_id already exists with conflicting provenance: {source_id}")
                continue
            source_additions.append(record)
            source_by_id[source_id] = record
        for event in incoming:
            occurrence = event["occurrence_id"]
            if occurrence in event_by_occurrence:
                if event_by_occurrence[occurrence] != event:
                    raise BackfillError(
                        f"occurrence {occurrence} already exists with different content; use an amendment for enrichment/correction"
                    )
                continue
            event_additions.append(event)
            event_by_occurrence[occurrence] = event
        candidate_events = existing_events + event_additions
        candidate_sources = existing_sources + source_additions
        _validate_references(candidate_events, existing_amendments, candidate_sources)
        for record in source_additions:
            _write_immutable(paths["sources"] / f"{record['source_id']}.json", record)
        for event in event_additions:
            safe_id = hashlib.sha256(event["occurrence_id"].encode("utf-8")).hexdigest()[:24]
            _write_immutable(paths["events"] / f"{safe_id}.json", event)
        persisted_events = _load_v2_events(paths)
        persisted_sources = _load_sources(paths)
        _validate_references(persisted_events, existing_amendments, persisted_sources)
        _write_jsonl(paths["event_projection"], persisted_events)
        _write_jsonl(paths["source_projection"], persisted_sources)
        _write_jsonl(paths["amendment_projection"], existing_amendments)
    return len(event_additions), len(source_additions)


def import_amendments(target: Path, source: Path, provenance: Path | None, *, producer_repository: str, producer_ref: str) -> tuple[int, int]:
    raw = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise BackfillError("amendment JSON must contain a list")
    incoming = [normalize_amendment(item, producer_repository=producer_repository, producer_ref=producer_ref) for item in raw]
    incoming_sources = _load_provenance_source(provenance) if provenance else []
    paths = _paths(target)
    with _lock(paths["root"]):
        events = _load_v2_events(paths)
        existing_amendments = _load_amendments(paths)
        existing_sources = _load_sources(paths)
        by_amendment = {item["amendment_id"]: item for item in existing_amendments}
        by_source = {item["source_id"]: item for item in existing_sources}
        source_additions = []
        amendment_additions = []
        for record in incoming_sources:
            sid = record["source_id"]
            if sid in by_source:
                if by_source[sid] != record:
                    raise BackfillError(f"source_id already exists with conflicting provenance: {sid}")
                continue
            source_additions.append(record)
            by_source[sid] = record
        for amendment in incoming:
            aid = amendment["amendment_id"]
            if aid in by_amendment:
                if by_amendment[aid] != amendment:
                    raise BackfillError(f"amendment_id conflict: {aid}")
                continue
            amendment_additions.append(amendment)
            by_amendment[aid] = amendment
        candidate_amendments = existing_amendments + amendment_additions
        candidate_sources = existing_sources + source_additions
        _validate_references(events, candidate_amendments, candidate_sources)
        for record in source_additions:
            _write_immutable(paths["sources"] / f"{record['source_id']}.json", record)
        for amendment in amendment_additions:
            _write_immutable(paths["amendments"] / f"{amendment['amendment_id']}.json", amendment)
        persisted_amendments = _load_amendments(paths)
        persisted_sources = _load_sources(paths)
        _validate_references(events, persisted_amendments, persisted_sources)
        _write_jsonl(paths["event_projection"], events)
        _write_jsonl(paths["source_projection"], persisted_sources)
        _write_jsonl(paths["amendment_projection"], persisted_amendments)
    return len(amendment_additions), len(source_additions)


def validate_ledger(target: Path) -> dict:
    paths = _paths(target)
    legacy = _read_jsonl(paths["legacy"])
    for event in legacy:
        validate_v1(event)
    events = _load_v2_events(paths)
    amendments = _load_amendments(paths)
    sources = _load_sources(paths)
    _validate_references(events, amendments, sources)
    effective = [_apply_amendments(event, amendments) for event in events]
    return {
        "legacy_events": len(legacy),
        "v2_events": len(events),
        "amendments": len(amendments),
        "provenance_records": len(sources),
        "effective_v2_events": len(effective),
        "canonicalization_version": CANONICALIZATION_VERSION,
    }


def canonicalization_vector(raw: dict) -> dict:
    event = normalize_v2(
        raw,
        producer_repository="lijust/EREI-Engineering-Framework",
        producer_ref="0" * 40,
        recorded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    return {"canonicalization_version": CANONICALIZATION_VERSION, "fingerprint": event["fingerprint"]}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retrospective EREI Task Learning V2 hardening tool")
    sub = parser.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import-json")
    imp.add_argument("--target", required=True)
    imp.add_argument("--source", required=True)
    imp.add_argument("--provenance", required=True)
    imp.add_argument("--producer-repository", default="lijust/EREI-Engineering-Framework")
    imp.add_argument("--producer-ref", required=True)
    amd = sub.add_parser("amend-json")
    amd.add_argument("--target", required=True)
    amd.add_argument("--source", required=True)
    amd.add_argument("--provenance")
    amd.add_argument("--producer-repository", default="lijust/EREI-Engineering-Framework")
    amd.add_argument("--producer-ref", required=True)
    val = sub.add_parser("validate")
    val.add_argument("--target", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        target = Path(args.target).resolve()
        if args.command == "import-json":
            events, sources = import_events(
                target,
                Path(args.source).resolve(),
                Path(args.provenance).resolve(),
                producer_repository=args.producer_repository,
                producer_ref=args.producer_ref,
            )
            payload = {"status": "imported", "events_added": events, "sources_added": sources}
        elif args.command == "amend-json":
            amendments, sources = import_amendments(
                target,
                Path(args.source).resolve(),
                Path(args.provenance).resolve() if args.provenance else None,
                producer_repository=args.producer_repository,
                producer_ref=args.producer_ref,
            )
            payload = {"status": "amended", "amendments_added": amendments, "sources_added": sources}
        else:
            payload = {"status": "valid", **validate_ledger(target)}
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0
    except (BackfillError, ContractValidationError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
