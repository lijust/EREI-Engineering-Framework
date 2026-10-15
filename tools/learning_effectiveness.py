#!/usr/bin/env python3
"""Compare two Learning Pattern Analysis reports without claiming causation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


class EffectivenessError(RuntimeError):
    pass


PRIMARY = (
    "verification_escape_task_rate",
    "final_failed_task_rate",
)
SECONDARY = (
    "rework_rate",
    "rework_free_task_rate",
    "verification_failure_rate",
    "verification_clean_task_rate",
    "success_with_deferred_rate",
    "verified_success_rate",
)


def _load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EffectivenessError(f"cannot read report {path}: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("current_epoch"), dict):
        raise EffectivenessError("input must be a Learning Pattern Analysis report")
    return value


def _dist(value: dict, key: str) -> dict[str, int]:
    raw = value.get("current_epoch", {}).get(key, {})
    if not isinstance(raw, dict):
        return {}
    result = {}
    for name, count in raw.items():
        if isinstance(count, int) and count >= 0:
            result[str(name)] = count
    return result


def _tvd(a: dict[str, int], b: dict[str, int]) -> float | None:
    ta, tb = sum(a.values()), sum(b.values())
    if not ta or not tb:
        return None
    keys = set(a) | set(b)
    return round(0.5 * sum(abs(a.get(k,0)/ta - b.get(k,0)/tb) for k in keys), 4)


def compare(before: dict, after: dict) -> dict:
    b = before["current_epoch"]
    a = after["current_epoch"]
    bm, am = int(b.get("material_tasks",0)), int(a.get("material_tasks",0))
    risk_distance = _tvd(_dist(before,"risks"), _dist(after,"risks"))
    outcome_distance = _tvd(_dist(before,"outcomes"), _dist(after,"outcomes"))
    comparability_reasons = []
    if bm < 5 or am < 5:
        comparability_reasons.append("sample_below_5_material_tasks")
    if risk_distance is None:
        comparability_reasons.append("risk_mix_unavailable")
    elif risk_distance > 0.25:
        comparability_reasons.append("risk_mix_changed_materially")
    if outcome_distance is None:
        comparability_reasons.append("outcome_mix_unavailable")

    metrics = {}
    for key in PRIMARY + SECONDARY:
        bv, av = b.get(key), a.get(key)
        if isinstance(bv,(int,float)) and isinstance(av,(int,float)):
            metrics[key] = {
                "before": bv,
                "after": av,
                "delta": round(av-bv,4),
            }

    primary_direction = {}
    for key in PRIMARY:
        if key in metrics:
            delta = metrics[key]["delta"]
            primary_direction[key] = "improved" if delta < 0 else "worsened" if delta > 0 else "held"

    return {
        "schema_version": 1,
        "status": "COMPARABLE_DIRECTIONAL_ONLY" if not comparability_reasons else "NEEDS_COMPARABILITY_REVIEW",
        "causation": "NOT_ESTABLISHED",
        "samples": {"before_material_tasks":bm,"after_material_tasks":am},
        "comparability": {
            "risk_mix_total_variation": risk_distance,
            "outcome_mix_total_variation": outcome_distance,
            "reasons": comparability_reasons,
        },
        "primary_quality_signals": primary_direction,
        "metric_deltas": metrics,
        "interpretation_rule": "Escape/final-failure deltas are primary quality signals; rework and verification-failure deltas are secondary iteration/catch signals and must not be optimized by weakening assurance.",
    }


def main(argv=None) -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--before",required=True)
    parser.add_argument("--after",required=True)
    args=parser.parse_args(argv)
    try:
        result=compare(_load(Path(args.before)),_load(Path(args.after)))
    except EffectivenessError as exc:
        print(json.dumps({"status":"ERROR","error":str(exc)},sort_keys=True))
        return 2
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
