#!/usr/bin/env python3
"""Validate the frozen VNext release scope against Framework registry and eval suites."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCOPE_PATH = Path("releases/VNEXT_RELEASE_SCOPE.json")
CAPABILITIES_PATH = Path("CAPABILITIES.json")
SCOPE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
EVAL_PATH_RE = re.compile(r"^evals/cases/[A-Za-z0-9._-]+\.eval\.json$")
SHA40_RE = re.compile(r"^[a-f0-9]{40}$")


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
        "required_eval_paths": [item["path"] for item in suites],
        "required_eval_cases": sorted([f"{suite}/{case}" for suite, case in expected_cases]),
        "required_eval_case_pairs": [
            {"suite_id": suite, "case_id": case}
            for suite, case in sorted(expected_cases)
        ],
    }


def load_scope(repo_root: Path, path: Path = SCOPE_PATH) -> tuple[dict, dict]:
    resolved = path if path.is_absolute() else repo_root / path
    value = _load(resolved, "release scope")
    return value, validate_scope(repo_root, value)


def _git(repo_root: Path, *args: str, allow_missing: bool = False) -> str | None:
    process = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        if allow_missing:
            return None
        raise ReleaseScopeError(f"git {' '.join(args)} failed: {process.stderr.strip()}")
    return process.stdout.strip()


def _git_blob(repo_root: Path, revision: str, path: str) -> str | None:
    value = _git(repo_root, "rev-parse", f"{revision}:{path}", allow_missing=True)
    if value is None:
        return None
    if not SHA40_RE.fullmatch(value):
        raise ReleaseScopeError(f"invalid blob identity for {revision}:{path}")
    return value


def _git_text(repo_root: Path, revision: str, path: str) -> str:
    value = _git(repo_root, "show", f"{revision}:{path}")
    assert value is not None
    return value


def _git_json(repo_root: Path, revision: str, path: str, label: str) -> dict:
    try:
        value = json.loads(_git_text(repo_root, revision, path))
    except json.JSONDecodeError as exc:
        raise ReleaseScopeError(f"invalid JSON in frozen {label} {revision}:{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseScopeError(f"frozen {label} must be a JSON object: {revision}:{path}")
    return value


def load_target_bound_scope(
    repo_root: Path,
    target_ref: str,
    *,
    closure_ref: str = "HEAD",
) -> tuple[dict | None, dict | None]:
    if not isinstance(target_ref, str) or not SHA40_RE.fullmatch(target_ref):
        raise ReleaseScopeError("target_ref must be an exact 40-character commit")
    scope_path = SCOPE_PATH.as_posix()
    target_scope_blob = _git_blob(repo_root, target_ref, scope_path)
    closure_scope_blob = _git_blob(repo_root, closure_ref, scope_path)

    if target_scope_blob is None and closure_scope_blob is None:
        return None, None
    if target_scope_blob is None or closure_scope_blob is None:
        raise ReleaseScopeError("VNext release scope presence changed after target freeze")
    if target_scope_blob != closure_scope_blob:
        raise ReleaseScopeError("VNext release scope changed after target freeze")

    scope = _git_json(repo_root, target_ref, scope_path, "release scope")
    raw_suites = scope.get("required_eval_suites")
    if not isinstance(raw_suites, list) or not raw_suites:
        raise ReleaseScopeError("frozen release scope required_eval_suites must be non-empty")

    dependencies = [scope_path, CAPABILITIES_PATH.as_posix()]
    for index, item in enumerate(raw_suites):
        path = item.get("path") if isinstance(item, dict) else None
        if not isinstance(path, str) or not EVAL_PATH_RE.fullmatch(path):
            raise ReleaseScopeError(f"frozen required_eval_suites[{index}].path is invalid")
        dependencies.append(path)

    for path in dependencies:
        target_blob = _git_blob(repo_root, target_ref, path)
        closure_blob = _git_blob(repo_root, closure_ref, path)
        if target_blob is None or closure_blob is None:
            raise ReleaseScopeError(f"release-scope dependency presence changed after target freeze: {path}")
        if target_blob != closure_blob:
            raise ReleaseScopeError(f"release-scope dependency drifted after target freeze: {path}")

    with tempfile.TemporaryDirectory() as tmp:
        frozen_root = Path(tmp)
        for path in dependencies:
            destination = frozen_root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(_git_text(repo_root, target_ref, path), encoding="utf-8")
        summary = validate_scope(frozen_root, scope)
    return scope, summary


def scoped_capability_versions(scope: dict) -> dict[str, str]:
    versions: dict[str, str] = {}
    for label in ("capabilities", "release_control_dependencies"):
        items = scope.get(label)
        if not isinstance(items, list):
            raise ReleaseScopeError(f"{label} must be an array")
        for index, item in enumerate(items):
            if not isinstance(item, dict) or set(item) != {"name", "version"}:
                raise ReleaseScopeError(f"{label}[{index}] must contain exactly name and version")
            name, version = item["name"], item["version"]
            if not isinstance(name, str) or not name or not isinstance(version, str) or not version:
                raise ReleaseScopeError(f"{label}[{index}] name/version must be non-empty strings")
            if name in versions:
                raise ReleaseScopeError(f"duplicate scoped capability binding: {name}")
            versions[name] = version
    if not versions:
        raise ReleaseScopeError("release scope must bind at least one capability/dependency")
    return versions


def required_eval_paths(scope: dict) -> list[str]:
    suites = scope.get("required_eval_suites")
    if not isinstance(suites, list) or not suites:
        raise ReleaseScopeError("required_eval_suites must be non-empty")
    paths: list[str] = []
    for index, item in enumerate(suites):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not item["path"]:
            raise ReleaseScopeError(f"required_eval_suites[{index}].path is invalid")
        paths.append(item["path"])
    if len(paths) != len(set(paths)):
        raise ReleaseScopeError("required eval suite paths must be unique")
    return paths


def validate_stable_manifest_against_scope(manifest: dict, scope: dict) -> dict:
    baseline = scope.get("target_baseline")
    if not isinstance(baseline, str) or not baseline:
        raise ReleaseScopeError("release scope target_baseline must be non-empty")
    if manifest.get("baseline") != baseline:
        raise ReleaseScopeError(
            f"Stable manifest baseline {manifest.get('baseline')!r} does not match frozen scope {baseline!r}"
        )
    expected = scoped_capability_versions(scope)
    actual = manifest.get("capabilities")
    if not isinstance(actual, dict):
        raise ReleaseScopeError("Stable manifest capabilities must be an object")
    excluded = scope.get("excluded_candidate_capabilities")
    if not isinstance(excluded, list) or any(not isinstance(item, str) or not item for item in excluded):
        raise ReleaseScopeError("excluded_candidate_capabilities must be a string array")
    leaked = sorted(set(actual) & set(excluded))
    if leaked:
        raise ReleaseScopeError(
            "Stable manifest contains capabilities excluded by frozen release scope: " + ", ".join(leaked)
        )
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        mismatched = sorted(
            name for name in set(actual) & set(expected)
            if actual[name] != expected[name]
        )
        raise ReleaseScopeError(
            "Stable manifest capabilities do not match frozen release scope: "
            f"missing={missing} extra={extra} version_mismatch={mismatched}"
        )
    return {
        "scope_id": scope.get("scope_id"),
        "baseline": baseline,
        "capabilities": expected,
    }


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
