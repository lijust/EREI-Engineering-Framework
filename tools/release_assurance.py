#!/usr/bin/env python3
"""Validate immutable Framework release manifests and V2 Stable assurance gates."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

try:
    from . import assurance_enforcement, exact_target_evidence, release_approval, release_target
except ImportError:
    import assurance_enforcement
    import exact_target_evidence
    import release_approval
    import release_target

SHA40_RE = re.compile(r"^[a-f0-9]{40}$")


class ReleaseError(RuntimeError):
    pass


def _text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReleaseError(f"{label} must be a non-empty string")
    return value.strip()


def _sha(value, label: str) -> str:
    text = _text(value, label)
    if not SHA40_RE.fullmatch(text):
        raise ReleaseError(f"{label} must be an exact 40-character commit")
    return text


def _load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReleaseError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseError(f"release manifest must be an object: {path}")
    return value


def _load_runner(repo_root: Path):
    runner_path = repo_root / "evals" / "runner.py"
    spec = importlib.util.spec_from_file_location("erei_release_eval_runner", runner_path)
    if spec is None or spec.loader is None:
        raise ReleaseError("unable to load eval runner")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def _validate_structured_approvals(manifest: dict, repo_root: Path) -> int:
    target_path = repo_root / release_target.DEFAULT_TARGET
    try:
        target_manifest = _load(target_path)
        release_target.validate_manifest_shape(target_manifest)
    except (OSError, release_target.ReleaseTargetError) as exc:
        raise ReleaseError(f"invalid or missing frozen release target: {exc}") from exc
    if target_manifest["framework_ref"] != manifest["framework_ref"]:
        raise ReleaseError("frozen release target framework_ref does not match release framework_ref")
    target_tree = target_manifest["target_tree"]

    validated = 0
    for approval_type, relative_path in release_approval.APPROVAL_PATHS.items():
        try:
            release_approval.load_and_validate(
                repo_root / relative_path,
                expected_type=approval_type,
                expected_target=manifest["framework_ref"],
                expected_tree=target_tree,
                require_approved=True,
            )
        except release_approval.ReleaseApprovalError as exc:
            raise ReleaseError(f"invalid {approval_type} release approval: {exc}") from exc
        validated += 1
    return validated


def validate_manifest(manifest: dict, *, repo_root: Path | None = None) -> dict:
    required = {
        "schema_version", "assurance_contract_version", "release_id", "baseline", "status",
        "framework_ref", "released_at", "capabilities", "notes",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise ReleaseError("release manifest missing fields: " + ", ".join(missing))
    if manifest["schema_version"] != 1:
        raise ReleaseError("unsupported release manifest schema_version")
    if type(manifest["assurance_contract_version"]) is not int or manifest["assurance_contract_version"] < 1:
        raise ReleaseError("invalid assurance_contract_version")
    _text(manifest["release_id"], "release_id")
    _text(manifest["baseline"], "baseline")
    if manifest["status"] not in {"stable", "candidate", "deprecated"}:
        raise ReleaseError("invalid release status")
    _sha(manifest["framework_ref"], "framework_ref")
    _text(manifest["released_at"], "released_at")
    if not isinstance(manifest["capabilities"], dict) or not manifest["capabilities"]:
        raise ReleaseError("capabilities must be a non-empty object")
    _text(manifest["notes"], "notes")

    result = {
        "release_id": manifest["release_id"],
        "status": manifest["status"],
        "framework_ref": manifest["framework_ref"],
        "assurance_contract_version": manifest["assurance_contract_version"],
        "next_stable_gate_applied": False,
        "stable_enforcement_satisfied": None,
        "exact_target_bindings_validated": 0,
        "approval_records_validated": 0,
    }
    if manifest["status"] == "stable" and manifest["assurance_contract_version"] >= 2:
        result["next_stable_gate_applied"] = True
        for key in ("approval_ref", "security_review_ref"):
            _sha(manifest.get(key), key)
        minimum_level = _text(manifest.get("minimum_eval_assurance_level"), "minimum_eval_assurance_level")
        if minimum_level != "exact_target_runtime":
            raise ReleaseError("V2 Stable requires minimum_eval_assurance_level=exact_target_runtime")
        evidence_path = _text(manifest.get("behavioral_eval_evidence"), "behavioral_eval_evidence")
        cycle = manifest.get("prospective_learning_cycle")
        if not isinstance(cycle, dict):
            raise ReleaseError("prospective_learning_cycle must be an object for V2 Stable")
        required_cycle = {
            "capture_ref", "review_ref", "feedback_ref", "improvement_ref", "adoption_ref", "measured_outcome_ref"
        }
        if set(cycle) != required_cycle:
            raise ReleaseError("prospective_learning_cycle must contain exactly capture/review/feedback/improvement/adoption/measured_outcome refs")
        for key in sorted(required_cycle):
            _text(cycle[key], f"prospective_learning_cycle.{key}")
        if repo_root is None:
            raise ReleaseError("repo_root is required to validate a V2 Stable release")

        try:
            enforcement = assurance_enforcement.load_and_validate(
                repo_root / "security" / "ASSURANCE_ENFORCEMENT.json"
            )
        except assurance_enforcement.EnforcementError as exc:
            raise ReleaseError(f"invalid assurance enforcement record: {exc}") from exc
        result["stable_enforcement_satisfied"] = enforcement["stable_enforcement_satisfied"]
        if not enforcement["stable_enforcement_satisfied"]:
            raise ReleaseError(
                "V2 Stable requires server branch/status-check enforcement or an independently verified equivalent fallback"
            )

        evidence = _load(repo_root / evidence_path)
        if evidence.get("framework_revision") != manifest["framework_ref"]:
            raise ReleaseError("behavioral eval evidence revision does not match release framework_ref")
        runner = _load_runner(repo_root)
        validated = runner.validate_execution_evidence(evidence)
        if validated.get("schema_version") != 2:
            raise ReleaseError("V2 Stable requires V2 execution evidence with explicit assurance levels")
        expected = runner._expected_cases([str(repo_root / "evals" / "cases")])
        observed = {(item["suite_id"], item["case_id"]): item for item in validated["executions"]}
        missing = expected - set(observed)
        nonpass = {key for key in expected & set(observed) if observed[key]["status"] != "pass"}
        lower = {
            key for key in expected & set(observed)
            if runner.ASSURANCE_LEVELS[runner.execution_assurance_level(observed[key], 2)] < runner.ASSURANCE_LEVELS[minimum_level]
        }
        extras = set(observed) - expected
        if missing or nonpass or lower or extras:
            raise ReleaseError(
                "behavioral eval evidence is insufficient: "
                f"missing={len(missing)} nonpass={len(nonpass)} lower_assurance={len(lower)} unexpected={len(extras)}"
            )

        result["approval_records_validated"] = _validate_structured_approvals(manifest, repo_root)

        for key in sorted(expected):
            try:
                exact_target_evidence.validate_binding(repo_root, manifest["framework_ref"], observed[key])
            except exact_target_evidence.ExactTargetEvidenceError as exc:
                raise ReleaseError(f"exact-target evidence binding failed for {key[0]}/{key[1]}: {exc}") from exc
        result["exact_target_bindings_validated"] = len(expected)
    elif manifest["status"] == "candidate":
        blockers = manifest.get("stable_blockers")
        if not isinstance(blockers, list) or not blockers or any(not isinstance(item, str) or not item.strip() for item in blockers):
            raise ReleaseError("candidate release must explicitly list stable_blockers")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--repo-root")
    args = parser.parse_args(argv)
    try:
        result = validate_manifest(
            _load(Path(args.manifest)),
            repo_root=Path(args.repo_root).resolve() if args.repo_root else None,
        )
    except (ReleaseError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "valid", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
