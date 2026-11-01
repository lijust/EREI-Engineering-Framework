"""Framework-neutral repair task / patch / verifier-result *contract preview*.

J2 P0: strict, bounded, deterministic identity and path validation only.
This is NOT a patch applier, tool runner, independent verifier, activation
engine or acceptance authority. No model/provider calls, filesystem writes,
project mutation or subprocesses.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

TASK_CONTRACT = "erei-repair-task-v1"
PATCH_CONTRACT = "erei-repair-patch-v1"
RESULT_CONTRACT = "erei-repair-verifier-result-v1"
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
TASK_ID = re.compile(r"ERT-[0-9]{8}-[A-Z0-9]{8}\Z")
PATH = re.compile(r"[A-Za-z0-9_./-]+\Z")
CHECK_ID = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
HUNK = re.compile(r"@@ -[0-9]+(?:,[0-9]+)? \+[0-9]+(?:,[0-9]+)? @@(?: .*)?\Z")
MAX_PATCH_BYTES = 65536
FORBIDDEN_COMPONENTS = frozenset({
    ".git", ".github", ".erei", "tests", "test", "evals",
    "secrets", "__pycache__", "docs",
})


class RepairContractDenied(ValueError):
    pass


def _exact(value: Any, keys: set[str], reason: str) -> dict:
    if type(value) is not dict or set(value) != keys:
        raise RepairContractDenied(reason)
    return value


def _digest(value: Any, expression: re.Pattern, reason: str) -> str:
    if type(value) is not str or expression.fullmatch(value) is None:
        raise RepairContractDenied(reason)
    return value


def _path(value: Any) -> str:
    if type(value) is not str or PATH.fullmatch(value) is None or len(value) > 180:
        raise RepairContractDenied("PATCH_PATH_NOT_CANONICAL")
    components = value.split("/")
    if (len(components) < 2 or any(not c or c in {".", ".."}
        or c.startswith(".") or c in FORBIDDEN_COMPONENTS
        for c in components) or value.startswith("/") or "\\" in value
        or components[-1].startswith("test_")):
        raise RepairContractDenied("PATCH_PATH_PROHIBITED")
    return value


def _task(task: Any) -> dict:
    task = _exact(task, {
        "contract", "task_id", "base_sha", "allowed_paths",
        "oracle_sha256", "worker_profile_sha256", "max_patch_bytes",
    }, "TASK_SCHEMA_INVALID")
    if task["contract"] != TASK_CONTRACT:
        raise RepairContractDenied("TASK_CONTRACT_INVALID")
    _digest(task["task_id"], TASK_ID, "TASK_ID_INVALID")
    _digest(task["base_sha"], SHA40, "BASE_SHA_INVALID")
    _digest(task["oracle_sha256"], SHA256, "ORACLE_IDENTITY_INVALID")
    _digest(task["worker_profile_sha256"], SHA256, "WORKER_PROFILE_IDENTITY_INVALID")
    paths = task["allowed_paths"]
    if (type(paths) is not list or not 1 <= len(paths) <= 8
        or any(type(p) is not str for p in paths)):
        raise RepairContractDenied("TASK_ALLOWED_PATHS_INVALID")
    safe = [_path(p) for p in paths]
    if len(set(safe)) != len(safe):
        raise RepairContractDenied("DUPLICATE_ALLOWED_PATH")
    if (type(task["max_patch_bytes"]) is not int
        or not 1 <= task["max_patch_bytes"] <= MAX_PATCH_BYTES):
        raise RepairContractDenied("TASK_PATCH_BUDGET_INVALID")
    return task


def _diff_paths(diff: str) -> list[str]:
    """Conservative existing-file-only unified diff envelope, not git apply."""
    if not diff.endswith("\n") or "\r" in diff or "\x00" in diff:
        raise RepairContractDenied("DIFF_TEXT_INVALID")
    lines = diff.splitlines()
    changed = []
    index = 0
    while index < len(lines):
        header = re.fullmatch(
            r"diff --git a/([A-Za-z0-9_./-]+) b/([A-Za-z0-9_./-]+)",
            lines[index],
        )
        if header is None or header.group(1) != header.group(2):
            raise RepairContractDenied("DIFF_HEADER_INVALID")
        name = _path(header.group(1))
        if name in changed:
            raise RepairContractDenied("DIFF_DUPLICATE_PATH")
        changed.append(name)
        index += 1
        if index < len(lines) and lines[index].startswith("index "):
            if re.fullmatch(
                r"index [0-9a-f]{7,64}\.\.[0-9a-f]{7,64}(?: 100644)?",
                lines[index],
            ) is None:
                raise RepairContractDenied("DIFF_INDEX_INVALID")
            index += 1
        if (index + 2 >= len(lines)
            or lines[index] != "--- a/" + name
            or lines[index + 1] != "+++ b/" + name):
            raise RepairContractDenied("DIFF_SOURCE_TARGET_INVALID")
        index += 2
        if HUNK.fullmatch(lines[index]) is None:
            raise RepairContractDenied("DIFF_HUNK_MISSING")
        additions = removals = 0
        while index < len(lines) and not lines[index].startswith("diff --git "):
            line = lines[index]
            if line.startswith("@@ "):
                if HUNK.fullmatch(line) is None:
                    raise RepairContractDenied("DIFF_HUNK_INVALID")
            elif line.startswith("+") and not line.startswith("+++ "):
                additions += 1
            elif line.startswith("-") and not line.startswith("--- "):
                removals += 1
            elif line.startswith(" "):
                pass
            elif line == "\\ No newline at end of file":
                pass
            else:
                raise RepairContractDenied("DIFF_LINE_INVALID")
            index += 1
        if not (additions or removals):
            raise RepairContractDenied("DIFF_NO_CHANGES")
    if not changed:
        raise RepairContractDenied("DIFF_EMPTY")
    return changed


def validate_patch(task: Any, proposal: Any) -> dict:
    """Validate a *claimed* patch envelope; never apply or execute it."""
    task = _task(task)
    proposal = _exact(proposal, {
        "contract", "task_id", "base_sha", "diff", "diff_sha256",
        "changed_paths",
    }, "PATCH_SCHEMA_INVALID")
    if (proposal["contract"] != PATCH_CONTRACT
        or proposal["task_id"] != task["task_id"]
        or proposal["base_sha"] != task["base_sha"]):
        raise RepairContractDenied("PATCH_TASK_OR_BASE_MISMATCH")
    _digest(proposal["diff_sha256"], SHA256, "PATCH_DIGEST_INVALID")
    diff = proposal["diff"]
    if type(diff) is not str:
        raise RepairContractDenied("PATCH_TEXT_INVALID")
    try:
        raw = diff.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise RepairContractDenied("PATCH_ENCODING_INVALID") from exc
    if not 1 <= len(raw) <= task["max_patch_bytes"]:
        raise RepairContractDenied("PATCH_SIZE_LIMIT")
    if hashlib.sha256(raw).hexdigest() != proposal["diff_sha256"]:
        raise RepairContractDenied("PATCH_DIGEST_MISMATCH")
    actual = _diff_paths(diff)
    claimed = proposal["changed_paths"]
    if type(claimed) is not list or claimed != actual or len(actual) > 8:
        raise RepairContractDenied("PATCH_CHANGED_PATHS_MISMATCH")
    if any(path not in task["allowed_paths"] for path in actual):
        raise RepairContractDenied("PATCH_OUTSIDE_APPROVED_SCOPE")
    return {
        "status": "PATCH_ENVELOPE_VALIDATED_NOT_AUTHORIZED",
        "task_id": task["task_id"], "base_sha": task["base_sha"],
        "patch_sha256": proposal["diff_sha256"],
        "changed_paths": actual, "executed": False,
        "project_writes": 0, "independently_verified": False,
        "acceptance_authorized": False,
    }


def bind_reported_result(task: Any, proposal: Any, result: Any) -> dict:
    """Bind reported result identities; NEVER trust proposer-supplied PASS."""
    patch = validate_patch(task, proposal)
    task = _task(task)
    result = _exact(result, {
        "contract", "task_id", "base_sha", "patch_sha256",
        "oracle_sha256", "worker_profile_sha256", "outcome",
        "checks", "provenance",
    }, "RESULT_SCHEMA_INVALID")
    if (result["contract"] != RESULT_CONTRACT
        or result["task_id"] != task["task_id"]
        or result["base_sha"] != task["base_sha"]
        or result["patch_sha256"] != patch["patch_sha256"]
        or result["oracle_sha256"] != task["oracle_sha256"]
        or result["worker_profile_sha256"] != task["worker_profile_sha256"]):
        raise RepairContractDenied("RESULT_IDENTITY_MISMATCH")
    if result["provenance"] != "caller_reported_unattested":
        raise RepairContractDenied("RESULT_PROVENANCE_NOT_ATTESTED")
    if (type(result["outcome"]) is not str
        or result["outcome"] not in {"pass", "fail", "blocked"}):
        raise RepairContractDenied("RESULT_OUTCOME_INVALID")
    checks = result["checks"]
    if (type(checks) is not list or len(checks) > 16
        or (result["outcome"] != "blocked" and not checks)):
        raise RepairContractDenied("RESULT_CHECKS_INVALID")
    seen = set()
    for check in checks:
        _exact(check, {"id", "passed"}, "RESULT_CHECK_INVALID")
        if (type(check["id"]) is not str
            or CHECK_ID.fullmatch(check["id"]) is None
            or type(check["passed"]) is not bool or check["id"] in seen):
            raise RepairContractDenied("RESULT_CHECK_INVALID")
        seen.add(check["id"])
    if (result["outcome"] == "pass" and not all(c["passed"] for c in checks)
        or result["outcome"] == "fail" and all(c["passed"] for c in checks)
        or result["outcome"] == "blocked" and checks):
        raise RepairContractDenied("RESULT_OUTCOME_CHECK_CONTRADICTION")
    return {
        "status": "RESULT_CLAIM_BOUND_NOT_INDEPENDENTLY_VERIFIED",
        "task_id": task["task_id"],
        "base_sha": task["base_sha"],
        "patch_sha256": patch["patch_sha256"],
        "oracle_sha256": task["oracle_sha256"],
        "worker_profile_sha256": task["worker_profile_sha256"],
        "reported_outcome": result["outcome"],
        "candidate_decision": (
            "REVIEW_REQUIRED" if result["outcome"] == "pass"
            else "REJECTED_CLAIM" if result["outcome"] == "fail"
            else "BLOCKED_CLAIM"
        ),
        "trusted_verifier_channel_established": False,
        "independently_verified": False,
        "acceptance_authorized": False,
        "executed": False, "model_calls": 0, "project_writes": 0,
        "learning_effectiveness": "NOT_ESTABLISHED",
        "stable_promotable": False,
    }
