#!/usr/bin/env python3
"""Validate human-authored Learning Development Outputs without third-party dependencies."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

OUTPUT_ID=re.compile(r"^LDO-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
RFC3339=re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})$")
CLASSES={
 "HEALTHY_PATTERN","PROJECT_LOCAL_ACTION","FRAMEWORK_FEEDBACK",
 "MEASUREMENT_ADJUSTMENT","NEEDS_MORE_EVIDENCE","CRITICAL_FOLLOWUP"
}
ROUTES={
 "no_change","project_change","framework_feedback","framework_candidate",
 "measurement_change","workflow_change","tooling_change","specialist_review","evidence_collection"
}
BOUNDARIES={"project_only","candidate_only","stable_review_required","cross_project_evidence_required"}
DIRECTIONS={"increase","decrease","hold","observe"}
PATTERN_CLASSES={
 "healthy_assurance_catch","verification_escape","execution_environment_conformance",
 "provider_runtime_conformance","exclusive_claim_concurrency","stale_contract_or_reference",
 "identity_or_authority_binding","measurement_model_gap","context_routing_gap",
 "review_debt","project_local_defect","unknown"
}

class OutputError(RuntimeError): pass

def _exact(value:dict,required:set[str],allowed:set[str],label:str)->None:
    if not isinstance(value,dict): raise OutputError(f"{label} must be an object")
    missing=required-set(value);unknown=set(value)-allowed
    if missing: raise OutputError(f"{label} missing fields: "+",".join(sorted(missing)))
    if unknown: raise OutputError(f"{label} unknown fields: "+",".join(sorted(unknown)))

def _text(value,label,*,nonempty=True)->None:
    if not isinstance(value,str) or (nonempty and not value.strip()): raise OutputError(f"{label} must be a string"+(" and non-empty" if nonempty else ""))

def _datetime(value,label)->None:
    _text(value,label)
    if not RFC3339.fullmatch(value): raise OutputError(f"{label} must be RFC3339 with timezone")
    try: parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc: raise OutputError(f"{label} is invalid") from exc
    if parsed.tzinfo is None: raise OutputError(f"{label} must include timezone")

def _scalar_or_null(value,label)->None:
    if value is None:return
    if isinstance(value,bool) or not isinstance(value,(str,int,float)): raise OutputError(f"{label} must be string, number or null")

def validate(value:dict)->dict:
    required={
      "schema_version","output_id","created_at","source","pattern","interpretation",
      "classification","development_route","evidence","expected_effect","success_metrics",
      "promotion_boundary"
    }
    _exact(value,required,required|{"notes"},"output")
    if type(value["schema_version"]) is not int or value["schema_version"]!=1: raise OutputError("schema_version must be integer 1")
    if not isinstance(value["output_id"],str) or not OUTPUT_ID.fullmatch(value["output_id"]): raise OutputError("invalid output_id")
    _datetime(value["created_at"],"created_at")

    source=value["source"]
    _exact(source,{"project_repository","epoch_id"},{"project_repository","epoch_id","review_id","framework_ref"},"source")
    _text(source["project_repository"],"source.project_repository")
    _text(source["epoch_id"],"source.epoch_id")
    for key in ("review_id","framework_ref"):
        if key in source:_text(source[key],f"source.{key}")

    pattern=value["pattern"]
    _exact(pattern,{"pattern_id","pattern_class","signal_summary"},{"pattern_id","pattern_class","signal_summary"},"pattern")
    _text(pattern["pattern_id"],"pattern.pattern_id")
    if pattern["pattern_class"] not in PATTERN_CLASSES: raise OutputError("invalid pattern_class")
    _text(pattern["signal_summary"],"pattern.signal_summary")

    _text(value["interpretation"],"interpretation")
    if value["classification"] not in CLASSES: raise OutputError("invalid classification")
    if value["development_route"] not in ROUTES: raise OutputError("invalid development_route")
    evidence=value["evidence"]
    if not isinstance(evidence,list) or not evidence: raise OutputError("evidence must be non-empty")
    for item in evidence:_text(item,"evidence item")
    if len(evidence)!=len(set(evidence)): raise OutputError("evidence must be unique")
    _text(value["expected_effect"],"expected_effect")

    metrics=value["success_metrics"]
    if not isinstance(metrics,list) or not metrics: raise OutputError("success_metrics required")
    for index,metric in enumerate(metrics):
        _exact(metric,{"metric","direction"},{"metric","direction","baseline","target","notes"},f"success_metrics[{index}]")
        _text(metric["metric"],f"success_metrics[{index}].metric")
        if metric["direction"] not in DIRECTIONS: raise OutputError("invalid success metric direction")
        for key in ("baseline","target"):
            if key in metric:_scalar_or_null(metric[key],f"success_metrics[{index}].{key}")
        if "notes" in metric:_text(metric["notes"],f"success_metrics[{index}].notes",nonempty=False)

    if value["promotion_boundary"] not in BOUNDARIES: raise OutputError("invalid promotion_boundary")
    if "notes" in value:_text(value["notes"],"notes",nonempty=False)
    if value["classification"]=="FRAMEWORK_FEEDBACK" and value["development_route"] not in {"framework_feedback","evidence_collection"}:
        raise OutputError("FRAMEWORK_FEEDBACK must route to framework_feedback or evidence_collection before candidate promotion")
    if value["development_route"]=="framework_candidate" and value["promotion_boundary"]=="project_only":
        raise OutputError("framework_candidate cannot use project_only promotion boundary")
    return {"status":"VALID","output_id":value["output_id"]}

def main(argv=None)->int:
    p=argparse.ArgumentParser();p.add_argument("--input",required=True);args=p.parse_args(argv)
    try:
        value=json.loads(Path(args.input).read_text(encoding="utf-8"));result=validate(value)
    except (OSError,json.JSONDecodeError,OutputError) as exc:
        print(json.dumps({"status":"INVALID","error":str(exc)},sort_keys=True));return 2
    print(json.dumps(result,sort_keys=True));return 0

if __name__=="__main__": raise SystemExit(main())
