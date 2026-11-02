"""J5-03B fixed, reviewed behavioral RED/GREEN *calibration*, no AI patch.

A trusted source-controlled Python snippet runs twice in separate verifier-side
child processes. It never imports, applies or runs a candidate-supplied diff.
The private expected vector stays verifier-only. Passing proves only this
literal fixture can distinguish an intentionally faulty reviewed version.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from tools import repair_evidence_contract as j2
from tools import repair_source_binding as j501
from tools import repair_verifier_boundary as j502

ORACLE_CONTRACT = "erei-j5-03b-fixed-behavior-oracle-v1"
TRACE_CONTRACT = "erei-j5-03b-fixed-behavior-trace-v1"
CASE = "price_text_normalization_trusted_fixed"
MAX_ORACLE_BYTES = 4096
MAX_TRACE_BYTES = 2048
RUN_TIMEOUT_SECONDS = 5
N_CASES = 4

# Reviewed literal source. 'red' intentionally fails to normalize the suffix.
# 'green' is a fixed control for this tiny calibration, not a model patch.
# No caller-controlled source text, program path, test code, or shell command.
_REVIEWED_FIXED_WORKER = (
    "import json,os,sys\n"
    "mode=sys.argv[1]\n"
    "items=['1,200 SAR','850',' 700 SAR ','0 SAR']\n"
    "def parse(value):\n"
    "    cleaned=value.strip().replace(',', '')\n"
    "    if mode=='green':\n"
    "        cleaned=cleaned.removesuffix('SAR').strip()\n"
    "    try:\n"
    "        return int(cleaned)\n"
    "    except ValueError:\n"
    "        return None\n"
    "out=[parse(item) for item in items]\n"
    "print(json.dumps({'contract':'erei-j5-03b-fixed-behavior-trace-v1',"
    "'mode':mode,'values':out,'pid':os.getpid()},"
    "sort_keys=True,separators=(',',':')))\n"
)


class BehaviorDenied(ValueError):
    """A trusted fixed behavior control could not be verified."""


def _oracle(path: Path, digest: str) -> list[int]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise BehaviorDenied("PRIVATE_BEHAVIOR_ORACLE_UNAVAILABLE") from exc
    if (not 1 <= len(raw) <= MAX_ORACLE_BYTES
        or hashlib.sha256(raw).hexdigest() != digest):
        raise BehaviorDenied("PRIVATE_BEHAVIOR_ORACLE_CHANGED")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise BehaviorDenied("PRIVATE_BEHAVIOR_ORACLE_JSON_INVALID") from exc
    if (type(data) is not dict
        or set(data) != {"contract", "case", "expected"}
        or data["contract"] != ORACLE_CONTRACT
        or data["case"] != CASE
        or type(data["expected"]) is not list
        or len(data["expected"]) != N_CASES
        or any(type(value) is not int or not 0 <= value <= 1000000
               for value in data["expected"])):
        raise BehaviorDenied("PRIVATE_BEHAVIOR_ORACLE_SCHEMA_INVALID")
    return data["expected"]


def _run_fixed(mode: str, workspace: Path) -> tuple[list[int | None], int, str]:
    if mode not in ("red", "green"):
        raise BehaviorDenied("UNREVIEWED_BEHAVIOR_MODE")
    env = {key: os.environ[key] for key in (
        "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP") if key in os.environ}
    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-S", "-c", _REVIEWED_FIXED_WORKER, mode],
            cwd=workspace, env=env,
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, timeout=RUN_TIMEOUT_SECONDS,
            check=False,
        )
        if (completed.returncode != 0
            or not 1 <= len(completed.stdout) <= MAX_TRACE_BYTES):
            raise BehaviorDenied("REVIEWED_BEHAVIOR_PROCESS_FAILED")
        trace = json.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, ValueError,
            UnicodeError) as exc:
        if isinstance(exc, BehaviorDenied):
            raise
        raise BehaviorDenied("REVIEWED_BEHAVIOR_PROCESS_UNAVAILABLE") from exc
    if (type(trace) is not dict
        or set(trace) != {"contract", "mode", "values", "pid"}
        or trace["contract"] != TRACE_CONTRACT
        or trace["mode"] != mode
        or type(trace["pid"]) is not int or trace["pid"] <= 0
        or type(trace["values"]) is not list
        or len(trace["values"]) != N_CASES
        or any((value is not None and
                (type(value) is not int or not 0 <= value <= 1000000))
               for value in trace["values"])):
        raise BehaviorDenied("REVIEWED_BEHAVIOR_TRACE_INVALID")
    trace_sha = hashlib.sha256(json.dumps(
        trace, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")).hexdigest()
    return trace["values"], trace["pid"], trace_sha


def observe_fixed_red_green(
    source_root: Path | str,
    task: dict,
    proposal: dict,
    trusted_pins: dict,
    *,
    candidate_workspace: Path | str,
    verifier_workspace: Path | str,
    oracle_fixture: Path | str,
    worker_profile_fixture: Path | str,
    candidate_mounts: list[Path | str] | tuple[Path | str, ...] = (),
    reported_result: dict | None = None,
) -> dict:
    """Return fail-closed fixed RED/GREEN evidence; no model acceptance."""
    topology = j502.preflight(
        source_root, task, proposal, trusted_pins,
        candidate_workspace=candidate_workspace,
        verifier_workspace=verifier_workspace,
        oracle_fixture=oracle_fixture,
        worker_profile_fixture=worker_profile_fixture,
        candidate_mounts=candidate_mounts,
        run_fixed_process_probes=False,
    )
    if (topology["decision"] != "BLOCK_AI_ACCEPTANCE"
        or topology["independently_verified"] is not False):
        raise BehaviorDenied("TOPOLOGY_AUTHORITY_UNEXPECTED")
    claim_status = "NO_UNTRUSTED_CLAIM"
    if reported_result is not None:
        claim = j2.bind_reported_result(task, proposal, reported_result)
        if claim.get("acceptance_authorized") is not False:
            raise BehaviorDenied("UNTRUSTED_CLAIM_AUTHORITY")
        claim_status = claim["status"]
    # The trusted fixture is validated by J5-02 prior to this bounded reread.
    expected = _oracle(Path(oracle_fixture).resolve(strict=True),
                       trusted_pins["oracle_sha256"])
    verifier = j502._directory(verifier_workspace, "verifier")
    with tempfile.TemporaryDirectory(prefix="j503b-behavior-", dir=verifier) as tmp:
        runtime = Path(tmp)
        red, red_pid, red_sha = _run_fixed("red", runtime)
        green, green_pid, green_sha = _run_fixed("green", runtime)
    if runtime.exists():
        raise BehaviorDenied("BEHAVIOR_WORKSPACE_REMOVAL_UNVERIFIED")
    if red_pid == green_pid:
        raise BehaviorDenied("BEHAVIOR_PROCESS_SEPARATION_NOT_OBSERVED")
    red_errors = sum(actual != wanted
                     for actual, wanted in zip(red, expected))
    green_errors = sum(actual != wanted
                       for actual, wanted in zip(green, expected))
    if red_errors < 1 or green_errors != 0:
        raise BehaviorDenied("REVIEWED_RED_GREEN_ORACLE_CONTROL_FAILED")
    return {
        "status": "J5_03B_TRUSTED_FIXED_BEHAVIOR_RED_GREEN_OBSERVED",
        "provenance": "TRUSTED_FIXED_BEHAVIOR_TWO_SUBPROCESSES",
        "scenario": CASE,
        "task_sha256": topology["task_sha256"],
        "base_sha": task["base_sha"],
        "patch_sha256": topology["patch_sha256"],
        "oracle_sha256": trusted_pins["oracle_sha256"],
        "worker_profile_sha256": trusted_pins["worker_profile_sha256"],
        "fixed_red_trace_sha256": red_sha,
        "fixed_green_trace_sha256": green_sha,
        "fixed_red_mismatches": red_errors,
        "fixed_green_mismatches": green_errors,
        "fixed_process_count": 2,
        "fixed_oracle_control_demonstrated": True,
        "disposable_verifier_workspace_cleaned": True,
        "reported_claim_status": claim_status,
        "model_patch_applied": False,
        "candidate_code_executed": False,
        "trusted_verifier_channel_established": False,
        "independent_model_patch_oracle_established": False,
        "independently_verified": False,
        "acceptance_authorized": False,
        "untrusted_code_execution_authorized": False,
        "worker_isolation_certified": False,
        "model_calls": 0,
        "project_writes": 0,
        "stable_promotable": False,
        "decision": "BLOCK_AI_ACCEPTANCE",
        "learning_effectiveness": "NOT_ESTABLISHED",
    }
