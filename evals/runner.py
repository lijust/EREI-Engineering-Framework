#!/usr/bin/env python3
"""EREI Engineering Framework zero-dependency evaluation runner."""
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
SUPPORTED_SCORERS = {
    "output_contains_all",
    "output_contains_none",
    "output_regex",
    "metadata_equals",
    "trace_tool_called",
    "trace_tool_not_called",
    "max_trace_steps",
}
TRACE_SCORERS = {"trace_tool_called", "trace_tool_not_called", "max_trace_steps"}
ASSURANCE_LEVELS = {
    "harness_smoke": 0,
    "reference_contract": 1,
    "managed_runtime": 2,
    "exact_target_runtime": 3,
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _valid_datetime(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate_suite(data: Any, source: str = "<memory>") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{source}: root must be an object"]
    allowed_root = {"schema_version", "suite_id", "artifact", "cases"}
    unknown_root = sorted(set(data) - allowed_root)
    if unknown_root:
        errors.append(f"{source}: unknown root fields: {unknown_root}")
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{source}: schema_version must be {SCHEMA_VERSION}")
    if not isinstance(data.get("suite_id"), str) or not data.get("suite_id"):
        errors.append(f"{source}: suite_id is required")
    if not isinstance(data.get("artifact"), str) or not data.get("artifact"):
        errors.append(f"{source}: artifact is required")

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        return errors + [f"{source}: cases must be a non-empty array"]

    seen: set[str] = set()
    for index, case in enumerate(cases):
        prefix = f"{source}: cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{prefix} must be an object")
            continue
        unknown_case = sorted(set(case) - {"id", "input", "expectations", "context", "tags"})
        if unknown_case:
            errors.append(f"{prefix} unknown fields: {unknown_case}")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"{prefix}.id is required")
        elif case_id in seen:
            errors.append(f"{prefix}.id duplicate: {case_id}")
        else:
            seen.add(case_id)
        if not isinstance(case.get("input"), dict):
            errors.append(f"{prefix}.input must be an object")
        if "context" in case and not isinstance(case["context"], dict):
            errors.append(f"{prefix}.context must be an object")
        if "tags" in case and (not isinstance(case["tags"], list) or not all(isinstance(tag, str) for tag in case["tags"])):
            errors.append(f"{prefix}.tags must be an array of strings")

        expectations = case.get("expectations")
        if not isinstance(expectations, list) or not expectations:
            errors.append(f"{prefix}.expectations must be a non-empty array")
            continue
        for expectation_index, expectation in enumerate(expectations):
            ep = f"{prefix}.expectations[{expectation_index}]"
            if not isinstance(expectation, dict):
                errors.append(f"{ep} must be an object")
                continue
            scorer_type = expectation.get("type")
            if scorer_type not in SUPPORTED_SCORERS:
                errors.append(f"{ep}.type unsupported: {scorer_type!r}")
                continue
            if scorer_type in {"output_contains_all", "output_contains_none"}:
                values = expectation.get("values")
                if not isinstance(values, list) or not values or not all(isinstance(v, str) for v in values):
                    errors.append(f"{ep}.values must be a non-empty array of strings")
            elif scorer_type == "output_regex":
                pattern = expectation.get("pattern")
                if not isinstance(pattern, str) or not pattern:
                    errors.append(f"{ep}.pattern is required")
                else:
                    try:
                        re.compile(pattern)
                    except re.error as exc:
                        errors.append(f"{ep}.pattern invalid regex: {exc}")
            elif scorer_type == "metadata_equals":
                if not isinstance(expectation.get("key"), str) or not expectation.get("key") or "value" not in expectation:
                    errors.append(f"{ep} requires key and value")
            elif scorer_type in {"trace_tool_called", "trace_tool_not_called"}:
                if not isinstance(expectation.get("tool"), str) or not expectation.get("tool"):
                    errors.append(f"{ep}.tool is required")
            elif scorer_type == "max_trace_steps":
                value = expectation.get("value")
                if type(value) is not int or value < 0:
                    errors.append(f"{ep}.value must be an integer >= 0")
    return errors


def discover_suites(paths: list[str]) -> list[Path]:
    suites: list[Path] = []
    for raw in paths:
        path = Path(raw)
        suites.extend(sorted(path.rglob("*.eval.json")) if path.is_dir() else [path])
    return suites


