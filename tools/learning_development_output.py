#!/usr/bin/env python3
"""Validate human-authored Learning Development Outputs without third-party dependencies."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

OUTPUT_ID=re.compile(r"^LDO-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
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

def validate(value:dict)->dict:
    required={
      "schema_version","output_id","created_at","source","pattern","interpretation",
      "classification","development_route","evidence","expected_effect","success_metrics",
      "promotion_boundary"
    }
    optional={"notes"}
    if not isinstance(value,dict): raise OutputError("output must be an object")
    unknown=set(value)-required-optional
    missing=required-set(value)
    if missing: raise OutputError("missing fields: "+",".join(sorted(missing)))
    if unknown: raise OutputError("unknown fields: "+",".join(sorted(unknown)))
    if value["schema_version"]!=1: raise OutputError("schema_version must be 1")
    if not isinstance(value["output_id"],str) or not OUTPUT_ID.match(value["output_id"]): raise OutputError("invalid output_id")
    if not isinstance(value["created_at"],str) or "T" not in value["created_at"]: raise OutputError("invalid created_at")
    source=value["source"]
    if not isinstance(source,dict) or not source.get("project_repository") or not source.get("epoch_id"): raise OutputError("source project_repository and epoch_id required")
    pattern=value["pattern"]
    if not isinstance(pattern,dict) or not pattern.get("pattern_id") or not pattern.get("pattern_class") or not pattern.get("signal_summary"): raise OutputError("pattern fields required")
    if pattern.get("pattern_class") not in PATTERN_CLASSES: raise OutputError("invalid pattern_class")
    if not isinstance(value["interpretation"],str) or not value["interpretation"].strip(): raise OutputError("interpretation required")
    if value["classification"] not in CLASSES: raise OutputError("invalid classification")
    if value["development_route"] not in ROUTES: raise OutputError("invalid development_route")
    evidence=value["evidence"]
    if not isinstance(evidence,list) or not evidence or len(evidence)!=len(set(evidence)): raise OutputError("evidence must be non-empty and unique")
    if not isinstance(value["expected_effect"],str) or not value["expected_effect"].strip(): raise OutputError("expected_effect required")
    metrics=value["success_metrics"]
    if not isinstance(metrics,list) or not metrics: raise OutputError("success_metrics required")
    for metric in metrics:
        if not isinstance(metric,dict) or not metric.get("metric") or metric.get("direction") not in DIRECTIONS:
            raise OutputError("invalid success metric")
    if value["promotion_boundary"] not in BOUNDARIES: raise OutputError("invalid promotion_boundary")
    if value["classification"]=="FRAMEWORK_FEEDBACK" and value["development_route"] not in {"framework_feedback","evidence_collection"}:
        raise OutputError("FRAMEWORK_FEEDBACK must route to framework_feedback or evidence_collection before candidate promotion")
    if value["development_route"]=="framework_candidate" and value["promotion_boundary"]=="project_only":
        raise OutputError("framework_candidate cannot use project_only promotion boundary")
    return {"status":"VALID","output_id":value["output_id"]}

def main(argv=None)->int:
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    args=p.parse_args(argv)
    try:
        value=json.loads(Path(args.input).read_text(encoding="utf-8"))
        result=validate(value)
    except (OSError,json.JSONDecodeError,OutputError) as exc:
        print(json.dumps({"status":"INVALID","error":str(exc)},sort_keys=True));return 2
    print(json.dumps(result,sort_keys=True));return 0

if __name__=="__main__": raise SystemExit(main())
