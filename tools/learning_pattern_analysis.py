#!/usr/bin/env python3
"""Deterministic project-local Learning Pattern Analysis.

This analyzer reads EREI project learning artifacts and surfaces evidence-backed
review debt, measurement gaps, repeated verification escapes and operational
hotspots. It never creates Framework Feedback or mutates Framework/project
state; its output is review input only.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

try:
    from tools import task_learning as authoritative_task_learning
except ImportError:
    import task_learning as authoritative_task_learning


class LearningPatternError(RuntimeError):
    pass


REVIEW_TRIGGER_LEVELS = {
    "REVIEW_RECOMMENDED",
    "REVIEW_DUE",
    "IMMEDIATE_REVIEW",
}


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LearningPatternError(f"invalid JSONL at {path}:{number}: {exc}") from exc
        if not isinstance(value, dict):
            raise LearningPatternError(f"JSONL record at {path}:{number} is not an object")
        rows.append(value)
    return rows


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LearningPatternError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LearningPatternError(f"invalid JSON at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise LearningPatternError(f"record at {path} is not an object")
    return value


def _occurrence(event: dict) -> str:
    value = event.get("occurrence_id") or event.get("task_id")
    if not isinstance(value, str) or not value:
        raise LearningPatternError("event is missing task/occurrence identity")
    return value


def _reviewed_occurrences(events: list[dict], reviews: list[dict]) -> set[str]:
    reviewed: set[str] = set()
    legacy_cutoff = 0
    for review in reviews:
        schema = review.get("schema_version", 1)
        if schema == 1 and isinstance(review.get("through_event_count"), int):
            legacy_cutoff = max(legacy_cutoff, review["through_event_count"])
        if schema == 2:
            members = review.get("reviewed_occurrence_ids", [])
            if isinstance(members, list):
                reviewed.update(item for item in members if isinstance(item, str) and item)
    if legacy_cutoff < 0 or legacy_cutoff > len(events):
        raise LearningPatternError("legacy review cutoff is outside the event ledger")
    reviewed.update(_occurrence(event) for event in events[:legacy_cutoff])
    return reviewed


def _rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def _top(counter: Counter, limit: int = 8) -> list[dict]:
    return [{"value": key, "count": value} for key, value in counter.most_common(limit)]


def _is_measured(event: dict, signal: str) -> bool:
    if event.get("schema_version", 1) == 1:
        return True
    assessment = event.get("signal_assessment")
    return isinstance(assessment, dict) and assessment.get(signal) == "measured"


def analyze(events: list[dict], reviews: list[dict], state: dict) -> dict:
    reviewed = _reviewed_occurrences(events, reviews)
    current = [event for event in events if _occurrence(event) not in reviewed]
    material = [event for event in current if event.get("material") is True]

    schema_counts = Counter(str(event.get("schema_version", "unknown")) for event in current)
    workflow_counts = Counter(str(event.get("workflow", "unknown")) for event in material)
    outcome_counts = Counter(str(event.get("outcome_class", "unknown")) for event in material)
    risk_counts = Counter(str(event.get("risk", "unknown")) for event in material)
    task_group_counts = Counter(
        str(event["task_group"]) for event in material
        if isinstance(event.get("task_group"), str) and event["task_group"]
    )

    rework_events = [
        event for event in material
        if isinstance(event.get("rework_cycles"), int) and _is_measured(event, "rework_cycles")
    ]
    verification_events = [
        event for event in material
        if isinstance(event.get("verification_failures"), int) and _is_measured(event, "verification_failures")
    ]
    rework_tasks = [event for event in rework_events if event.get("rework_cycles", 0) > 0]
    verification_failure_tasks = [
        event for event in verification_events if event.get("verification_failures", 0) > 0
    ]
    escapes = [
        event for event in current
        if event.get("verification_escape") is True and _is_measured(event, "verification_escape")
    ]
    material_escape_events = [
        event for event in material
        if event.get("verification_escape") is True and _is_measured(event, "verification_escape")
    ]
    escape_assessed_material = [event for event in material if _is_measured(event, "verification_escape")]
    feedback_events = [
        event for event in current
        if event.get("framework_feedback_created") is True and _is_measured(event, "framework_feedback_created")
    ]

    failure_stage_counts: Counter = Counter()
    unknown_stage_failures = 0
    for event in verification_failure_tasks:
        stage = event.get("failure_stage") if event.get("schema_version") == 2 else None
        if not isinstance(stage, str) or not stage:
            stage = "unknown"
        failure_stage_counts[stage] += 1
        if stage == "unknown":
            unknown_stage_failures += 1

    failure_subject_counts = Counter(
        str(event.get("failure_subject", "unknown"))
        for event in verification_failure_tasks
        if event.get("failure_subject")
    )

    trigger = state.get("trigger", {}) if isinstance(state, dict) else {}
    trigger_level = trigger.get("level", "UNKNOWN")
    signals: list[dict] = []

    def add(code: str, severity: str, evidence: dict, interpretation: str) -> None:
        signals.append({
            "code": code,
            "severity": severity,
            "evidence": evidence,
            "interpretation": interpretation,
        })

    if trigger_level in REVIEW_TRIGGER_LEVELS and current:
        add(
            "REVIEW_DEBT",
            "high" if trigger_level == "IMMEDIATE_REVIEW" else "medium",
            {"trigger": trigger_level, "unreviewed_events": len(current)},
            "The deterministic learning trigger requires review, but the current epoch still contains unreviewed work.",
        )

    if len(escapes) >= 2:
        add(
            "VERIFICATION_ESCAPE_CLUSTER",
            "high",
            {
                "count": len(escapes),
                "task_ids": [event.get("task_id") for event in escapes],
                "workflows": sorted({str(event.get("workflow", "unknown")) for event in escapes}),
            },
            "Multiple verification escapes in one epoch justify explicit root-cause comparison rather than treating each escape as isolated by default.",
        )

    if len(schema_counts) > 1:
        add(
            "MIXED_LEARNING_SCHEMA_EPOCH",
            "medium",
            {"schema_versions": dict(sorted(schema_counts.items()))},
            "Mixed V1/V2 events reduce metric comparability because V1 lacks V2 assessment/stage semantics.",
        )

    unknown_stage_rate = _rate(unknown_stage_failures, len(verification_failure_tasks))
    if len(verification_failure_tasks) >= 3 and unknown_stage_rate is not None and unknown_stage_rate >= 0.30:
        add(
            "VERIFICATION_STAGE_COVERAGE_GAP",
            "medium",
            {
                "verification_failure_tasks": len(verification_failure_tasks),
                "unknown_stage_failure_tasks": unknown_stage_failures,
            },
            "A material share of verification failures cannot be classified as pre-merge, post-merge or runtime, limiting interpretation of the raw failure rate.",
        )

    if len(escapes) >= 2 and not feedback_events:
        add(
            "FEEDBACK_CONVERSION_GAP",
            "high",
            {"verification_escapes": len(escapes), "framework_feedback_tasks": 0},
            "Repeated escapes occurred without a Framework Feedback event in the epoch. This does not prove a Framework defect, but it requires an explicit feedback/no-feedback decision in Learning Review.",
        )

    rework_rate = _rate(len(rework_tasks), len(rework_events))
    verification_rate = _rate(len(verification_failure_tasks), len(verification_events))
    rework_free_rate = _rate(len(rework_events) - len(rework_tasks), len(rework_events))
    rework_cycles_total = sum(event.get("rework_cycles", 0) for event in rework_events)
    rework_assessment_coverage_rate = _rate(len(rework_events), len(material))
    rework_cycles_per_material_task = (
        round(rework_cycles_total / len(material), 4)
        if material and len(rework_events) == len(material)
        else None
    )
    rework_cycles_per_reworked_task = round(rework_cycles_total / len(rework_tasks), 4) if rework_tasks else None
    verification_clean_rate = _rate(len(verification_events) - len(verification_failure_tasks), len(verification_events))
    verification_failures_total = sum(event.get("verification_failures", 0) for event in verification_events)
    verification_assessment_coverage_rate = _rate(len(verification_events), len(material))
    verification_failures_per_material_task = (
        round(verification_failures_total / len(material), 4)
        if material and len(verification_events) == len(material)
        else None
    )
    verification_escape_assessment_coverage_rate = _rate(len(escape_assessed_material), len(material))
    verification_escape_rate = _rate(len(material_escape_events), len(escape_assessed_material))
    final_failed_task_rate = _rate(sum(event.get("outcome_class") == "failed" for event in material), len(material))
    verified_success_rate = _rate(sum(event.get("outcome_class") == "verified_success" for event in material), len(material))
    success_with_deferred_rate = _rate(sum(event.get("outcome_class") == "success_with_deferred" for event in material), len(material))
    known_stage_failure_tasks = len(verification_failure_tasks) - unknown_stage_failures
    stage_coverage_rate = _rate(known_stage_failure_tasks, len(verification_failure_tasks))

    if len(rework_events) >= 8 and rework_rate is not None and rework_rate >= 0.50:
        add(
            "HIGH_REWORK_DENSITY",
            "medium",
            {"assessed_material_tasks": len(rework_events), "rework_rate": rework_rate},
            "High rework density is a hotspot signal. Separate healthy review catches from avoidable workflow/tooling friction before assigning causation.",
        )

    if len(verification_events) >= 8 and verification_rate is not None and verification_rate >= 0.40:
        add(
            "HIGH_VERIFICATION_CATCH_DENSITY",
            "medium",
            {
                "assessed_material_tasks": len(verification_events),
                "verification_failure_rate": verification_rate,
                "failure_stages": dict(sorted(failure_stage_counts.items())),
            },
            "A high verification-failure rate is not automatically negative. Pre-merge catches can indicate effective assurance; escapes remain the stronger negative signal.",
        )

    if task_group_counts:
        repeated_groups = {key: count for key, count in task_group_counts.items() if count >= 3}
        if repeated_groups:
            add(
                "REPEATED_TASK_GROUPS",
                "low",
                {"task_groups": dict(sorted(repeated_groups.items()))},
                "Repeated task groups are useful review cohorts and should be compared for recurring failure subjects, rework and escapes.",
            )

    return {
        "schema_version": 1,
        "source": {
            "total_events": len(events),
            "total_reviews": len(reviews),
            "state_epoch_id": state.get("epoch_id"),
            "state_trigger": trigger,
        },
        "current_epoch": {
            "unreviewed_events": len(current),
            "material_tasks": len(material),
            "schema_versions": dict(sorted(schema_counts.items())),
            "outcomes": dict(sorted(outcome_counts.items())),
            "risks": dict(sorted(risk_counts.items())),
            "workflows": dict(sorted(workflow_counts.items())),
            "rework_tasks": len(rework_tasks),
            "total_rework_cycles": rework_cycles_total,
            "rework_rate": rework_rate,
            "rework_free_task_rate": rework_free_rate,
            "rework_assessment_coverage_rate": rework_assessment_coverage_rate,
            "rework_cycles_per_material_task": rework_cycles_per_material_task,
            "rework_cycles_per_reworked_task": rework_cycles_per_reworked_task,
            "verification_failure_tasks": len(verification_failure_tasks),
            "verification_failures": verification_failures_total,
            "verification_failure_rate": verification_rate,
            "verification_clean_task_rate": verification_clean_rate,
            "verification_assessment_coverage_rate": verification_assessment_coverage_rate,
            "verification_failures_per_material_task": verification_failures_per_material_task,
            "verification_escapes": len(material_escape_events),
            "verification_escape_task_rate": verification_escape_rate,
            "verification_escape_assessment_coverage_rate": verification_escape_assessment_coverage_rate,
            "verification_stage_coverage_rate": stage_coverage_rate,
            "final_failed_task_rate": final_failed_task_rate,
            "verified_success_rate": verified_success_rate,
            "success_with_deferred_rate": success_with_deferred_rate,
            "framework_feedback_tasks": len(feedback_events),
            "failure_stages": dict(sorted(failure_stage_counts.items())),
            "top_workflows": _top(workflow_counts),
            "top_task_groups": _top(task_group_counts),
            "top_failure_subjects": _top(failure_subject_counts, 5),
        },
        "metric_semantics": {
            "rework_rate": "Share of assessed material tasks with at least one material iteration after the first candidate. It is not task restart rate, final failure rate, or execution accuracy.",
            "verification_failure_rate": "Share of assessed material tasks with at least one failed deterministic verification attempt during execution. It is a catch-density signal, not final task failure rate.",
            "verification_escape_task_rate": "Share of assessed material tasks where a prior verification/completion assumption was later contradicted. This is a stronger negative quality signal than raw verification-failure rate.",
            "final_failed_task_rate": "Share of material tasks whose terminal outcome is failed.",
            "rework_free_task_rate": "Share of assessed material tasks that required no recorded material rework cycle.",
            "verification_clean_task_rate": "Share of assessed material tasks with no recorded failed verification attempt."
        },
        "signals": signals,
        "recommendations": [
            "Close any REVIEW_RECOMMENDED/REVIEW_DUE/IMMEDIATE_REVIEW debt before accumulating another large material cohort.",
            "Compare every verification escape against prior escapes for reusable mechanism, not only project-local symptom.",
            "Do not treat pre-merge deterministic catches as equivalent to escaped defects.",
            "Prefer V2 occurrence/stage/assessment semantics for new events so learning metrics remain comparable.",
            "Create Framework Feedback only when evidence supports a reusable Framework limitation; record an explicit no-feedback rationale otherwise.",
        ],
    }


def _render_markdown(report: dict) -> str:
    epoch = report["current_epoch"]
    lines = [
        "# Learning Pattern Analysis",
        "",
        f"- Unreviewed events: **{epoch['unreviewed_events']}**",
        f"- Material tasks: **{epoch['material_tasks']}**",
        f"- Rework rate: **{epoch['rework_rate']}** (assessment coverage: **{epoch['rework_assessment_coverage_rate']}**; iteration density, not accuracy)",
        f"- Rework-free task rate: **{epoch['rework_free_task_rate']}** (assessment coverage: **{epoch['rework_assessment_coverage_rate']}**)",
        f"- Verification-failure rate: **{epoch['verification_failure_rate']}** (assessment coverage: **{epoch['verification_assessment_coverage_rate']}**; catch density, not final failure)",
        f"- Verification-clean task rate: **{epoch['verification_clean_task_rate']}** (assessment coverage: **{epoch['verification_assessment_coverage_rate']}**)",
        f"- Verification escape rate: **{epoch['verification_escape_task_rate']}** (assessment coverage: **{epoch['verification_escape_assessment_coverage_rate']}**)",
        f"- Final failed-task rate: **{epoch['final_failed_task_rate']}**",
        f"- Framework-feedback tasks: **{epoch['framework_feedback_tasks']}**",
        "",
        "## Signals",
        "",
    ]
    if not report["signals"]:
        lines.append("- No candidate pattern signal crossed the deterministic analysis thresholds.")
    for signal in report["signals"]:
        lines.append(f"- **{signal['code']}** ({signal['severity']}): {signal['interpretation']}")
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in report["recommendations"])
    return "\n".join(lines) + "\n"


def analyze_target(target: Path) -> dict:
    learning = target / ".erei" / "learning"
    try:
        authoritative_task_learning.status(target)
    except authoritative_task_learning.LearningError as exc:
        raise LearningPatternError(f"authoritative Task Learning rebuild failed: {exc}") from exc
    events = _read_jsonl(learning / "TASK_EVENTS.jsonl")
    reviews = _read_jsonl(learning / "LEARNING_REVIEWS.jsonl")
    state = _read_json(learning / "LEARNING_STATE.json")
    if not events:
        raise LearningPatternError("no prospective Task Learning events found")
    return analyze(events, reviews, state)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze EREI Task Learning patterns without mutating project state.")
    parser.add_argument("--target", required=True)
    parser.add_argument("--json-output")
    parser.add_argument("--markdown-output")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        report = analyze_target(Path(args.target).resolve())
        payload = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.json_output:
            Path(args.json_output).write_text(payload, encoding="utf-8")
        if args.markdown_output:
            Path(args.markdown_output).write_text(_render_markdown(report), encoding="utf-8")
        if not args.json_output:
            print(payload, end="")
        return 0
    except (LearningPatternError, OSError) as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
