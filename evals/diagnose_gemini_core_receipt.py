#!/usr/bin/env python3
"""Offline, read-only diagnosis of one already-captured Gemini Core receipt.

Never calls Gemini, reads a key, prints model text, or changes evidence.
Only fixed diagnostic categories, size, model identity and integrity flags
are printed; no retrospective independent acceptance or changed scoring.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from evals.adapters import gemini_core13_exact_target as adapter

MAX_VERDICT_BYTES = 32_000
MAX_RAW_BYTES = adapter.MAX_RESPONSE_BYTES


class ReceiptDiagnosticError(Exception):
    """Controlled local evidence failure; error text is never emitted."""


def strict_json(blob: bytes):
    def unique(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise ValueError("duplicate key")
            result[k] = v
        return result

    return json.loads(blob, object_pairs_hook=unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite")))


def bounded_read(path: Path, limit: int) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ReceiptDiagnosticError("missing or linked evidence")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ReceiptDiagnosticError("evidence exceeds local bound")
    return data


def _result(code: str, **meta):
    return {
        "kind": "OFFLINE_GEMINI_CORE_RECEIPT_DIAGNOSIS",
        "classification": code,
        "network_requests": 0,
        "model_calls": 0,
        "evidence_files_written": 0,
        "behavioral_pass_inferred": False,
        "independently_accepted": False,
        "stable_ready": False,
        **meta,
    }


def diagnose(directory: Path) -> dict:
    # No shell, no Git, no imports from untrusted disk, no source modifications.
    directory = directory.expanduser().resolve()
    try:
        verdict = strict_json(bounded_read(directory / "verdict.json", MAX_VERDICT_BYTES))
        if not isinstance(verdict, dict):
            return _result("VERDICT_FORMAT_INVALID")
        if (verdict.get("status") != "MODEL_RESPONSE_INVALID_UNVERIFIED"
                or verdict.get("passed") is not False):
            return _result("NOT_AN_INVALID_CORE_RECEIPT")
        model = verdict.get("model_requested")
        if not isinstance(model, str) or model not in adapter.CORE_MODELS:
            return _result("UNEXPECTED_MODEL_IN_VERDICT")
        raw = bounded_read(directory / "provider-raw.json", MAX_RAW_BYTES)
    except (OSError, ValueError, TypeError, ReceiptDiagnosticError):
        return _result("RECEIPT_UNREADABLE_OR_INVALID")

    verified_hash = (hashlib.sha256(raw).hexdigest()
                     == verdict.get("provider_response_sha256"))
    identity = {"model_requested": model, "raw_sha256_verified": verified_hash,
                "raw_bytes": len(raw)}
    if not verified_hash:
        return _result("RAW_SHA256_MISMATCH", **identity)

    try:
        envelope = strict_json(raw)
    except (ValueError, UnicodeError, TypeError):
        return _result("PROVIDER_JSON_INVALID_OR_DUPLICATE", **identity)
    if not isinstance(envelope, dict):
        return _result("PROVIDER_ROOT_NOT_OBJECT", **identity)
    if envelope.get("modelVersion") != model:
        return _result("PROVIDER_MODEL_MISMATCH_OR_MISSING", **identity)
    if not isinstance(envelope.get("usageMetadata"), dict):
        return _result("PROVIDER_USAGE_METADATA_MISSING", **identity)

    candidates = envelope.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 1:
        return _result("CANDIDATE_COUNT_OR_TYPE_INVALID", **identity)
    candidate = candidates[0]
    if not isinstance(candidate, dict):
        return _result("CANDIDATE_COUNT_OR_TYPE_INVALID", **identity)
    reason = candidate.get("finishReason")
    if reason != "STOP":
        # Never echo arbitrary provider strings in the diagnostic.
        known = {"MAX_TOKENS", "SAFETY", "RECITATION", "OTHER", "MALFORMED_FUNCTION_CALL"}
        finish_kind = reason if isinstance(reason, str) and reason in known else "UNKNOWN_OR_MISSING"
        return _result("PROVIDER_DID_NOT_FINISH_NORMALLY",
                       **identity, finish_reason_category=finish_kind)

    content = candidate.get("content")
    parts = content.get("parts") if isinstance(content, dict) else None
    if not isinstance(parts, list) or len(parts) != 1:
        return _result("PART_COUNT_INVALID", **identity)
    part = parts[0]
    if not isinstance(part, dict) or set(part) != {"text"}:
        return _result("PART_TYPE_OR_SHAPE_INVALID", **identity)
    text = part.get("text")
    if not isinstance(text, str):
        return _result("MODEL_TEXT_MISSING", **identity)
    text_bytes = len(text.encode("utf-8"))
    if text_bytes > MAX_RAW_BYTES:
        return _result("MODEL_TEXT_OVERSIZE", **identity)

    # Match existing adapter's fence tolerance, but print NO generated text.
    fence = re.fullmatch(r"\x60\x60\x60(?:json)?\s*(.*?)\s*\x60\x60\x60", text,
                         flags=re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    try:
        answer = strict_json(text.encode("utf-8"))
    except (ValueError, UnicodeError, TypeError):
        return _result("MODEL_TEXT_NOT_STRICT_JSON", **identity,
                       generated_text_bytes=text_bytes)
    if not isinstance(answer, dict) or set(answer) != {"output", "metadata"}:
        return _result("MODEL_JSON_ROOT_SHAPE_INVALID", **identity,
                       generated_text_bytes=text_bytes)

    output = answer["output"]
    if not isinstance(output, dict):
        return _result("MODEL_OUTPUT_NOT_SIMULATION_OBJECT", **identity,
                       generated_text_bytes=text_bytes)
    if set(output) != {"contract", "decision", "actions", "state"}:
        return _result("MODEL_SIMULATION_FIELDS_INVALID", **identity,
                       generated_text_bytes=text_bytes)
    if output.get("contract") != adapter.contract.SIMULATION_CONTRACT:
        return _result("MODEL_SIMULATION_CONTRACT_MISMATCH", **identity,
                       generated_text_bytes=text_bytes)
    metadata = answer["metadata"]
    if (not isinstance(metadata, dict) or set(metadata) != {"risk"}
            or not isinstance(metadata.get("risk"), str)
            or metadata["risk"] not in adapter.contract.RISK_LEVELS):
        return _result("MODEL_RISK_METADATA_INVALID", **identity,
                       generated_text_bytes=text_bytes)
    try:
        adapter.parse_gemini_result(raw)
    except adapter.GeminiAdapterError:
        return _result("MODEL_STRICT_ADAPTER_REJECTED_OTHER", **identity,
                       generated_text_bytes=text_bytes)
    return _result("MODEL_SHAPE_VALID_BUT_PRIOR_SCORING_EXCEPTION", **identity,
                   generated_text_bytes=text_bytes)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--evidence-dir", required=True, type=Path)
    args = p.parse_args(argv)
    try:
        result = diagnose(args.evidence_dir)
    except Exception:
        # Do not allow filesystem exception paths or JSON fragments to leak.
        result = _result("RECEIPT_DIAGNOSTIC_UNAVAILABLE")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["classification"] not in {
        "RECEIPT_DIAGNOSTIC_UNAVAILABLE", "RECEIPT_UNREADABLE_OR_INVALID",
        "RAW_SHA256_MISMATCH",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
