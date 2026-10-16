#!/usr/bin/env python3
"""Execute behavioral Framework evals against an independent adapter and retain bound evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import secrets
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from . import runner
except ImportError:
    import runner

SHA40_RE = re.compile(r"^[a-f0-9]{40}$")
FORBIDDEN_EXACT_TARGET_MARKERS = (
    "evals/fixtures/",
    "reference_oracle_adapter",
    "mock_adapter",
    "framework-mock-adapter",
)


class ExactTargetRunError(RuntimeError):
    pass


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExactTargetRunError(f"{label} must be a non-empty string")
    return value.strip()


def _sha40(value: str, label: str) -> str:
    text = _text(value, label)
    if not SHA40_RE.fullmatch(text):
        raise ExactTargetRunError(f"{label} must be an exact 40-character commit")
    return text


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _command_digest(command: str) -> str:
    return hashlib.sha256(command.encode("utf-8")).hexdigest()


def _blinded_request(suite: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    """Keep scorer expectations/tags and enumerable case identifiers outside adapter input.

    Unpredictable one-use IDs are deliberately preferred to unsalted hashes
    of published suite/case names (which are trivial to reverse by enumeration).
    Canonical original IDs stay solely in trusted harness evidence.
    """
    artifact = _text(suite.get("artifact"), "artifact")
    case_input = case.get("input")
    context = case.get("context", {})
    if not isinstance(case_input, dict) or not isinstance(context, dict):
        raise ExactTargetRunError("case input/context must be objects")
    return {
        "protocol_version": "1.0",
        "suite_id": f"blind-suite-{secrets.token_hex(8)}",
        "case_id": f"blind-case-{secrets.token_hex(8)}",
        "artifact": artifact,
        "input": case_input,
        "context": context,
    }


def _validate_adapter_command(command: str) -> str:
    command = _text(command, "adapter command")
    normalized = command.replace("\\", "/").lower()
    if any(marker in normalized for marker in FORBIDDEN_EXACT_TARGET_MARKERS):
        raise ExactTargetRunError("reference/mock fixtures cannot be claimed as exact_target_runtime")
    return command


def _validate_manifest_path(value: str) -> str:
    path = Path(_text(value, "manifest path"))
    raw = path.as_posix()
    if path.is_absolute() or ".." in path.parts or not raw.startswith("evals/exact-target-runs/") or path.suffix != ".json":
        raise ExactTargetRunError("manifest path must be a relative JSON path under evals/exact-target-runs/")
    return raw


def run_suites(
    paths: list[str],
    *,
    adapter_command: str,
    adapter_id: str,
    adapter_revision: str,
    runtime_id: str,
    runtime_version: str,
    runtime_evidence: list[str],
    framework_ref: str,
    manifest_relpath: str,
    timeout: float = 120.0,
    produced_at: str | None = None,
    run_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    command = _validate_adapter_command(adapter_command)
    adapter_id = _text(adapter_id, "adapter_id")
    adapter_revision = _sha40(adapter_revision, "adapter_revision")
    runtime_id = _text(runtime_id, "runtime_id")
    runtime_version = _text(runtime_version, "runtime_version")
    framework_ref = _sha40(framework_ref, "framework_ref")
    manifest_relpath = _validate_manifest_path(manifest_relpath)
    if not isinstance(runtime_evidence, list) or not runtime_evidence:
        raise ExactTargetRunError("at least one runtime identity evidence reference is required")
    normalized_evidence = [_text(item, "runtime evidence") for item in runtime_evidence]
    if len(set(normalized_evidence)) != len(normalized_evidence):
        raise ExactTargetRunError("runtime identity evidence contains duplicates")
    if timeout <= 0:
        raise ExactTargetRunError("timeout must be > 0")

    suites = runner.discover_suites(paths)
    if not suites:
        raise ExactTargetRunError("no eval suites found")
    now = produced_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    generated_run_id = run_id or f"ETR-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(4).upper()}"
    executions: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []

    for path in suites:
        data = runner.load_json(path)
        errors = runner.validate_suite(data, str(path))
        if errors:
            raise ExactTargetRunError("; ".join(errors))
        if not runner.suite_required_for_level(data, "exact_target_runtime"):
            continue
        for case in data["cases"]:
            request = _blinded_request(data, case)
            try:
                response = runner.call_adapter(command, request, timeout, case["expectations"])
                scorer_results = [runner.score(expectation, response) for expectation in case["expectations"]]
                status = "pass" if all(item[0] for item in scorer_results) else "fail"
                response_digest = _canonical_digest(response)
            except Exception:
                status = "fail"
                response_digest = _canonical_digest({
                    "adapter_error": True,
                    "suite_id": data["suite_id"],
                    "case_id": case["id"],
                })
            executions.append({
                "suite_id": data["suite_id"],
                "case_id": case["id"],
                "status": status,
                "response_digest": response_digest,
            })
            evidence_rows.append({
                "suite_id": data["suite_id"],
                "case_id": case["id"],
                "status": status,
                "adapter_id": adapter_id,
                "adapter_revision": adapter_revision,
                "assurance_level": "exact_target_runtime",
                "independent_runtime": True,
                "evidence_ref": f"exact-target-run:{manifest_relpath}#{data['suite_id']}/{case['id']}",
            })

    if not executions:
        raise ExactTargetRunError("no behavioral_runtime eval cases found for exact-target execution")

    manifest = {
        "schema_version": 1,
        "run_id": generated_run_id,
        "produced_at": now,
        "framework_revision": framework_ref,
        "adapter": {"id": adapter_id, "revision": adapter_revision},
        "runtime": {
            "id": runtime_id,
            "version": runtime_version,
            "independent_runtime": True,
            "identity_evidence": normalized_evidence,
        },
        "adapter_command_digest": _command_digest(command),
        "executions": executions,
    }
    evidence = {
        "schema_version": 2,
        "framework_revision": framework_ref,
        "produced_at": now,
        "executions": evidence_rows,
    }
    return manifest, evidence


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ExactTargetRunError(f"unable to resolve git HEAD: {exc}") from exc


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--adapter-id", required=True)
    parser.add_argument("--adapter-revision", required=True)
    parser.add_argument("--runtime-id", required=True)
    parser.add_argument("--runtime-version", required=True)
    parser.add_argument("--runtime-evidence", action="append", required=True)
    parser.add_argument("--framework-ref", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args(argv)
    try:
        if _git_head() != args.framework_ref:
            raise ExactTargetRunError("--framework-ref must equal the exact checked-out git HEAD")
        manifest_path = Path(args.manifest)
        evidence_path = Path(args.evidence)
        manifest_relpath = _validate_manifest_path(manifest_path.as_posix())
        if manifest_path.exists() or evidence_path.exists():
            raise ExactTargetRunError("exact-target output files are immutable; choose new paths")
        manifest, evidence = run_suites(
            args.paths,
            adapter_command=args.adapter,
            adapter_id=args.adapter_id,
            adapter_revision=args.adapter_revision,
            runtime_id=args.runtime_id,
            runtime_version=args.runtime_version,
            runtime_evidence=args.runtime_evidence,
            framework_ref=args.framework_ref,
            manifest_relpath=manifest_relpath,
            timeout=args.timeout,
        )
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except ExactTargetRunError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    failed = sum(1 for item in manifest["executions"] if item["status"] != "pass")
    print(json.dumps({"run_id": manifest["run_id"], "total": len(manifest["executions"]), "failed": failed}, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
