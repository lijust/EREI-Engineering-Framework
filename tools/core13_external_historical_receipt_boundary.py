"""Framework-side read-only receipt admission boundary for historical project evidence.

The source project remains responsible for executing/independently verifying
its task. A JSON receipt supplied by a caller is NOT independently attested.
Historical runs must not become prospective Task Learning tasks or model wins.
Reuses the existing mainline typed policy -> deterministic reducer, without
inventing a second framework runtime or writing any project file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from tools.learning_proposal_runtime import evaluate_proposal

CONTRACT = "erei-cross-project-historical-receipt-v1"
STATUS = "FRAMEWORK_HISTORICAL_RECEIPT_READONLY_BOUNDARY_PASS"
BLOCKED = "FRAMEWORK_HISTORICAL_RECEIPT_BLOCKED"
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
PROJECT = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
STATUS_CODE = re.compile(r"[A-Z][A-Z0-9_]{5,95}\Z")
CHECK_NAME = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
MAX_BYTES = 32768


class ReceiptDenied(ValueError):
    pass


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ReceiptDenied("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _digest(item):
    return hashlib.sha256(json.dumps(
        item, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")).hexdigest()


def inspect(record: object) -> dict:
    if type(record) is not dict or set(record) != {
        "contract", "project", "source", "runtime", "result", "attestation",
    } or record["contract"] != CONTRACT:
        raise ReceiptDenied("RECEIPT_CONTRACT_INVALID")
    if (type(record["project"]) is not str
        or PROJECT.fullmatch(record["project"]) is None):
        raise ReceiptDenied("PROJECT_IDENTITY_UNEXPECTED")
    source = record["source"]
    if (type(source) is not dict or set(source) != {
        "origin", "old_sha256", "fixed_sha256"
    } or source["origin"] != "git_pinned_historical"
        or any(type(source[k]) is not str or SHA256.fullmatch(source[k]) is None
               for k in ("old_sha256", "fixed_sha256"))
        or source["old_sha256"] == source["fixed_sha256"]):
        raise ReceiptDenied("HISTORICAL_SOURCE_IDENTITY_INVALID")
    runtime = record["runtime"]
    if (type(runtime) is not dict or set(runtime) != {
        "kind", "known_canary_verified", "host_mounts", "model_calls",
        "model_generated_code_executed", "untrusted_execution_certified",
    } or runtime["kind"] != "docker_trusted_historical_only"
        or runtime["known_canary_verified"] is not True
        or type(runtime["host_mounts"]) is not int or runtime["host_mounts"] != 0
        or type(runtime["model_calls"]) is not int or runtime["model_calls"] != 0
        or runtime["model_generated_code_executed"] is not False
        or runtime["untrusted_execution_certified"] is not False):
        raise ReceiptDenied("RUNTIME_SCOPE_INVALID")
    result = record["result"]
    # Every domain owns its own functional oracle. Framework only validates
    # a typed receipt shape; it CANNOT trust the reported pass/fail itself.
    if (type(result) is not dict or set(result) != {"status", "checks"}
        or type(result["status"]) is not str
        or STATUS_CODE.fullmatch(result["status"]) is None
        or type(result["checks"]) is not list
        or not 1 <= len(result["checks"]) <= 16):
        raise ReceiptDenied("HISTORICAL_RESULT_INVALID")
    names = set()
    for check in result["checks"]:
        if (type(check) is not dict or set(check) != {"id", "passed"}
            or type(check["id"]) is not str
            or CHECK_NAME.fullmatch(check["id"]) is None
            or check["id"] in names
            or check["passed"] is not True):
            raise ReceiptDenied("HISTORICAL_CHECK_INVALID")
        names.add(check["id"])
    attestation = record["attestation"]
    if (type(attestation) is not dict or set(attestation) != {
        "level", "source_verified_claim", "independent_model_patch_oracle"
    } or attestation["level"] != "operator_observed_not_independently_attested"
        or attestation["source_verified_claim"] is not True
        or attestation["independent_model_patch_oracle"] is not False):
        raise ReceiptDenied("ATTESTATION_LEVEL_INVALID")

    # The existing Framework P1 proposal policy is authoritative here.
    # This was a retrospective replay, not a prospective engineering task.
    # A deterministic *non-model* omission is an in-memory reference check.
    preview = evaluate_proposal(
        {"contract": "erei-proposal-v1", "decision": "omit_task", "actions": []},
        {"task_events": []},
        {"domain": "task_capture", "facts": {"engineering_execution": False}},
    )
    if (preview.get("status") != "AUTHORIZED_IN_MEMORY_PREVIEW"
        or preview.get("decision") != "omit_task"
        or preview.get("materialized_state") != {"task_events": []}
        or preview.get("executed") is not False
        or preview.get("independently_verified") is not False):
        raise ReceiptDenied("FRAMEWORK_POLICY_REDUCER_BOUNDARY_FAILED")
    return {
        "status": STATUS,
        "receipt_sha256": _digest(record),
        "historical_evidence_readonly": True,
        "producer_claim_rechecked_from_git": False,
        "independent_provider_or_model_receipt": False,
        "framework_policy_preview": "AUTHORIZED_IN_MEMORY_PREVIEW",
        "framework_decision": "omit_task",
        "prospective_task_events_added": 0,
        "learning_exposure_confirmed": False,
        "learning_effectiveness": "NOT_ESTABLISHED",
        "independent_model_patch_oracle_established": False,
        "model_calls": 0,
        "project_writes": 0,
        "stable_promotable": False,
        "decision": "BLOCK_AI_ACCEPTANCE",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only external historical evidence policy boundary"
    )
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.receipt.is_symlink() or args.receipt.stat().st_size > MAX_BYTES:
            raise ReceiptDenied("RECEIPT_SIZE_OR_PATH_INVALID")
        record = json.loads(
            args.receipt.read_text(encoding="utf-8"),
            object_pairs_hook=_unique,
            parse_constant=lambda _: (_ for _ in ()).throw(
                ReceiptDenied("NON_FINITE_JSON")),
        )
        report = inspect(record)
    except (ReceiptDenied, OSError, ValueError, OverflowError, TypeError,
            KeyError, AttributeError):
        print(json.dumps({"status": BLOCKED, "project_writes": 0,
                          "model_calls": 0, "stable_promotable": False}))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
