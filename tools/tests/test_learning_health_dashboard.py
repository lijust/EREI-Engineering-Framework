import importlib.util
import pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("learning_health_dashboard",ROOT/"learning_health_dashboard.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

pattern={
 "source":{"state_epoch_id":"EPOCH-023","state_trigger":{"level":"IMMEDIATE_REVIEW"}},
 "current_epoch":{
   "material_tasks":29,"rework_free_task_rate":0.2414,"verification_clean_task_rate":0.4138,
   "verification_escape_task_rate":0.069,"final_failed_task_rate":0.0,
   "rework_assessment_coverage_rate":0.75,"verification_assessment_coverage_rate":0.8,
   "verification_escape_assessment_coverage_rate":0.6,
   "rework_cycles_per_material_task":None,"verification_failures_per_material_task":None
 },
 "signals":[{"code":"REVIEW_DEBT","severity":"high","interpretation":"Review is overdue."}]
}
text=mod.render(pattern)
assert "EPOCH-023" in text
assert "0.069" in text
assert "assessment coverage: **0.75**" in text
assert "assessment coverage: **0.8**" in text
assert "assessment coverage: **0.6**" in text
assert "incomplete coverage is not full-cohort precision" in text
assert "iteration, not automatic task restart" in text
assert "REVIEW_DEBT" in text
print("PASS: learning health dashboard preserves metric semantics.")
