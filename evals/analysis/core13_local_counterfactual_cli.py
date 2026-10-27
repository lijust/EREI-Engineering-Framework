"""Owner-local, read-only counterfactual classification against frozen PR98.

The hypothetical replay result is an analysis metric, NEVER a model PASS.
Neither the frozen scorer, model receipt nor evidence is rewritten.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
from pathlib import Path

from evals.analysis.core13_counterfactual_state import classify

SHA = "31d4e518b9e71a9585df9097e7ca07a7e25af916"
TREE = "913c6a0daaa7a6efa7d6d2148aa0294812fab360"
PATHS = ("evals/cases/task-learning-review.eval.json",
         "evals/cases/candidate-capability-activation.eval.json")
VARIANTS = {
    "core13_learning_action_union_schema_v4": "V4",
    "core13_learning_policy_state_replay_v5": "V5",
}
SCORING = {
    "EXPERIMENTAL_MODEL_RESPONSE_SCORED_PASS_UNVERIFIED": True,
    "EXPERIMENTAL_MODEL_RESPONSE_SCORED_FAIL_UNVERIFIED": False,
}


def _git(root, *args):
    env = {k:v for k,v in os.environ.items() if not k.upper().startswith("GIT_")}
    return subprocess.check_output(
        ["git","--no-replace-objects","-C",str(root),*args],
        env=env,stdin=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
        timeout=10,
    )


def load_frozen(root):
    root = root.resolve(strict=True)
    if (_git(root,"rev-parse","HEAD").decode().strip()!=SHA or
        _git(root,"rev-parse","HEAD^{tree}").decode().strip()!=TREE or
        _git(root,"status","--porcelain","--untracked-files=all")):
        raise ValueError("frozen source not pristine")
    actual = (root / "evals" / "runner.py")
    blob = _git(root,"show",f"{SHA}:evals/runner.py")
    if (actual.is_symlink() or not actual.is_file() or
        actual.read_bytes().replace(b"\r\n",b"\n") != blob):
        raise ValueError("frozen runner differs")
    scope = {"__name__":"immutable_pr98_scoring",
             "__file__":str(actual)}
    exec(compile(blob,str(actual),"exec"),scope)
    cases = {}
    for path in PATHS:
        data = json.loads(_git(root,"show",f"{SHA}:{path}"))
        for case in data["cases"]:
            if case["id"] in cases:
                raise ValueError("duplicate frozen case id")
            cases[case["id"]] = case
    return scope["score_simulation"],scope["simulate_actions"],cases


def strict_json(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1000000:
        raise ValueError("invalid receipt file")
    def pairs(xs):
        result = {}
        for k,v in xs:
            if k in result:
                raise ValueError("duplicate JSON key")
            result[k] = v
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))


def ids(raw):
    items = []
    for part in raw.split(","):
        part = part.strip()
        if re.fullmatch(r"[1-9]\d{0,5}-[1-9]\d{0,5}",part):
            start,end = map(int,part.split("-"))
            if end < start or end-start>130:
                raise ValueError("invalid issue range")
            items.extend(range(start,end+1))
        elif re.fullmatch(r"[1-9]\d{0,5}",part):
            items.append(int(part))
        else:
            raise ValueError("invalid issue syntax")
    if len(items)>130 or len(set(items))!=len(items):
        raise ValueError("duplicate or excessive issue ids")
    return items


def case_audit(folder, case_lookup, scorer, replay):
    verdict = strict_json(folder/"verdict.json")
    case_id = verdict.get("case_id")
    variant = VARIANTS.get(verdict.get("experiment"))
    observed = SCORING.get(verdict.get("status"))
    if (not variant or case_id not in case_lookup or
        type(verdict.get("passed")) is not bool or observed is None or
        verdict["passed"] is not observed or
        verdict.get("independently_accepted") is not False or
        verdict.get("stable_ready") is not False):
        raise ValueError("receipt identity or admission mismatch")
    normalized = strict_json(folder/"adapter-normalized.json")
    request = strict_json(folder/"blind-request.json")
    fixture = case_lookup[case_id]
    # Strict JSON textual identity keeps booleans distinct from integers.
    signature = lambda x: json.dumps(x, sort_keys=True, separators=(",",":"),
                                     ensure_ascii=False,allow_nan=False)
    if signature(request["input"]) != signature(fixture["input"]):
        raise ValueError("frozen input mismatch")
    expectations = fixture["expectations"]
    if len(expectations)!=1 or expectations[0]["type"]!="behavioral_simulation":
        raise ValueError("unsupported frozen scorer shape")
    assessed = classify(expectations[0],normalized,fixture["input"],
                        score_fn=scorer,replay_fn=replay)
    if assessed["raw_model_pass"] is not observed:
        raise ValueError("raw scorer diverges from historical verdict")
    return {"case_id":case_id,"variant":variant,
            "raw_model_pass":observed,
            "replay_counterfactual_pass":assessed["counterfactual_replay_pass"],
            "failure_class":assessed["failure_class"],
            "difference_fields":assessed["different_state_fields"],
            "independently_accepted":False,"stable_ready":False}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frozen-target-root",required=True,type=Path)
    p.add_argument("--evidence-root",required=True,type=Path)
    p.add_argument("--issues",default="5-32")
    args=p.parse_args(argv)
    try:
        scorer,replay,cases=load_frozen(args.frozen_target_root)
        root=args.evidence_root.resolve(strict=True)
        results=[]
        for n in ids(args.issues):
            folder=root / ("github-issue-%07d"%n)
            if not folder.is_dir() or folder.is_symlink():
                results.append({"issue":n,"status":"MISSING"})
                continue
            try:
                row=case_audit(folder,cases,scorer,replay)
                results.append({"issue":n,"status":"VERIFIED",**row})
            except (OSError,ValueError,KeyError,TypeError,IndexError):
                results.append({"issue":n,"status":"EVIDENCE_INTEGRITY_BLOCKED"})
        print(json.dumps({"kind":"CORE13_LOCAL_COUNTERFACTUAL_ANALYSIS",
                          "frozen_target_head_verified":True,
                          "scorer_changed":False,"network_calls":0,"model_calls":0,
                          "counterfactual_is_not_model_pass":True,
                          "results":results},sort_keys=True))
        return 0
    except Exception:
        print('{"kind":"CORE13_LOCAL_COUNTERFACTUAL_ANALYSIS","status":"AUDIT_BLOCKED","network_calls":0,"model_calls":0}')
        return 2

if __name__=="__main__":
    raise SystemExit(main())
