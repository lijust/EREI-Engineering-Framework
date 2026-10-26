#!/usr/bin/env python3
"""One owner-authorized local Gemini schema-experiment call, never CI.

For exploratory A/B use ONLY: same immutable PR98 Core13 case/model/scorer,
but Gemini request adds candidate responseJsonSchema. Every call writes a NEW
separate receipt. No auto retry, no rewrite of baseline or Stable promotion.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from evals.adapters import gemini_core13_exact_target as gemini
from evals import run_gemini_core_smoke as smoke
from evals.experiments import gemini_core13_schema_candidate as candidate


def generate_candidate_raw_once(prompt: str, *, key: str, model: str, timeout: float) -> tuple[bytes, bytes]:
    """Make exactly one bounded GenerateContent POST, no retry or redirects."""
    endpoint = gemini.model_endpoint(model)
    if (not isinstance(key, str) or not key or key != key.strip()
            or not key.isascii() or any(c in key for c in "\r\n\x00")):
        raise gemini.GeminiAdapterError("invalid API key input", safe_code="CANDIDATE_KEY_REJECTED")
    if not 5 <= timeout <= 120:
        raise gemini.GeminiAdapterError("invalid timeout", safe_code="CANDIDATE_TIMEOUT_REJECTED")
    request_bytes = candidate.build_candidate_body(prompt, model=model)
    request = urllib.request.Request(
        endpoint,
        headers={
            "x-goog-api-key": key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        data=request_bytes,
        method="POST",
    )
    try:
        with urllib.request.build_opener(gemini.NoRedirect()).open(
            request, timeout=timeout
        ) as response:
            raw = response.read(gemini.MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise gemini.GeminiAdapterError(
            "provider returned HTTP error; body redacted",
            safe_code="CANDIDATE_HTTP_ERROR", http_status=int(exc.code)
        ) from None
    except (OSError, urllib.error.URLError, ValueError, gemini.GeminiAdapterError):
        raise gemini.GeminiAdapterError(
            "candidate transport rejected; no retry", safe_code="CANDIDATE_TRANSPORT_ERROR"
        ) from None
    if len(raw) > gemini.MAX_RESPONSE_BYTES:
        raise gemini.GeminiAdapterError(
            "candidate provider body oversize", safe_code="CANDIDATE_RESPONSE_OVERSIZE"
        )
    return raw, request_bytes


def record_candidate(prepared: dict, output: Path, *, key: str, model: str,
                     timeout: float, expected_body_sha256: str | None = None) -> dict:
    """Persist raw bytes BEFORE strict parsing/scoring; distinct experiment."""
    raw, body = generate_candidate_raw_once(
        prepared["prompt"], key=key, model=model, timeout=timeout
    )
    (output / "provider-raw.json").write_bytes(raw)
    if (expected_body_sha256 is not None
            and smoke.sha(body) != expected_body_sha256):
        raise gemini.GeminiAdapterError(
            "candidate request body differs from retained preflight manifest",
            safe_code="CANDIDATE_REQUEST_DRIFT",
        )
    verdict = {
        "schema_version": 1,
        "evidence_kind": "observed_experimental_unverified",
        "experiment": "core13_native_response_json_schema_v1",
        "experimental_schema": True,
        "independently_accepted": False,
        "stable_ready": False,
        "source_head": gemini.EXPECTED_TARGET_HEAD,
        "source_tree": gemini.EXPECTED_TARGET_TREE,
        "adapter_source_revision": prepared["adapter_source"]["adapter_source_revision"],
        "model_requested": model,
        "case_id": prepared["case"]["id"],
        "suite_id": prepared["suite"]["suite_id"],
        "provider_response_sha256": smoke.sha(raw),
        "request_body_sha256": smoke.sha(body),
        "response_schema_sha256": smoke.sha(
            smoke.canonical_bytes(candidate.response_json_schema())
        ),
        "blind_request_sha256": smoke.sha(
            smoke.canonical_bytes(prepared["request"])
        ),
        "prompt_sha256": smoke.sha(prepared["prompt"].encode("utf-8")),
        "captured_at_utc": datetime.now(timezone.utc).replace(
            microsecond=0
        ).isoformat(),
        "passed": False,
    }
    try:
        envelope = json.loads(
            raw, object_pairs_hook=smoke._unique,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("invalid nonfinite JSON")),
        )
        if not isinstance(envelope, dict):
            raise ValueError("provider envelope invalid")
        verdict["provider_model_version"] = envelope.get("modelVersion")
        verdict["provider_response_id"] = envelope.get("responseId")
        verdict["usage_metadata"] = envelope.get("usageMetadata")
        if (verdict["provider_model_version"] != model
                or not isinstance(verdict["usage_metadata"], dict)):
            raise ValueError("provider model/usage mismatch")
        normalized = gemini.parse_gemini_result(raw)
        (output / "adapter-normalized.json").write_bytes(smoke.json_bytes(normalized))
        scores = [
            prepared["runner"].score(expectation, normalized, prepared["case"]["input"])
            for expectation in prepared["case"]["expectations"]
        ]
        verdict["scorer_results"] = [
            {"passed": bool(ok), "reason": reason} for ok, reason in scores
        ]
        verdict["passed"] = bool(scores) and all(ok for ok, _ in scores)
        verdict["status"] = (
            "EXPERIMENTAL_MODEL_RESPONSE_SCORED_PASS_UNVERIFIED"
            if verdict["passed"] else
            "EXPERIMENTAL_MODEL_RESPONSE_SCORED_FAIL_UNVERIFIED"
        )
    except (TypeError, KeyError, ValueError, AttributeError, gemini.GeminiAdapterError) as exc:
        verdict["status"] = "EXPERIMENTAL_MODEL_RESPONSE_INVALID_UNVERIFIED"
        verdict["failure_type"] = type(exc).__name__
    (output / "verdict.json").write_bytes(smoke.json_bytes(verdict))
    return verdict


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target-root", type=Path, required=True)
    p.add_argument("--model", choices=gemini.CORE_MODELS,
                   default="gemini-3.5-flash-lite")
    p.add_argument("--case-id", choices=sorted(
        c for ids in smoke.CASES.values() for c in ids), required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--timeout", type=float, default=90)
    p.add_argument("--live", action="store_true")
    p.add_argument("--confirm-free-tier", action="store_true")
    p.add_argument("--confirm-experimental-schema", action="store_true")
    a = p.parse_args(argv)
    try:
        if not (a.live and a.confirm_free_tier and a.confirm_experimental_schema):
            raise gemini.GeminiAdapterError("explicit owner authorization missing")
        if not 5 <= a.timeout <= 120:
            raise gemini.GeminiAdapterError("timeout blocked")
        gemini.model_endpoint(a.model)
        source = Path(__file__).resolve().parents[2]
        prepared = smoke.prepare(a.target_root, a.case_id, source)
        output = a.output_dir.expanduser().resolve()
        for prohibited in (prepared["root"], source):
            if output == prohibited or prohibited in output.parents:
                raise gemini.GeminiAdapterError("evidence dir must be outside source")
        if output.exists():
            raise gemini.GeminiAdapterError("immutable receipt folder exists")
        key = os.environ.get("GEMINI_API_KEY") or getpass.getpass(
            "Gemini Free-tier API key (hidden, not saved): "
        )
        if not key:
            raise gemini.GeminiAdapterError("no local API key")
        # Persist an immutable, secret-free request/source manifest BEFORE
        # the only POST. Even HTTP 400/timeout must have schema provenance.
        candidate_body = candidate.build_candidate_body(
            prepared["prompt"], model=a.model
        )
        captured_at = datetime.now(timezone.utc).replace(
            microsecond=0
        ).isoformat()
        provenance = {
            "schema_version": 1,
            "kind": "CORE13_EXPERIMENT_REQUEST_PROVENANCE",
            "evidence_kind": "observed_experimental_unverified",
            "experiment": "core13_native_response_json_schema_v1",
            "source_head": gemini.EXPECTED_TARGET_HEAD,
            "source_tree": gemini.EXPECTED_TARGET_TREE,
            "adapter_source_revision": prepared["adapter_source"]["adapter_source_revision"],
            "case_id": a.case_id,
            "suite_id": prepared["suite"]["suite_id"],
            "model_requested": a.model,
            "captured_at_utc": captured_at,
            "request_body_sha256": smoke.sha(candidate_body),
            "response_schema_sha256": smoke.sha(
                smoke.canonical_bytes(candidate.response_json_schema())
            ),
            "blind_request_sha256": smoke.sha(
                smoke.canonical_bytes(prepared["request"])
            ),
            "prompt_sha256": smoke.sha(prepared["prompt"].encode("utf-8")),
            "network_requests_authorized_max": 1,
            "independently_accepted": False,
            "stable_ready": False,
        }
        output.mkdir(parents=True, exist_ok=False)
        (output / "blind-request.json").write_bytes(
            smoke.json_bytes(prepared["request"])
        )
        (output / "candidate-provenance.json").write_bytes(
            smoke.json_bytes(provenance)
        )
        try:
            verdict = record_candidate(
                prepared, output, key=key, model=a.model, timeout=a.timeout,
                expected_body_sha256=provenance["request_body_sha256"],
            )
        except gemini.GeminiAdapterError as exc:
            (output / "attempt-failed.json").write_bytes(smoke.json_bytes({
                "evidence_kind": "observed_experimental_unverified",
                "status": "EXPERIMENTAL_MODEL_REQUEST_FAILED_NOT_SCORED",
                "case_id": a.case_id,
                "model_requested": a.model,
                "experiment": "core13_native_response_json_schema_v1",
                "reason_category": exc.safe_code,
                "provider_http_status": exc.http_status,
                "stable_ready": False,
            }))
            print("EXPERIMENTAL_MODEL_REQUEST_FAILED_NOT_SCORED: "
                  + exc.safe_code
                  + (f" HTTP_{exc.http_status}" if exc.http_status else "")
                  + " (no auto retry; secret/provider body redacted)", file=sys.stderr)
            return 2
        print(json.dumps({
            "case_id": a.case_id,
            "status": verdict["status"],
            "passed": verdict["passed"],
            "model_requested": a.model,
            "provider_model_version": verdict.get("provider_model_version"),
            "usage_metadata": verdict.get("usage_metadata"),
            "experiment": "core13_native_response_json_schema_v1",
            "evidence_dir": str(output),
            "independently_accepted": False,
            "stable_ready": False,
        }, sort_keys=True))
        return 0 if verdict["passed"] else 1
    except (OSError, ValueError, TypeError, gemini.GeminiAdapterError):
        print("SCHEMA_EXPERIMENT_BLOCKED_UNVERIFIED", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
