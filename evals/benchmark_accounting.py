"""Offline pilot scheduling/accounting. No model, network, subprocess or writes."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

ARMS = ("V1", "V2")
COSTS = ("model_usd", "tools_usd", "ci_usd", "human_usd")
ASSESSMENTS = ("first_candidate_passed", "independent_completion_passed")
STATUSES = {"started", "completed", "failed", "timeout", "blocked", "canceled"}


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def bad_constant(value):
        raise ValueError(f"non-finite JSON number: {value}")

    return json.loads(text, object_pairs_hook=pairs, parse_constant=bad_constant)


def digest(plan):
    raw = json.dumps(plan, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def schedule(plan):
    if not isinstance(plan, dict) or type(plan.get("schema_version")) is not int or plan["schema_version"] != 1:
        raise ValueError("expected plan schema_version 1")
    if type(plan.get("repetitions")) is not int or plan["repetitions"] != 2:
        raise ValueError("this pilot requires exactly two repetitions")
    seed = plan.get("allocation_seed")
    tasks = plan.get("tasks")
    if not isinstance(seed, str) or not seed.strip():
        raise ValueError("allocation_seed is required")
    if not isinstance(tasks, list) or len(tasks) != 12:
        raise ValueError("this pilot requires 12 proposed tasks")
    ids = []
    for task in tasks:
        task_id = task.get("task_id") if isinstance(task, dict) else None
        if not isinstance(task_id, str) or not re.fullmatch(r"[A-Z]+-[0-9]{2}", task_id):
            raise ValueError("invalid task_id")
        if task_id in ids:
            raise ValueError("duplicate task_id")
        ids.append(task_id)
    blocks = []
    for task_id in sorted(ids):
        order_hash = hashlib.sha256(f"{seed}:{task_id}".encode()).digest()
        initial = ARMS if order_hash[0] % 2 == 0 else ARMS[::-1]
        for repetition in (1, 2):
            order = initial if repetition == 1 else initial[::-1]
            key = hashlib.sha256(f"{seed}:{task_id}:{repetition}".encode()).hexdigest()
            rows = [{
                "run_id": f"{task_id}-R{repetition}-{arm}",
                "task_id": task_id, "repetition": repetition, "arm": arm,
            } for arm in order]
            blocks.append((key, rows))
    return [row for _, rows in sorted(blocks) for row in rows]


def exact_keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError(f"{label} has missing or unexpected fields")


def nonnegative(value, label):
    if value is None:
        return
    try:
        valid = type(value) in (int, float) and math.isfinite(value) and value >= 0
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(f"{label} must be finite, non-negative or null")


def finite_sum(values):
    result = sum(values)
    nonnegative(result, "aggregate")
    return result


def metric(values, assigned):
    assessed = sum(value is not None for value in values)
    successes = sum(value is True for value in values)
    unknown = assigned - assessed
    return {
        "successes": successes, "assessed": assessed, "assigned": assigned,
        "unknown": unknown, "assessment_coverage": assessed / assigned,
        "rate": successes / assigned if unknown == 0 else None,
        # Missing-data bounds, NOT a sampling confidence interval.
        "missing_data_bounds": [successes / assigned, (successes + unknown) / assigned],
    }


def summarize(plan, records=None):
    planned = schedule(plan)
    plan_hash = digest(plan)
    if records is None:
        records = {"plan_sha256": plan_hash, "evidence_kind": "no_observations", "runs": []}
    exact_keys(records, ("plan_sha256", "evidence_kind", "runs"), "records")
    if records["plan_sha256"] != plan_hash:
        raise ValueError("records do not bind the exact plan")
    if records["evidence_kind"] not in {"synthetic", "observed_unverified", "no_observations"}:
        raise ValueError("invalid evidence_kind")
    if not isinstance(records["runs"], list):
        raise ValueError("runs must be a list")
    if records["evidence_kind"] == "no_observations" and records["runs"]:
        raise ValueError("no_observations cannot contain runs")
    by_id = {item["run_id"]: item for item in planned}
    observed = {}
    for row in records["runs"]:
        exact_keys(row, ("run_id", "status", *ASSESSMENTS, "review_evidence", "attempts"), "run")
        run_id = row["run_id"]
        if not isinstance(run_id, str) or run_id not in by_id or run_id in observed:
            raise ValueError("unknown or duplicate run_id")
        if row["status"] not in STATUSES:
            raise ValueError("invalid run status")
        for field in ASSESSMENTS:
            if row[field] is not None and type(row[field]) is not bool:
                raise ValueError(f"{field} must be boolean or null")
        evidence = row["review_evidence"]
        if not isinstance(evidence, list) or any(not isinstance(x, str) or not x.strip() for x in evidence):
            raise ValueError("review_evidence must contain non-empty references")
        if any(row[field] is not None for field in ASSESSMENTS) and not evidence:
            raise ValueError("assessed outcomes require review_evidence")
        if row["independent_completion_passed"] is True and row["status"] != "completed":
            raise ValueError("accepted completion conflicts with terminal status")
        if row["status"] == "started" and row["independent_completion_passed"] is not None:
            raise ValueError("unfinished run cannot have a final completion assessment")
        if row["first_candidate_passed"] is True and row["independent_completion_passed"] is not True:
            raise ValueError("first-candidate success requires accepted completion")
        attempts = row["attempts"]
        if not isinstance(attempts, list) or not attempts:
            raise ValueError("observed run requires at least one recorded attempt")
        for number, attempt in enumerate(attempts, 1):
            exact_keys(attempt, ("attempt_no", "evidence_ref", "wall_seconds", *COSTS), "attempt")
            if type(attempt["attempt_no"]) is not int or attempt["attempt_no"] != number:
                raise ValueError("attempt numbers must be consecutive from one")
            if not isinstance(attempt["evidence_ref"], str) or not attempt["evidence_ref"].strip():
                raise ValueError("attempt evidence_ref is required")
            for field in ("wall_seconds", *COSTS):
                nonnegative(attempt[field], field)
        observed[run_id] = row
    summaries = {}
    for arm in ARMS:
        ids = [row["run_id"] for row in planned if row["arm"] == arm]
        rows = [observed[run_id] for run_id in ids if run_id in observed]
        attempts = [item for row in rows for item in row["attempts"]]
        completed = metric([row["independent_completion_passed"] for row in rows], len(ids))
        all_terminal = len(rows) == len(ids) and all(row["status"] != "started" for row in rows)
        cost_complete = sum(all(item[field] is not None for field in COSTS) for item in attempts)
        known_cost = finite_sum(item[field] for item in attempts for field in COSTS if item[field] is not None)
        full_cost = all_terminal and cost_complete == len(attempts)
        cost_per_success = (
            known_cost / completed["successes"]
            if full_cost and completed["unknown"] == 0 and completed["successes"] else None
        )
        summaries[arm] = {
            "assigned_runs": len(ids), "observed_runs": len(rows),
            "missing_run_ids": [run_id for run_id in ids if run_id not in observed],
            "status_counts": {status: sum(row["status"] == status for row in rows) for status in sorted(STATUSES)},
            "attempts": len(attempts),
            "first_candidate": metric([row["first_candidate_passed"] for row in rows], len(ids)),
            "declared_independent_completion": completed,
            "known_cost_subtotal_usd": known_cost,
            "cost_complete_attempts": cost_complete,
            "total_cost_usd": known_cost if full_cost else None,
            "cost_per_declared_verified_run_usd": cost_per_success,
            "known_attempt_wall_seconds_sum": finite_sum(item["wall_seconds"] for item in attempts if item["wall_seconds"] is not None),
            "time_assessed_attempts": sum(item["wall_seconds"] is not None for item in attempts),
        }
    return {
        "schema_version": 1, "plan_sha256": plan_hash,
        "evidence_kind": records["evidence_kind"],
        "execution_authorized": False,
        "comparability": "NOT_VERIFIED",
        "evidence_authenticity": "NOT_VERIFIED",
        "effectiveness": "NOT_ESTABLISHED",
        "scheduled_runs": planned, "arms": summaries,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--records", type=Path)
    args = parser.parse_args(argv)
    try:
        plan = strict_json(args.plan.read_text(encoding="utf-8"))
        records = strict_json(args.records.read_text(encoding="utf-8")) if args.records else None
        result = summarize(plan, records)
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(2, f"benchmark accounting error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
