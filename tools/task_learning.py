#!/usr/bin/env python3
"""Project-local task learning ledger and deterministic review trigger for EREI.

Uses only the Python standard library. Every engineering execution can emit one
structured event. The tool derives learning state from immutable event/review
ledgers and never modifies Framework Core or a project Framework pin.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

RISK_LEVELS = {"L0", "L1", "L2", "L3", "L4"}
OUTCOME_CLASSES = {"verified_success", "success_with_deferred", "blocked", "failed", "canceled"}
DURATION_CLASSES = {"short", "medium", "long", "unknown"}
TASK_ID_RE = re.compile(r"^ETASK-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
REVIEW_ID_RE = re.compile(r"^ELR-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
FEEDBACK_FP_RE = re.compile(r"^[a-f0-9]{64}$")
TRIGGER_LEVELS = {
    "LEARNING_HEALTHY": 0,
    "LEARNING_WATCH": 1,
    "REVIEW_RECOMMENDED": 2,
    "REVIEW_DUE": 3,
    "IMMEDIATE_REVIEW": 4,
}


class LearningError(RuntimeError):
    pass


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0)


def _timestamp(now):
    return now.isoformat().replace("+00:00", "Z")


def _event_id(now):
    return f"ETASK-{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8].upper()}"


def _review_id(now):
    return f"ELR-{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8].upper()}"


def _nonempty(value, label):
    value = value.strip()
    if not value:
        raise LearningError(f"{label} must not be empty")
    return value


def _fingerprint(event):
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
    canonical = json.dumps(semantic, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@contextmanager
def _lock(directory, timeout_seconds=5.0):
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


def _read_jsonl(path):
    if not path.exists():
        return []
    values = []
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


def _write_jsonl(path, values):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in values),
        encoding="utf-8",
    )
    os.replace(temp, path)


def _paths(target):
    if not target.exists() or not target.is_dir():
        raise LearningError(f"target project does not exist or is not a directory: {target}")
    erei = target / ".erei"
    if not (erei / "framework.json").exists():
        raise LearningError("target is not an EREI-integrated project: missing .erei/framework.json")
    root = erei / "learning"
    return {
        "root": root,
        "events": root / "TASK_EVENTS.jsonl",
        "reviews": root / "LEARNING_REVIEWS.jsonl",
        "state": root / "LEARNING_STATE.json",
        "summary": root / "LEARNING_SUMMARY.md",
    }


def validate_event(event):
    required = {
        "schema_version", "task_id", "recorded_at", "project", "framework_ref", "workflow",
        "risk", "terminal_state", "outcome_class", "material", "rework_cycles",
        "verification_failures", "verification_escape", "framework_feedback_created",
        "manual_workaround", "context_gap", "unexpected_scope_growth",
        "security_or_data_critical_event", "duration_class", "fingerprint",
    }
    missing = sorted(required - set(event))
    if missing:
        raise LearningError("task event missing fields: " + ", ".join(missing))
    if event["schema_version"] != 1:
        raise LearningError("unsupported task event schema_version")
    if not isinstance(event.get("task_id"), str) or not TASK_ID_RE.fullmatch(event["task_id"]):
        raise LearningError("invalid task_id")
    if not isinstance(event["project"], dict) or not str(event["project"].get("repository", "")).strip():
        raise LearningError("task event project.repository is required")
    if event["risk"] not in RISK_LEVELS:
        raise LearningError("invalid task risk")
    if event["outcome_class"] not in OUTCOME_CLASSES:
        raise LearningError("invalid outcome_class")
    if event["duration_class"] not in DURATION_CLASSES:
        raise LearningError("invalid duration_class")
    for key in [
        "material", "verification_escape", "framework_feedback_created", "manual_workaround",
        "context_gap", "unexpected_scope_growth", "security_or_data_critical_event",
    ]:
        if not isinstance(event[key], bool):
            raise LearningError(f"{key} must be boolean")
    for key in ["rework_cycles", "verification_failures"]:
        if not isinstance(event[key], int) or event[key] < 0:
            raise LearningError(f"{key} must be a non-negative integer")
    for fingerprint in event.get("feedback_fingerprints", []):
        if not isinstance(fingerprint, str) or not FEEDBACK_FP_RE.fullmatch(fingerprint):
            raise LearningError("invalid feedback fingerprint")
    if event["fingerprint"] != _fingerprint(event):
        raise LearningError(f"task event fingerprint mismatch: {event.get('task_id', 'UNKNOWN')}")


def validate_review(review, *, expected_epoch, previous_cutoff, total_events):
    required = {
        "schema_version", "review_id", "closed_at", "epoch_id", "through_event_count",
        "trigger", "metrics", "findings", "decision", "evidence",
    }
    missing = sorted(required - set(review))
    if missing:
        raise LearningError("learning review missing fields: " + ", ".join(missing))
    if review["schema_version"] != 1:
        raise LearningError("unsupported learning review schema_version")
    if not isinstance(review["review_id"], str) or not REVIEW_ID_RE.fullmatch(review["review_id"]):
        raise LearningError("invalid learning review_id")
    if review["epoch_id"] != expected_epoch:
        raise LearningError("learning review epoch sequence mismatch")
    cutoff = review["through_event_count"]
    if not isinstance(cutoff, int) or cutoff < previous_cutoff or cutoff > total_events:
        raise LearningError("invalid learning review cutoff")
    if not isinstance(review["trigger"], dict) or review["trigger"].get("level") not in TRIGGER_LEVELS:
        raise LearningError("invalid learning review trigger")
    if not isinstance(review["metrics"], dict):
        raise LearningError("learning review metrics must be an object")
    if not isinstance(review["findings"], str) or not review["findings"].strip():
        raise LearningError("learning review findings are required")
    if not isinstance(review["decision"], str) or not review["decision"].strip():
        raise LearningError("learning review decision is required")
    if (
        not isinstance(review["evidence"], list)
        or not review["evidence"]
        or any(not isinstance(item, str) or not item.strip() for item in review["evidence"])
    ):
        raise LearningError("learning review evidence is required")
    return cutoff


def _trigger(metrics):
    reasons = []
    level = "LEARNING_HEALTHY"

    def raise_to(candidate, reason):
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
    if metrics["material_tasks"] >= 8 and metrics["rework_rate"] >= 0.25:
        raise_to("REVIEW_RECOMMENDED", "rework_rate_at_or_above_25_percent")
    if metrics["material_tasks"] >= 8 and metrics["verification_failure_rate"] >= 0.15:
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


def derive_state(events, reviews, now=None):
    for event in events:
        validate_event(event)
    cutoff = 0
    for index, review in enumerate(reviews, start=1):
        cutoff = validate_review(
            review,
            expected_epoch=f"EPOCH-{index:03d}",
            previous_cutoff=cutoff,
            total_events=len(events),
        )
    current = events[cutoff:]
    material = [event for event in current if event["material"]]
    denominator = max(len(material), 1)
    feedback_counts = Counter(
        fingerprint
        for event in current
        for fingerprint in event.get("feedback_fingerprints", [])
        if isinstance(fingerprint, str) and fingerprint
    )
    metrics = {
        "tasks": len(current),
        "material_tasks": len(material),
        "verified_successes": sum(event["outcome_class"] == "verified_success" for event in current),
        "blocked_tasks": sum(event["outcome_class"] == "blocked" for event in current),
        "failed_tasks": sum(event["outcome_class"] == "failed" for event in current),
        "rework_tasks": sum(event["rework_cycles"] > 0 for event in material),
        "total_rework_cycles": sum(event["rework_cycles"] for event in material),
        "verification_failure_tasks": sum(event["verification_failures"] > 0 for event in material),
        "verification_failures": sum(event["verification_failures"] for event in material),
        "verification_escapes": sum(event["verification_escape"] for event in current),
        "framework_feedback_tasks": sum(event["framework_feedback_created"] for event in current),
        "manual_workarounds": sum(event["manual_workaround"] for event in current),
        "context_gaps": sum(event["context_gap"] for event in current),
        "unexpected_scope_growth_tasks": sum(event["unexpected_scope_growth"] for event in current),
        "security_or_data_critical_events": sum(event["security_or_data_critical_event"] for event in current),
        "max_feedback_fingerprint_occurrences": max(feedback_counts.values(), default=0),
        "rework_rate": round(
            sum(event["rework_cycles"] > 0 for event in material) / denominator, 4
        ) if material else 0.0,
        "verification_failure_rate": round(
            sum(event["verification_failures"] > 0 for event in material) / denominator, 4
        ) if material else 0.0,
    }
    return {
        "schema_version": 1,
        "epoch_id": f"EPOCH-{len(reviews) + 1:03d}",
        "updated_at": _timestamp(now or _utc_now()),
        "last_review_id": reviews[-1].get("review_id") if reviews else None,
        "last_review_at": reviews[-1].get("closed_at") if reviews else None,
        "event_cutoff": cutoff,
        "total_events": len(events),
        "metrics_since_last_review": metrics,
        "trigger": _trigger(metrics),
    }


def _render_summary(state):
    metrics = state["metrics_since_last_review"]
    trigger = state["trigger"]
    lines = [
        "# Task Learning Summary",
        "",
        f"- Epoch: `{state['epoch_id']}`",
        f"- Trigger: **{trigger['level']}**",
        f"- Tasks since last review: **{metrics['tasks']}**",
        f"- Material tasks: **{metrics['material_tasks']}**",
        f"- Framework-feedback tasks: **{metrics['framework_feedback_tasks']}**",
        f"- Rework rate: **{metrics['rework_rate']:.1%}**",
        f"- Verification-failure rate: **{metrics['verification_failure_rate']:.1%}**",
        f"- Verification escapes: **{metrics['verification_escapes']}**",
        f"- Manual workarounds: **{metrics['manual_workarounds']}**",
        f"- Context gaps: **{metrics['context_gaps']}**",
        f"- Critical security/data events: **{metrics['security_or_data_critical_events']}**",
        "",
        "## Review trigger reasons",
        "",
    ]
    lines += [f"- `{reason}`" for reason in trigger["reasons"]] if trigger["reasons"] else ["- None."]
    lines += [
        "",
        "Derived deterministically from project-local task events. It never authorizes Framework self-modification.",
        "",
    ]
    return "\n".join(lines)


def _persist(paths, state):
    paths["root"].mkdir(parents=True, exist_ok=True)
    temp_state = paths["state"].with_suffix(".json.tmp")
    temp_summary = paths["summary"].with_suffix(".md.tmp")
    temp_state.write_text(
        json.dumps(state, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    temp_summary.write_text(_render_summary(state), encoding="utf-8")
    os.replace(temp_state, paths["state"])
    os.replace(temp_summary, paths["summary"])


def build_event(args, now=None):
    current = now or _utc_now()
    event = {
        "schema_version": 1,
        "task_id": args.task_id.strip() if args.task_id else _event_id(current),
        "recorded_at": _timestamp(current),
        "project": {"repository": _nonempty(args.project_repository, "project repository")},
        "framework_ref": _nonempty(args.framework_ref, "framework ref"),
        "workflow": _nonempty(args.workflow, "workflow"),
        "risk": args.risk,
        "terminal_state": _nonempty(args.terminal_state, "terminal state"),
        "outcome_class": args.outcome_class,
        "material": args.material,
        "rework_cycles": args.rework_cycles,
        "verification_failures": args.verification_failures,
        "verification_escape": args.verification_escape,
        "framework_feedback_created": args.framework_feedback_created,
        "manual_workaround": args.manual_workaround,
        "context_gap": args.context_gap,
        "unexpected_scope_growth": args.unexpected_scope_growth,
        "security_or_data_critical_event": args.security_or_data_critical_event,
        "duration_class": args.duration_class,
    }
    if args.project_name and args.project_name.strip():
        event["project"]["name"] = args.project_name.strip()
    for key, values in [
        ("feedback_ids", args.feedback_id),
        ("feedback_fingerprints", args.feedback_fingerprint),
        ("tags", args.tag),
    ]:
        values = sorted({item.strip() for item in values if item.strip()})
        if values:
            event[key] = values
    event["fingerprint"] = _fingerprint(event)
    validate_event(event)
    return event


def capture(target, event):
    paths = _paths(target)
    with _lock(paths["root"]):
        events = _read_jsonl(paths["events"])
        reviews = _read_jsonl(paths["reviews"])
        events.append(event)
        _write_jsonl(paths["events"], events)
        state = derive_state(events, reviews)
        _persist(paths, state)
    return state


def status(target):
    paths = _paths(target)
    with _lock(paths["root"]):
        events = _read_jsonl(paths["events"])
        reviews = _read_jsonl(paths["reviews"])
        state = derive_state(events, reviews)
        _persist(paths, state)
    return state


def close_review(target, args, now=None):
    paths = _paths(target)
    current = now or _utc_now()
    with _lock(paths["root"]):
        events = _read_jsonl(paths["events"])
        reviews = _read_jsonl(paths["reviews"])
        before = derive_state(events, reviews, current)
        evidence = sorted({_nonempty(item, "review evidence") for item in args.evidence})
        if before["metrics_since_last_review"]["tasks"] == 0:
            raise LearningError("cannot close an empty learning epoch")
        if not evidence:
            raise LearningError("at least one review evidence reference is required")
        review = {
            "schema_version": 1,
            "review_id": args.review_id.strip() if args.review_id else _review_id(current),
            "closed_at": _timestamp(current),
            "epoch_id": before["epoch_id"],
            "through_event_count": len(events),
            "trigger": before["trigger"],
            "metrics": before["metrics_since_last_review"],
            "findings": _nonempty(args.findings, "review findings"),
            "decision": _nonempty(args.decision, "review decision"),
            "evidence": evidence,
        }
        if not REVIEW_ID_RE.fullmatch(review["review_id"]):
            raise LearningError("invalid learning review_id")
        actions = sorted({item.strip() for item in args.action if item.strip()})
        if actions:
            review["actions"] = actions
        reviews.append(review)
        _write_jsonl(paths["reviews"], reviews)
        after = derive_state(events, reviews, current)
        _persist(paths, after)
    return review, after


def validate_ledgers(target):
    paths = _paths(target)
    events = _read_jsonl(paths["events"])
    reviews = _read_jsonl(paths["reviews"])
    state = derive_state(events, reviews)
    return {
        "valid": True,
        "events": len(events),
        "reviews": len(reviews),
        "epoch_id": state["epoch_id"],
        "trigger": state["trigger"],
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="EREI project-local task learning and review trigger.")
    sub = parser.add_subparsers(dest="command", required=True)

    capture_cmd = sub.add_parser("capture")
    capture_cmd.add_argument("--target", required=True)
    capture_cmd.add_argument("--project-repository", required=True)
    capture_cmd.add_argument("--project-name")
    capture_cmd.add_argument("--framework-ref", required=True)
    capture_cmd.add_argument("--task-id")
    capture_cmd.add_argument("--workflow", required=True)
    capture_cmd.add_argument("--risk", required=True, choices=sorted(RISK_LEVELS))
    capture_cmd.add_argument("--terminal-state", required=True)
    capture_cmd.add_argument("--outcome-class", required=True, choices=sorted(OUTCOME_CLASSES))
    capture_cmd.add_argument("--material", action=argparse.BooleanOptionalAction, default=True)
    capture_cmd.add_argument("--rework-cycles", type=int, default=0)
    capture_cmd.add_argument("--verification-failures", type=int, default=0)
    capture_cmd.add_argument("--verification-escape", action="store_true")
    capture_cmd.add_argument("--framework-feedback-created", action="store_true")
    capture_cmd.add_argument("--manual-workaround", action="store_true")
    capture_cmd.add_argument("--context-gap", action="store_true")
    capture_cmd.add_argument("--unexpected-scope-growth", action="store_true")
    capture_cmd.add_argument("--security-or-data-critical-event", action="store_true")
    capture_cmd.add_argument("--duration-class", choices=sorted(DURATION_CLASSES), default="unknown")
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


def main(argv=None):
    try:
        args = parse_args(argv)
        target = Path(args.target).resolve()
        if args.command == "capture":
            event = build_event(args)
            state = capture(target, event)
            payload = {
                "status": "captured",
                "task_id": event["task_id"],
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
    except LearningError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
