import importlib.util
import pathlib
import tempfile
import json

MODULE = pathlib.Path(__file__).resolve().parents[1] / "learning_pattern_analysis.py"
spec = importlib.util.spec_from_file_location("learning_pattern_analysis", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def event(task_id, schema=2, **overrides):
    value = {
        "schema_version": schema,
        "task_id": task_id,
        "recorded_at": "2026-10-15T00:00:00Z",
        "project": {"repository": "example/repo"},
        "framework_ref": "a" * 40,
        "workflow": "feature-development",
        "risk": "L2",
        "terminal_state": "COMPLETE_VERIFIED",
        "outcome_class": "verified_success",
        "material": True,
        "rework_cycles": 0,
        "verification_failures": 0,
        "verification_escape": False,
        "framework_feedback_created": False,
        "manual_workaround": False,
        "context_gap": False,
        "unexpected_scope_growth": False,
        "security_or_data_critical_event": False,
        "duration_class": "medium",
    }
    if schema == 2:
        value.update({
            "occurrence_id": task_id.replace("ETASK-", "EOCC-"),
            "signal_assessment": {
                "rework_cycles": "measured",
                "verification_failures": "measured",
                "verification_escape": "measured",
                "framework_feedback_created": "measured",
                "manual_workaround": "measured",
                "context_gap": "measured",
                "unexpected_scope_growth": "measured",
                "security_or_data_critical_event": "measured",
            },
            "failure_stage": "none",
        })
    value.update(overrides)
    return value


def signal_codes(report):
    return {item["code"] for item in report["signals"]}


events = [
    event("ETASK-20261015T000001Z-AAAABBBB", schema=1),
    event(
        "ETASK-20261015T000002Z-AAAABBBC",
        schema=2,
        rework_cycles=2,
        verification_failures=1,
        verification_escape=True,
        failure_stage="runtime",
        failure_subject="first escaped runtime defect",
        task_group="group-a",
    ),
    event(
        "ETASK-20261015T000003Z-AAAABBBD",
        schema=2,
        rework_cycles=1,
        verification_failures=1,
        verification_escape=True,
        failure_stage="post_merge",
        failure_subject="second escaped defect",
        task_group="group-a",
    ),
]

state = {
    "epoch_id": "EPOCH-002",
    "trigger": {"level": "IMMEDIATE_REVIEW", "reasons": ["verification_escape_observed"]},
}
report = mod.analyze(events, [], state)
codes = signal_codes(report)
assert report["current_epoch"]["unreviewed_events"] == 3
assert report["current_epoch"]["verification_escapes"] == 2
assert report["current_epoch"]["rework_rate"] == 0.6667
assert report["current_epoch"]["rework_free_task_rate"] == 0.3333
assert report["current_epoch"]["verification_failure_rate"] == 0.6667
assert report["current_epoch"]["verification_clean_task_rate"] == 0.3333
assert report["current_epoch"]["verification_escape_task_rate"] == 0.6667
assert report["current_epoch"]["final_failed_task_rate"] == 0.0
assert report["current_epoch"]["rework_assessment_coverage_rate"] == 1.0
assert report["current_epoch"]["verification_assessment_coverage_rate"] == 1.0
assert report["current_epoch"]["verification_escape_assessment_coverage_rate"] == 1.0
assert "execution accuracy" in report["metric_semantics"]["rework_rate"]
assert "REVIEW_DEBT" in codes
assert "VERIFICATION_ESCAPE_CLUSTER" in codes
assert "FEEDBACK_CONVERSION_GAP" in codes
assert "MIXED_LEARNING_SCHEMA_EPOCH" in codes

unassessed = event(
    "ETASK-20261015T000004Z-AAAABBBE",
    schema=2,
    signal_assessment={
        "rework_cycles": "not_assessed",
        "verification_failures": "not_assessed",
        "verification_escape": "not_assessed",
        "framework_feedback_created": "not_assessed",
        "manual_workaround": "not_assessed",
        "context_gap": "not_assessed",
        "unexpected_scope_growth": "not_assessed",
        "security_or_data_critical_event": "not_assessed",
    },
)
nonmaterial_escape = event(
    "ETASK-20261015T000005Z-AAAABBBF",
    schema=2,
    material=False,
    verification_escape=True,
)
coverage_report = mod.analyze([events[0], unassessed, nonmaterial_escape], [], {"epoch_id":"EPOCH-003","trigger":{"level":"LEARNING_HEALTHY","reasons":[]}})
assert coverage_report["current_epoch"]["material_tasks"] == 2
assert coverage_report["current_epoch"]["rework_assessment_coverage_rate"] == 0.5
assert coverage_report["current_epoch"]["verification_assessment_coverage_rate"] == 0.5
assert coverage_report["current_epoch"]["rework_free_task_rate"] == 1.0
assert coverage_report["current_epoch"]["verification_clean_task_rate"] == 1.0
assert coverage_report["current_epoch"]["verification_escape_task_rate"] == 0.0
assert coverage_report["current_epoch"]["verification_escapes"] == 0
assert coverage_report["current_epoch"]["rework_cycles_per_material_task"] is None
assert coverage_report["current_epoch"]["verification_failures_per_material_task"] is None
coverage_markdown = mod._render_markdown(coverage_report)
assert "Rework-free task rate: **1.0** (assessment coverage: **0.5**)" in coverage_markdown
assert "Verification-clean task rate: **1.0** (assessment coverage: **0.5**)" in coverage_markdown
assert "Verification escape rate: **0.0** (assessment coverage: **0.5**)" in coverage_markdown

reviews = [{    "schema_version": 1,
    "through_event_count": 1,
}]
report_after_cutoff = mod.analyze(events, reviews, state)
assert report_after_cutoff["current_epoch"]["unreviewed_events"] == 2

v2_review = [{
    "schema_version": 2,
    "reviewed_occurrence_ids": [events[1]["occurrence_id"]],
}]
report_v2_review = mod.analyze(events, v2_review, state)
assert report_v2_review["current_epoch"]["unreviewed_events"] == 2

with tempfile.TemporaryDirectory() as tmp:
    target = pathlib.Path(tmp)
    learning = target / ".erei" / "learning"
    learning.mkdir(parents=True)
    (learning / "TASK_EVENTS.jsonl").write_text(
        "".join(json.dumps(item) + "\n" for item in events),
        encoding="utf-8",
    )
    (learning / "LEARNING_REVIEWS.jsonl").write_text("", encoding="utf-8")
    (learning / "LEARNING_STATE.json").write_text(json.dumps(state), encoding="utf-8")
    loaded = mod.analyze_target(target)
    assert loaded["current_epoch"]["verification_escapes"] == 2

print("PASS: learning pattern analysis detects review debt, mixed evidence and escape clusters.")
