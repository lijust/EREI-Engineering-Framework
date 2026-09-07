#!/usr/bin/env python3
"""Derive current VNext Stable readiness from live machine-readable assurance sources."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from . import assurance_enforcement, exact_target_evidence, prospective_cycle_status, release_target
except ImportError:
    import assurance_enforcement
    import exact_target_evidence
    import prospective_cycle_status
    import release_target

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


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA40_RE.fullmatch(value):
        raise StableReadinessError(f"{label} must be an exact 40-character commit")
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
    return _sha(value, "git HEAD")


def _assert_git_commit(repo_root: Path, revision: str, label: str) -> str:
    revision = _sha(revision, label)
    try:
        subprocess.check_output(
            ["git", "cat-file", "-e", f"{revision}^{{commit}}"],
            cwd=repo_root,
            text=True,
            stderr=subprocess.STDOUT,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise StableReadinessError(f"{label} does not resolve to a fetched git commit: {revision}") from exc
    return revision


def _event_target_revision(event_path: Path) -> str | None:
    try:
        event = json.loads(event_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StableReadinessError(f"unable to read GitHub event payload {event_path}: {exc}") from exc
    if not isinstance(event, dict):
        raise StableReadinessError("GitHub event payload must be an object")
    pull_request = event.get("pull_request")
    if pull_request is None:
        return None
    if not isinstance(pull_request, dict):
        raise StableReadinessError("GitHub pull_request payload must be an object")
    head = pull_request.get("head")
    if not isinstance(head, dict):
        raise StableReadinessError("GitHub pull_request.head payload must be an object")
    return _sha(head.get("sha"), "GitHub pull request head.sha")


def _target_revision(repo_root: Path, explicit: str | None = None) -> str:
    frozen_path = repo_root / release_target.DEFAULT_TARGET
    if frozen_path.exists():
        try:
            manifest = release_target.load_and_validate_target(repo_root, release_target.DEFAULT_TARGET)
        except release_target.ReleaseTargetError as exc:
            raise StableReadinessError(f"invalid frozen release target: {exc}") from exc
        frozen_ref = manifest["framework_ref"]
        if explicit is not None and explicit != frozen_ref:
            raise StableReadinessError(
                f"--target-ref {explicit} cannot override frozen release target {frozen_ref}"
            )
        return frozen_ref
    if explicit is not None:
        return _assert_git_commit(repo_root, explicit, "target_ref")
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path:
        event_target = _event_target_revision(Path(event_path))
        if event_target is not None:
            return _assert_git_commit(repo_root, event_target, "GitHub pull request head.sha")
    return _git_head(repo_root)


def _evaluate_evidence_file(repo_root: Path, runner, expected: set[tuple[str, str]], path: Path, target_ref: str) -> dict[str, Any]:
    evidence = runner.validate_execution_evidence(_load_json(path))
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
    revision_matches_target = evidence["framework_revision"] == target_ref
    complete = (
        schema_version == 2
        and revision_matches_target
        and not missing
        and not lower
        and not nonpassing
        and not unexpected
        and len(passing) == len(expected)
        and bound == len(expected)
        and not binding_errors
    )
    return {
        "evidence_path": path.relative_to(repo_root).as_posix(),
        "complete": complete,
        "framework_revision": evidence["framework_revision"],
        "revision_matches_target": revision_matches_target,
        "evidence_schema_version": schema_version,
        "expected_cases": len(expected),
        "evidence_records": len(observed),
        "passing_exact_target": len(set(passing) & expected),
        "bound_exact_target": bound,
        "missing_count": len(missing),
        "lower_assurance_count": len(lower),
        "nonpassing_count": len(nonpassing),
        "unexpected_count": len(unexpected),
        "binding_error_count": len(binding_errors),
        "binding_errors": binding_errors,
    }


def eval_gate(repo_root: Path, target_ref: str) -> dict[str, Any]:
    runner = _load_runner(repo_root)
    expected = runner._expected_cases([str(repo_root / "evals" / "cases")])
    paths = sorted((repo_root / "evals").glob("EXECUTION_EVIDENCE*.json"))
    if not paths:
        raise StableReadinessError("no execution-evidence files found")
    reports = [_evaluate_evidence_file(repo_root, runner, expected, path, target_ref) for path in paths]
    complete = [item for item in reports if item["complete"]]
    return {
        "status": "pass" if len(complete) == 1 else "blocked",
        "target_framework_revision": target_ref,
        "evidence_file_count": len(reports),
        "complete_evidence_file_count": len(complete),
        "selected_evidence_path": complete[0]["evidence_path"] if len(complete) == 1 else None,
        "evidence_reports": reports,
    }


def approval_gate(repo_root: Path, target_ref: str, preapproval_ready: bool) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    for path in sorted((repo_root / "releases").glob("*.json")):
        value = _load_json(path)
        if (
            value.get("status") == "stable"
            and value.get("assurance_contract_version", 0) >= 2
            and value.get("framework_ref") == target_ref
        ):
            matches.append(value)
    if matches:
        if len(matches) != 1:
            return {"status": "blocked", "reason": "multiple V2 Stable manifests target selected Framework revision"}
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


def report(repo_root: Path, *, target_ref: str | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    checkout_ref = _git_head(repo_root)
    selected_target = _target_revision(repo_root, target_ref)
    try:
        cycle = prospective_cycle_status.load_and_validate(repo_root / "learning" / "PROSPECTIVE_CYCLE_STATUS.json")
    except prospective_cycle_status.CycleStatusError as exc:
        raise StableReadinessError(f"invalid prospective cycle status: {exc}") from exc
    try:
        enforcement = assurance_enforcement.load_and_validate(repo_root / "security" / "ASSURANCE_ENFORCEMENT.json")
    except assurance_enforcement.EnforcementError as exc:
        raise StableReadinessError(f"invalid assurance enforcement: {exc}") from exc
    eval_result = eval_gate(repo_root, selected_target)
    cycle_pass = cycle["status"] == "complete"
    eval_pass = eval_result["status"] == "pass"
    enforcement_pass = enforcement["stable_enforcement_satisfied"]
    preapproval = cycle_pass and eval_pass and enforcement_pass
    approvals = approval_gate(repo_root, selected_target, preapproval)
    derived = derive_readiness(
        cycle_pass=cycle_pass,
        eval_pass=eval_pass,
        enforcement_pass=enforcement_pass,
        approvals_pass=approvals["status"] == "pass",
    )
    return {
        "checkout_revision": checkout_ref,
        "target_framework_revision": selected_target,
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
    parser.add_argument("--target-ref")
    parser.add_argument("--require-ready-for-final-approvals", action="store_true")
    parser.add_argument("--require-stable-ready", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = report(Path(args.repo_root), target_ref=args.target_ref)
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
