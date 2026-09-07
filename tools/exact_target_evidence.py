#!/usr/bin/env python3
"""Validate exact-target eval run manifests and bind V2 execution evidence to them."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

SHA40_RE = re.compile(r"^[a-f0-9]{40}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
RUN_ID_RE = re.compile(r"^ETR-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
REF_RE = re.compile(r"^exact-target-run:(?P<path>[^#]+)#(?P<suite>[^/]+)/(?P<case>[^/]+)$")


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


def validate_run_manifest(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ExactTargetEvidenceError("exact-target run manifest must be an object")
    root_fields = {
        "schema_version", "run_id", "produced_at", "framework_revision", "adapter",
        "runtime", "adapter_command_digest", "executions",
    }
    _exact_fields(data, root_fields, "run manifest")
    if data["schema_version"] != 1:
        raise ExactTargetEvidenceError("run manifest schema_version must be 1")
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
        _exact_fields(item, {"suite_id", "case_id", "status", "response_digest"}, f"executions[{index}]")
        suite = _text(item["suite_id"], f"executions[{index}].suite_id")
        case = _text(item["case_id"], f"executions[{index}].case_id")
        key = (suite, case)
        if key in seen:
            raise ExactTargetEvidenceError(f"duplicate exact-target execution {suite}/{case}")
        seen.add(key)
        if item["status"] not in {"pass", "fail", "inconclusive"}:
            raise ExactTargetEvidenceError(f"executions[{index}].status invalid")
        _sha256(item["response_digest"], f"executions[{index}].response_digest")
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


def validate_binding(repo_root: Path, framework_revision: str, execution: dict[str, Any]) -> dict[str, Any]:
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
