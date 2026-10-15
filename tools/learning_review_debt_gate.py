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


def _validate_state(state: dict) -> None:
    if state.get("schema_version") not in {1, 2}:
        raise ReviewDebtError("learning state schema_version must be 1 or 2")
    epoch_id = state.get("epoch_id")
    if not isinstance(epoch_id, str) or not epoch_id.startswith("EPOCH-"):
        raise ReviewDebtError("learning state epoch_id is invalid")
    trigger = state.get("trigger")
    if not isinstance(trigger, dict) or trigger.get("level") not in TRIGGER_LEVELS:
        raise ReviewDebtError("learning state trigger.level is missing or invalid")
    metrics = state.get("metrics_since_last_review")
    if not isinstance(metrics, dict):
        raise ReviewDebtError("learning state metrics_since_last_review is required")
    material_tasks = metrics.get("material_tasks")
    if not isinstance(material_tasks, int) or material_tasks < 0:
        raise ReviewDebtError("learning state material_tasks must be a non-negative integer")


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
    if defer["schema_version"] != 1:
        raise ReviewDebtError("defer schema_version must be 1")
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
    if not isinstance(defer["baseline_material_tasks"], int) or defer["baseline_material_tasks"] < 0:
        raise ReviewDebtError("baseline_material_tasks must be non-negative")
    if not isinstance(defer["max_additional_material_tasks"], int) or not 0 <= defer["max_additional_material_tasks"] <= 10:
        raise ReviewDebtError("max_additional_material_tasks must be between 0 and 10")
    if not isinstance(defer["reason"], str) or len(defer["reason"].strip()) < 20:
        raise ReviewDebtError("defer reason is too short")
    if not isinstance(defer["reviewed_by_role"], str) or len(defer["reviewed_by_role"].strip()) < 3:
        raise ReviewDebtError("reviewed_by_role is required")
    evidence = defer["evidence"]
    if not isinstance(evidence, list) or not evidence or len(evidence) != len(set(evidence)):
        raise ReviewDebtError("defer evidence must be a non-empty unique list")
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
    level = trigger.get("level")
    if level != "IMMEDIATE_REVIEW":
        return {"status": "PASS_NO_IMMEDIATE_REVIEW", "epoch_id": state.get("epoch_id"), "trigger": level}
    if defer is None:
        return {
            "status": "BLOCK_IMMEDIATE_REVIEW_DEBT",
            "epoch_id": state.get("epoch_id"),
            "trigger": level,
            "reason": "IMMEDIATE_REVIEW requires review closure or a bounded defer record",
        }
    details = validate_defer(defer, state, now)
    return {
        "status": "PASS_BOUNDED_REVIEW_DEFER",
        "epoch_id": state.get("epoch_id"),
        "trigger": level,
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
