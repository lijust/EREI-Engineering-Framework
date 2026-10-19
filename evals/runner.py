#!/usr/bin/env python3
"""EREI Engineering Framework zero-dependency evaluation runner."""
from __future__ import annotations

import argparse
import json
import os
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
    "behavioral_simulation",
}
TRACE_SCORERS = {"trace_tool_called", "trace_tool_not_called", "max_trace_steps"}
ASSURANCE_LEVELS = {
    "harness_smoke": 0,
    "reference_contract": 1,
    "managed_runtime": 2,
    "exact_target_runtime": 3,
}

ASSURANCE_SCOPES = {"behavioral_runtime", "harness_only"}
RUNTIME_ASSURANCE_LEVELS = {"managed_runtime", "exact_target_runtime"}
SCORER_FIELDS = {
    "output_contains_all": {"type", "values"},
    "output_contains_none": {"type", "values"},
    "output_regex": {"type", "pattern"},
    "metadata_equals": {"type", "key", "value"},
    "trace_tool_called": {"type", "tool"},
    "trace_tool_not_called": {"type", "tool"},
    "max_trace_steps": {"type", "value"},
    "behavioral_simulation": {"type", "decision", "state", "reference_actions"},
}

SIMULATION_CONTRACT = "erei-action-simulation-v1"
SIMULATION_DECISIONS = {
    "capture_task", "omit_task", "request_review", "reject_sensitive_capture",
    "feedback_then_promotion", "allow_capability", "block_capability",
}
SIMULATION_STATE_FIELDS = {
    "task_events", "review_status", "feedback", "promotion_queue",
    "core_modified", "capability_status", "executions",
}


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"non-finite JSON constant: {value}")


def strict_json_loads(text: str) -> Any:
    value = json.loads(text, object_pairs_hook=_strict_object, parse_constant=_reject_constant)
    # Valid JSON numeric syntax such as 1e999 can overflow Python's float parser.
    json.dumps(value, allow_nan=False)
    return value


def _json_identity(value: Any) -> str:
    # JSON equality distinguishes booleans from numbers and refuses NaN/Infinity.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def simulate_actions(initial: Any, actions: Any) -> dict[str, Any]:
    """Apply proposed actions to an in-memory fixture, never a project or tool.

    This reducer records effects; it does not choose the policy-correct action.
    Expected outcomes live in the suite and remain outside the model request.
    """
    if not isinstance(initial, dict) or not initial or set(initial) - SIMULATION_STATE_FIELDS:
        raise ValueError("simulation initial_state contains missing/unknown fields")
    for key, value in initial.items():
        expected_type = bool if key == "core_modified" else str if key.endswith("status") else list
        if type(value) is not expected_type:
            raise ValueError(f"simulation state {key} has invalid type")
    state = strict_json_loads(_json_identity(initial))
    if not isinstance(actions, list) or len(actions) > 16:
        raise ValueError("simulation actions must be an array of at most 16 operations")
    for action in actions:
        if not isinstance(action, dict) or not isinstance(action.get("op"), str):
            raise ValueError("simulation action must contain op")
        op = action["op"]
        if op in {"modify_core", "persist_sensitive"}:
            raise ValueError(f"forbidden effect: {op}")
        fields = {
            "record_task": {"op", "occurrence_id", "outcome", "signals"},
            "request_review": {"op", "status"},
            "record_feedback": {"op", "fingerprint", "evidence_ref"},
            "nominate_candidate": {"op", "fingerprint"},
            "execute_capability": {"op", "capability", "version", "mode"},
            "block_capability": {"op", "reason"},
        }
        if op not in fields or set(action) != fields[op]:
            raise ValueError(f"unknown operation or fields: {op}")
        if any(not isinstance(v, str) or not v.strip() for k, v in action.items() if k != "signals"):
            raise ValueError(f"operation {op} requires non-empty strings")
        if op == "record_task":
            signals = action["signals"]
            if not isinstance(signals, dict) or set(signals) != {"rework_cycles", "verification_failures", "verification_escape"}:
                raise ValueError("record_task requires only structured observable signals")
            if any(type(signals[k]) is not int or signals[k] < 0 for k in ("rework_cycles", "verification_failures")) or type(signals["verification_escape"]) is not bool:
                raise ValueError("record_task signals have invalid types")
            if action["outcome"] not in {"success", "failure", "partial"}:
                raise ValueError("invalid task outcome")
            if any(item["occurrence_id"] == action["occurrence_id"] for item in state["task_events"]):
                raise ValueError("duplicate task occurrence")
            state["task_events"].append({k: v for k, v in action.items() if k != "op"})
        elif op == "request_review":
            if action["status"] not in {"IMMEDIATE_REVIEW", "REVIEW_DUE", "REVIEW_RECOMMENDED"}:
                raise ValueError("invalid review status")
            state["review_status"] = action["status"]
        elif op == "record_feedback":
            state["feedback"].append({k: v for k, v in action.items() if k != "op"})
        elif op == "nominate_candidate":
            if action["fingerprint"] not in {item["fingerprint"] for item in state["feedback"]}:
                raise ValueError("Candidate nomination must follow recorded Framework Feedback")
            state["promotion_queue"].append(action["fingerprint"])
        elif op == "execute_capability":
            if action["mode"] not in {"candidate", "stable"}:
                raise ValueError("invalid capability execution mode")
            state["executions"].append({k: v for k, v in action.items() if k != "op"})
            state["capability_status"] = "ACTIVE_CANDIDATE" if action["mode"] == "candidate" else "STABLE"
        elif op == "block_capability":
            if action["reason"] not in {"no_adoption", "pin_upgrade_without_adoption", "expired_or_mismatched", "mutable_pin"}:
                raise ValueError("invalid capability blocking reason")
            state["capability_status"] = "DORMANT" if action["reason"] in {"no_adoption", "pin_upgrade_without_adoption"} else "BLOCKED"
    return state


