import importlib.util
import pathlib
from datetime import datetime, timezone

ROOT=pathlib.Path(__file__).resolve().parents[1]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

gate=load("learning_review_debt_gate","learning_review_debt_gate.py")
eff=load("learning_effectiveness","learning_effectiveness.py")

state={
 "schema_version":1,
 "epoch_id":"EPOCH-023",
 "updated_at":"2026-10-15T00:00:00Z",
 "last_review_id":"ELR-20261005T143400Z-A15C4062",
 "last_review_at":"2026-10-05T14:34:00Z",
 "event_cutoff":126,
 "total_events":155,
 "metrics_since_last_review":{
   "tasks":29,"material_tasks":29,"verified_successes":11,"blocked_tasks":0,"failed_tasks":0,
   "rework_tasks":22,"total_rework_cycles":47,"verification_failure_tasks":17,
   "verification_failures":38,"verification_escapes":2,"framework_feedback_tasks":0,
   "manual_workarounds":0,"context_gaps":0,"unexpected_scope_growth_tasks":0,
   "security_or_data_critical_events":0,"max_feedback_fingerprint_occurrences":0,
   "rework_rate":0.7586,"verification_failure_rate":0.5862
 },
 "trigger":{"level":"IMMEDIATE_REVIEW","reasons":["verification_escape_observed"]}
}
assert gate.evaluate(state,None,datetime(2026,10,15,tzinfo=timezone.utc))["status"]=="BLOCK_IMMEDIATE_REVIEW_DEBT"
try:
    gate.evaluate({},None,datetime(2026,10,15,tzinfo=timezone.utc))
    raise AssertionError("expected malformed state failure")
except gate.ReviewDebtError:
    pass
bool_state=dict(state)
bool_state["schema_version"]=True
try:
    gate.evaluate(bool_state,None,datetime(2026,10,15,tzinfo=timezone.utc))
    raise AssertionError("expected boolean schema version failure")
except gate.ReviewDebtError:
    pass
truncated={
 "schema_version":2,"epoch_id":"EPOCH-garbage","updated_at":"2026-10-15T00:00:00Z",
 "last_review_id":None,"last_review_at":None,"legacy_event_cutoff":0,"reviewed_occurrence_count":0,
 "total_events":0,"metrics_since_last_review":{"material_tasks":0},
 "trigger":{"level":"LEARNING_HEALTHY","reasons":[]}
}
try:
    gate.evaluate(truncated,None,datetime(2026,10,15,tzinfo=timezone.utc))
    raise AssertionError("expected schema-invalid state failure")
except gate.ReviewDebtError:
    pass
defer={
 "schema_version":1,"defer_id":"ELD-20261015T000000Z-ABCDEF12","epoch_id":"EPOCH-023",
 "recorded_at":"2026-10-15T00:00:00Z","expires_at":"2026-10-16T00:00:00Z",
 "baseline_material_tasks":28,"max_additional_material_tasks":2,
 "reason":"A bounded source-only repair is required before the review can close.",
 "reviewed_by_role":"chief-engineer","evidence":["review:pending"]
}
defer["fingerprint"]=gate.defer_fingerprint(defer)
assert gate.evaluate(state,defer,datetime(2026,10,15,12,tzinfo=timezone.utc))["status"]=="PASS_BOUNDED_REVIEW_DEFER"
critical_state={
    **state,
    "metrics_since_last_review":{
        **state["metrics_since_last_review"],
        "security_or_data_critical_events":1,
    },
    "trigger":{
        "level":"IMMEDIATE_REVIEW",
        "reasons":["security_or_data_critical_event_observed"],
    },
}
critical_result=gate.evaluate(critical_state,defer,datetime(2026,10,15,12,tzinfo=timezone.utc))
assert critical_result["status"]=="BLOCK_CRITICAL_SECURITY_OR_DATA_REVIEW"
assert critical_result["critical_events"]==1
bad=dict(defer);bad["max_additional_material_tasks"]=0
bad["fingerprint"]=gate.defer_fingerprint(bad)
try:
    gate.validate_defer(bad,state,datetime(2026,10,15,12,tzinfo=timezone.utc))
    raise AssertionError("expected bounded allowance failure")
except gate.ReviewDebtError:
    pass
bad_timestamp=dict(defer)
bad_timestamp["recorded_at"]="2026-10-15 00:00:00+00:00"
bad_timestamp["fingerprint"]=gate.defer_fingerprint(bad_timestamp)
try:
    gate.validate_defer(bad_timestamp,state,datetime(2026,10,15,12,tzinfo=timezone.utc))
    raise AssertionError("expected non-RFC3339 timestamp failure")
except gate.ReviewDebtError:
    pass
bad_state_timestamp=dict(state)
bad_state_timestamp["updated_at"]="2026-10-15 00:00:00+00:00"
try:
    gate.evaluate(bad_state_timestamp,None,datetime(2026,10,15,12,tzinfo=timezone.utc))
    raise AssertionError("expected non-RFC3339 state timestamp failure")
