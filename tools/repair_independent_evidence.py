"""J5-03 trusted, fixed-only *source observation*; NOT patch execution.

Source bytes are read from the exact J5-01 verified Git blob and copied to a
fresh disposable verifier-controlled folder as DATA. A reviewed literal Python
subprocess reads/parses the source text without importing/executing that text.
It is an actual source-derived observation, NOT a candidate patch acceptance,
not a sealed malicious-code sandbox, and not an authenticated result channel.
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

MAX_SOURCE_BYTES = 65536
MAX_ORACLE_BYTES = 4096
MAX_TRACE_BYTES = 4096
RUN_TIMEOUT_SECONDS = 5
CASE = "baseline_python_ast"
ORACLE_CONTRACT = "erei-j5-03-trusted-source-oracle-v1"
TRACE_CONTRACT = "erei-j5-03-fixed-source-observation-v1"
OBS_KEYS = ("source_sha256", "source_bytes", "line_count",
            "function_count", "class_count", "syntax_valid")
OBS_TYPE = (str, int, int, int, int, bool)

# Fixed reviewed literal script. The source file is PARSED as bytes/text only.
# It is never compiled, imported, exec'd, evaluated, or launched.
_INSPECTOR = (
    "import ast,hashlib,json,pathlib,sys;"
    "raw=pathlib.Path(sys.argv[1]).read_bytes();"
    "tree=ast.parse(raw.decode('utf-8'));"
    "nodes=list(ast.walk(tree));"
    "out={'contract':'erei-j5-03-fixed-source-observation-v1',"
    "'source_sha256':hashlib.sha256(raw).hexdigest(),"
    "'source_bytes':len(raw),"
    "'line_count':len(raw.splitlines()),"
    "'function_count':sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))"
    " for n in nodes),"
    "'class_count':sum(isinstance(n,ast.ClassDef) for n in nodes),"
    "'syntax_valid':True};"
    "print(json.dumps(out,sort_keys=True,separators=(',',':')))"
)


class EvidenceDenied(ValueError):
    """Fail closed; no paths, private bytes or subprocess logs in reasons."""


def _json_exact(raw: bytes, *, contract: str, fields: set[str]) -> dict:
    try:
        value = json.loads(raw)
    except (TypeError, UnicodeError, ValueError) as exc:
        raise EvidenceDenied("EVIDENCE_JSON_INVALID") from exc
    if (type(value) is not dict or set(value) != fields
        or value.get("contract") != contract):
        raise EvidenceDenied("EVIDENCE_SCHEMA_INVALID")
    return value


def _observation(value: dict, *, contract: str) -> dict:
    value = _json_exact(
        json.dumps(value, ensure_ascii=True, allow_nan=False).encode("utf-8"),
        contract=contract, fields={"contract", *OBS_KEYS},
    )
    for key, expected_type in zip(OBS_KEYS, OBS_TYPE):
        if type(value[key]) is not expected_type:
            raise EvidenceDenied("EVIDENCE_OBSERVATION_TYPE_INVALID")
    if (j501.SHA256.fullmatch(value["source_sha256"]) is None
        or not 1 <= value["source_bytes"] <= MAX_SOURCE_BYTES
        or not 0 <= value["line_count"] <= MAX_SOURCE_BYTES
        or not 0 <= value["function_count"] <= MAX_SOURCE_BYTES
        or not 0 <= value["class_count"] <= MAX_SOURCE_BYTES):
        raise EvidenceDenied("EVIDENCE_OBSERVATION_BOUNDS_INVALID")
    return value


def _private_oracle(path: Path, expected_digest: str) -> dict:
    # J5-02 already checks regular/read-only/no-hardlinks and pinned digest,
    # but perform a fresh bounded read and digest check immediately before run.
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise EvidenceDenied("ORACLE_UNAVAILABLE") from exc
    if (not 1 <= len(raw) <= MAX_ORACLE_BYTES
        or hashlib.sha256(raw).hexdigest() != expected_digest):
        raise EvidenceDenied("ORACLE_CHANGED_OR_OVERSIZE")
    oracle = _json_exact(
        raw, contract=ORACLE_CONTRACT,
        fields={"contract", "case", "expected"},
    )
    if oracle["case"] != CASE:
        raise EvidenceDenied("ORACLE_CASE_NOT_REVIEWED")
    expected = oracle["expected"]
    if type(expected) is not dict:
        raise EvidenceDenied("ORACLE_EXPECTED_SCHEMA_INVALID")
    _observation({"contract": TRACE_CONTRACT, **expected},
                 contract=TRACE_CONTRACT)
    return expected


def _source_bytes(root: Path, source: dict) -> bytes:
    # Reuse J5-01's Git command, Git blob mode/path and raw SHA checks.
    oid = source["git_blob_sha"]
    raw = j501._git(root, "cat-file", "blob", oid)
    if (not 1 <= len(raw) <= MAX_SOURCE_BYTES
        or hashlib.sha256(raw).hexdigest() != source["source_sha256"]):
        raise EvidenceDenied("PINNED_SOURCE_BYTES_CHANGED_OR_OVERSIZE")
    return raw


def _actual_fixed_observation(verifier_workspace: Path, raw: bytes) -> dict:
    # The temporary verifier copy is never visible through candidate_view,
    # never mounted into a candidate container, and removed before returning.
    # This is NOT an OS principal/MAC separation from malicious host code.
    path = None
    try:
        with tempfile.TemporaryDirectory(prefix="j503-trusted-", dir=verifier_workspace) as name:
            path = Path(name) / "source-as-data.py.txt"
            path.write_bytes(raw)
            env = {
                key: os.environ[key] for key in
                ("SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP")
                if key in os.environ
            }
            result = subprocess.run(
                [sys.executable, "-I", "-S", "-c", _INSPECTOR, str(path)],
                cwd=name, env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                timeout=RUN_TIMEOUT_SECONDS, check=False,
            )
            if (result.returncode != 0 or not 1 <= len(result.stdout) <= MAX_TRACE_BYTES):
                raise EvidenceDenied("FIXED_INSPECTOR_RUNTIME_FAILED")
            trace = _json_exact(
                result.stdout, contract=TRACE_CONTRACT,
                fields={"contract", *OBS_KEYS},
            )
            _observation(trace, contract=TRACE_CONTRACT)
            if (trace["source_sha256"] != hashlib.sha256(raw).hexdigest()
                or trace["source_bytes"] != len(raw)):
                raise EvidenceDenied("FIXED_INSPECTOR_SOURCE_IDENTITY_MISMATCH")
    except (OSError, subprocess.SubprocessError, UnicodeError, ValueError) as exc:
        if isinstance(exc, EvidenceDenied):
            raise
        raise EvidenceDenied("FIXED_INSPECTOR_UNAVAILABLE") from exc
    if path is None or path.parent.exists():
        raise EvidenceDenied("DISPOSABLE_VERIFIER_CLEANUP_UNVERIFIED")
    return trace


def observe_fixed_source(
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
    """Real fixed-source observation from a verifier-owned process only.

    A passing source AST observation cannot demonstrate the correctness of
    the proposed diff: the diff is only identity-validated, never applied.
    """
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
        or topology["trusted_verifier_channel_established"] is not False):
        raise EvidenceDenied("TOPOLOGY_AUTHORITY_MISMATCH")
    # J2 rejects forged provenance/authority in reported claims. No claimed
    # result is ever passed to the worker or used to select the observed result.
    claim_status = "NO_UNTRUSTED_CLAIM"
    if reported_result is not None:
        claim_status = j2.bind_reported_result(
            task, proposal, reported_result)["status"]

    source = j501.bind_pinned_source(source_root, task, proposal, trusted_pins)
    if len(source["sources"]) != 1:
        raise EvidenceDenied("FIXED_CASE_REQUIRES_EXACTLY_ONE_SOURCE")
    root = j502._directory(source_root, "source")
    verifier = j502._directory(verifier_workspace, "verifier")
    oracle_path = Path(oracle_fixture).resolve(strict=True)
    oracle = _private_oracle(oracle_path, trusted_pins["oracle_sha256"])
    raw = _source_bytes(root, source["sources"][0])
    # Fresh ephemeral verifier working directory. Runs reviewed inspector only.
    trace = _actual_fixed_observation(verifier, raw)
    checks = [
        {"id": key, "passed": trace[key] == oracle[key]}
        for key in OBS_KEYS
    ]
    match = all(check["passed"] for check in checks)
    trace_sha = hashlib.sha256(json.dumps(
        trace, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")).hexdigest()
    return {
        "status": ("J5_03_FIXED_SOURCE_OBSERVATION_MATCH"
                   if match else "J5_03_FIXED_SOURCE_OBSERVATION_MISMATCH"),
        "provenance": "TRUSTED_FIXED_INSPECTOR_PROCESS_OBSERVED",
        "scenario": CASE,
        "task_sha256": source["task_sha256"],
        "base_sha": source["base_sha"],
        "patch_sha256": source["patch_sha256"],
        "oracle_sha256": source["oracle_sha256"],
        "worker_profile_sha256": source["worker_profile_sha256"],
        "source_sha256": source["sources"][0]["source_sha256"],
        "fixed_trace_sha256": trace_sha,
        "fixed_process_exit_code": 0,
        "fixed_checks": checks,
        "fixed_oracle_matched": match,
        "reported_claim_status": claim_status,
        "disposable_verifier_workspace_cleaned": True,
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
