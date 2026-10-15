#!/usr/bin/env python3
"""Validate release enforcement truth without trusting self-asserted fallback equivalence."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SHA40_RE = re.compile(r"^[a-f0-9]{40}$")


class EnforcementError(RuntimeError):
    pass


def _exact_fields(value: Any, required: set[str], label: str) -> None:
    if not isinstance(value, dict):
        raise EnforcementError(f"{label} must be an object")
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required)
    if missing:
        raise EnforcementError(f"{label} missing fields: {', '.join(missing)}")
    if unknown:
        raise EnforcementError(f"{label} unknown fields: {', '.join(unknown)}")


def _bool(value: Any, label: str) -> bool:
    if type(value) is not bool:
        raise EnforcementError(f"{label} must be boolean")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EnforcementError(f"{label} must be a non-empty string")
    return value.strip()


def _sha(value: Any, label: str) -> str:
    text = _text(value, label)
    if not SHA40_RE.fullmatch(text):
        raise EnforcementError(f"{label} must be an exact 40-character SHA")
    return text


def _review(value: Any) -> dict[str, Any]:
    required = {"target_framework_ref", "target_tree", "provenance"}
    _exact_fields(value, required, "fallback.equivalence_review")
    target = _sha(value["target_framework_ref"], "fallback.equivalence_review.target_framework_ref")
    tree = _sha(value["target_tree"], "fallback.equivalence_review.target_tree")
    provenance = value["provenance"]
    _exact_fields(provenance, {"kind", "pr_number", "actor_login"}, "fallback.equivalence_review.provenance")
    if provenance["kind"] != "github_codex_clean_review":
        raise EnforcementError("fallback equivalence provenance must use github_codex_clean_review")
    if type(provenance["pr_number"]) is not int or provenance["pr_number"] < 1:
        raise EnforcementError("fallback equivalence provenance.pr_number must be integer >= 1")
    _text(provenance["actor_login"], "fallback equivalence provenance.actor_login")
    return {
        "target_framework_ref": target,
        "target_tree": tree,
        "provenance": dict(provenance),
    }


def validate_enforcement(
    value: dict,
    *,
    expected_target_ref: str | None = None,
    expected_target_tree: str | None = None,
    authenticated_fallback: bool = False,
) -> dict:
    top = {
        "schema_version", "repository", "main_branch", "status",
        "server_enforcement", "fallback", "evidence", "limitations",
    }
    _exact_fields(value, top, "assurance enforcement")
    version = value["schema_version"]
    if type(version) is not int or version not in {1, 2}:
        raise EnforcementError("unsupported assurance enforcement schema_version")
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

    common = {
        "mode", "required_workflow", "release_branch_prefix", "exact_candidate_sha_required",
        "release_assurance_contract_version", "architecture_approval_required",
        "security_approval_required", "exact_target_runtime_evidence_required",
        "complete_prospective_cycle_required", "stable_promotion_policy",
    }
    fallback = value["fallback"]
    if version == 1:
        required = common | {"equivalent_enforcement_verified"}
    else:
        required = common | {"equivalence_review"}
    _exact_fields(fallback, required, "fallback")
    if fallback["mode"] != "controlled_release_v2":
        raise EnforcementError("fallback.mode must be controlled_release_v2")
    if fallback["required_workflow"] != "Framework Assurance Gate":
        raise EnforcementError("fallback.required_workflow mismatch")
    if fallback["release_branch_prefix"] != "release/":
        raise EnforcementError("fallback.release_branch_prefix must be release/")
    for key in (
        "exact_candidate_sha_required", "architecture_approval_required", "security_approval_required",
        "exact_target_runtime_evidence_required", "complete_prospective_cycle_required",
    ):
        _bool(fallback[key], f"fallback.{key}")
    if fallback["release_assurance_contract_version"] != 2:
        raise EnforcementError("fallback.release_assurance_contract_version must be 2")
    if fallback["stable_promotion_policy"] != "blocked_until_server_or_equivalent_enforcement":
        raise EnforcementError("fallback.stable_promotion_policy mismatch")

    equivalence_review = None
    if version == 1:
        legacy_claim = _bool(
            fallback["equivalent_enforcement_verified"],
            "fallback.equivalent_enforcement_verified",
        )
        fallback_claimed = legacy_claim
        if legacy_claim and authenticated_fallback:
            raise EnforcementError(
                "legacy fallback equivalence cannot satisfy Stable enforcement because it is not target-bound"
            )
    else:
        raw_review = fallback["equivalence_review"]
        if raw_review is not None:
            equivalence_review = _review(raw_review)
        fallback_claimed = equivalence_review is not None

    if expected_target_ref is not None:
        expected_target_ref = _sha(expected_target_ref, "expected_target_ref")
    if expected_target_tree is not None:
        expected_target_tree = _sha(expected_target_tree, "expected_target_tree")
    if equivalence_review is not None:
        if expected_target_ref is not None and equivalence_review["target_framework_ref"] != expected_target_ref:
            raise EnforcementError("fallback equivalence target ref does not match selected release target")
        if expected_target_tree is not None and equivalence_review["target_tree"] != expected_target_tree:
            raise EnforcementError("fallback equivalence target tree does not match selected release target")

    if authenticated_fallback and not fallback_claimed:
        raise EnforcementError("authenticated_fallback cannot be true without a target-bound equivalence review")

    for label in ("evidence", "limitations"):
        items = value[label]
        if not isinstance(items, list) or not items:
            raise EnforcementError(f"{label} must be a non-empty array")
        normalized = [_text(item, f"{label} item") for item in items]
        if len(normalized) != len(set(normalized)):
            raise EnforcementError(f"{label} items must be unique")

    server_equivalent = branch_protected and checks_enforced
    fallback_equivalent = bool(fallback_claimed and authenticated_fallback)
    stable_enforcement_satisfied = server_equivalent or fallback_equivalent

    if value["status"] == "enforced" and not (server_equivalent or fallback_claimed):
        raise EnforcementError(
            "status=enforced requires server enforcement or a target-bound fallback equivalence review"
        )

    return {
        "schema_version": version,
        "server_enforcement_satisfied": server_equivalent,
        "fallback_equivalence_claimed": fallback_claimed,
        "fallback_equivalent_verified": fallback_equivalent,
        "stable_enforcement_satisfied": stable_enforcement_satisfied,
        "equivalence_review": equivalence_review,
    }


def load_and_validate(
    path: Path,
    *,
    expected_target_ref: str | None = None,
    expected_target_tree: str | None = None,
    authenticated_fallback: bool = False,
) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EnforcementError(f"unable to load enforcement record: {exc}") from exc
    if not isinstance(value, dict):
        raise EnforcementError("assurance enforcement record must be an object")
    return validate_enforcement(
        value,
        expected_target_ref=expected_target_ref,
        expected_target_tree=expected_target_tree,
        authenticated_fallback=authenticated_fallback,
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", nargs="?", default="security/ASSURANCE_ENFORCEMENT.json")
    parser.add_argument("--target-ref")
    parser.add_argument("--target-tree")
    args = parser.parse_args(argv)
    try:
        result = load_and_validate(
            Path(args.record),
            expected_target_ref=args.target_ref,
            expected_target_tree=args.target_tree,
        )
    except EnforcementError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "valid", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
