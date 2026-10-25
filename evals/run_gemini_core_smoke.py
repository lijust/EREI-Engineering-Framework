#!/usr/bin/env python3
"""Execute exactly ONE public Core13 case using a real Gemini response.

Explicit --live and --confirm-free-tier required. Saves provider's raw JSON
envelope, usage and frozen-target scorer verdict locally, never GitHub/CI.
The record is an observed model response but NOT independent release approval.
"""
from __future__ import annotations

import argparse
import getpass
import hashlib
import importlib.util
import json
import os
import secrets
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from evals.adapters import gemini_core13_exact_target as gemini

CASES = {
    "task-learning-review.eval.json": (
        "TLR-001-SUCCESS-STILL-LEARNING-DATA",
        "TLR-002-EXPLANATION-NO-EVENT",
        "TLR-003-VERIFICATION-ESCAPE",
        "TLR-004-TWENTY-MATERIAL-TASKS",
        "TLR-005-REPEATED-FEEDBACK",
        "TLR-006-PRIVATE-REASONING",
        "TLR-007-REVIEW-NOT-SELF-MODIFICATION",
    ),
    "candidate-capability-activation.eval.json": (
        "CCA-001-PRESENCE-IS-NOT-ACTIVATION",
        "CCA-002-EXACT-BOUNDED-ADOPTION",
        "CCA-003-PIN-UPGRADE-DOES-NOT-ACTIVATE",
        "CCA-004-EXPIRED-OR-MISMATCHED",
        "CCA-005-STABLE-NEEDS-NO-CANDIDATE-RECORD",
        "CCA-006-MUTABLE-PIN-BLOCKED",
    ),
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False,
                      sort_keys=True, separators=(",", ":")).encode("utf-8")


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, allow_nan=False,
                       sort_keys=True, indent=2) + "\n").encode("utf-8")


FROZEN_EVAL_FILES = {"evals/runner.py"} | {
    "evals/cases/" + name for name in CASES
}


