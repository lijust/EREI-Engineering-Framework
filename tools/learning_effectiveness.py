#!/usr/bin/env python3
"""Compare two Learning Pattern Analysis reports without claiming causation."""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path




if __package__:
    from . import capability_activation, validation_contract
else:
    import importlib.util
    _activation_spec = importlib.util.spec_from_file_location("_erei_capability_activation", Path(__file__).with_name("capability_activation.py"))
    capability_activation = importlib.util.module_from_spec(_activation_spec)
    _activation_spec.loader.exec_module(capability_activation)
    _validation_spec = importlib.util.spec_from_file_location("_erei_validation_contract", Path(__file__).with_name("validation_contract.py"))
    validation_contract = importlib.util.module_from_spec(_validation_spec)
    _validation_spec.loader.exec_module(validation_contract)


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


def _record_fields(value, fields: set[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != fields:
        raise EffectivenessError(f"{label} must contain exactly: {', '.join(sorted(fields))}")
    return value


def _record_text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise EffectivenessError(f"{label} must be non-empty text without surrounding whitespace")
    return value


def _record_refs(value, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise EffectivenessError(f"{label} must contain evidence references")
    refs = [_record_text(item, label) for item in value]
    if len(set(refs)) != len(refs):
        raise EffectivenessError(f"{label} must contain unique references")
    return refs


def _record_sha(value, label: str, length: int = 40) -> str:
    text = _record_text(value, label)
    if not re.fullmatch(r"[a-f0-9]{" + str(length) + r"}", text):
        raise EffectivenessError(f"{label} must be an exact {length}-character digest")
    return text


def assess_intervention(value: dict) -> dict:
    """Account for declared exposure; do not authenticate evidence or infer effect.

    This pure calculation neither reads a project ledger nor authorizes a
    Candidate. Project dispatch must pass the existing activation boundary.
    """
    _record_fields(value, {"schema_version", "intervention_id", "finding_refs", "root_cause",
                          "development_output_ref", "implementation", "adoption", "cohort"}, "intervention")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise EffectivenessError("intervention schema_version must be integer 1")
    for key in ("intervention_id", "root_cause", "development_output_ref"):
        _record_text(value[key], key)
    _record_refs(value["finding_refs"], "finding_refs")
    implementation = _record_fields(value["implementation"], {"repository", "ref"}, "implementation")
    _record_text(implementation["repository"], "implementation.repository")
    _record_sha(implementation["ref"], "implementation.ref")
    cohort = _record_fields(value["cohort"], {"repository", "ref", "ledger_sha256", "epoch_id",
                                            "eligibility_rule", "selection_ref", "tasks"}, "cohort")
    for key in ("repository", "epoch_id", "eligibility_rule"):
        _record_text(cohort[key], "cohort." + key)
    for key in ("ref", "selection_ref"):
        _record_sha(cohort[key], "cohort." + key)
    _record_sha(cohort["ledger_sha256"], "cohort.ledger_sha256", 64)
    adoption = value["adoption"]
    if adoption is not None:
        _record_fields(adoption, {"repository", "ref", "implementation_ref", "evidence"}, "adoption")
        _record_text(adoption["repository"], "adoption.repository")
        _record_sha(adoption["ref"], "adoption.ref")
        _record_sha(adoption["implementation_ref"], "adoption.implementation_ref")
        _record_refs(adoption["evidence"], "adoption.evidence")
        if adoption["repository"] != cohort["repository"]:
            raise EffectivenessError("adoption and cohort repositories must match")
        if adoption["implementation_ref"] != implementation["ref"]:
            raise EffectivenessError("adoption must identify the declared implementation ref")
    tasks = cohort["tasks"]
    if not isinstance(tasks, list):
        raise EffectivenessError("cohort.tasks must be an array")
    seen, prospective = set(), []
    for row in tasks:
        _record_fields(row, {"occurrence_id", "identity_basis", "exposed", "recurred", "evidence"}, "cohort task")
        basis = row["identity_basis"]
        if basis not in ("prospective", "legacy_assumed"):
            raise EffectivenessError("identity_basis must be prospective or legacy_assumed")
        identity = _record_text(row["occurrence_id"], "occurrence_id")
        valid_identity = validation_contract.OCCURRENCE_ID_RE.fullmatch(identity)
        if basis == "legacy_assumed":
            valid_identity = valid_identity or validation_contract.TASK_ID_RE.fullmatch(identity)
        if not valid_identity:
            raise EffectivenessError("occurrence_id does not match its identity_basis")
        if identity in seen:
            raise EffectivenessError("duplicate cohort occurrence_id")
        seen.add(identity)
        for key in ("exposed", "recurred"):
            if row[key] is not None and type(row[key]) is not bool:
                raise EffectivenessError(f"{key} must be boolean or null")
        _record_refs(row["evidence"], "task.evidence")
        if row["exposed"] is True and adoption is None:
            raise EffectivenessError("recorded exposure requires an adoption record")
        if basis == "prospective":
            prospective.append(row)
    eligible = len(prospective)
    exposure_assessed = sum(row["exposed"] is not None for row in prospective)
    exposed = [row for row in prospective if row["exposed"] is True]
    assessed = [row for row in exposed if row["recurred"] is not None]
    recurrences = sum(row["recurred"] is True for row in assessed)
    if not eligible:
        status = "NO_PROSPECTIVE_ELIGIBLE_TASKS"
    elif not exposure_assessed:
        status = "EXPOSURE_UNASSESSED"
    elif not exposed:
        status = "NO_RECORDED_EXPOSURE"
    elif not assessed:
        status = "OUTCOMES_UNASSESSED"
    elif len(assessed) < len(exposed) or exposure_assessed < eligible:
        status = "PARTIAL_OUTCOME_ASSESSMENT"
    else:
        status = "OBSERVED_OUTCOMES_ONLY"
    return {
        "schema_version": 1, "intervention_id": value["intervention_id"], "status": status,
        "effectiveness": "NOT_ESTABLISHED", "causation": "NOT_ESTABLISHED",
        "evidence_authenticity": "NOT_VERIFIED",
        "adoption_status": "RECORDED" if adoption is not None else "NOT_RECORDED",
        "trace": {key: value[key] for key in ("finding_refs", "root_cause", "development_output_ref", "implementation", "adoption")},
        "cohort": {key: cohort[key] for key in cohort if key != "tasks"},
        "declared_eligible_count": len(tasks), "legacy_assumed_count": len(tasks) - eligible,
        "prospective": {
            "eligible": eligible, "exposure_assessed": exposure_assessed, "exposed": len(exposed),
            "outcome_assessed_exposed": len(assessed), "recurrences": recurrences,
            "exposure_assessment_coverage": exposure_assessed / eligible if eligible else None,
            "outcome_assessment_coverage": len(assessed) / len(exposed) if exposed else None,
            "recurrence_rate_among_assessed_exposed": recurrences / len(assessed) if assessed else None,
        },
    }


def _unique_record_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_intervention(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant,
                          object_pairs_hook=_unique_record_keys)
    except (OSError, ValueError) as exc:
        raise EffectivenessError(f"cannot read intervention {path}: {exc}") from exc


def compare_target(target: Path, before_path: Path, after_path: Path, intervention_path: Path | None = None) -> dict:
    """Governed project dispatch; compare remains a pure artifact calculation."""
    capability_activation.require_active(target, "framework_effectiveness_measurement")
    result = compare(_load(before_path), _load(after_path))
    if intervention_path is not None:
        # Separate accounting: these task rows are not implicitly joined to the
        # before/after report populations and cannot upgrade their conclusions.
        result["intervention"] = assess_intervention(_load_intervention(intervention_path))
    return result


def main(argv=None) -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--before",required=True)
    parser.add_argument("--after",required=True)
    parser.add_argument("--intervention", help="Optional declared exposure record; no causal claim")
    args=parser.parse_args(argv)
    try:
        result=compare_target(Path(args.target), Path(args.before), Path(args.after),
                              Path(args.intervention) if args.intervention else None)
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
