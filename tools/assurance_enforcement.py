#!/usr/bin/env python3
"""Validate the Framework's machine-readable server/fallback enforcement truth."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from . import github_review_provenance
except ImportError:
    import github_review_provenance


class EnforcementError(RuntimeError):
    pass


def _exact_fields(value: dict, required: set[str], label: str) -> None:
    if not isinstance(value, dict):
        raise EnforcementError(f"{label} must be an object")
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required)
    if missing:
        raise EnforcementError(f"{label} missing fields: {', '.join(missing)}")
    if unknown:
        raise EnforcementError(f"{label} unknown fields: {', '.join(unknown)}")


def _bool(value, label: str) -> bool:
    if type(value) is not bool:
        raise EnforcementError(f"{label} must be boolean")
    return value


def _text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EnforcementError(f"{label} must be a non-empty string")
    return value.strip()


def validate_enforcement(value: dict, *, expected_target: str | None = None) -> dict:
    top = {
        "schema_version", "repository", "main_branch", "status",
        "server_enforcement", "fallback", "evidence", "limitations",
    }
    _exact_fields(value, top, "assurance enforcement")
    if type(value["schema_version"]) is not int or value["schema_version"] != 2:
        raise EnforcementError("assurance enforcement schema_version must be integer 2")
    if _text(value["repository"], "repository") != "lijust/EREI-Engineering-Framework":
        raise EnforcementError("repository mismatch")
    if _text(value["main_branch"], "main_branch") != "main":
        raise EnforcementError("main_branch must be main")
    if value["status"] not in {"candidate_control", "enforced"}:
        raise EnforcementError("invalid enforcement status")

    server_required = {"branch_protection_enabled", "required_status_checks_enforced", "source"}
    server = value["server_enforcement"]
    _exact_fields(server, server_required, "server_enforcement")
    branch_protected = _bool(server["branch_protection_enabled"], "branch_protection_enabled")
    checks_enforced = _bool(server["required_status_checks_enforced"], "required_status_checks_enforced")
    _text(server["source"], "server_enforcement.source")

    fallback_required = {
        "mode", "required_workflow", "release_branch_prefix", "exact_candidate_sha_required",
        "release_assurance_contract_version", "architecture_approval_required",
        "security_approval_required", "exact_target_runtime_evidence_required",
        "complete_prospective_cycle_required", "equivalent_enforcement_verified",
        "equivalence_target_ref", "review_provenance", "stable_promotion_policy",
    }
    fallback = value["fallback"]
    _exact_fields(fallback, fallback_required, "fallback")
    if fallback["mode"] != "controlled_release_v2":
        raise EnforcementError("fallback.mode must be controlled_release_v2")
    if fallback["required_workflow"] != "Framework Assurance Gate":
        raise EnforcementError("fallback.required_workflow mismatch")
    if fallback["release_branch_prefix"] != "release/":
        raise EnforcementError("fallback.release_branch_prefix must be release/")
    for key in (
        "exact_candidate_sha_required", "architecture_approval_required", "security_approval_required",
        "exact_target_runtime_evidence_required", "complete_prospective_cycle_required",
        "equivalent_enforcement_verified",
    ):
        _bool(fallback[key], f"fallback.{key}")
    if fallback["release_assurance_contract_version"] != 2:
        raise EnforcementError("fallback.release_assurance_contract_version must be 2")
    if fallback["stable_promotion_policy"] != "blocked_until_server_or_equivalent_enforcement":
        raise EnforcementError("fallback.stable_promotion_policy mismatch")

    equivalent = fallback["equivalent_enforcement_verified"]
    if equivalent:
        target = _text(fallback["equivalence_target_ref"], "fallback.equivalence_target_ref")
        import re
        if re.fullmatch(r"[a-f0-9]{40}", target) is None:
            raise EnforcementError("fallback.equivalence_target_ref must be an exact commit")
        if expected_target is not None and target != expected_target:
            raise EnforcementError(
                f"fallback equivalence target mismatch: expected {expected_target}, got {target}"
            )
        try:
            github_review_provenance.validate_descriptor(
                fallback["review_provenance"],
                expected_purpose="enforcement_equivalence",
            )
        except github_review_provenance.ReviewProvenanceError as exc:
            raise EnforcementError(f"invalid fallback.review_provenance: {exc}") from exc
    else:
        if fallback["equivalence_target_ref"] is not None:
            raise EnforcementError("fallback.equivalence_target_ref must be null until equivalence is verified")
        if fallback["review_provenance"] is not None:
            raise EnforcementError("fallback.review_provenance must be null until equivalence is verified")

    for label in ("evidence", "limitations"):
        items = value[label]
        if not isinstance(items, list) or not items:
            raise EnforcementError(f"{label} must be a non-empty array")
        normalized = [_text(item, f"{label} item") for item in items]
        if len(normalized) != len(set(normalized)):
            raise EnforcementError(f"{label} items must be unique")

    server_equivalent = branch_protected and checks_enforced
    fallback_equivalent = fallback["equivalent_enforcement_verified"]
    stable_enforcement_satisfied = server_equivalent or fallback_equivalent
    if value["status"] == "enforced" and not stable_enforcement_satisfied:
        raise EnforcementError("status=enforced requires server enforcement or verified equivalent fallback")
    return {
        "server_enforcement_satisfied": server_equivalent,
        "fallback_equivalent_verified": fallback_equivalent,
        "stable_enforcement_satisfied": stable_enforcement_satisfied,
        "equivalence_target_ref": fallback["equivalence_target_ref"],
    }


def verify_live_server_enforcement(value: dict, *, token: str | None = None) -> dict:
    """Authenticate declared GitHub server protection instead of trusting JSON booleans.

    This verifier deliberately supports classic protection only. Ruleset-only
    configurations need a separate independently verified ruleset policy.
    GitHub authentication/permissions failures are hard blockers, not passes.
    """
    summary = validate_enforcement(value)
    if not summary["server_enforcement_satisfied"]:
        raise EnforcementError("server branch/status protection is not asserted in this record")
    token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise EnforcementError("live server enforcement requires authenticated GitHub API access")
    api = f"https://api.github.com/repos/{value['repository']}"
    branch = value["main_branch"]
    try:
        branch_info = github_review_provenance._github_json(f"{api}/branches/{branch}", token)
        protection = github_review_provenance._github_json(f"{api}/branches/{branch}/protection", token)
    except github_review_provenance.ReviewProvenanceError as exc:
        raise EnforcementError(f"unable to authenticate live branch protection: {exc}") from exc

    if not isinstance(branch_info, dict) or branch_info.get("protected") is not True:
        raise EnforcementError("GitHub main branch is not live-protected")
    if not isinstance(protection, dict):
        raise EnforcementError("GitHub branch-protection response is not an object")

    admin = protection.get("enforce_admins")
    if not isinstance(admin, dict) or admin.get("enabled") is not True:
        raise EnforcementError("branch protection does not enforce restrictions on administrators")
    checks = protection.get("required_status_checks")
    if not isinstance(checks, dict) or checks.get("strict") is not True:
        raise EnforcementError("required status checks are absent or not strict")
    required = checks.get("checks")
    if not isinstance(required, list):
        raise EnforcementError("required status checks lack authenticated GitHub-App bindings")
    # The exact Actions job is named assurance in assurance-gate.yml.
    # The standard GitHub Actions App ID binds the required check source.
    if not any(
        isinstance(item, dict)
        and item.get("context") == "assurance"
        and item.get("app_id") == 15368
        for item in required
    ):
        raise EnforcementError("Framework assurance check is not required from GitHub Actions")

    reviews = protection.get("required_pull_request_reviews")
    if (
        not isinstance(reviews, dict)
        or type(reviews.get("required_approving_review_count")) is not int
        or reviews["required_approving_review_count"] < 1
        or reviews.get("dismiss_stale_reviews") is not True
    ):
        raise EnforcementError("stale-dismissing pull-request approval protection is not enforced")
    bypass = reviews.get("bypass_pull_request_allowances")
    if not isinstance(bypass, dict) or any(
        not isinstance(bypass.get(k), list) or bool(bypass[k])
        for k in ("users", "teams", "apps")
    ):
        raise EnforcementError("GitHub PR bypass allowances must explicitly contain empty user/team/app lists")
    for key in ("allow_force_pushes", "allow_deletions"):
        setting = protection.get(key)
        if not isinstance(setting, dict) or setting.get("enabled") is not False:
            raise EnforcementError(f"branch protection must explicitly disable {key}")

    # A GitHub status-check context and App ID authenticate only the
    # producer/name, NOT the workflow file that generated the check.
    # A PR can replace the "assurance" job with a no-op and produce the
    # same green check. Classic branch protection alone is insufficient
    # evidence of immutable trusted workflow identity. Fail closed until
    # an independently enforceable workflow-identity control is available.
    raise EnforcementError(
        "classic status-check protection cannot authenticate trusted "
        "assurance workflow identity; server equivalence is blocked"
    )


def verify_effective_enforcement(
    repo_root: Path,
    value: dict,
    *,
    expected_target: str,
    closure_ref: str = "HEAD",
    token: str | None = None,
) -> dict:
    """Authenticate at least one asserted enforcement path.

    A live server proof may authorize its supported path. The current fallback
    authenticates a review only; no deployed equivalent-authority verifier is
    connected, so that path always denies Stable promotion.
    """
    declared = validate_enforcement(value, expected_target=expected_target)
    if not declared["stable_enforcement_satisfied"]:
        raise EnforcementError("no verified Stable enforcement mode has been asserted")

    errors: list[str] = []
    if declared["server_enforcement_satisfied"]:
        try:
            proof = verify_live_server_enforcement(value, token=token)
            return {"status": "verified", "mode": "server", "server": proof, "fallback": None}
        except EnforcementError as exc:
            errors.append(f"server: {exc}")

    if declared["fallback_equivalent_verified"]:
        try:
            verify_authenticated_equivalence(
                repo_root,
                value,
                expected_target=expected_target,
                closure_ref=closure_ref,
                token=token,
            )
            raise EnforcementError(
                "authenticated review does not establish effective enforcement; "
                "independent authority verifier is unavailable"
            )
        except EnforcementError as exc:
            errors.append(f"fallback: {exc}")

    raise EnforcementError("all asserted enforcement proofs failed: " + "; ".join(errors))


def load_and_validate(path: Path, *, expected_target: str | None = None) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EnforcementError(f"unable to load enforcement record: {exc}") from exc
    if not isinstance(value, dict):
        raise EnforcementError("assurance enforcement record must be an object")
    return validate_enforcement(value, expected_target=expected_target)


def verify_authenticated_equivalence(
    repo_root: Path,
    value: dict,
    *,
    expected_target: str,
    closure_ref: str = "HEAD",
    token: str | None = None,
) -> dict:
    result = validate_enforcement(value, expected_target=expected_target)
    fallback = value["fallback"]
    if not fallback["equivalent_enforcement_verified"]:
        return {"status": "not_required", **result}
    try:
        review = github_review_provenance.verify_artifact_review(
            repo_root,
            repository=value["repository"],
            target_ref=expected_target,
            closure_ref=closure_ref,
            artifact_path="security/ASSURANCE_ENFORCEMENT.json",
            descriptor=fallback["review_provenance"],
            expected_purpose="enforcement_equivalence",
            token=token,
        )
    except github_review_provenance.ReviewProvenanceError as exc:
        raise EnforcementError(f"authenticated enforcement review provenance failed: {exc}") from exc
    return {"status": "authenticated_review_only", "authority_verified": False,
            "declared_control": result, "review": review}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", nargs="?", default="security/ASSURANCE_ENFORCEMENT.json")
    args = parser.parse_args(argv)
    try:
        result = load_and_validate(Path(args.record))
    except EnforcementError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "valid", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