def nested_value(mapping: dict[str, Any], dotted_key: str) -> Any:
    current: Any = mapping
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted_key)
        current = current[part]
    return current


def validate_adapter_response(response: Any, expectations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if not isinstance(response, dict):
        raise RuntimeError("adapter response must be a JSON object")
    if "output" not in response:
        raise RuntimeError("adapter response must contain output")
    if "metadata" in response and not isinstance(response["metadata"], dict):
        raise RuntimeError("adapter response metadata must be an object")
    if "trace" in response:
        trace = response["trace"]
        if not isinstance(trace, list):
            raise RuntimeError("adapter response trace must be an array")
        for index, step in enumerate(trace):
            if not isinstance(step, dict):
                raise RuntimeError(f"adapter response trace[{index}] must be an object")
            if "type" in step and not isinstance(step["type"], str):
                raise RuntimeError(f"adapter response trace[{index}].type must be a string")
            if step.get("type") == "tool" and (not isinstance(step.get("name"), str) or not step["name"]):
                raise RuntimeError(f"adapter response trace[{index}] tool step requires name")
    required_expectations = expectations or []
    if any(item.get("type") in TRACE_SCORERS for item in required_expectations) and "trace" not in response:
        raise RuntimeError("trace evidence is required by this eval case but is missing")
    if any(item.get("type") == "metadata_equals" for item in required_expectations) and "metadata" not in response:
        raise RuntimeError("metadata evidence is required by this eval case but is missing")
    return response


def trace_tool_names(trace: Any) -> list[str]:
    if not isinstance(trace, list):
        raise RuntimeError("trace evidence must be an array")
    names: list[str] = []
    for index, step in enumerate(trace):
        if not isinstance(step, dict):
            raise RuntimeError(f"trace[{index}] must be an object")
        if step.get("type") == "tool":
            name = step.get("name")
            if not isinstance(name, str) or not name:
                raise RuntimeError(f"trace[{index}] tool step requires name")
            names.append(name)
    return names


def score(expectation: dict[str, Any], response: dict[str, Any]) -> tuple[bool, str]:
    scorer_type = expectation["type"]
    output = response.get("output", "")
    if not isinstance(output, str):
        output = json.dumps(output, ensure_ascii=False, sort_keys=True)
    lower_output = output.lower()

    if scorer_type == "output_contains_all":
        missing = [v for v in expectation["values"] if v.lower() not in lower_output]
        return (not missing, "all required values present" if not missing else f"missing: {missing}")
    if scorer_type == "output_contains_none":
        found = [v for v in expectation["values"] if v.lower() in lower_output]
        return (not found, "no forbidden values present" if not found else f"forbidden values found: {found}")
    if scorer_type == "output_regex":
        matched = re.search(expectation["pattern"], output, flags=re.MULTILINE) is not None
        return (matched, "regex matched" if matched else f"regex did not match: {expectation['pattern']}")
    if scorer_type == "metadata_equals":
        try:
            actual = nested_value(response["metadata"], expectation["key"])
        except (KeyError, TypeError):
            return (False, f"metadata key missing: {expectation['key']}")
        return (actual == expectation["value"], f"actual={actual!r}, expected={expectation['value']!r}")

    trace = response.get("trace")
    if trace is None:
        return (False, "trace evidence missing")
    names = trace_tool_names(trace)
    if scorer_type == "trace_tool_called":
        return (expectation["tool"] in names, f"tools={names!r}")
    if scorer_type == "trace_tool_not_called":
        return (expectation["tool"] not in names, f"tools={names!r}")
    if scorer_type == "max_trace_steps":
        count = len(trace)
        return (count <= expectation["value"], f"trace_steps={count}, max={expectation['value']}")
    raise RuntimeError(f"unsupported scorer at runtime: {scorer_type}")


def call_adapter(command: str, request: dict[str, Any], timeout: float, expectations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    argv = shlex.split(command)
    if not argv:
        raise RuntimeError("adapter command is empty")
    process = subprocess.run(
        argv,
        input=json.dumps(request, ensure_ascii=False),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(f"adapter exited {process.returncode}; stderr={process.stderr.strip()!r}")
    try:
        response = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"adapter stdout is not valid JSON: {exc}") from exc
    return validate_adapter_response(response, expectations)


def command_validate(args: argparse.Namespace) -> int:
    suites = discover_suites(args.paths)
    if not suites:
        print("No *.eval.json suites found.", file=sys.stderr)
        return 2
    all_errors: list[str] = []
    for path in suites:
        try:
            errors = validate_suite(load_json(path), str(path))
        except Exception as exc:
            errors = [f"{path}: {exc}"]
        if errors:
            all_errors.extend(errors)
        else:
            print(f"PASS validate {path}")
    for error in all_errors:
        print(f"FAIL {error}", file=sys.stderr)
    return 1 if all_errors else 0


def command_run(args: argparse.Namespace) -> int:
    suites = discover_suites(args.paths)
    if not suites:
        print("No *.eval.json suites found.", file=sys.stderr)
        return 2
    total = 0
    failed = 0
    for path in suites:
        data = load_json(path)
        errors = validate_suite(data, str(path))
        if errors:
            for error in errors:
                print(f"FAIL {error}", file=sys.stderr)
            return 2
        for case in data["cases"]:
            total += 1
            request = {
                "protocol_version": "1.0",
                "suite_id": data["suite_id"],
                "case_id": case["id"],
                "artifact": data["artifact"],
                "input": case["input"],
                "context": case.get("context", {}),
                "tags": case.get("tags", []),
            }
            try:
                response = call_adapter(args.adapter, request, args.timeout, case["expectations"])
                results = [(expectation["type"],) + score(expectation, response) for expectation in case["expectations"]]
                passed = all(result[1] for result in results)
            except Exception as exc:
                passed = False
                results = [("adapter/evidence", False, str(exc))]
            print(("PASS" if passed else "FAIL"), f"{data['suite_id']}/{case['id']}")
            for scorer_type, scorer_passed, detail in results:
                print(" ", "PASS" if scorer_passed else "FAIL", scorer_type, detail)
            if not passed:
                failed += 1
    print(f"Summary: {total - failed} passed, {failed} failed, {total} total")
    return 1 if failed else 0


def _expected_cases(paths: list[str]) -> set[tuple[str, str]]:
    expected: set[tuple[str, str]] = set()
    for path in discover_suites(paths):
        data = load_json(path)
        errors = validate_suite(data, str(path))
        if errors:
            raise RuntimeError("; ".join(errors))
        for case in data["cases"]:
            expected.add((data["suite_id"], case["id"]))
    return expected


def execution_assurance_level(execution: dict[str, Any], schema_version: int) -> str:
    return "harness_smoke" if schema_version == 1 else execution["assurance_level"]


def validate_execution_evidence(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise RuntimeError("execution evidence root must be an object")
    version = data.get("schema_version")
    if version == 1:
        required = {"schema_version", "framework_revision", "executions"}
    elif version == 2:
        required = {"schema_version", "framework_revision", "produced_at", "executions"}
    else:
        raise RuntimeError("unsupported execution evidence schema_version")
    unknown = sorted(set(data) - required)
    if unknown or set(data) != required:
        raise RuntimeError(f"execution evidence V{version} has unexpected/missing fields")
    revision = data["framework_revision"]
    if not isinstance(revision, str) or not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise RuntimeError("framework_revision must be an exact commit")
    if version == 2 and not _valid_datetime(data["produced_at"]):
        raise RuntimeError("produced_at must be a valid date-time")
    executions = data["executions"]
    if not isinstance(executions, list):
        raise RuntimeError("executions must be an array")
    seen: set[tuple[str, str]] = set()
    for index, execution in enumerate(executions):
        if not isinstance(execution, dict):
            raise RuntimeError(f"executions[{index}] must be an object")
        if version == 1:
            required_execution = {"suite_id", "case_id", "status", "adapter_id", "evidence_ref"}
        else:
            required_execution = {
                "suite_id", "case_id", "status", "adapter_id", "adapter_revision",
                "assurance_level", "independent_runtime", "evidence_ref",
            }
        if set(execution) != required_execution:
            raise RuntimeError(f"executions[{index}] has unexpected/missing fields")
        key = (execution["suite_id"], execution["case_id"])
        if not all(isinstance(item, str) and item for item in key):
            raise RuntimeError(f"executions[{index}] suite_id/case_id are required")
        if key in seen:
            raise RuntimeError(f"duplicate execution evidence: {key}")
        seen.add(key)
        if execution["status"] not in {"pass", "fail", "inconclusive"}:
            raise RuntimeError(f"executions[{index}] invalid status")
        if not isinstance(execution["adapter_id"], str) or not execution["adapter_id"]:
            raise RuntimeError(f"executions[{index}] adapter_id required")
        if not isinstance(execution["evidence_ref"], str) or not execution["evidence_ref"]:
            raise RuntimeError(f"executions[{index}] evidence_ref required")
        if version == 2:
            adapter_revision = execution["adapter_revision"]
            if not isinstance(adapter_revision, str) or not re.fullmatch(r"[a-f0-9]{40}", adapter_revision):
                raise RuntimeError(f"executions[{index}] adapter_revision must be an exact commit")
            level = execution["assurance_level"]
            if level not in ASSURANCE_LEVELS:
                raise RuntimeError(f"executions[{index}] invalid assurance_level")
            if type(execution["independent_runtime"]) is not bool:
                raise RuntimeError(f"executions[{index}] independent_runtime must be boolean")
            if level == "reference_contract" and execution["independent_runtime"]:
                raise RuntimeError(f"executions[{index}] reference_contract cannot claim independent runtime")
            if level in {"managed_runtime", "exact_target_runtime"} and not execution["independent_runtime"]:
                raise RuntimeError(f"executions[{index}] {level} requires independent_runtime=true")
    return data


def command_coverage(args: argparse.Namespace) -> int:
    try:
        expected = _expected_cases(args.paths)
        evidence = validate_execution_evidence(load_json(Path(args.evidence)))
    except Exception as exc:
        print(f"FAIL coverage evidence: {exc}", file=sys.stderr)
        return 2
    minimum_level = args.minimum_level
    schema_version = evidence["schema_version"]
    observed = {(item["suite_id"], item["case_id"]): item for item in evidence["executions"]}
    eligible = {
        key: item for key, item in observed.items()
        if ASSURANCE_LEVELS[execution_assurance_level(item, schema_version)] >= ASSURANCE_LEVELS[minimum_level]
    }
    passed = {key for key, item in eligible.items() if item["status"] == "pass"}
    missing = sorted(expected - set(observed))
    lower_assurance = sorted((expected & set(observed)) - set(eligible))
    nonpass = sorted(key for key in expected & set(eligible) if eligible[key]["status"] != "pass")
    extras = sorted(set(observed) - expected)
    coverage = 0.0 if not expected else round(len(passed & expected) / len(expected), 4)
    payload = {
        "framework_revision": evidence["framework_revision"],
        "minimum_assurance_level": minimum_level,
        "expected_cases": len(expected),
        "evidence_records": len(observed),
        "passing_cases_at_level": len(passed & expected),
        "coverage": coverage,
        "missing": [f"{suite}/{case}" for suite, case in missing],
        "lower_assurance": [f"{suite}/{case}" for suite, case in lower_assurance],
        "nonpassing": [f"{suite}/{case}" for suite, case in nonpass],
        "unexpected": [f"{suite}/{case}" for suite, case in extras],
        "complete": not missing and not lower_assurance and not nonpass and not extras,
    }
    print(json.dumps(payload, sort_keys=True))
    if args.require_complete and not payload["complete"]:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EREI zero-dependency eval harness")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="validate machine-readable eval suites")
    validate.add_argument("paths", nargs="+")
    validate.set_defaults(func=command_validate)
    run = subparsers.add_parser("run", help="run suites through a CLI adapter")
    run.add_argument("paths", nargs="+")
    run.add_argument("--adapter", required=True)
    run.add_argument("--timeout", type=float, default=120.0)
    run.set_defaults(func=command_run)
    coverage = subparsers.add_parser("coverage", help="measure retained execution evidence coverage at a stated assurance level")
    coverage.add_argument("paths", nargs="+")
    coverage.add_argument("--evidence", required=True)
    coverage.add_argument("--minimum-level", choices=tuple(ASSURANCE_LEVELS), default="harness_smoke")
    coverage.add_argument("--require-complete", action="store_true")
    coverage.set_defaults(func=command_coverage)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
