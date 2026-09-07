#!/usr/bin/env python3
"""Derive current VNext Stable readiness from live machine-readable assurance sources."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from . import assurance_enforcement, exact_target_evidence, prospective_cycle_status
except ImportError:
    import assurance_enforcement
    import exact_target_evidence
    import prospective_cycle_status

SHA40_RE = re.compile(r"^[a-f0-9]{40}$")


class StableReadinessError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StableReadinessError(f"unable to load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise StableReadinessError(f"{path} must contain a JSON object")
    return value


def _load_runner(repo_root: Path):
    path = repo_root / "evals" / "runner.py"
    spec = importlib.util.spec_from_file_location("erei_readiness_eval_runner", path)
    if spec is None or spec.loader is None:
        raise StableReadinessError("unable to load eval runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git_head(repo_root: Path) -> str:
    try:
        value = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True, stderr=subprocess.STDOUT
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise StableReadinessError(f"unable to resolve git HEAD: {exc}") from exc
    if not SHA40_RE.fullmatch(value):
        raise StableReadinessError("git HEAD is not an exact 40-character commit")
    return value


def eval_gate(repo_root: Path, head_ref: str) -> dict[str, Any]:
    runner = _load_runner(repo_root)
    evidence = runner.validate_execution_evidence(_load_json(repo_root / "evals" / "EXECUTION_EVIDENCE.json"))
    expected = runner._expected_cases([str(repo_root / "evals" / "cases")])
    observed = {(item["suite_id"], item["case_id"]): item for item in evidence["executions"]}
    schema_version = evidence["schema_version"]
    exact_rows = {
        key: item for key, item in observed.items()
        if runner.ASSURANCE_LEVELS[runner.execution_assurance_level(item, schema_version)]
        >= runner.ASSURANCE_LEVELS["exact_target_runtime"]
    }
    passing = {key: item for key, item in exact_rows.items() if item["status"] == "pass"}
    missing = expected - set(observed)
    lower = (expected & set(observed)) - set(exact_rows)
    nonpassing = {key for key in expected & set(exact_rows) if exact_rows[key]["status"] != "pass"}
    unexpected = set(observed) - expected
    binding_errors: list[str] = []
    bound = 0
    if schema_version == 2:
        for key, item in passing.items():
            try:
                exact_target_evidence.validate_binding(repo_root, evidence["framework_revision"], item)
                bound += 1
            except exact_target_evidence.ExactTargetEvidenceError as exc:
                binding_errors.append(f"{key[0]}/{key[1]}: {exc}")
    revision_matches_head = evidence["framework_revision"] == head_ref
    complete = (
        schema_version == 2
        and revision_matches_head
        and not missing
        and not lower
        and not nonpassing
        and not unexpected
        and len(passing) == len(expected)
        and bound == len(expected)
        and not binding_errors
    )
    return {
        "status": "pass" if complete else "blocked",
        "framework_revision": evidence["framework_revision"],
        "head_revision": head_ref,
        "revision_matches_head": revision_matches_head,
        "evidence_schema_version": schema_version,
        "expected_cases": len(expected),
        "evidence_records": len(observed),
        "passing_exact_target": len(passing & expected.keys()) if False else len(set(passing) & expected),
        "bound_exact_target": bound,
        "missing_count": len(missing),
        "lower_assurance_count": len(lower),
        "nonpassing_count": len(nonpassing),
        "unexpected_count": len(unexpected),
        "binding_error_count": len(binding_errors),
        "binding_errors": binding_errors,
    }


def approval_gate(repo_root: Path, head_ref: str, preapproval_ready: bool) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    for path in sorted((repo_root / "releases").glob("*.json")):
        value = _load_json(path)
        if (
            value.get("status") == "stable"
            and value.get("assurance_contract_version", 0) >= 2
            and value.get("framework_ref") == head_ref
        ):
            matches.append(value)
    if matches:
        if len(matches) != 1:
            return {"status": "blocked", "reason": "multiple V2 Stable manifests target current HEAD"}
        manifest = matches[0]
        approval = manifest.get("approval_ref")
        security = manifest.get("security_review_ref")
        valid = isinstance(approval, str) and bool(SHA40_RE.fullmatch(approval)) and isinstance(security, str) and bool(SHA40_RE.fullmatch(security))
        return {
            "status": "pass" if valid else "blocked",
            "approval_ref_bound": isinstance(approval, str) and bool(SHA40_RE.fullmatch(approval)),
            "security_review_ref_bound": isinstance(security, str) and bool(SHA40_RE.fullmatch(security)),
        }
    return {
        "status": "pending" if preapproval_ready else "deferred",
        "reason": "final immutable architecture/security approval refs are bound only after all pre-approval gates pass",
    }


def derive_readiness(*, cycle_pass: bool, eval_pass: bool, enforcement_pass: bool, approvals_pass: bool) -> dict[str, Any]:
    preapproval = cycle_pass and eval_pass and enforcement_pass
    blockers: list[str] = []
    if not cycle_pass:
        blockers.append("prospective_cycle_incomplete")
    if not eval_pass:
        blockers.append("exact_target_runtime_evidence_incomplete")
    if not enforcement_pass:
        blockers.append("release_enforcement_not_satisfied")
    if not approvals_pass:
        blockers.append("final_architecture_security_approvals_not_bound")
    return {
        "ready_for_final_approvals": preapproval,
        "stable_ready": preapproval and approvals_pass,
        "blockers": blockers,
    }


def report(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    head_ref = _git_head(repo_root)
    try:
        cycle = prospective_cycle_status.load_and_validate(repo_root / "learning" / "PROSPECTIVE_CYCLE_STATUS.json")
    except prospective_cycle_status.CycleStatusError as exc:
        raise StableReadinessError(f"invalid prospective cycle status: {exc}") from exc
    try:
        enforcement = assurance_enforcement.load_and_validate(repo_root / "security" / "ASSURANCE_ENFORCEMENT.json")
    except assurance_enforcement.EnforcementError as exc:
        raise StableReadinessError(f"invalid assurance enforcement: {exc}") from exc
    eval_result = eval_gate(repo_root, head_ref)
    cycle_pass = cycle["status"] == "complete"
    eval_pass = eval_result["status"] == "pass"
    enforcement_pass = enforcement["stable_enforcement_satisfied"]
    preapproval = cycle_pass and eval_pass and enforcement_pass
    approvals = approval_gate(repo_root, head_ref, preapproval)
    derived = derive_readiness(
        cycle_pass=cycle_pass,
        eval_pass=eval_pass,
        enforcement_pass=enforcement_pass,
        approvals_pass=approvals["status"] == "pass",
    )
    return {
        "framework_head": head_ref,
        "gates": {
            "prospective_cycle": {"status": "pass" if cycle_pass else "blocked", "cycle_id": cycle["cycle_id"], "completed_steps": cycle["completed_steps"]},
            "exact_target_runtime": eval_result,
            "release_enforcement": {"status": "pass" if enforcement_pass else "blocked", **enforcement},
            "final_architecture_security_approvals": approvals,
        },
        **derived,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--require-ready-for-final-approvals", action="store_true")
    parser.add_argument("--require-stable-ready", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = report(Path(args.repo_root))
    except StableReadinessError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    if args.require_stable_ready and not result["stable_ready"]:
        return 1
    if args.require_ready_for_final_approvals and not result["ready_for_final_approvals"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
