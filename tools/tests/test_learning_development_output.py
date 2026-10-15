import importlib.util
import pathlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("learning_development_output",ROOT/"learning_development_output.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

value={
 "schema_version":1,
 "output_id":"LDO-20261015T180000Z-ABCDEF12",
 "created_at":"2026-10-15T18:00:00Z",
 "source":{"project_repository":"example/repo","epoch_id":"EPOCH-023","review_id":"ELR-X","framework_ref":"a"*40},
 "pattern":{"pattern_id":"LP-EXAMPLE-001","pattern_class":"verification_escape","signal_summary":"A prior proof was contradicted later."},
 "interpretation":"The escape indicates a reusable conformance gap, not a final product failure.",
 "classification":"FRAMEWORK_FEEDBACK",
 "development_route":"framework_feedback",
 "evidence":["task:1","review:1"],
 "expected_effect":"Reduce recurrence of the same verification escape.",
 "success_metrics":[{"metric":"verification_escape_task_rate","direction":"decrease","baseline":0.1,"target":0.0}],
 "promotion_boundary":"stable_review_required"
}
assert mod.validate(value)["status"]=="VALID"
bool_schema=dict(value);bool_schema["schema_version"]=True
try:
    mod.validate(bool_schema)
    raise AssertionError("expected boolean schema_version failure")
except mod.OutputError:
    pass
bad=dict(value);bad["development_route"]="framework_candidate"
try:
    mod.validate(bad)
    raise AssertionError("expected feedback route boundary failure")
except mod.OutputError:
    pass
bad_pattern=dict(value)
bad_pattern["pattern"]=dict(value["pattern"])
bad_pattern["pattern"]["pattern_class"]="NOT_IN_TAXONOMY"
try:
    mod.validate(bad_pattern)
    raise AssertionError("expected pattern taxonomy failure")
except mod.OutputError:
    pass
for mutate in (
    lambda x: x.__setitem__("created_at","T"),
    lambda x: x.__setitem__("source",{"project_repository":123,"epoch_id":"EPOCH-023"}),
    lambda x: x.__setitem__("source",{"project_repository":"example/repo","epoch_id":True}),
    lambda x: x.__setitem__("source",{"project_repository":"example/repo","epoch_id":"EPOCH-023","unknown":"x"}),
):
    candidate=dict(value)
    candidate["source"]=dict(value["source"])
    mutate(candidate)
    try:
        mod.validate(candidate)
        raise AssertionError("expected nested schema parity failure")
    except mod.OutputError:
        pass
bad_metric=dict(value)
bad_metric["success_metrics"]=[{"metric":"verification_escape_task_rate","direction":"decrease","unexpected":1}]
try:
    mod.validate(bad_metric)
    raise AssertionError("expected success metric additionalProperties failure")
except mod.OutputError:
    pass
print("PASS: Learning Development Output validation preserves schema, promotion boundary and taxonomy.")
