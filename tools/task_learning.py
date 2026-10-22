#!/usr/bin/env python3
"""Project-local Task Learning V2 with immutable occurrences and deterministic reviews.

Authoritative V2 events/reviews are individual immutable JSON files so parallel Git
branches normally merge without editing one shared ledger. JSONL, state and Markdown
are rebuildable projections except that V1 positional review membership requires
the original complete event projection. Legacy V1 JSONL remains readable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from validation_contract import (
    ContractValidationError,
    OCCURRENCE_ID_RE,
    REVIEW_ID_RE,
    validate_learning_review_shape,
    validate_task_event_shape,
)

RISK_LEVELS = {"L0", "L1", "L2", "L3", "L4"}
OUTCOME_CLASSES = {"verified_success", "success_with_deferred", "blocked", "failed", "canceled"}
DURATION_CLASSES = {"short", "medium", "long", "unknown"}
SIGNAL_KEYS = (
    "rework_cycles", "verification_failures", "verification_escape",
    "framework_feedback_created", "manual_workaround", "context_gap",
    "unexpected_scope_growth", "security_or_data_critical_event",
)
TRIGGER_LEVELS = {
    "INSUFFICIENT_EVIDENCE": -1,
    "LEARNING_HEALTHY": 0,
    "LEARNING_WATCH": 1,
    "REVIEW_RECOMMENDED": 2,
    "REVIEW_DUE": 3,
    "IMMEDIATE_REVIEW": 4,
}


class LearningError(RuntimeError):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _timestamp(now: datetime) -> str:
    return now.isoformat().replace("+00:00", "Z")


def _event_id(now: datetime) -> str:
    return f"ETASK-{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8].upper()}"


def _occurrence_id(now: datetime) -> str:
    return f"EOCC-{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8].upper()}"


def _review_id(now: datetime) -> str:
    return f"ELR-{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8].upper()}"


def _nonempty(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LearningError(f"{label} must not be empty")
    return value.strip()


def _fingerprint(event: dict) -> str:
    semantic = {
        "project": event["project"],
        "framework_ref": event["framework_ref"],
        "workflow": event["workflow"],
        "risk": event["risk"],
        "terminal_state": event["terminal_state"],
        "outcome_class": event["outcome_class"],
        "material": event["material"],
        "rework_cycles": event["rework_cycles"],
        "verification_failures": event["verification_failures"],
        "verification_escape": event["verification_escape"],
        "framework_feedback_created": event["framework_feedback_created"],
        "manual_workaround": event["manual_workaround"],
        "context_gap": event["context_gap"],
        "unexpected_scope_growth": event["unexpected_scope_growth"],
        "security_or_data_critical_event": event["security_or_data_critical_event"],
        "duration_class": event["duration_class"],
        "feedback_ids": event.get("feedback_ids", []),
        "feedback_fingerprints": event.get("feedback_fingerprints", []),
        "tags": event.get("tags", []),
    }
    # V1 fingerprints are a frozen wire contract. Adding absent V2 fields would
    # invalidate historical evidence produced by the Stable V1 implementation.
    if event.get("schema_version") == 2:
        semantic.update({
            "task_group": event.get("task_group", ""),
            "failure_stage": event.get("failure_stage", "unknown"),
            "failure_subject": event.get("failure_subject", ""),
            "signal_assessment": event.get("signal_assessment", {}),
        })
    canonical = json.dumps(semantic, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _occurrence(event: dict) -> str:
    return event.get("occurrence_id") or event["task_id"]


def _event_digest(events: list[dict]) -> str:
    members = sorted(
        ({"occurrence_id": _occurrence(event), "fingerprint": event["fingerprint"]} for event in events),
        key=lambda item: item["occurrence_id"],
    )
    canonical = json.dumps(members, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@contextmanager
def _lock(directory: Path, timeout_seconds: float = 5.0):
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = directory / ".learning.lock"
    deadline = time.monotonic() + timeout_seconds
    fd = None
    while fd is None:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(fd, f"pid={os.getpid()}\n".encode("utf-8"))
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise LearningError(f"learning ledger is busy: {lock_path}")
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
        raise LearningError(f"invalid JSON at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LearningError(f"record at {path} is not an object")
    return value


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
            raise LearningError(f"invalid JSONL at {path}:{number}: {exc}") from exc
        if not isinstance(item, dict):
            raise LearningError(f"JSONL record at {path}:{number} is not an object")
        values.append(item)
    return values


def _write_jsonl(path: Path, values: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in values),
        encoding="utf-8",
    )
    os.replace(temp, path)


def _write_immutable_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = _read_json(path)
        if existing == value:
            return
        raise LearningError(f"immutable record already exists with different content: {path}")
    temp = path.with_name(path.name + f".{uuid4().hex}.tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if path.exists():
        temp.unlink(missing_ok=True)
        raise LearningError(f"immutable record already exists: {path}")
    os.replace(temp, path)


def _paths(target: Path) -> dict[str, Path]:
    if not target.exists() or not target.is_dir():
        raise LearningError(f"target project does not exist or is not a directory: {target}")
    erei = target / ".erei"
    if not (erei / "framework.json").exists():
        raise LearningError("target is not an EREI-integrated project: missing .erei/framework.json")
    root = erei / "learning"
    return {
        "root": root,
        "event_dir": root / "events",
        "review_dir": root / "reviews",
        "events": root / "TASK_EVENTS.jsonl",
        "reviews": root / "LEARNING_REVIEWS.jsonl",
        "state": root / "LEARNING_STATE.json",
        "summary": root / "LEARNING_SUMMARY.md",
    }


def _ledger_generation(paths: dict[str, Path]) -> str:
    """Hash the complete read-only learning-ledger surface to detect concurrent changes."""
    digest = hashlib.sha256()

    def add_file(label: str, path: Path) -> None:
        digest.update(label.encode("utf-8"))
        digest.update(b"\0")
        try:
            data = path.read_bytes()
        except FileNotFoundError:
            digest.update(b"<missing>")
        else:
            digest.update(data)
        digest.update(b"\0")

    add_file("events-projection", paths["events"])
    add_file("reviews-projection", paths["reviews"])

    for label, directory in (("event", paths["event_dir"]), ("review", paths["review_dir"])):
        digest.update(label.encode("utf-8"))
        digest.update(b"\0")
        if not directory.exists():
            digest.update(b"<missing-dir>\0")
            continue
        for path in sorted(directory.glob("*.json")):
            digest.update(path.name.encode("utf-8"))
            digest.update(b"\0")
            try:
                digest.update(path.read_bytes())
            except FileNotFoundError:
                # A concurrent filesystem change will also change the post-read generation.
                digest.update(b"<changed-during-read>")
            digest.update(b"\0")

    return digest.hexdigest()


def validate_event(event: dict) -> None:
    try:
        validate_task_event_shape(event)
    except ContractValidationError as exc:
        raise LearningError(str(exc)) from exc
    if event["fingerprint"] != _fingerprint(event):
        raise LearningError(f"task event fingerprint mismatch: {event.get('task_id', 'UNKNOWN')}")


def _deduplicate_records(records: list[dict], key_fn, label: str, *, preserve_order: bool = False) -> list[dict]:
    result: dict[str, dict] = {}
    for item in records:
        key = key_fn(item)
        if key in result and result[key] != item:
            raise LearningError(f"conflicting duplicate {label}: {key}")
        result[key] = item
    return list(result.values()) if preserve_order else sorted(result.values(), key=key_fn)


def _immutable_records(directory: Path, key_fn, label: str) -> list[dict]:
    if not directory.exists():
        return []
    records: list[dict] = []
    for path in sorted(directory.glob("*.json")):
        value = _read_json(path)
        key = key_fn(value)
        if not isinstance(key, str) or not key:
            raise LearningError(f"immutable {label} has no valid identity: {path}")
        if path.stem != key:
            raise LearningError(f"immutable {label} filename does not match identity: {path.name} != {key}.json")
        records.append(value)
    return _deduplicate_records(records, key_fn, f"immutable {label} identity")


def _merge_legacy_projection_with_immutable(
    projection: list[dict],
    immutable: list[dict],
    *,
    key_fn,
    label: str,
    preserve_projection_order: bool = False,
) -> list[dict]:
    immutable_by_key = {key_fn(item): item for item in immutable}
    legacy: list[dict] = []
    projected_keys: set[str] = set()
    for item in projection:
        version = item.get("schema_version")
        if type(version) is not int:
            raise LearningError(f"{label} schema_version must be an integer")
        if preserve_projection_order:
            key = key_fn(item)
            if key in projected_keys:
                raise LearningError(f"duplicate {label} projection identity: {key}")
            projected_keys.add(key)
        if version == 1:
            legacy.append(item)
            continue
        if version == 2:
            key = key_fn(item)
            authoritative = immutable_by_key.get(key)
            if authoritative is None:
                raise LearningError(
                    f"V2 {label} exists only in rebuildable projection without immutable authority: {key}"
                )
            if authoritative != item:
                raise LearningError(f"V2 {label} projection does not match immutable authority: {key}")
            if preserve_projection_order:
                legacy.append(authoritative)
            continue
        # Preserve unsupported projection records so strict schema validation reports the real contract error.
        legacy.append(item)
    return _deduplicate_records(
        legacy + immutable, key_fn, f"{label} identity", preserve_order=preserve_projection_order
    )


def _load_events(paths: dict[str, Path], *, admitted_new_occurrence: str | None = None) -> list[dict]:
    projection = _read_jsonl(paths["events"])
    immutable = _immutable_records(paths["event_dir"], _occurrence, "event")
    immutable_only = {_occurrence(item) for item in immutable} - {_occurrence(item) for item in projection}
    # A V1 cutoff binds positions, which cannot be recovered by sorting or
    # appending missing rows. Only capture may admit its one just-written event,
    # after validating the complete prior snapshot under the same lock.
    ambiguous = immutable_only - ({admitted_new_occurrence} if admitted_new_occurrence else set())
    if ambiguous and any(review["schema_version"] == 1 for review in _load_reviews(paths)):
        raise LearningError(
            "legacy review membership cannot be proven for immutable-only events; "
            "original projection recovery required: " + ", ".join(sorted(ambiguous))
        )
    events = _merge_legacy_projection_with_immutable(
        projection,
        immutable,
        key_fn=_occurrence,
        label="event",
        # Legacy review cutoffs address append positions, not lexicographic IDs.
        # Keep known positions; missing legacy positions are rejected above.
        preserve_projection_order=True,
    )
    seen_task_ids: dict[str, str] = {}
    for event in events:
        validate_event(event)
        task_id = event["task_id"]
        occurrence = _occurrence(event)
        if task_id in seen_task_ids and seen_task_ids[task_id] != occurrence:
            raise LearningError(f"duplicate task_id across occurrences: {task_id}")
        seen_task_ids[task_id] = occurrence
    return events


def _review_identity(review: dict) -> str:
    value = review.get("review_id")
    return value if isinstance(value, str) else ""


def _load_reviews(paths: dict[str, Path]) -> list[dict]:
    projection = _read_jsonl(paths["reviews"])
    immutable = _immutable_records(paths["review_dir"], _review_identity, "review")
    reviews = _merge_legacy_projection_with_immutable(
        projection,
        immutable,
        key_fn=_review_identity,
        label="review",
    )
    try:
        for review in reviews:
            validate_learning_review_shape(review)
    except ContractValidationError as exc:
        raise LearningError(str(exc)) from exc
    return reviews


def _is_measured(event: dict, signal: str) -> bool:
    if event.get("schema_version") == 1:
        return True
    return event.get("signal_assessment", {}).get(signal) == "measured"


def _cohorts(events: list[dict]) -> dict:
    by_risk: dict[str, dict[str, int]] = defaultdict(lambda: {"tasks": 0, "material_tasks": 0})
    by_workflow: dict[str, dict[str, int]] = defaultdict(lambda: {"tasks": 0, "material_tasks": 0})
    for event in events:
        for bucket in (by_risk[event["risk"]], by_workflow[event["workflow"]]):
            bucket["tasks"] += 1
            bucket["material_tasks"] += int(event["material"])
    return {
        "by_risk": {key: by_risk[key] for key in sorted(by_risk)},
        "by_workflow": {key: by_workflow[key] for key in sorted(by_workflow)},
    }


def _metrics(events: list[dict]) -> dict:
    material = [event for event in events if event["material"]]
    rework_assessed = [event for event in material if _is_measured(event, "rework_cycles")]
    verification_assessed = [event for event in material if _is_measured(event, "verification_failures")]
    feedback_counts = Counter(
        fingerprint
        for event in events
        for fingerprint in event.get("feedback_fingerprints", [])
    )
    unassessed_signal_values = sum(
        1
        for event in events
        for signal in SIGNAL_KEYS
        if not _is_measured(event, signal)
    )
    failure_stages = Counter(event.get("failure_stage", "unknown") for event in events if event["verification_failures"] > 0)
    failure_subjects = Counter(event.get("failure_subject", "unknown") for event in events if event["verification_failures"] > 0)
    return {
        "tasks": len(events),
        "material_tasks": len(material),
        "verified_successes": sum(event["outcome_class"] == "verified_success" for event in events),
        "blocked_tasks": sum(event["outcome_class"] == "blocked" for event in events),
        "failed_tasks": sum(event["outcome_class"] == "failed" for event in events),
        "rework_assessed_material_tasks": len(rework_assessed),
        "verification_assessed_material_tasks": len(verification_assessed),
        "unassessed_signal_values": unassessed_signal_values,
        "rework_tasks": sum(event["rework_cycles"] > 0 for event in rework_assessed),
        "total_rework_cycles": sum(event["rework_cycles"] for event in rework_assessed),
        "verification_failure_tasks": sum(event["verification_failures"] > 0 for event in verification_assessed),
        "verification_failures": sum(event["verification_failures"] for event in verification_assessed),
        "verification_escapes": sum(event["verification_escape"] for event in events if _is_measured(event, "verification_escape")),
        "framework_feedback_tasks": sum(event["framework_feedback_created"] for event in events if _is_measured(event, "framework_feedback_created")),
        "manual_workarounds": sum(event["manual_workaround"] for event in events if _is_measured(event, "manual_workaround")),
        "context_gaps": sum(event["context_gap"] for event in events if _is_measured(event, "context_gap")),
        "unexpected_scope_growth_tasks": sum(event["unexpected_scope_growth"] for event in events if _is_measured(event, "unexpected_scope_growth")),
        "security_or_data_critical_events": sum(event["security_or_data_critical_event"] for event in events if _is_measured(event, "security_or_data_critical_event")),
        "max_feedback_fingerprint_occurrences": max(feedback_counts.values(), default=0),
        "rework_rate": round(sum(event["rework_cycles"] > 0 for event in rework_assessed) / len(rework_assessed), 4) if rework_assessed else None,
        "verification_failure_rate": round(sum(event["verification_failures"] > 0 for event in verification_assessed) / len(verification_assessed), 4) if verification_assessed else None,
        "failure_stages": dict(sorted(failure_stages.items())),
        "failure_subjects": dict(sorted(failure_subjects.items())),
        "cohorts": _cohorts(events),
    }


def _trigger(metrics: dict) -> dict:
    reasons: list[str] = []
    if metrics["tasks"] == 0 or (
        metrics["material_tasks"] > 0
        and metrics["rework_assessed_material_tasks"] == 0
        and metrics["verification_assessed_material_tasks"] == 0
    ):
        level = "INSUFFICIENT_EVIDENCE"
        reasons.append("no_measured_learning_evidence")
    else:
        level = "LEARNING_HEALTHY"

    def raise_to(candidate: str, reason: str) -> None:
        nonlocal level
        if TRIGGER_LEVELS[candidate] > TRIGGER_LEVELS[level]:
            level = candidate
        reasons.append(reason)

    if metrics["security_or_data_critical_events"] > 0:
        raise_to("IMMEDIATE_REVIEW", "security_or_data_critical_event_observed")
    if metrics["verification_escapes"] > 0:
        raise_to("IMMEDIATE_REVIEW", "verification_escape_observed")
    if metrics["material_tasks"] >= 40:
        raise_to("REVIEW_DUE", "40_material_tasks_since_last_review")
    if metrics["max_feedback_fingerprint_occurrences"] >= 3:
        raise_to("REVIEW_DUE", "same_framework_feedback_pattern_seen_3_times")
    if metrics["framework_feedback_tasks"] >= 5:
        raise_to("REVIEW_DUE", "5_framework_feedback_tasks_since_last_review")
    if metrics["material_tasks"] >= 20:
        raise_to("REVIEW_RECOMMENDED", "20_material_tasks_since_last_review")
    if (
        metrics["rework_assessed_material_tasks"] >= 8
        and metrics["rework_rate"] is not None
        and metrics["rework_rate"] >= 0.25
    ):
        raise_to("REVIEW_RECOMMENDED", "rework_rate_at_or_above_25_percent")
    if (
        metrics["verification_assessed_material_tasks"] >= 8
        and metrics["verification_failure_rate"] is not None
        and metrics["verification_failure_rate"] >= 0.15
    ):
        raise_to("REVIEW_RECOMMENDED", "verification_failure_rate_at_or_above_15_percent")
    if metrics["manual_workarounds"] >= 3:
        raise_to("REVIEW_RECOMMENDED", "3_manual_workarounds_since_last_review")
    if metrics["context_gaps"] >= 3:
        raise_to("REVIEW_RECOMMENDED", "3_context_gaps_since_last_review")
    if metrics["material_tasks"] >= 10:
        raise_to("LEARNING_WATCH", "10_material_tasks_since_last_review")
    if metrics["framework_feedback_tasks"] >= 2:
        raise_to("LEARNING_WATCH", "2_framework_feedback_tasks_since_last_review")
    return {"level": level, "reasons": list(dict.fromkeys(reasons))}


def _reviewed_occurrences(events: list[dict], reviews: list[dict]) -> tuple[set[str], int]:
    by_occurrence = {_occurrence(event): event for event in events}
    reviewed: set[str] = set()
    legacy_cutoff = 0
    for index, review in enumerate(reviews, start=1):
        expected_epoch = f"EPOCH-{index:03d}"
        if review["epoch_id"] != expected_epoch:
            raise LearningError("learning review epoch sequence mismatch")
        if review["schema_version"] == 1:
            cutoff = review["through_event_count"]
            if cutoff < legacy_cutoff or cutoff > len(events):
                raise LearningError("invalid legacy learning review cutoff")
            selected = events[legacy_cutoff:cutoff]
            # A V1 positional cutoff must not re-close occurrences explicitly
            # reviewed by an earlier V2 review in a mixed review history.
            overlap = sorted({_occurrence(event) for event in selected} & reviewed)
            if overlap:
                raise LearningError("review re-closes occurrences: " + ", ".join(overlap))
            # A past V1 cutoff cannot close an occurrence recorded after
            # the review itself. This catches a common pre-sorted projection
            # failure even when all row fingerprints and immutable files match.
            closure = datetime.fromisoformat(review["closed_at"].replace("Z", "+00:00"))
            future = sorted(
                _occurrence(event) for event in selected
                if datetime.fromisoformat(event["recorded_at"].replace("Z", "+00:00")) > closure
            )
            if future:
                raise LearningError("legacy review covers event recorded after closure: " + ", ".join(future))
            legacy_cutoff = cutoff
        else:
            ids = review["reviewed_occurrence_ids"]
            missing = sorted(set(ids) - set(by_occurrence))
            overlap = sorted(set(ids) & reviewed)
            if missing:
                raise LearningError("review references missing occurrences: " + ", ".join(missing))
            if overlap:
                raise LearningError("review re-closes occurrences: " + ", ".join(overlap))
            selected = [by_occurrence[item] for item in ids]
            if review["event_digest"] != _event_digest(selected):
                raise LearningError("learning review event digest mismatch")
            expected_metrics = _metrics(selected)
            expected_trigger = _trigger(expected_metrics)
            if review["metrics"] != expected_metrics:
                raise LearningError("learning review metrics do not match reviewed events")
            if review["trigger"] != expected_trigger:
                raise LearningError("learning review trigger does not match reviewed events")
        reviewed.update(_occurrence(event) for event in selected)
    return reviewed, legacy_cutoff


def derive_state(events: list[dict], reviews: list[dict], now: datetime | None = None) -> dict:
    for event in events:
        validate_event(event)
    try:
        for review in reviews:
            validate_learning_review_shape(review)
    except ContractValidationError as exc:
        raise LearningError(str(exc)) from exc
    reviewed, legacy_cutoff = _reviewed_occurrences(events, reviews)
    current = [event for event in events if _occurrence(event) not in reviewed]
    metrics = _metrics(current)
    return {
        "schema_version": 2,
        "epoch_id": f"EPOCH-{len(reviews) + 1:03d}",
        "updated_at": _timestamp(now or _utc_now()),
        "last_review_id": reviews[-1].get("review_id") if reviews else None,
        "last_review_at": reviews[-1].get("closed_at") if reviews else None,
        "legacy_event_cutoff": legacy_cutoff,
        "reviewed_occurrence_count": len(reviewed),
        "total_events": len(events),
        "metrics_since_last_review": metrics,
        "trigger": _trigger(metrics),
    }


def _format_rate(value) -> str:
    return "unknown" if value is None else f"{value:.1%}"


def _render_summary(state: dict) -> str:
    metrics = state["metrics_since_last_review"]
    trigger = state["trigger"]
    lines = [
        "# Task Learning Summary",
        "",
        f"- Epoch: `{state['epoch_id']}`",
        f"- Trigger: **{trigger['level']}**",
        f"- Tasks since last review: **{metrics['tasks']}**",
        f"- Material tasks: **{metrics['material_tasks']}**",
        f"- Rework assessment coverage: **{metrics['rework_assessed_material_tasks']}/{metrics['material_tasks']}**",
        f"- Verification assessment coverage: **{metrics['verification_assessed_material_tasks']}/{metrics['material_tasks']}**",
        f"- Rework rate: **{_format_rate(metrics['rework_rate'])}**",
        f"- Verification-failure rate: **{_format_rate(metrics['verification_failure_rate'])}**",
        f"- Verification escapes: **{metrics['verification_escapes']}**",
        f"- Framework-feedback tasks: **{metrics['framework_feedback_tasks']}**",
        f"- Unassessed signal values: **{metrics['unassessed_signal_values']}**",
        "",
        "## Review trigger reasons",
        "",
    ]
    lines += [f"- `{reason}`" for reason in trigger["reasons"]] if trigger["reasons"] else ["- None."]
    lines += [
        "",
        "V2 event/review JSON files are immutable authority. Legacy positional reviews also require the original complete event projection.",
        "Task Learning never authorizes Framework self-modification.",
        "",
    ]
    return "\n".join(lines)


def _persist_projections(paths: dict[str, Path], events: list[dict], reviews: list[dict], state: dict) -> None:
    paths["root"].mkdir(parents=True, exist_ok=True)
    _write_jsonl(paths["events"], events)
    _write_jsonl(paths["reviews"], reviews)
    temp_state = paths["state"].with_suffix(".json.tmp")
    temp_summary = paths["summary"].with_suffix(".md.tmp")
    temp_state.write_text(json.dumps(state, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    temp_summary.write_text(_render_summary(state), encoding="utf-8")
    os.replace(temp_state, paths["state"])
    os.replace(temp_summary, paths["summary"])


def _assessment(value) -> tuple[object, str]:
    return (value, "measured") if value is not None else (None, "not_assessed")


def build_event(args: argparse.Namespace, now: datetime | None = None) -> dict:
    current = now or _utc_now()
    feedback_ids = sorted({item.strip() for item in getattr(args, "feedback_id", []) if item.strip()})
    feedback_fingerprints = sorted({item.strip() for item in getattr(args, "feedback_fingerprint", []) if item.strip()})
    tags = sorted({item.strip() for item in getattr(args, "tag", []) if item.strip()})

    rework_value, rework_assessment = _assessment(getattr(args, "rework_cycles", None))
    verification_value, verification_assessment = _assessment(getattr(args, "verification_failures", None))
    bool_values: dict[str, bool] = {}
    assessment = {
        "rework_cycles": rework_assessment,
        "verification_failures": verification_assessment,
    }
    for key in SIGNAL_KEYS[2:]:
        raw = getattr(args, key, None)
        bool_values[key] = bool(raw) if raw is not None else False
        assessment[key] = "measured" if raw is not None else "not_assessed"
    if feedback_ids or feedback_fingerprints:
        bool_values["framework_feedback_created"] = True
        assessment["framework_feedback_created"] = "measured"

    rework_cycles = 0 if rework_value is None else rework_value
    verification_failures = 0 if verification_value is None else verification_value
    failure_stage = getattr(args, "failure_stage", None)
    if failure_stage is None:
        failure_stage = "unknown" if verification_failures > 0 else "none"

    event = {
        "schema_version": 2,
        "task_id": args.task_id.strip() if getattr(args, "task_id", None) else _event_id(current),
        "occurrence_id": args.occurrence_id.strip() if getattr(args, "occurrence_id", None) else _occurrence_id(current),
        "recorded_at": _timestamp(current),
        "project": {"repository": _nonempty(args.project_repository, "project repository")},
        "framework_ref": _nonempty(args.framework_ref, "framework ref"),
        "workflow": _nonempty(args.workflow, "workflow"),
        "risk": args.risk,
        "terminal_state": _nonempty(args.terminal_state, "terminal state"),
        "outcome_class": args.outcome_class,
        "material": args.material,
        "rework_cycles": rework_cycles,
        "verification_failures": verification_failures,
        "verification_escape": bool_values["verification_escape"],
        "framework_feedback_created": bool_values["framework_feedback_created"],
        "manual_workaround": bool_values["manual_workaround"],
        "context_gap": bool_values["context_gap"],
        "unexpected_scope_growth": bool_values["unexpected_scope_growth"],
        "security_or_data_critical_event": bool_values["security_or_data_critical_event"],
        "duration_class": args.duration_class,
        "signal_assessment": assessment,
        "failure_stage": failure_stage,
    }
    if getattr(args, "project_name", None) and args.project_name.strip():
        event["project"]["name"] = args.project_name.strip()
    if getattr(args, "task_group", None) and args.task_group.strip():
        event["task_group"] = args.task_group.strip()
    if getattr(args, "failure_subject", None) and args.failure_subject.strip():
        event["failure_subject"] = args.failure_subject.strip()
    if feedback_ids:
        event["feedback_ids"] = feedback_ids
    if feedback_fingerprints:
        event["feedback_fingerprints"] = feedback_fingerprints
    if tags:
        event["tags"] = tags
    event["fingerprint"] = _fingerprint(event)
    validate_event(event)
    return event


def capture(target: Path, event: dict) -> tuple[dict, bool]:
    paths = _paths(target)
    validate_event(event)
    with _lock(paths["root"]):
        events = _load_events(paths)
        reviews = _load_reviews(paths)
        current_state = derive_state(events, reviews)
        occurrence = _occurrence(event)
        existing = next((item for item in events if _occurrence(item) == occurrence), None)
        if existing is not None:
            if existing["fingerprint"] != event["fingerprint"]:
                raise LearningError(f"occurrence_id already exists with conflicting semantics: {occurrence}")
            _persist_projections(paths, events, reviews, current_state)
            return current_state, True
        if any(item["task_id"] == event["task_id"] for item in events):
            raise LearningError(f"task_id already exists under another occurrence: {event['task_id']}")
        candidate_events = events + [event]
        state = derive_state(candidate_events, reviews)
        _write_immutable_json(paths["event_dir"] / f"{occurrence}.json", event)
        persisted_events = _load_events(paths, admitted_new_occurrence=occurrence)
        state = derive_state(persisted_events, reviews)
        _persist_projections(paths, persisted_events, reviews, state)
    return state, False


def authoritative_snapshot(target: Path, max_attempts: int = 4) -> dict:
    """Read a stable authoritative learning snapshot without mutating the project."""
    if type(max_attempts) is not int or max_attempts < 1:
        raise LearningError("max_attempts must be a positive integer")
    paths = _paths(target)
    last_error: LearningError | None = None

    for _ in range(max_attempts):
        before = _ledger_generation(paths)
        try:
            events = _load_events(paths)
            reviews = _load_reviews(paths)
            state = derive_state(events, reviews)
        except LearningError as exc:
            last_error = exc
            after_error = _ledger_generation(paths)
            if after_error != before:
                continue
            raise

        after = _ledger_generation(paths)
        if after == before:
            return {
                "events": events,
                "reviews": reviews,
                "state": state,
                "generation": after,
            }

    message = "learning ledgers changed during read-only snapshot"
    if last_error is not None:
        message += f": {last_error}"
    raise LearningError(message)

def status(target: Path) -> dict:
    paths = _paths(target)
    with _lock(paths["root"]):
        events = _load_events(paths)
        reviews = _load_reviews(paths)
        state = derive_state(events, reviews)
        _persist_projections(paths, events, reviews, state)
    return state


def close_review(target: Path, args: argparse.Namespace, now: datetime | None = None) -> tuple[dict, dict]:
    paths = _paths(target)
    current = now or _utc_now()
    with _lock(paths["root"]):
        events = _load_events(paths)
        reviews = _load_reviews(paths)
        before = derive_state(events, reviews, current)
        reviewed, _ = _reviewed_occurrences(events, reviews)
        current_events = [event for event in events if _occurrence(event) not in reviewed]
        if not current_events:
            raise LearningError("cannot close an empty learning epoch")
        evidence = sorted({_nonempty(item, "review evidence") for item in args.evidence})
        review = {
            "schema_version": 2,
            "review_id": args.review_id.strip() if args.review_id else _review_id(current),
            "closed_at": _timestamp(current),
            "epoch_id": before["epoch_id"],
            "reviewed_occurrence_ids": sorted(_occurrence(event) for event in current_events),
            "event_digest": _event_digest(current_events),
            "trigger": before["trigger"],
            "metrics": before["metrics_since_last_review"],
            "findings": _nonempty(args.findings, "review findings"),
            "decision": _nonempty(args.decision, "review decision"),
            "evidence": evidence,
        }
        actions = sorted({item.strip() for item in args.action if item.strip()})
        if actions:
            review["actions"] = actions
        try:
            validate_learning_review_shape(review)
        except ContractValidationError as exc:
            raise LearningError(str(exc)) from exc
        candidate_reviews = reviews + [review]
        after = derive_state(events, candidate_reviews, current)
        _write_immutable_json(paths["review_dir"] / f"{review['review_id']}.json", review)
        persisted_reviews = _load_reviews(paths)
        after = derive_state(events, persisted_reviews, current)
        _persist_projections(paths, events, persisted_reviews, after)
    return review, after


def validate_ledgers(target: Path) -> dict:
    snapshot = authoritative_snapshot(target)
    events = snapshot["events"]
    reviews = snapshot["reviews"]
    state = snapshot["state"]
    return {
        "valid": True,
        "events": len(events),
        "reviews": len(reviews),
        "epoch_id": state["epoch_id"],
        "trigger": state["trigger"],
        "generation": snapshot["generation"],
    }


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EREI project-local Task Learning V2 and review trigger.")
    sub = parser.add_subparsers(dest="command", required=True)

    capture_cmd = sub.add_parser("capture")
    capture_cmd.add_argument("--target", required=True)
    capture_cmd.add_argument("--project-repository", required=True)
    capture_cmd.add_argument("--project-name")
    capture_cmd.add_argument("--framework-ref", required=True)
    capture_cmd.add_argument("--task-id")
    capture_cmd.add_argument("--occurrence-id")
    capture_cmd.add_argument("--task-group")
    capture_cmd.add_argument("--workflow", required=True)
    capture_cmd.add_argument("--risk", required=True, choices=sorted(RISK_LEVELS))
    capture_cmd.add_argument("--terminal-state", required=True)
    capture_cmd.add_argument("--outcome-class", required=True, choices=sorted(OUTCOME_CLASSES))
    capture_cmd.add_argument("--material", action=argparse.BooleanOptionalAction, default=True)
    capture_cmd.add_argument("--rework-cycles", type=int, default=None)
    capture_cmd.add_argument("--verification-failures", type=int, default=None)
    capture_cmd.add_argument("--verification-escape", action=argparse.BooleanOptionalAction, default=None)
    capture_cmd.add_argument("--framework-feedback-created", action=argparse.BooleanOptionalAction, default=None)
    capture_cmd.add_argument("--manual-workaround", action=argparse.BooleanOptionalAction, default=None)
    capture_cmd.add_argument("--context-gap", action=argparse.BooleanOptionalAction, default=None)
    capture_cmd.add_argument("--unexpected-scope-growth", action=argparse.BooleanOptionalAction, default=None)
    capture_cmd.add_argument("--security-or-data-critical-event", action=argparse.BooleanOptionalAction, default=None)
    capture_cmd.add_argument("--duration-class", choices=sorted(DURATION_CLASSES), default="unknown")
    capture_cmd.add_argument("--failure-stage", choices=("none", "pre_merge", "post_merge", "runtime", "unknown"))
    capture_cmd.add_argument("--failure-subject")
    capture_cmd.add_argument("--feedback-id", action="append", default=[])
    capture_cmd.add_argument("--feedback-fingerprint", action="append", default=[])
    capture_cmd.add_argument("--tag", action="append", default=[])

    for name in ["status", "validate"]:
        command = sub.add_parser(name)
        command.add_argument("--target", required=True)

    review_cmd = sub.add_parser("review-close")
    review_cmd.add_argument("--target", required=True)
    review_cmd.add_argument("--review-id")
    review_cmd.add_argument("--findings", required=True)
    review_cmd.add_argument("--decision", required=True)
    review_cmd.add_argument("--evidence", action="append", default=[], required=True)
    review_cmd.add_argument("--action", action="append", default=[])
    return parser.parse_args(argv)


def main(argv=None) -> int:
    try:
        args = parse_args(argv)
        target = Path(args.target).resolve()
        if args.command == "capture":
            event = build_event(args)
            state, idempotent = capture(target, event)
            payload = {
                "status": "already_captured" if idempotent else "captured",
                "task_id": event["task_id"],
                "occurrence_id": event["occurrence_id"],
                "epoch_id": state["epoch_id"],
                "review_trigger": state["trigger"],
                "total_events": state["total_events"],
            }
        elif args.command == "status":
            payload = status(target)
        elif args.command == "review-close":
            review, state = close_review(target, args)
            payload = {
                "status": "review_closed",
                "review_id": review["review_id"],
                "closed_epoch": review["epoch_id"],
                "next_epoch": state["epoch_id"],
                "review_trigger": state["trigger"],
            }
        else:
            payload = validate_ledgers(target)
    except (LearningError, ContractValidationError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