def frozen_blob(root: Path, relative_path: str) -> bytes:
    """Read original target Git object directly; never consume worktree or pyc.

    CRLF checkouts, git assume-unchanged and ignored __pycache__ cannot
    influence the source used for the blind prompt or evaluator.
    """
    if relative_path not in FROZEN_EVAL_FILES:
        raise gemini.GeminiAdapterError("unexpected target evaluation file")
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    try:
        blob = subprocess.check_output(
            ["git", "--no-replace-objects", "-C", str(root.resolve()), "show",
             f"{gemini.EXPECTED_TARGET_HEAD}:{relative_path}"],
            stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=10, env=env,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise gemini.GeminiAdapterError("immutable evaluation Git blob unavailable") from None
    if not isinstance(blob, bytes) or not blob or len(blob) > 512_000:
        raise gemini.GeminiAdapterError("invalid/oversize frozen evaluator Git blob")
    return blob


def frozen_runner(root: Path):
    """Compile and exec VERIFIED Git blob bytes only; do not load cached pyc."""
    import types

    code_bytes = frozen_blob(root, "evals/runner.py")
    path = root / "evals" / "runner.py"
    try:
        source = code_bytes.decode("utf-8-sig")
        executable = compile(source, str(path), "exec", dont_inherit=True)
    except (UnicodeError, SyntaxError, ValueError) as exc:
        raise gemini.GeminiAdapterError("frozen evaluator source invalid") from None
    module = types.ModuleType("erei_frozen_core_scorer")
    module.__file__ = str(path)
    module.__package__ = ""
    # exec does NOT import using SourceFileLoader and does NOT consult .pyc.
    exec(executable, module.__dict__)
    return module


def source_identity(adapter_root: Path) -> dict:
    isolated = {k: v for k, v in os.environ.items()
                if not k.upper().startswith("GIT_")}
    try:
        head = subprocess.check_output(
            ["git", "--no-replace-objects", "-C", str(adapter_root), "rev-parse", "--verify", "HEAD"],
            text=True, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=10, env=isolated,
        ).strip()
        dirty = subprocess.check_output(
            ["git", "--no-replace-objects", "-C", str(adapter_root), "status", "--porcelain", "--untracked-files=all"],
            text=True, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=10, env=isolated,
        ).strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        raise gemini.GeminiAdapterError("adapter source revision unavailable") from None
    if dirty:
        raise gemini.GeminiAdapterError("adapter checkout is dirty; source is not reproducible")
    return {"adapter_source_revision": head}


def load_one(root: Path, case_id: str, evaluator) -> tuple[dict, dict, dict]:
    name = next((name for name, ids in CASES.items() if case_id in ids), None)
    if name is None:
        raise gemini.GeminiAdapterError("case ID outside frozen Core13")
    path = root / "evals" / "cases" / name
    try:
        suite = evaluator.strict_json_loads(
            frozen_blob(root, "evals/cases/" + name).decode("utf-8-sig")
        )
    except (UnicodeError, ValueError, TypeError):
        raise gemini.GeminiAdapterError("frozen suite Git blob invalid") from None
    errors = evaluator.validate_suite(suite, str(path))
    if errors:
        raise gemini.GeminiAdapterError("frozen source suite invalid")
    exact = [item for item in suite["cases"] if item["id"] == case_id]
    if len(exact) != 1 or len(suite["cases"]) != len(CASES[name]):
        raise gemini.GeminiAdapterError("frozen case set changed")
    case = exact[0]
    request = {
        "protocol_version": "2.0",
        "suite_id": "blind-suite-" + secrets.token_hex(8),
        "case_id": "blind-case-" + secrets.token_hex(8),
        "artifact": suite["artifact"],
        "input": case["input"],
        "context": case.get("context", {}),
    }
    return suite, case, request


def prepare(root: Path, case_id: str, adapter_root: Path) -> dict:
    """All-source, quota, path and scoring preflight; ZERO API usage."""
    root = root.resolve()
    gemini.verify_frozen_target(root)
    runner = frozen_runner(root)
    suite, case, request = load_one(root, case_id, runner)
    prompt = gemini.prepare_one(request, root)
    return {
        "root": root,
        "runner": runner,
        "suite": suite,
        "case": case,
        "request": request,
        "prompt": prompt,
        "adapter_source": source_identity(adapter_root),
    }


def record_one(prepared: dict, output: Path, key: str, timeout: float,
               *, model: str = gemini.MODEL) -> dict:
    """Only network call in this function. Write raw before attempting scoring."""
    gemini.model_endpoint(model)  # reject unsupported model before generating
    raw = gemini.generate_raw_once(prepared["prompt"], key=key, timeout=timeout, model=model)
    # Preserve exact provider payload before interpreting any model response.
    (output / "provider-raw.json").write_bytes(raw)
    verdict: dict = {
        "schema_version": 1,
        "evidence_kind": "observed_unverified",
        "independently_accepted": False,
        "stable_ready": False,
        "source_head": gemini.EXPECTED_TARGET_HEAD,
        "source_tree": gemini.EXPECTED_TARGET_TREE,
        "adapter_source_revision": prepared["adapter_source"]["adapter_source_revision"],
        "model_requested": model,
        "case_id": prepared["case"]["id"],
        "suite_id": prepared["suite"]["suite_id"],
        "provider_response_sha256": sha(raw),
        "blind_request_sha256": sha(canonical_bytes(prepared["request"])),
        "prompt_sha256": sha(prepared["prompt"].encode("utf-8")),
        "captured_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "passed": False,
    }
    try:
        # Metadata comes from the response, not a locally invented token estimate.
        envelope = json.loads(
            raw,
            object_pairs_hook=_unique,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite JSON")),
        )
        if not isinstance(envelope, dict):
            raise ValueError("invalid provider envelope")
        verdict["provider_model_version"] = envelope.get("modelVersion")
        verdict["provider_response_id"] = envelope.get("responseId")
        verdict["usage_metadata"] = envelope.get("usageMetadata")
        if not isinstance(verdict["usage_metadata"], dict):
            raise ValueError("provider usage metadata missing")
        if not isinstance(verdict["provider_model_version"], str) or not verdict["provider_model_version"]:
            raise ValueError("provider model version missing")
        if verdict["provider_model_version"] != model:
            raise ValueError("provider model identity differs from selected runtime")
        normalized = gemini.parse_gemini_result(raw)
        (output / "adapter-normalized.json").write_bytes(json_bytes(normalized))
        scores = [
            prepared["runner"].score(expectation, normalized, prepared["case"]["input"])
            for expectation in prepared["case"]["expectations"]
        ]
        verdict["scorer_results"] = [{"passed": bool(success), "reason": detail}
                                      for success, detail in scores]
        verdict["passed"] = bool(scores) and all(item[0] for item in scores)
        verdict["status"] = ("MODEL_RESPONSE_SCORED_PASS_UNVERIFIED"
                             if verdict["passed"] else "MODEL_RESPONSE_SCORED_FAIL_UNVERIFIED")
    except (ValueError, TypeError, KeyError, AttributeError, gemini.GeminiAdapterError) as exc:
        verdict["status"] = "MODEL_RESPONSE_INVALID_UNVERIFIED"
        verdict["failure_type"] = type(exc).__name__
    (output / "verdict.json").write_bytes(json_bytes(verdict))
    return verdict


def _unique(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate provider JSON key")
        result[name] = value
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target-root", type=Path, required=True)
    p.add_argument("--model", choices=gemini.CORE_MODELS, default=gemini.MODEL,
                   help="pin exact runtime; select gemini-3.6-flash for the verified fallback")
    p.add_argument("--case-id", choices=sorted(
        item for ids in CASES.values() for item in ids), required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--timeout", type=float, default=90)
    p.add_argument("--live", action="store_true")
    p.add_argument("--confirm-free-tier", action="store_true",
                   help="owner confirms key belongs to EREI Gemini Free tier")
    a = p.parse_args(argv)
    try:
        if not a.live or not a.confirm_free_tier:
            raise gemini.GeminiAdapterError("explicit --live AND --confirm-free-tier required")
        if not 5 <= a.timeout <= 120:
            raise gemini.GeminiAdapterError("timeout must be 5..120 seconds")
        gemini.model_endpoint(a.model)
        adapter_root = Path(__file__).resolve().parents[1]
        prepared = prepare(a.target_root, a.case_id, adapter_root)
        output = a.output_dir.expanduser().resolve()
        for prohibited in (prepared["root"], adapter_root):
            if output == prohibited or prohibited in output.parents:
                raise gemini.GeminiAdapterError("evidence directory must be OUTSIDE source checkout")
        if output.exists():
            raise gemini.GeminiAdapterError("evidence output already exists (never overwrite)")
        key = os.environ.get("GEMINI_API_KEY") or getpass.getpass(
            "Gemini Free-tier API key (hidden, not saved): "
        )
        if not key:
            raise gemini.GeminiAdapterError("empty API key")
        output.mkdir(parents=True, exist_ok=False)
        (output / "blind-request.json").write_bytes(json_bytes(prepared["request"]))
        try:
            result = record_one(prepared, output, key, a.timeout, model=a.model)
        except gemini.GeminiAdapterError as exc:
            (output / "attempt-failed.json").write_bytes(json_bytes({
                "schema_version": 1, "case_id": a.case_id,
                "source_head": gemini.EXPECTED_TARGET_HEAD,
                "model_requested": a.model,
                "status": "MODEL_REQUEST_FAILED_NOT_SCORED",
                "reason_category": exc.safe_code,
                "provider_http_status": exc.http_status,
                "evidence_kind": "observed_unverified",
                "stable_ready": False,
            }))
            print(
                "MODEL_REQUEST_FAILED_NOT_SCORED: "
                + exc.safe_code
                + (f" HTTP_{exc.http_status}" if exc.http_status is not None else "")
                + " (no auto retry; provider error and key redacted)",
                file=sys.stderr,
            )
            return 2
        print(json.dumps({
            "case_id": a.case_id, "status": result["status"],
            "pass": result["passed"], "evidence_dir": str(output),
            "model_requested": a.model,
            "model_version": result.get("provider_model_version"),
            "usage_metadata": result.get("usage_metadata"),
            "independently_accepted": False,
        }, sort_keys=True))
        return 0 if result["passed"] else 1
    except (ValueError, TypeError, OSError, gemini.GeminiAdapterError) as exc:
        # Do not show any prompt, private API key or provider response in errors.
        print("CORE_SMOKE_BLOCKED: " + type(exc).__name__, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
