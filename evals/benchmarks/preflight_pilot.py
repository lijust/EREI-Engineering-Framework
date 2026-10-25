"""Read-only, fail-closed T15 *pre-execution readiness*; never runs a model.

Reports exact missing budget/runtime/hidden-acceptance approvals for all 48
planned V1/V2 slots, WITHOUT filling defaults, estimating costs, authorizing
model calls, or treating operator calibration as independent acceptance.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    from evals import benchmark_accounting
except ImportError:  # direct execution from evals/benchmarks/
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import benchmark_accounting


SHA64 = re.compile(r"[a-f0-9]{64}\Z")
SHA40 = re.compile(r"[a-f0-9]{40}\Z")
TASKS = {*(f"APP-{i:02}" for i in range(1, 7)),
         *(f"PY-{i:02}" for i in range(1, 7))}
LIMITED_FLAGS = ("authorized",)
HASH_FIELDS = (
    ("execution", "runtime_digest"),
    ("execution", "environment_digest"),
    ("execution", "tool_permissions_digest"),
    ("review", "hidden_acceptance_package_sha256"),
    ("review", "analysis_preregistration_sha256"),
)


def preflight(plan: dict, records: dict | None = None) -> dict:
    schedule = benchmark_accounting.schedule(plan)
    if set(t["task_id"] for t in plan["tasks"]) != TASKS:
        raise ValueError("exact frozen twelve task identities required")
    if plan.get("state") != "DRAFT_NOT_EXECUTABLE":
        raise ValueError("this script is only for non-executable draft plans")
    execution = plan.get("execution")
    review = plan.get("review")
    refs = plan.get("framework_refs")
    if not all(isinstance(x, dict) for x in (execution, review, refs)):
        raise ValueError("missing execution, review or framework references")
    if type(execution.get("authorized")) is not bool or execution["authorized"]:
        raise ValueError("paid/model execution authorization must stay false")
    if not isinstance(refs.get("V1"), str) or not SHA40.fullmatch(refs["V1"]):
        raise ValueError("V1 reference must be pinned to immutable SHA")
    blockers = []

    def missing(code: str, present: bool) -> None:
        if not present:
            blockers.append(code)

    missing("V2_FRAMEWORK_SHA_MISSING", isinstance(refs.get("V2"), str)
            and bool(SHA40.fullmatch(refs["V2"])))
    for key in ("model_id", "model_revision"):
        missing("EXECUTION_" + key.upper() + "_MISSING",
                isinstance(execution.get(key), str) and bool(execution[key].strip()))
    for section, key in HASH_FIELDS:
        val = plan[section].get(key)
        missing(section.upper() + "_" + key.upper() + "_MISSING",
                isinstance(val, str) and bool(SHA64.fullmatch(val)))

    for key in ("per_run_token_cap", "per_run_time_cap_seconds"):
        val = execution.get(key)
        missing("EXECUTION_" + key.upper() + "_MISSING",
                type(val) is int and 0 < val < 1_000_000_000)
    val = execution.get("total_budget_usd")
    missing("EXECUTION_TOTAL_BUDGET_USD_MISSING",
            type(val) in (int, float) and val > 0 and val < 1e12)
    missing("EXECUTION_BUDGET_APPROVAL_REF_MISSING",
            isinstance(execution.get("budget_approval_ref"), str)
            and bool(execution["budget_approval_ref"].strip()))
    missing("INDEPENDENT_REVIEWER_MISSING",
            isinstance(review.get("independent_reviewer"), str)
            and bool(review["independent_reviewer"].strip()))

    for task in plan["tasks"]:
        task_id = task["task_id"]
        missing(f"TASK_{task_id}_HIDDEN_ACCEPTANCE_MISSING",
                isinstance(task.get("hidden_acceptance_sha256"), str)
                and bool(SHA64.fullmatch(task["hidden_acceptance_sha256"])))
        missing(f"TASK_{task_id}_PINNED_SOURCE_MISSING",
                isinstance(task.get("source"), dict)
                and isinstance(task["source"].get("commit"), str)
                and bool(SHA40.fullmatch(task["source"]["commit"])))
        missing(f"TASK_{task_id}_CALIBRATION_PACKAGE_MISSING",
                isinstance(task.get("calibration_package"), dict)
                and task["calibration_package"].get("task_id") == task_id)
    accounting = benchmark_accounting.summarize(plan, records)
    if accounting["execution_authorized"] is not False:
        raise ValueError("accounting attempted authority promotion")
    schedule_count = len(schedule)
    if schedule_count != 48:
        raise ValueError("not exactly 48 assigned comparison slots")
    already = sum(accounting["arms"][arm]["observed_runs"] for arm in ("V1", "V2"))
    return {
        "schema_version": 1,
        "kind": "READ_ONLY_T15_PILOT_PREFLIGHT",
        "plan_sha256": accounting["plan_sha256"],
        "required_pairs": 24,
        "required_slots": schedule_count,
        "observed_slots": already,
        "missing_slots": schedule_count - already,
        "blocking_preparation_fields": sorted(blockers),
        "preparation_fields_complete": not blockers,
        "model_execution_authorized": False,
        "independent_acceptance_verified": False,
        "hidden_acceptance_verified": False,
        "model_effectiveness_established": False,
        "next_step": (
            "OWNER_AND_INDEPENDENT_SOURCE_REVIEW_REQUIRED"
            if not blockers else "COMPLETE_PINNED_PREFLIGHT_FIELDS_WITHOUT_MODEL_CALLS"
        ),
        "stable_ready": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--records", type=Path)
    ns = p.parse_args(argv)
    try:
        plan = benchmark_accounting.strict_json(ns.plan.read_text(encoding="utf-8"))
        records = (benchmark_accounting.strict_json(ns.records.read_text(encoding="utf-8"))
                   if ns.records else None)
        report = preflight(plan, records)
    except (OSError, ValueError, TypeError) as e:
        p.exit(2, f"T15 preflight blocked: {e}\n")
    print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
