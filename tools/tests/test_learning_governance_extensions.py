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
 "epoch_id":"EPOCH-023",
 "trigger":{"level":"IMMEDIATE_REVIEW","reasons":["verification_escape_observed"]},
 "metrics_since_last_review":{"material_tasks":29}
}
assert gate.evaluate(state,None,datetime(2026,10,15,tzinfo=timezone.utc))["status"]=="BLOCK_IMMEDIATE_REVIEW_DEBT"
defer={
 "schema_version":1,"defer_id":"ELD-20261015T000000Z-ABCDEF12","epoch_id":"EPOCH-023",
 "recorded_at":"2026-10-15T00:00:00Z","expires_at":"2026-10-16T00:00:00Z",
 "baseline_material_tasks":28,"max_additional_material_tasks":2,
 "reason":"A bounded source-only repair is required before the review can close.",
 "reviewed_by_role":"chief-engineer","evidence":["review:pending"]
}
defer["fingerprint"]=gate.defer_fingerprint(defer)
assert gate.evaluate(state,defer,datetime(2026,10,15,12,tzinfo=timezone.utc))["status"]=="PASS_BOUNDED_REVIEW_DEFER"
bad=dict(defer);bad["max_additional_material_tasks"]=0
bad["fingerprint"]=gate.defer_fingerprint(bad)
try:
    gate.validate_defer(bad,state,datetime(2026,10,15,12,tzinfo=timezone.utc))
    raise AssertionError("expected bounded allowance failure")
except gate.ReviewDebtError:
    pass

before={"current_epoch":{
 "material_tasks":10,"risks":{"L3":10},"outcomes":{"verified_success":8,"success_with_deferred":2},
 "verification_escape_task_rate":0.2,"final_failed_task_rate":0.1,
 "rework_rate":0.7,"rework_free_task_rate":0.3,
 "verification_failure_rate":0.6,"verification_clean_task_rate":0.4,
 "success_with_deferred_rate":0.2,"verified_success_rate":0.8
}}
after={"current_epoch":{
 "material_tasks":10,"risks":{"L3":9,"L2":1},"outcomes":{"verified_success":9,"success_with_deferred":1},
 "verification_escape_task_rate":0.0,"final_failed_task_rate":0.0,
 "rework_rate":0.6,"rework_free_task_rate":0.4,
 "verification_failure_rate":0.7,"verification_clean_task_rate":0.3,
 "success_with_deferred_rate":0.1,"verified_success_rate":0.9
}}
report=eff.compare(before,after)
assert report["status"]=="COMPARABLE_DIRECTIONAL_ONLY"
assert report["causation"]=="NOT_ESTABLISHED"
assert report["primary_quality_signals"]["verification_escape_task_rate"]=="improved"
assert report["metric_deltas"]["verification_failure_rate"]["delta"]==0.1
print("PASS: review-debt and effectiveness semantics are fail-closed and causation-safe.")