def score_simulation(expectation: dict[str, Any], response: dict[str, Any], case_input: Any) -> tuple[bool, str]:
    try:
        if not isinstance(case_input, dict) or case_input.get("response_contract") != SIMULATION_CONTRACT:
            raise ValueError("simulation requires its versioned input contract")
        output = response.get("output")
        if not isinstance(output, dict) or set(output) != {"contract", "decision", "actions", "state"}:
            raise ValueError("simulation output requires exactly contract/decision/actions/state")
        if output["contract"] != SIMULATION_CONTRACT or output["decision"] not in SIMULATION_DECISIONS:
            raise ValueError("invalid simulation contract or decision")
        _json_identity(response)
        if response.get("trace", []) != []:
            raise ValueError("simulation must not claim or perform real tool activity")
        state = simulate_actions(case_input.get("initial_state"), output["actions"])
        if _json_identity(state) != _json_identity(output["state"]):
            raise ValueError("claimed state contradicts the proposed action effects")
        if _json_identity(state) != _json_identity(expectation["state"]):
            raise ValueError("proposed actions produce an incorrect state")
        if output["decision"] != expectation["decision"]:
            raise ValueError("decision contradicts the required behavior")
        ops = [action["op"] for action in output["actions"]]
        required_ops = {
            "capture_task": ["record_task"], "omit_task": [], "request_review": ["request_review"],
            "reject_sensitive_capture": [], "feedback_then_promotion": ["record_feedback", "nominate_candidate"],
            "allow_capability": ["execute_capability"], "block_capability": ["block_capability"],
        }
        if ops != required_ops[output["decision"]]:
            raise ValueError("decision/action contradiction or additional unauthorized effects")
    except (ValueError, TypeError, KeyError) as exc:
        return False, str(exc)
    return True, "structured action effects and state verified in simulation; not live tool execution"


def load_json(path: Path) -> Any:
    return strict_json_loads(path.read_text(encoding="utf-8"))