except gate.ReviewDebtError:
    pass
future=dict(defer)
future["recorded_at"]="2026-10-17T00:00:00Z"
future["expires_at"]="2026-10-18T00:00:00Z"
future["fingerprint"]=gate.defer_fingerprint(future)
try:
    gate.validate_defer(future,state,datetime(2026,10,15,12,tzinfo=timezone.utc))
    raise AssertionError("expected future-dated defer failure")
except gate.ReviewDebtError:
    pass
bad_evidence=dict(defer)
bad_evidence["evidence"]=[1]
bad_evidence["fingerprint"]=gate.defer_fingerprint(bad_evidence)
try:
    gate.validate_defer(bad_evidence,state,datetime(2026,10,15,12,tzinfo=timezone.utc))
    raise AssertionError("expected non-string defer evidence failure")
except gate.ReviewDebtError:
    pass
bool_budget=dict(defer)
bool_budget["max_additional_material_tasks"]=True
bool_budget["fingerprint"]=gate.defer_fingerprint(bool_budget)
try:
    gate.validate_defer(bool_budget,state,datetime(2026,10,15,12,tzinfo=timezone.utc))
    raise AssertionError("expected boolean defer budget failure")
except gate.ReviewDebtError:
    pass
bad_id=dict(defer)
bad_id["defer_id"]="ELD-NOT-VALID"
bad_id["fingerprint"]=gate.defer_fingerprint(bad_id)
try:
    gate.validate_defer(bad_id,state,datetime(2026,10,15,12,tzinfo=timezone.utc))
    raise AssertionError("expected invalid defer id failure")
except gate.ReviewDebtError:
    pass
expires_now=dict(defer)
expires_now["expires_at"]="2026-10-15T12:00:00Z"
expires_now["fingerprint"]=gate.defer_fingerprint(expires_now)
try:
    gate.validate_defer(expires_now,state,datetime(2026,10,15,12,tzinfo=timezone.utc))
    raise AssertionError("expected expiry-at-now failure")
except gate.ReviewDebtError:
    pass

before={"current_epoch":{
 "material_tasks":10,"risks":{"L3":10},"workflows":{"feature-development":10},"outcomes":{"verified_success":8,"success_with_deferred":2},
 "verification_escape_task_rate":0.2,"final_failed_task_rate":0.1,
 "rework_rate":0.7,"rework_free_task_rate":0.3,
 "verification_failure_rate":0.6,"verification_clean_task_rate":0.4,
 "success_with_deferred_rate":0.2,"verified_success_rate":0.8,
 "rework_assessment_coverage_rate":1.0,"verification_assessment_coverage_rate":1.0,
 "verification_escape_assessment_coverage_rate":1.0
}}
after={"current_epoch":{
 "material_tasks":10,"risks":{"L3":9,"L2":1},"workflows":{"feature-development":9,"bug-fix":1},"outcomes":{"verified_success":9,"success_with_deferred":1},
 "verification_escape_task_rate":0.0,"final_failed_task_rate":0.0,
 "rework_rate":0.6,"rework_free_task_rate":0.4,
 "verification_failure_rate":0.7,"verification_clean_task_rate":0.3,
 "success_with_deferred_rate":0.1,"verified_success_rate":0.9,
 "rework_assessment_coverage_rate":1.0,"verification_assessment_coverage_rate":1.0,
 "verification_escape_assessment_coverage_rate":1.0
}}
report=eff.compare(before,after)
assert report["status"]=="COMPARABLE_DIRECTIONAL_ONLY"
assert report["causation"]=="NOT_ESTABLISHED"
assert report["primary_quality_signals"]["verification_escape_task_rate"]=="improved"
assert report["metric_deltas"]["verification_failure_rate"]["delta"]==0.1
changed_workflow={"current_epoch":dict(after["current_epoch"])}
changed_workflow["current_epoch"]["workflows"]={"security-critical-change":10}
workflow_report=eff.compare(before,changed_workflow)
assert workflow_report["status"]=="NEEDS_COMPARABILITY_REVIEW"
assert "workflow_mix_changed_materially" in workflow_report["comparability"]["reasons"]
coverage_shift={"current_epoch":dict(after["current_epoch"])}
coverage_shift["current_epoch"]["verification_escape_assessment_coverage_rate"]=0.5
coverage_report=eff.compare(before,coverage_shift)
assert coverage_report["status"]=="NEEDS_COMPARABILITY_REVIEW"
assert coverage_report["primary_quality_signals"]["verification_escape_task_rate"]=="not_comparable"
assert "verification_escape_assessment_coverage_rate_below_80_percent" in coverage_report["comparability"]["reasons"]
assert "verification_escape_assessment_coverage_rate_changed_materially" in coverage_report["comparability"]["reasons"]
print("PASS: review-debt and effectiveness semantics are fail-closed and causation-safe.")
