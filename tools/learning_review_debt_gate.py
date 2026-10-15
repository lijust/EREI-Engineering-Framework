#!/usr/bin/env python3
"""Fail-closed bounded gate for unresolved IMMEDIATE_REVIEW learning debt."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


class ReviewDebtError(RuntimeError):
    pass


TRIGGER_LEVELS = {
    "INSUFFICIENT_EVIDENCE",
    "LEARNING_HEALTHY",
    "LEARNING_WATCH",
    "REVIEW_RECOMMENDED",
    "REVIEW_DUE",
    "IMMEDIATE_REVIEW",
}
EPOCH_ID_RE = __import__("re").compile(r"^EPOCH-[0-9]{3,}$")
RFC3339_RE = __import__("re").compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)
V1_METRICS = {
    "tasks", "material_tasks", "verified_successes", "blocked_tasks", "failed_tasks",
    "rework_tasks", "total_rework_cycles", "verification_failure_tasks",
    "verification_failures", "verification_escapes", "framework_feedback_tasks",
    "manual_workarounds", "context_gaps", "unexpected_scope_growth_tasks",
    "security_or_data_critical_events", "max_feedback_fingerprint_occurrences",
    "rework_rate", "verification_failure_rate",
}
V2_REQUIRED_METRICS = V1_METRICS | {
    "rework_assessed_material_tasks", "verification_assessed_material_tasks",
    "unassessed_signal_values", "failure_stages", "failure_subjects", "cohorts",
}


def _nonnegative_int(value, label: str) -> None:
    if type(value) is not int or value < 0:
        raise ReviewDebtError(f"{label} must be a non-negative integer")


def _rate(value, label: str, *, nullable: bool) -> None:
    if value is None and nullable:
        return
    if type(value) not in {int, float} or not 0 <= value <= 1:
        raise ReviewDebtError(f"{label} must be a number between 0 and 1" + (" or null" if nullable else ""))


def _optional_text(value, label: str) -> None:
    if value is not None and (not isinstance(value, str) or not value.strip()):
        raise ReviewDebtError(f"{label} must be null or a non-empty string")


def _validate_state(state: dict) -> None:
    if not isinstance(state, dict):
        raise ReviewDebtError("learning state must be an object")
    version = state.get("schema_version")
    if type(version) is not int:
        raise ReviewDebtError("learning state schema_version must be an integer")
    if version == 1:
        required = {
            "schema_version", "epoch_id", "updated_at", "last_review_id", "last_review_at",
            "event_cutoff", "total_events", "metrics_since_last_review", "trigger",
        }
        allowed = required
    elif version == 2:
        required = {
            "schema_version", "epoch_id", "updated_at", "last_review_id", "last_review_at",
            "legacy_event_cutoff", "reviewed_occurrence_count", "total_events",
            "metrics_since_last_review", "trigger",
        }
        allowed = required
    else:
        raise ReviewDebtError("learning state schema_version must be 1 or 2")
    missing = sorted(required - set(state))
    unknown = sorted(set(state) - allowed)
    if missing:
        raise ReviewDebtError("learning state missing fields: " + ", ".join(missing))
    if unknown:
        raise ReviewDebtError("learning state unknown fields: " + ", ".join(unknown))
    if not isinstance(state["epoch_id"], str) or not EPOCH_ID_RE.fullmatch(state["epoch_id"]):
        raise ReviewDebtError("learning state epoch_id is invalid")
    _parse_time(state["updated_at"])
    _optional_text(state["last_review_id"], "last_review_id")
    if state["last_review_at"] is not None:
        _parse_time(state["last_review_at"])
    if version == 1:
        _nonnegative_int(state["event_cutoff"], "event_cutoff")
    else:
        _nonnegative_int(state["legacy_event_cutoff"], "legacy_event_cutoff")
        _nonnegative_int(state["reviewed_occurrence_count"], "reviewed_occurrence_count")
    _nonnegative_int(state["total_events"], "total_events")

    metrics = state["metrics_since_last_review"]
    if not isinstance(metrics, dict):
        raise ReviewDebtError("learning state metrics_since_last_review must be an object")
    required_metrics = V1_METRICS if version == 1 else V2_REQUIRED_METRICS
    missing_metrics = sorted(required_metrics - set(metrics))
    if missing_metrics:
        raise ReviewDebtError("learning state metrics missing fields: " + ", ".join(missing_metrics))
    if version == 1:
        unknown_metrics = sorted(set(metrics) - V1_METRICS)
        if unknown_metrics:
            raise ReviewDebtError("learning state metrics unknown fields: " + ", ".join(unknown_metrics))
    integer_metrics = required_metrics - {
        "rework_rate", "verification_failure_rate", "failure_stages", "failure_subjects", "cohorts",
    }
    for key in integer_metrics:
        _nonnegative_int(metrics[key], f"metrics_since_last_review.{key}")
    _rate(metrics["rework_rate"], "metrics_since_last_review.rework_rate", nullable=version == 2)
    _rate(metrics["verification_failure_rate"], "metrics_since_last_review.verification_failure_rate", nullable=version == 2)
    if version == 2:
        for key in ("failure_stages", "failure_subjects", "cohorts"):
            if not isinstance(metrics[key], dict):
                raise ReviewDebtError(f"metrics_since_last_review.{key} must be an object")

    trigger = state["trigger"]
    if not isinstance(trigger, dict) or set(trigger) != {"level", "reasons"}:
        raise ReviewDebtError("learning state trigger must contain exactly level and reasons")
    allowed_levels = set(TRIGGER_LEVELS)
    if version == 1:
        allowed_levels.discard("INSUFFICIENT_EVIDENCE")
    if trigger.get("level") not in allowed_levels:
        raise ReviewDebtError("learning state trigger.level is missing or invalid")
    reasons = trigger.get("reasons")
    if not isinstance(reasons, list) or any(not isinstance(item, str) or not item.strip() for item in reasons):
        raise ReviewDebtError("learning state trigger.reasons must be an array of non-empty strings")
    if len(reasons) != len(set(reasons)):
        raise ReviewDebtError("learning state trigger.reasons must be unique")


def _read(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReviewDebtError(f"cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReviewDebtError(f"{path} must contain a JSON object")
    return value


def _parse_time(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ReviewDebtError("timestamp must be non-empty")
    if not RFC3339_RE.fullmatch(value):
        raise ReviewDebtError(f"invalid RFC3339 timestamp: {value}")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        result = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ReviewDebtError(f"invalid RFC3339 timestamp: {value}") from exc
    if result.tzinfo is None:
        raise ReviewDebtError("timestamp must include timezone")
    return result.astimezone(timezone.utc)


def defer_fingerprint(value: dict) -> str:
    semantic = {
        "schema_version": value.get("schema_version"),
        "defer_id": value.get("defer_id"),
        "epoch_id": value.get("epoch_id"),
        "recorded_at": value.get("recorded_at"),
        "expires_at": value.get("expires_at"),
        "baseline_material_tasks": value.get("baseline_material_tasks"),
        "max_additional_material_tasks": value.get("max_additional_material_tasks"),
        "reason": value.get("reason"),
        "reviewed_by_role": value.get("reviewed_by_role"),
        "evidence": sorted(value.get("evidence", [])),
    }
    canonical = json.dumps(semantic, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_defer(defer: dict, state: dict, now: datetime) -> dict:
    required = {
        "schema_version","defer_id","epoch_id","recorded_at","expires_at",
        "baseline_material_tasks","max_additional_material_tasks","reason",
        "reviewed_by_role","evidence","fingerprint",
    }
    if set(defer) != required:
        raise ReviewDebtError("defer record fields must exactly match the V1 contract")
    if type(defer["schema_version"]) is not int or defer["schema_version"] != 1:
        raise ReviewDebtError("defer schema_version must be integer 1")
    if not isinstance(defer["defer_id"], str) or not __import__("re").fullmatch(r"ELD-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}", defer["defer_id"]):
        raise ReviewDebtError("defer_id is invalid")
    if defer["epoch_id"] != state.get("epoch_id"):
        raise ReviewDebtError("defer epoch_id does not match current learning epoch")
    recorded = _parse_time(defer["recorded_at"])
    expires = _parse_time(defer["expires_at"])
    if expires <= recorded:
        raise ReviewDebtError("defer expiry must be after recorded_at")
    if expires - recorded > __import__("datetime").timedelta(days=7):
        raise ReviewDebtError("defer may not exceed seven days")
    if recorded > now:
        raise ReviewDebtError("defer recorded_at cannot be in the future")
    if now >= expires:
        raise ReviewDebtError("defer is expired")
    if type(defer["baseline_material_tasks"]) is not int or defer["baseline_material_tasks"] < 0:
        raise ReviewDebtError("baseline_material_tasks must be a non-negative integer")
    if type(defer["max_additional_material_tasks"]) is not int or not 0 <= defer["max_additional_material_tasks"] <= 10:
        raise ReviewDebtError("max_additional_material_tasks must be an integer between 0 and 10")
    if not isinstance(defer["reason"], str) or len(defer["reason"].strip()) < 20:
        raise ReviewDebtError("defer reason is too short")
    if not isinstance(defer["reviewed_by_role"], str) or len(defer["reviewed_by_role"].strip()) < 3:
        raise ReviewDebtError("reviewed_by_role is required")
    evidence = defer["evidence"]
    if (
        not isinstance(evidence, list)
        or not evidence
        or any(not isinstance(item, str) or not item.strip() for item in evidence)
        or len(evidence) != len(set(evidence))
    ):
        raise ReviewDebtError("defer evidence must be a non-empty unique list of non-empty strings")
    if not isinstance(defer["fingerprint"], str) or not __import__("re").fullmatch(r"[a-f0-9]{64}", defer["fingerprint"]):
        raise ReviewDebtError("defer fingerprint must be lowercase sha256")
    if defer["fingerprint"] != defer_fingerprint(defer):
        raise ReviewDebtError("defer fingerprint mismatch")

    current = int(state.get("metrics_since_last_review", {}).get("material_tasks", 0))
    if current < defer["baseline_material_tasks"]:
        raise ReviewDebtError("current material task count is below defer baseline")
    additional = current - defer["baseline_material_tasks"]
    if additional > defer["max_additional_material_tasks"]:
        raise ReviewDebtError("bounded defer material-task allowance exceeded")
    return {"additional_material_tasks": additional}


def evaluate(state: dict, defer: dict | None, now: datetime) -> dict:
    _validate_state(state)
    trigger = state["trigger"]
    reported_level = trigger.get("level")
    metrics = state["metrics_since_last_review"]
    critical_events = metrics["security_or_data_critical_events"]
    verification_escapes = metrics["verification_escapes"]

    if critical_events > 0:
        return {
            "status": "BLOCK_CRITICAL_SECURITY_OR_DATA_REVIEW",
            "epoch_id": state.get("epoch_id"),
            "trigger": reported_level,
            "effective_trigger": "IMMEDIATE_REVIEW",
            "critical_events": critical_events,
            "reason": "security/data critical evidence requires review closure and cannot be bypassed by a bounded defer",
        }

    evidence_requires_immediate = verification_escapes > 0
    effective_immediate = reported_level == "IMMEDIATE_REVIEW" or evidence_requires_immediate
    if not effective_immediate:
        return {
            "status": "PASS_NO_IMMEDIATE_REVIEW",
            "epoch_id": state.get("epoch_id"),
            "trigger": reported_level,
            "effective_trigger": reported_level,
        }

    if defer is None:
        return {
            "status": "BLOCK_IMMEDIATE_REVIEW_DEBT",
            "epoch_id": state.get("epoch_id"),
            "trigger": reported_level,
            "effective_trigger": "IMMEDIATE_REVIEW",
            "verification_escapes": verification_escapes,
            "reason": "IMMEDIATE_REVIEW evidence requires review closure or a bounded defer record",
        }
    details = validate_defer(defer, state, now)
    return {
        "status": "PASS_BOUNDED_REVIEW_DEFER",
        "epoch_id": state.get("epoch_id"),
        "trigger": reported_level,
        "effective_trigger": "IMMEDIATE_REVIEW",
        "verification_escapes": verification_escapes,
        "defer_id": defer["defer_id"],
        **details,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True)
    parser.add_argument("--defer")
    parser.add_argument("--now")
    args = parser.parse_args(argv)
    try:
        state = _read(Path(args.state))
        defer = _read(Path(args.defer)) if args.defer else None
        now = _parse_time(args.now) if args.now else datetime.now(timezone.utc)
        result = evaluate(state, defer, now)
    except ReviewDebtError as exc:
        print(json.dumps({"status":"BLOCK_INVALID_REVIEW_DEFER","error":str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"].startswith("PASS_") else 3


if __name__ == "__main__":
    raise SystemExit(main())