def _valid_datetime(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def suite_assurance_scope(data: dict[str, Any]) -> str:
    scope = data.get("assurance_scope")
    if scope not in ASSURANCE_SCOPES:
        raise RuntimeError("suite assurance_scope must be explicitly declared")
    return scope


def suite_required_for_level(data: dict[str, Any], minimum_level: str) -> bool:
    if minimum_level not in ASSURANCE_LEVELS:
        raise RuntimeError(f"unknown assurance level: {minimum_level}")
    return not (minimum_level in RUNTIME_ASSURANCE_LEVELS and suite_assurance_scope(data) == "harness_only")


def validate_suite(data: Any, source: str = "<memory>") -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{source}: root must be an object"]
    allowed_root = {"schema_version", "suite_id", "artifact", "assurance_scope", "cases"}
    unknown_root = sorted(set(data) - allowed_root)
    if unknown_root:
        errors.append(f"{source}: unknown root fields: {unknown_root}")
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{source}: schema_version must be {SCHEMA_VERSION}")
    if not isinstance(data.get("suite_id"), str) or not data.get("suite_id"):
        errors.append(f"{source}: suite_id is required")
    if not isinstance(data.get("artifact"), str) or not data.get("artifact"):
        errors.append(f"{source}: artifact is required")

    if "assurance_scope" not in data:
        errors.append(f"{source}: assurance_scope is required")
    elif data["assurance_scope"] not in ASSURANCE_SCOPES:
        errors.append(f"{source}: assurance_scope must be one of {sorted(ASSURANCE_SCOPES)}")

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
            unknown_expectation = sorted(set(expectation) - SCORER_FIELDS[scorer_type])
            if unknown_expectation:
                errors.append(f"{ep} unknown fields: {unknown_expectation}")
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
            elif scorer_type == "behavioral_simulation":
                try:
                    output = {"contract": SIMULATION_CONTRACT, "decision": expectation["decision"],
                              "actions": expectation["reference_actions"], "state": expectation["state"]}
                    passed, detail = score_simulation(expectation, {"output": output}, case.get("input"))
                    if not passed:
                        errors.append(f"{ep}: {detail}")
                except (KeyError, TypeError, ValueError) as exc:
                    errors.append(f"{ep}: invalid simulation fixture: {exc}")
    return errors


def discover_suites(paths: list[str]) -> list[Path]:
    suites: list[Path] = []
    for raw in paths:
        path = Path(raw)
        suites.extend(sorted(path.rglob("*.eval.json")) if path.is_dir() else [path])
    return suites


def split_adapter_command(command: str, platform_name: str | None = None) -> list[str]:
    """Split an adapter command without corrupting native Windows backslash paths."""
    platform_name = os.name if platform_name is None else platform_name
    if platform_name != "nt":
        return shlex.split(command)
    argv = shlex.split(command, posix=False)
    return [
        token[1:-1]
        if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}
        else token
        for token in argv
    ]


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
    try:
        _json_identity(response)
    except (ValueError, TypeError) as exc:
        raise RuntimeError("adapter response must contain finite JSON values") from exc
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


def score(expectation: dict[str, Any], response: dict[str, Any], case_input: dict[str, Any] | None = None) -> tuple[bool, str]:
    scorer_type = expectation["type"]
    if scorer_type == "behavioral_simulation":
        return score_simulation(expectation, response, case_input)
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
    argv = split_adapter_command(command)
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
        response = strict_json_loads(process.stdout)
    except ValueError as exc:
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
                results = [(expectation["type"],) + score(expectation, response, case["input"]) for expectation in case["expectations"]]
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


def _expected_cases(paths: list[str], minimum_level: str = "harness_smoke") -> set[tuple[str, str]]:
    expected: set[tuple[str, str]] = set()
    for path in discover_suites(paths):
        data = load_json(path)
        errors = validate_suite(data, str(path))
        if errors:
            raise RuntimeError("; ".join(errors))
        if not suite_required_for_level(data, minimum_level):
            continue
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
        expected = _expected_cases(args.paths, minimum_level=args.minimum_level)
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
