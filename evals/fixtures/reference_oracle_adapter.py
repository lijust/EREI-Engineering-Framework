#!/usr/bin/env python3
"""Deterministic reference-contract adapter for executing every EREI eval scorer path.

This is deliberately NOT model/runtime evidence. It derives a canonical response from
the published eval expectations so CI can prove that every case is executable and
that scorer/trace/metadata contracts remain internally consistent. Stable assurance
must use independently produced runtime evidence at the required assurance level.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "evals" / "cases"


def _case(suite_id: str, case_id: str) -> dict[str, Any]:
    for path in sorted(CASES.glob("*.eval.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("suite_id") != suite_id:
            continue
        for case in data.get("cases", []):
            if case.get("id") == case_id:
                return case
    raise RuntimeError(f"unknown eval case: {suite_id}/{case_id}")


def _nested_set(mapping: dict[str, Any], dotted_key: str, value: Any) -> None:
    current = mapping
    parts = dotted_key.split(".")
    for part in parts[:-1]:
        child = current.get(part)
        if child is None:
            child = {}
            current[part] = child
        if not isinstance(child, dict):
            raise RuntimeError(f"metadata expectation collision at {dotted_key}")
        current = child
    leaf = parts[-1]
    if leaf in current and current[leaf] != value:
        raise RuntimeError(f"conflicting metadata expectations at {dotted_key}")
    current[leaf] = value


def build_response(case: dict[str, Any]) -> dict[str, Any]:
    output_parts: list[str] = []
    forbidden: list[str] = []
    metadata: dict[str, Any] = {}
    called_tools: list[str] = []
    forbidden_tools: set[str] = set()
    max_trace_steps: int | None = None
    regex_patterns: list[str] = []

    for expectation in case["expectations"]:
        kind = expectation["type"]
        if kind == "output_contains_all":
            output_parts.extend(expectation["values"])
        elif kind == "output_contains_none":
            forbidden.extend(expectation["values"])
        elif kind == "output_regex":
            regex_patterns.append(expectation["pattern"])
        elif kind == "metadata_equals":
            _nested_set(metadata, expectation["key"], expectation["value"])
        elif kind == "trace_tool_called":
            tool = expectation["tool"]
            if tool not in called_tools:
                called_tools.append(tool)
        elif kind == "trace_tool_not_called":
            forbidden_tools.add(expectation["tool"])
        elif kind == "max_trace_steps":
            max_trace_steps = expectation["value"] if max_trace_steps is None else min(max_trace_steps, expectation["value"])

    conflict_tools = forbidden_tools.intersection(called_tools)
    if conflict_tools:
        raise RuntimeError(f"contradictory trace expectations: {sorted(conflict_tools)}")
    if max_trace_steps is not None and len(called_tools) > max_trace_steps:
        raise RuntimeError("required tool calls exceed max_trace_steps")

    output = " | ".join(dict.fromkeys(output_parts)) or "reference contract response"
    lower = output.lower()
    conflicts = [value for value in forbidden if value.lower() in lower]
    if conflicts:
        raise RuntimeError(f"contradictory output expectations: {conflicts}")
    if regex_patterns:
        raise RuntimeError(
            "reference oracle intentionally refuses to synthesize arbitrary regex output; "
            f"case must provide explicit reference fixture for patterns={regex_patterns!r}"
        )

    response: dict[str, Any] = {
        "output": output,
        "evidence": {
            "level": "reference_contract",
            "independent_runtime": False,
            "note": "Expectation-derived CI oracle; not target-runtime evidence.",
        },
    }
    if metadata:
        response["metadata"] = metadata
    if any(expectation["type"].startswith("trace_") or expectation["type"] == "max_trace_steps" for expectation in case["expectations"]):
        response["trace"] = [{"type": "tool", "name": tool} for tool in called_tools]
    return response


def main() -> int:
    try:
        request = json.loads(sys.stdin.read())
        if not isinstance(request, dict):
            raise RuntimeError("request must be an object")
        suite_id = request.get("suite_id")
        case_id = request.get("case_id")
        if not isinstance(suite_id, str) or not isinstance(case_id, str):
            raise RuntimeError("suite_id and case_id are required")
        response = build_response(_case(suite_id, case_id))
    except Exception as exc:
        print(f"reference-oracle error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(response, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
