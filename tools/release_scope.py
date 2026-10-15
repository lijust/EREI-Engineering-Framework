#!/usr/bin/env python3
"""Validate the frozen VNext release scope against Framework registry and eval suites."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCOPE_PATH = Path("releases/VNEXT_RELEASE_SCOPE.json")
CAPABILITIES_PATH = Path("CAPABILITIES.json")
SCOPE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
EVAL_PATH_RE = re.compile(r"^evals/cases/[A-Za-z0-9._-]+\.eval\.json$")


class ReleaseScopeError(RuntimeError):
    pass


def _load(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseScopeError(f"unable to load {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseScopeError(f"{label} must be a JSON object")
    return value


def _unique_text_list(value, label: str, *, minimum: int = 0) -> list[str]:
    if (
        not isinstance(value, list)
        or len(value) < minimum
        or any(not isinstance(item, str) or not item.strip() for item in value)
        or len(value) != len(set(value))
    ):
        raise ReleaseScopeError(f"{label} must be a unique string array with at least {minimum} item(s)")
    return value


def validate_scope(repo_root: Path, value: dict) -> dict:
    fields = {
        "schema_version", "scope_id", "status", "release_family", "target_baseline",
        "capabilities", "release_control_dependencies", "required_eval_suites",
        "excluded_candidate_capabilities",
        "post_promotion_gates", "rationale",
    }
    if set(value) != fields:
        raise ReleaseScopeError(
            f"release scope fields mismatch missing={sorted(fields-set(value))} "
            f"unknown={sorted(set(value)-fields)}"
        )
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ReleaseScopeError("release scope schema_version must be integer 1")
    if not isinstance(value["scope_id"], str) or not SCOPE_ID_RE.fullmatch(value["scope_id"]):
        raise ReleaseScopeError("invalid release scope_id")
    if value["status"] != "approved":
        raise ReleaseScopeError("release scope status must be approved")
    for key in ("release_family", "target_baseline", "rationale"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise ReleaseScopeError(f"{key} must be non-empty")
    if len(value["rationale"].strip()) < 20:
        raise ReleaseScopeError("rationale must contain at least 20 characters")

    def capability_bindings(raw, label: str, *, minimum: int = 0) -> list[dict]:
        if not isinstance(raw, list) or len(raw) < minimum:
            raise ReleaseScopeError(f"{label} must contain at least {minimum} item(s)")
        result = []
        seen = set()
        for index, item in enumerate(raw):
            if not isinstance(item, dict) or set(item) != {"name", "version"}:
                raise ReleaseScopeError(f"{label}[{index}] must contain exactly name and version")
            name, version = item["name"], item["version"]
            if not isinstance(name, str) or not name.strip() or not isinstance(version, str) or not version.strip():
                raise ReleaseScopeError(f"{label}[{index}] name/version must be non-empty strings")
            if name in seen:
                raise ReleaseScopeError(f"{label} contains duplicate capability: {name}")
            seen.add(name)
            result.append({"name": name, "version": version})
        return result

    capabilities = capability_bindings(value["capabilities"], "capabilities", minimum=1)
    dependencies = capability_bindings(value["release_control_dependencies"], "release_control_dependencies")
    excluded = _unique_text_list(value["excluded_candidate_capabilities"], "excluded_candidate_capabilities")
    _unique_text_list(value["post_promotion_gates"], "post_promotion_gates")

    included_names = {item["name"] for item in capabilities + dependencies}
    overlap = included_names & set(excluded)
    if overlap:
        raise ReleaseScopeError("included and excluded capabilities overlap: " + ", ".join(sorted(overlap)))

    registry = _load(repo_root / CAPABILITIES_PATH, "capability registry")
    development = registry.get("development_line")
    registered = development.get("capabilities") if isinstance(development, dict) else None
    if not isinstance(registered, dict):
        raise ReleaseScopeError("CAPABILITIES.json has no development_line.capabilities")
    missing_caps = sorted((included_names | set(excluded)) - set(registered))
    if missing_caps:
        raise ReleaseScopeError("release scope references unknown capabilities: " + ", ".join(missing_caps))
    for binding in capabilities + dependencies:
        registered_version = registered[binding["name"]].get("version") if isinstance(registered[binding["name"]], dict) else None
        if registered_version != binding["version"]:
            raise ReleaseScopeError(
                f"release scope version mismatch for {binding['name']}: "
                f"scope={binding['version']!r} registry={registered_version!r}"
            )
    for name in excluded:
        record = registered[name]
        if not isinstance(record, dict) or record.get("status") != "candidate":
            raise ReleaseScopeError(f"excluded capability must currently be Candidate: {name}")

    suites = value["required_eval_suites"]
    if not isinstance(suites, list) or not suites:
        raise ReleaseScopeError("required_eval_suites must be non-empty")
    seen_paths: set[str] = set()
    seen_ids: set[str] = set()
    covered_capabilities: set[str] = set()
    expected_cases: list[tuple[str, str]] = []
    for index, item in enumerate(suites):
        if not isinstance(item, dict) or set(item) != {"path", "suite_id", "covers"}:
            raise ReleaseScopeError(
                f"required_eval_suites[{index}] must contain exactly path, suite_id and covers"
            )
        path = item["path"]
        suite_id = item["suite_id"]
        covers = _unique_text_list(item["covers"], f"required_eval_suites[{index}].covers", minimum=1)
        if not isinstance(path, str) or not EVAL_PATH_RE.fullmatch(path):
            raise ReleaseScopeError(f"required_eval_suites[{index}].path is invalid")
        if not isinstance(suite_id, str) or not suite_id:
            raise ReleaseScopeError(f"required_eval_suites[{index}].suite_id is invalid")
        if path in seen_paths or suite_id in seen_ids:
            raise ReleaseScopeError("required eval suite paths and suite_ids must be unique")
        unknown_covered = sorted(set(covers) - included_names)
        if unknown_covered:
            raise ReleaseScopeError(
                "required eval suite covers capabilities outside release scope: " + ", ".join(unknown_covered)
            )
        seen_paths.add(path); seen_ids.add(suite_id)
        covered_capabilities.update(covers)
        suite_path = repo_root / path
        suite = _load(suite_path, "eval suite")
        if suite.get("suite_id") != suite_id:
            raise ReleaseScopeError(
                f"eval suite identity mismatch for {path}: scope={suite_id!r} file={suite.get('suite_id')!r}"
            )
        cases = suite.get("cases")
        if not isinstance(cases, list) or not cases:
            raise ReleaseScopeError(f"eval suite has no cases: {path}")
        case_ids: set[str] = set()
        for case in cases:
            case_id = case.get("id") if isinstance(case, dict) else None
            if not isinstance(case_id, str) or not case_id:
                raise ReleaseScopeError(f"eval suite has invalid case id: {path}")
            if case_id in case_ids:
                raise ReleaseScopeError(f"eval suite has duplicate case id {case_id}: {path}")
            case_ids.add(case_id)
            expected_cases.append((suite_id, case_id))

    missing_coverage = sorted(included_names - covered_capabilities)
    if missing_coverage:
        raise ReleaseScopeError(
            "release scope capabilities lack required eval-suite coverage: " + ", ".join(missing_coverage)
        )

    return {
        "status": "VALID",
        "scope_id": value["scope_id"],
        "release_family": value["release_family"],
        "target_baseline": value["target_baseline"],
        "capabilities": capabilities,
        "release_control_dependencies": dependencies,
        "excluded_candidate_capabilities": excluded,
        "required_eval_suite_count": len(suites),
        "required_eval_case_count": len(expected_cases),
        "covered_capabilities": sorted(covered_capabilities),
        "required_eval_cases": sorted([f"{suite}/{case}" for suite, case in expected_cases]),
    }


def load_scope(repo_root: Path, path: Path = SCOPE_PATH) -> tuple[dict, dict]:
    resolved = path if path.is_absolute() else repo_root / path
    value = _load(resolved, "release scope")
    return value, validate_scope(repo_root, value)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--scope", default=str(SCOPE_PATH))
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()
    try:
        _, result = load_scope(root, Path(args.scope))
    except ReleaseScopeError as exc:
        print(json.dumps({"status": "INVALID", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
