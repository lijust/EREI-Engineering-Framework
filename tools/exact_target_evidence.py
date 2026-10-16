#!/usr/bin/env python3
"""Validate reconstructible exact-target manifests and their durable runtime provenance bindings."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import types
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from . import exact_target_package_identity
except ImportError:
    import exact_target_package_identity

SHA40_RE = re.compile(r"^[a-f0-9]{40}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
RUN_ID_RE = re.compile(r"^ETR-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
REF_RE = re.compile(r"^exact-target-run:(?P<path>[^#]+)#(?P<suite>[^/]+)/(?P<case>[^/]+)$")
RETAINED_RESPONSE_FIELDS = {"output", "metadata", "trace"}
OFFICIAL_REPOSITORY = "lijust/EREI-Engineering-Framework"


class ExactTargetEvidenceError(RuntimeError):
    pass


def _datetime(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ExactTargetEvidenceError(f"{label} must be a non-empty date-time")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ExactTargetEvidenceError(f"{label} must be a valid date-time") from exc
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExactTargetEvidenceError(f"{label} must be a non-empty string")
    return value.strip()


def _exact_fields(value: dict[str, Any], fields: set[str], label: str) -> None:
    if set(value) != fields:
        missing = sorted(fields - set(value))
        unknown = sorted(set(value) - fields)
        raise ExactTargetEvidenceError(f"{label} fields mismatch missing={missing} unknown={unknown}")


def _sha40(value: Any, label: str) -> str:
    text = _text(value, label)
    if not SHA40_RE.fullmatch(text):
        raise ExactTargetEvidenceError(f"{label} must be an exact 40-character commit")
    return text


def _sha256(value: Any, label: str) -> str:
    text = _text(value, label)
    if not SHA256_RE.fullmatch(text):
        raise ExactTargetEvidenceError(f"{label} must be a lowercase SHA-256 digest")
    return text


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _file_digest(path: Path, label: str) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ExactTargetEvidenceError(f"unable to hash {label} {path}: {exc}") from exc


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExactTargetEvidenceError(f"unable to load {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ExactTargetEvidenceError(f"{label} must be a JSON object")
    return value


def _adapter_error_digest(suite_id: str, case_id: str) -> str:
    return _canonical_digest({"adapter_error": True, "suite_id": suite_id, "case_id": case_id})


def _validate_retained_response(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ExactTargetEvidenceError(f"{label} must be an object")
    unknown = sorted(set(value) - RETAINED_RESPONSE_FIELDS)
    if unknown:
        raise ExactTargetEvidenceError(f"{label} contains unknown fields: {unknown}")
    if "output" not in value:
        raise ExactTargetEvidenceError(f"{label}.output is required")
    if "metadata" in value and not isinstance(value["metadata"], dict):
        raise ExactTargetEvidenceError(f"{label}.metadata must be an object")
    if "trace" in value:
        trace = value["trace"]
        if not isinstance(trace, list):
            raise ExactTargetEvidenceError(f"{label}.trace must be an array")
        for index, step in enumerate(trace):
            if not isinstance(step, dict):
                raise ExactTargetEvidenceError(f"{label}.trace[{index}] must be an object")
            if "type" in step and not isinstance(step["type"], str):
                raise ExactTargetEvidenceError(f"{label}.trace[{index}].type must be a string")
            if step.get("type") == "tool" and (not isinstance(step.get("name"), str) or not step["name"]):
                raise ExactTargetEvidenceError(f"{label}.trace[{index}] tool step requires name")
    return value


def _load_runner(repo_root: Path):
    runner_path = repo_root / "evals" / "runner.py"
    try:
        source = runner_path.read_bytes()
        module = types.ModuleType("erei_exact_target_eval_runner")
        module.__file__ = str(runner_path)
        exec(compile(source, str(runner_path), "exec"), module.__dict__)
    except (OSError, SyntaxError) as exc:
        raise ExactTargetEvidenceError(f"unable to load eval runner for exact-target reconstruction: {exc}") from exc
    return module


def _git(repo_root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise ExactTargetEvidenceError(f"git {' '.join(args)} failed: {process.stderr.strip()}")
    return process.stdout.strip()


def _is_git_checkout(repo_root: Path) -> bool:
    process = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--is-inside-work-tree"],
        text=True,
        capture_output=True,
        check=False,
    )
    return process.returncode == 0 and process.stdout.strip() == "true"


def _first_add_commit(repo_root: Path, path: Path, closure_ref: str = "HEAD") -> str:
    commits = [
        row.strip()
        for row in _git(
            repo_root,
            "log",
            "--diff-filter=A",
            "--reverse",
            "--format=%H",
            closure_ref,
            "--",
            path.as_posix(),
        ).splitlines()
        if row.strip()
    ]
    if len(commits) != 1:
        raise ExactTargetEvidenceError(
            f"retained evidence path must have exactly one first-add commit in current history: {path}"
        )
    return _sha40(commits[0], f"first-add commit for {path}")


def _validate_history_binding(
    repo_root: Path,
    identity: dict[str, Any],
    *,
    closure_ref: str = "HEAD",
    materialized_root: Path | None = None,
) -> dict[str, Any]:
    if not _is_git_checkout(repo_root):
        raise ExactTargetEvidenceError("governed history verification requires an original Git checkout")
    if closure_ref != "HEAD":
        _sha40(closure_ref, "history closure_ref")
        if _git(repo_root, "rev-parse", f"{closure_ref}^{{commit}}") != closure_ref:
            raise ExactTargetEvidenceError("history closure_ref does not identify its exact commit")
    manifest_path = Path(identity["run_manifest_path"])
    evidence_path = Path(identity["execution_evidence_path"])
    identity_path = Path(identity["runtime_identity_path"])
    paths = (manifest_path, evidence_path, identity_path)
    first_adds = {_first_add_commit(repo_root, path, closure_ref) for path in paths}
    if len(first_adds) != 1:
        raise ExactTargetEvidenceError(
            "retained exact-target manifest, execution evidence, and runtime identity must be added by one commit"
        )
    evidence_commit = next(iter(first_adds))
    parents = _git(repo_root, "rev-list", "--parents", "-n", "1", evidence_commit).split()
    if len(parents) != 2:
        raise ExactTargetEvidenceError("exact-target evidence commit must be a single-parent commit")
    parent = _sha40(parents[1], "exact-target evidence commit parent")
    if parent != identity["release_carrier_ref"]:
        raise ExactTargetEvidenceError(
            "exact-target evidence commit parent must equal the recorded release_carrier_ref"
        )
    first_parent_history = {
        row.strip()
        for row in _git(repo_root, "rev-list", "--first-parent", closure_ref).splitlines()
        if row.strip()
    }
    if evidence_commit not in first_parent_history:
        raise ExactTargetEvidenceError(
            "exact-target evidence commit must be on the release HEAD first-parent history"
        )

    changes: list[tuple[str, str]] = []
    raw = _git(
        repo_root,
        "diff-tree",
        "--no-commit-id",
        "--name-status",
        "-r",
        "--no-renames",
        evidence_commit,
    )
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            raise ExactTargetEvidenceError(f"unexpected evidence commit diff row: {line}")
        changes.append((parts[0], parts[1]))
    expected_changes = {("A", path.as_posix()) for path in paths}
    if set(changes) != expected_changes or len(changes) != 3:
        raise ExactTargetEvidenceError(
            "exact-target evidence commit must add exactly the retained manifest, execution evidence, and runtime identity"
        )

    # Endpoint blob equality alone misses a change that was later reverted.
    # Traverse the full *first-parent* closure and reject each content change
    # to any governed file after its one-shot import, including later reverts.
    later_commits = [
        value.strip()
        for value in _git(
            repo_root, "rev-list", "--first-parent",
            f"{evidence_commit}..{closure_ref}",
        ).splitlines()
        if value.strip()
    ]
    for commit in later_commits:
        parents = _git(repo_root, "rev-list", "--parents", "-n", "1", commit).split()
        if len(parents) < 2:
            raise ExactTargetEvidenceError("post-import first-parent history has no parent")
        changed = _git(
            repo_root, "diff-tree", "--no-commit-id", "--name-only", "-r",
            parents[1], commit, "--", *(p.as_posix() for p in paths),
        )
        if changed:
            raise ExactTargetEvidenceError(
                "retained exact-target evidence changed after its evidence commit: " + changed
            )

    for path in paths:
        first_blob = _git(repo_root, "rev-parse", f"{evidence_commit}:{path.as_posix()}")
        current_blob = _git(repo_root, "rev-parse", f"{closure_ref}:{path.as_posix()}")
        if first_blob != current_blob:
            raise ExactTargetEvidenceError(
                f"retained exact-target evidence changed after its evidence commit: {path.as_posix()}"
            )
        if materialized_root is not None:
            copied = (materialized_root / path).resolve()
            try:
                if not copied.is_file() or not copied.is_relative_to(materialized_root.resolve()):
                    raise ExactTargetEvidenceError(f"materialized evidence file is missing or outside carrier: {path}")
                source_blob = _git(repo_root, "hash-object", str(copied))
            except (OSError, ValueError) as exc:
                raise ExactTargetEvidenceError(f"unable to verify materialized evidence file: {path}") from exc
            if source_blob != current_blob:
                raise ExactTargetEvidenceError(
                    f"materialized evidence bytes differ from exact carrier Git blob: {path.as_posix()}"
                )
    return {
        "evidence_commit": evidence_commit,
        "release_carrier_ref": parent,
        "retained_paths": [path.as_posix() for path in paths],
    }


def validate_run_manifest(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ExactTargetEvidenceError("exact-target run manifest must be an object")
    root_fields = {
        "schema_version", "run_id", "produced_at", "framework_revision", "adapter",
        "runtime", "adapter_command_digest", "executions",
    }
    _exact_fields(data, root_fields, "run manifest")
    if data["schema_version"] != 2:
        raise ExactTargetEvidenceError("exact-target run manifest schema_version must be 2 for reconstructible evidence")
    if not isinstance(data["run_id"], str) or not RUN_ID_RE.fullmatch(data["run_id"]):
        raise ExactTargetEvidenceError("run_id must match ETR-YYYYMMDDTHHMMSSZ-XXXXXXXX")
    _datetime(data["produced_at"], "produced_at")
    _sha40(data["framework_revision"], "framework_revision")
    _sha256(data["adapter_command_digest"], "adapter_command_digest")

    adapter = data["adapter"]
    if not isinstance(adapter, dict):
        raise ExactTargetEvidenceError("adapter must be an object")
    _exact_fields(adapter, {"id", "revision"}, "adapter")
    _text(adapter["id"], "adapter.id")
    _sha40(adapter["revision"], "adapter.revision")

    runtime = data["runtime"]
    if not isinstance(runtime, dict):
        raise ExactTargetEvidenceError("runtime must be an object")
    _exact_fields(runtime, {"id", "version", "independent_runtime", "identity_evidence"}, "runtime")
    _text(runtime["id"], "runtime.id")
    _text(runtime["version"], "runtime.version")
    if runtime["independent_runtime"] is not True:
        raise ExactTargetEvidenceError("exact-target run requires independent_runtime=true")
    identity_evidence = runtime["identity_evidence"]
    if not isinstance(identity_evidence, list) or not identity_evidence:
        raise ExactTargetEvidenceError("runtime.identity_evidence must be a non-empty array")
    normalized = [_text(item, "runtime.identity_evidence item") for item in identity_evidence]
    if len(set(normalized)) != len(normalized):
        raise ExactTargetEvidenceError("runtime.identity_evidence contains duplicates")

    executions = data["executions"]
    if not isinstance(executions, list) or not executions:
        raise ExactTargetEvidenceError("executions must be a non-empty array")
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(executions):
        if not isinstance(item, dict):
            raise ExactTargetEvidenceError(f"executions[{index}] must be an object")
        fields = {"suite_id", "case_id", "status", "response_digest", "response", "adapter_error"}
        _exact_fields(item, fields, f"executions[{index}]")
        suite = _text(item["suite_id"], f"executions[{index}].suite_id")
        case = _text(item["case_id"], f"executions[{index}].case_id")
        key = (suite, case)
        if key in seen:
            raise ExactTargetEvidenceError(f"duplicate exact-target execution {suite}/{case}")
        seen.add(key)
        if item["status"] not in {"pass", "fail"}:
            raise ExactTargetEvidenceError(f"executions[{index}].status must be pass or fail")
        digest = _sha256(item["response_digest"], f"executions[{index}].response_digest")
        if type(item["adapter_error"]) is not bool:
            raise ExactTargetEvidenceError(f"executions[{index}].adapter_error must be a boolean")
        if item["adapter_error"]:
            if item["response"] is not None:
                raise ExactTargetEvidenceError(f"executions[{index}] adapter_error requires response=null")
            if item["status"] != "fail":
                raise ExactTargetEvidenceError(f"executions[{index}] adapter_error cannot be recorded as pass")
            expected_digest = _adapter_error_digest(suite, case)
        else:
            response = _validate_retained_response(item["response"], f"executions[{index}].response")
            expected_digest = _canonical_digest(response)
        if digest != expected_digest:
            raise ExactTargetEvidenceError(f"executions[{index}] response_digest does not match retained response")
    return data


def parse_evidence_ref(value: Any) -> tuple[Path, str, str]:
    text = _text(value, "evidence_ref")
    match = REF_RE.fullmatch(text)
    if not match:
        raise ExactTargetEvidenceError("exact-target evidence_ref must use exact-target-run:<path>#<suite>/<case>")
    raw_path = match.group("path")
    path = Path(raw_path)
    if path.is_absolute() or ".." in path.parts or not raw_path.startswith("evals/exact-target-runs/") or path.suffix != ".json":
        raise ExactTargetEvidenceError("exact-target evidence_ref path must be a relative JSON path under evals/exact-target-runs/")
    if path.name.endswith(".identity.json"):
        raise ExactTargetEvidenceError("exact-target evidence_ref cannot point to a runtime identity file")
    return path, match.group("suite"), match.group("case")


def _published_case(repo_root: Path, suite_id: str, case_id: str):
    runner = _load_runner(repo_root)
    matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for suite_path in runner.discover_suites([str(repo_root / "evals" / "cases")]):
        suite = runner.load_json(suite_path)
        errors = runner.validate_suite(suite, str(suite_path))
        if errors:
            raise ExactTargetEvidenceError("published eval suite invalid during evidence reconstruction: " + "; ".join(errors))
        if suite.get("suite_id") != suite_id:
            continue
        if not runner.suite_required_for_level(suite, "exact_target_runtime"):
            raise ExactTargetEvidenceError(f"suite {suite_id} is not eligible for exact_target_runtime evidence")
        for case in suite["cases"]:
            if case.get("id") == case_id:
                matches.append((suite, case))
    if len(matches) != 1:
        raise ExactTargetEvidenceError(
            f"expected exactly one published behavioral case for {suite_id}/{case_id}, found {len(matches)}"
        )
    return runner, matches[0][0], matches[0][1]


def _durable_identity_binding(
    repo_root: Path,
    framework_revision: str,
    manifest_path: Path,
    manifest: dict[str, Any],
    execution: dict[str, Any],
) -> dict[str, Any]:
    try:
        identity_path = exact_target_package_identity.identity_path_for_manifest(manifest_path)
    except exact_target_package_identity.ExactTargetPackageIdentityError as exc:
        raise ExactTargetEvidenceError(str(exc)) from exc
    identity_file = repo_root / identity_path
    try:
        identity = exact_target_package_identity.validate_runtime_identity(
            _load_json(identity_file, "runtime identity")
        )
    except exact_target_package_identity.ExactTargetPackageIdentityError as exc:
        raise ExactTargetEvidenceError(f"runtime identity invalid: {exc}") from exc

    if identity["repository"] != OFFICIAL_REPOSITORY:
        raise ExactTargetEvidenceError("runtime identity repository does not match official Framework repository")
    if Path(identity["run_manifest_path"]) != manifest_path:
        raise ExactTargetEvidenceError("runtime identity run_manifest_path does not match evidence_ref manifest")
    if Path(identity["runtime_identity_path"]) != identity_path:
        raise ExactTargetEvidenceError("runtime identity retained path does not match derived identity path")
    if identity["framework_ref"] != framework_revision or manifest["framework_revision"] != framework_revision:
        raise ExactTargetEvidenceError("runtime identity/framework manifest revision mismatch")
    if identity["adapter_id"] != manifest["adapter"]["id"] or identity["adapter_id"] != execution.get("adapter_id"):
        raise ExactTargetEvidenceError("runtime identity adapter id mismatch")
    if identity["adapter_revision"] != manifest["adapter"]["revision"] or identity["adapter_revision"] != execution.get("adapter_revision"):
        raise ExactTargetEvidenceError("runtime identity adapter revision mismatch")
    if identity["runtime_id"] != manifest["runtime"]["id"]:
        raise ExactTargetEvidenceError("runtime identity runtime id mismatch")
    if identity["runtime_version"] != manifest["runtime"]["version"]:
        raise ExactTargetEvidenceError("runtime identity runtime version mismatch")
    if identity["run_id"] != manifest["run_id"]:
        raise ExactTargetEvidenceError("runtime identity run_id mismatch")
    if set(manifest["runtime"]["identity_evidence"]) != exact_target_package_identity.expected_runtime_evidence(identity):
        raise ExactTargetEvidenceError("retained runtime provenance does not match run manifest identity evidence")

    manifest_file = repo_root / manifest_path
    if _file_digest(manifest_file, "run manifest") != identity["run_manifest_sha256"]:
        raise ExactTargetEvidenceError("retained run manifest digest does not match runtime identity")

    evidence_path = Path(identity["execution_evidence_path"])
    evidence_file = repo_root / evidence_path
    if _file_digest(evidence_file, "execution evidence") != identity["execution_evidence_sha256"]:
        raise ExactTargetEvidenceError("retained execution evidence digest does not match runtime identity")
    runner = _load_runner(repo_root)
    try:
        evidence = runner.validate_execution_evidence(_load_json(evidence_file, "execution evidence"))
    except Exception as exc:
        raise ExactTargetEvidenceError(f"retained execution evidence is invalid: {exc}") from exc
    if evidence.get("schema_version") != 2:
        raise ExactTargetEvidenceError("retained exact-target execution evidence must use schema_version 2")
    if evidence.get("framework_revision") != framework_revision:
        raise ExactTargetEvidenceError("retained execution evidence framework revision mismatch")
    matches = [
        row for row in evidence["executions"]
        if row.get("suite_id") == execution.get("suite_id") and row.get("case_id") == execution.get("case_id")
    ]
    if len(matches) != 1:
        raise ExactTargetEvidenceError("retained execution evidence must contain the referenced case exactly once")
    if matches[0] != execution:
        raise ExactTargetEvidenceError("caller execution row does not match digest-bound retained execution evidence")
    return identity


def validate_binding(
    repo_root: Path,
    framework_revision: str,
    execution: dict[str, Any],
    *,
    history_repo: Path | None = None,
    history_ref: str = "HEAD",
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    if execution.get("assurance_level") != "exact_target_runtime" or execution.get("independent_runtime") is not True:
        raise ExactTargetEvidenceError("binding validation requires exact_target_runtime with independent_runtime=true")
    path, suite_id, case_id = parse_evidence_ref(execution.get("evidence_ref"))
    if suite_id != execution.get("suite_id") or case_id != execution.get("case_id"):
        raise ExactTargetEvidenceError("evidence_ref suite/case does not match execution record")
    manifest = validate_run_manifest(_load_json(repo_root / path, "exact-target run manifest"))
    if manifest["framework_revision"] != framework_revision:
        raise ExactTargetEvidenceError("exact-target run framework_revision mismatch")
    if manifest["adapter"]["id"] != execution.get("adapter_id"):
        raise ExactTargetEvidenceError("exact-target run adapter_id mismatch")
    if manifest["adapter"]["revision"] != execution.get("adapter_revision"):
        raise ExactTargetEvidenceError("exact-target run adapter_revision mismatch")

    identity = _durable_identity_binding(repo_root, framework_revision, path, manifest, execution)
    if history_repo is not None:
        # Stable carrier validation materializes files without .git. Verify the
        # ORIGINAL Git history and exact carrier revision instead of skipping it.
        _validate_history_binding(
            Path(history_repo).resolve(), identity,
            closure_ref=history_ref, materialized_root=repo_root,
        )
    elif _is_git_checkout(repo_root):
        _validate_history_binding(repo_root, identity)

    match = next(
        (item for item in manifest["executions"] if item["suite_id"] == suite_id and item["case_id"] == case_id),
        None,
    )
    if match is None:
        raise ExactTargetEvidenceError("exact-target run manifest does not contain referenced case")
    if match["status"] != execution.get("status"):
        raise ExactTargetEvidenceError("exact-target run case status mismatch")

    runner, _suite, case = _published_case(repo_root, suite_id, case_id)
    if match["adapter_error"]:
        if match["status"] != "fail":
            raise ExactTargetEvidenceError("adapter-error execution cannot validate as pass")
        return manifest

    try:
        response = runner.validate_adapter_response(match["response"], case["expectations"])
        scorer_results = [runner.score(expectation, response) for expectation in case["expectations"]]
    except Exception as exc:
        raise ExactTargetEvidenceError(f"retained response cannot be revalidated: {exc}") from exc
    recomputed_status = "pass" if all(item[0] for item in scorer_results) else "fail"
    if recomputed_status != match["status"]:
        raise ExactTargetEvidenceError(
            f"retained response rescoring mismatch: stored={match['status']} recomputed={recomputed_status}"
        )
    if recomputed_status != execution.get("status"):
        raise ExactTargetEvidenceError("execution evidence status does not match reconstructed scorer result")
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    args = parser.parse_args(argv)
    try:
        result = validate_run_manifest(_load_json(Path(args.manifest), "run manifest"))
    except ExactTargetEvidenceError as exc:
        print(f"ERROR: {exc}")
        return 2
    print(json.dumps({"status": "valid", "run_id": result["run_id"], "executions": len(result["executions"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
