#!/usr/bin/env python3
"""Validate reconstructible exact-target run manifests and bind V2 execution evidence."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

SHA40_RE = re.compile(r"^[a-f0-9]{40}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
RUN_ID_RE = re.compile(r"^ETR-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
REF_RE = re.compile(r"^exact-target-run:(?P<path>[^#]+)#(?P<suite>[^/]+)/(?P<case>[^/]+)$")
RETAINED_RESPONSE_FIELDS = {"output", "metadata", "trace"}


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
    spec = importlib.util.spec_from_file_location("erei_exact_target_eval_runner", runner_path)
    if spec is None or spec.loader is None:
        raise ExactTargetEvidenceError("unable to load eval runner for exact-target reconstruction")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def validate_binding(repo_root: Path, framework_revision: str, execution: dict[str, Any]) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    if execution.get("assurance_level") != "exact_target_runtime" or execution.get("independent_runtime") is not True:
        raise ExactTargetEvidenceError("binding validation requires exact_target_runtime with independent_runtime=true")
    path, suite_id, case_id = parse_evidence_ref(execution.get("evidence_ref"))
    if suite_id != execution.get("suite_id") or case_id != execution.get("case_id"):
        raise ExactTargetEvidenceError("evidence_ref suite/case does not match execution record")
    try:
        manifest = json.loads((repo_root / path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExactTargetEvidenceError(f"unable to load exact-target run manifest {path}: {exc}") from exc
    validate_run_manifest(manifest)
    if manifest["framework_revision"] != framework_revision:
        raise ExactTargetEvidenceError("exact-target run framework_revision mismatch")
    if manifest["adapter"]["id"] != execution.get("adapter_id"):
        raise ExactTargetEvidenceError("exact-target run adapter_id mismatch")
    if manifest["adapter"]["revision"] != execution.get("adapter_revision"):
        raise ExactTargetEvidenceError("exact-target run adapter_revision mismatch")
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
        data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        result = validate_run_manifest(data)
    except (OSError, json.JSONDecodeError, ExactTargetEvidenceError) as exc:
        print(f"ERROR: {exc}")
        return 2
    print(json.dumps({"status": "valid", "run_id": result["run_id"], "executions": len(result["executions"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
