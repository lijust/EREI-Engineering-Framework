#!/usr/bin/env python3
"""EREI Engineering Framework zero-dependency evaluation runner."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_suite(data: Any, source: str = "<memory>") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{source}: root must be an object"]
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
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"{prefix}.id is required")
        elif case_id in seen:
            errors.append(f"{prefix}.id duplicate: {case_id}")
        else:
            seen.add(case_id)
        if not isinstance(case.get("input"), dict):
            errors.append(f"{prefix}.input must be an object")

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
                if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
                    errors.append(f"{ep}.values must be an array of strings")
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
                if not isinstance(expectation.get("key"), str) or "value" not in expectation:
                    errors.append(f"{ep} requires key and value")
            elif scorer_type in {"trace_tool_called", "trace_tool_not_called"}:
                if not isinstance(expectation.get("tool"), str) or not expectation.get("tool"):
                    errors.append(f"{ep}.tool is required")
            elif scorer_type == "max_trace_steps":
                value = expectation.get("value")
                if not isinstance(value, int) or value < 0:
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
        current = current[part]
    return current


def trace_tool_names(trace: Any) -> list[str]:
    if not isinstance(trace, list):
        return []
    return [
        step["name"]
        for step in trace
        if isinstance(step, dict)
        and step.get("type") == "tool"
        and isinstance(step.get("name"), str)
    ]


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
            actual = nested_value(response.get("metadata", {}), expectation["key"])
        except (KeyError, TypeError):
            return (False, f"metadata key missing: {expectation['key']}")
        return (actual == expectation["value"], f"actual={actual!r}, expected={expectation['value']!r}")

    names = trace_tool_names(response.get("trace", []))
    if scorer_type == "trace_tool_called":
        return (expectation["tool"] in names, f"tools={names!r}")
    if scorer_type == "trace_tool_not_called":
        return (expectation["tool"] not in names, f"tools={names!r}")
    if scorer_type == "max_trace_steps":
        trace = response.get("trace", [])
        count = len(trace) if isinstance(trace, list) else 0
        return (count <= expectation["value"], f"trace_steps={count}, max={expectation['value']}")

    raise RuntimeError(f"unsupported scorer at runtime: {scorer_type}")


def call_adapter(command: str, request: dict[str, Any], timeout: float) -> dict[str, Any]:
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
    response = json.loads(process.stdout)
    if not isinstance(response, dict) or "output" not in response:
        raise RuntimeError("adapter response must be a JSON object containing output")
    return response


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
                response = call_adapter(args.adapter, request, args.timeout)
                results = [
                    (expectation["type"],) + score(expectation, response)
                    for expectation in case["expectations"]
                ]
                passed = all(result[1] for result in results)
            except Exception as exc:
                passed = False
                results = [("adapter", False, str(exc))]

            print(("PASS" if passed else "FAIL"), f"{data['suite_id']}/{case['id']}")
            for scorer_type, scorer_passed, detail in results:
                print(" ", "PASS" if scorer_passed else "FAIL", scorer_type, detail)
            if not passed:
                failed += 1

    print(f"Summary: {total - failed} passed, {failed} failed, {total} total")
    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EREI zero-dependency eval harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate machine-readable eval suites")
    validate.add_argument("paths", nargs="+", help="suite files or directories")
    validate.set_defaults(func=command_validate)

    run = subparsers.add_parser("run", help="run suites through a CLI adapter")
    run.add_argument("paths", nargs="+", help="suite files or directories")
    run.add_argument("--adapter", required=True, help="adapter command")
    run.add_argument("--timeout", type=float, default=120.0, help="seconds per eval case")
    run.set_defaults(func=command_run)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
