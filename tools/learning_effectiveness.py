#!/usr/bin/env python3
"""Compare two Learning Pattern Analysis reports without claiming causation."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path




if __package__:
    from . import capability_activation
else:
    import importlib.util
    _activation_spec = importlib.util.spec_from_file_location("_erei_capability_activation", Path(__file__).with_name("capability_activation.py"))
    capability_activation = importlib.util.module_from_spec(_activation_spec)
    _activation_spec.loader.exec_module(capability_activation)


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
COVERAGE_BY_METRIC = {
    "verification_escape_task_rate": "verification_escape_assessment_coverage_rate",
    "rework_rate": "rework_assessment_coverage_rate",
    "rework_free_task_rate": "rework_assessment_coverage_rate",
    "verification_failure_rate": "verification_assessment_coverage_rate",
    "verification_clean_task_rate": "verification_assessment_coverage_rate",
}
MIN_ASSESSMENT_COVERAGE = 0.80
MAX_COVERAGE_DELTA = 0.10


def _reject_constant(value: str):
    raise ValueError(f"non-finite JSON constant: {value}")


def _load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    except (OSError, ValueError) as exc:
        raise EffectivenessError(f"cannot read report {path}: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(value.get("current_epoch"), dict):
        raise EffectivenessError("input must be a Learning Pattern Analysis report")
    return value


def _epoch(report: dict) -> dict:
    if not isinstance(report, dict) or not isinstance(report.get("current_epoch"), dict):
        raise EffectivenessError("input must be a Learning Pattern Analysis report")
    epoch = report["current_epoch"]
    for key in PRIMARY + SECONDARY + tuple(set(COVERAGE_BY_METRIC.values())):
        value = epoch.get(key)
        if value is not None and (
            type(value) not in {int, float}
            or not 0 <= value <= 1
            or not math.isfinite(value)
        ):
            raise EffectivenessError(f"{key} must be a finite rate between 0 and 1, or null")
    count = epoch.get("material_tasks")
    if count is not None and (type(count) is not int or count < 0):
        raise EffectivenessError("material_tasks must be a nonnegative integer, or null")
    return epoch


def _dist(value: dict, key: str) -> dict[str, int]:
    raw = value["current_epoch"].get(key, {})
    if not isinstance(raw, dict):
        raise EffectivenessError(f"{key} must be an object of nonnegative integer counts")
    if any(not isinstance(name, str) or type(count) is not int or count < 0
           for name, count in raw.items()):
        raise EffectivenessError(f"{key} must contain nonnegative integer counts")
    return raw


def _tvd(a: dict[str, int], b: dict[str, int]) -> float | None:
    ta, tb = sum(a.values()), sum(b.values())
    if not ta or not tb:
        return None
    keys = set(a) | set(b)
    return round(0.5 * sum(abs(a.get(k,0)/ta - b.get(k,0)/tb) for k in keys), 4)


def compare(before: dict, after: dict) -> dict:
    b, a = _epoch(before), _epoch(after)
    bm, am = b.get("material_tasks"), a.get("material_tasks")
    risk_distance = _tvd(_dist(before,"risks"), _dist(after,"risks"))
    workflow_distance = _tvd(_dist(before,"workflows"), _dist(after,"workflows"))
    outcome_distance = _tvd(_dist(before,"outcomes"), _dist(after,"outcomes"))
    comparability_reasons = []
    if bm is None or am is None:
        comparability_reasons.append("material_task_count_unavailable")
    elif bm < 5 or am < 5:
        comparability_reasons.append("sample_below_5_material_tasks")
    if risk_distance is None:
        comparability_reasons.append("risk_mix_unavailable")
    elif risk_distance > 0.25:
        comparability_reasons.append("risk_mix_changed_materially")
    if workflow_distance is None:
        comparability_reasons.append("workflow_mix_unavailable")
    elif workflow_distance > 0.25:
        comparability_reasons.append("workflow_mix_changed_materially")
    if outcome_distance is None:
        comparability_reasons.append("outcome_mix_unavailable")

    coverage = {}
    for key in sorted(set(COVERAGE_BY_METRIC.values())):
        bv, av = b.get(key), a.get(key)
        comparable = True
        reasons = []
        if type(bv) not in {int, float} or type(av) not in {int, float} or not (0 <= bv <= 1 and 0 <= av <= 1):
            comparable = False
            reasons.append("coverage_unavailable")
            comparability_reasons.append(key + "_unavailable")
        else:
            if min(bv, av) < MIN_ASSESSMENT_COVERAGE:
                comparable = False
                reasons.append("coverage_below_80_percent")
                comparability_reasons.append(key + "_below_80_percent")
            if abs(av - bv) > MAX_COVERAGE_DELTA:
                comparable = False
                reasons.append("coverage_changed_materially")
                comparability_reasons.append(key + "_changed_materially")
        coverage[key] = {"before": bv, "after": av, "comparable": comparable, "reasons": reasons}

    metrics = {}
    for key in PRIMARY + SECONDARY:
        bv, av = b.get(key), a.get(key)
        if bv is not None and av is not None:
            metrics[key] = {
                "before": bv,
                "after": av,
                "delta": round(av-bv,4),
            }

    primary_direction = {}
    for key in PRIMARY:
        if key not in metrics:
            primary_direction[key] = "not_comparable"
            comparability_reasons.append(key + "_unavailable")
        else:
            coverage_key = COVERAGE_BY_METRIC.get(key)
            if coverage_key and not coverage.get(coverage_key, {}).get("comparable", False):
                primary_direction[key] = "not_comparable"
            else:
                delta = metrics[key]["delta"]
                primary_direction[key] = "improved" if delta < 0 else "worsened" if delta > 0 else "held"

    return {
        "schema_version": 1,
        "status": "COMPARABLE_DIRECTIONAL_ONLY" if not comparability_reasons else "NEEDS_COMPARABILITY_REVIEW",
        "causation": "NOT_ESTABLISHED",
        "samples": {"before_material_tasks":bm,"after_material_tasks":am},
        "comparability": {
            "risk_mix_total_variation": risk_distance,
            "workflow_mix_total_variation": workflow_distance,
            "outcome_mix_total_variation": outcome_distance,
            "assessment_coverage": coverage,
            "reasons": list(dict.fromkeys(comparability_reasons)),
        },
        "primary_quality_signals": primary_direction,
        "metric_deltas": metrics,
        "interpretation_rule": "Escape/final-failure deltas are primary quality signals; rework and verification-failure deltas are secondary iteration/catch signals and must not be optimized by weakening assurance.",
    }


def compare_target(target: Path, before_path: Path, after_path: Path) -> dict:
    """Governed project dispatch; compare remains a pure artifact calculation."""
    capability_activation.require_active(target, "framework_effectiveness_measurement")
    return compare(_load(before_path), _load(after_path))


def main(argv=None) -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--before",required=True)
    parser.add_argument("--after",required=True)
    args=parser.parse_args(argv)
    try:
        result=compare_target(Path(args.target), Path(args.before), Path(args.after))
    except capability_activation.InactiveCapabilityError as exc:
        print(json.dumps(exc.result, sort_keys=True))
        return 3
    except (capability_activation.ActivationError, OSError, EffectivenessError) as exc:
        print(json.dumps({"status":"ERROR","error":str(exc)},sort_keys=True))
        return 2
    print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
