#!/usr/bin/env python3
"""ONE public-text Gemini fallback probe. No Core score, private payload, or retry.

Use only after operator confirms selected project/model is in Free tier.
No production data, no key in args/files, no provider response body logs.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

from evals.adapters.gemini_core13_exact_target import NoRedirect

ALLOWED_DIAGNOSTIC_MODELS = ("gemini-3.6-flash", "gemini-3.5-flash-lite")
MAX_RESPONSE_BYTES = 64_000


def probe(*, model: str, key: str, opener: Any = None,
          core_config_diagnostic: bool = False) -> dict:
    """Make at most one request with constant public prompt and bounded output."""
    if model not in ALLOWED_DIAGNOSTIC_MODELS:
        return {"status": "UNAPPROVED_DIAGNOSTIC_MODEL", "counted_core_cases": 0}
    if (not isinstance(key, str) or not key.strip() or key != key.strip()
            or not key.isascii() or any(c in key for c in "\r\n\x00")):
        return {"status": "KEY_FORMAT_INVALID", "counted_core_cases": 0}
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent"
    # Compare exactly the Core config while keeping a TINY PUBLIC prompt.
    # Diagnostic only: NOT a Core run, no Framework source or acceptance labels.
    message = ('Respond ONLY with this JSON object: {"status":"READY"}'
               if core_config_diagnostic else "Reply with exactly READY.")
    config = ({"responseMimeType": "application/json", "maxOutputTokens": 4096,
               "thinkingConfig": {"thinkingLevel": "low"}}
              if core_config_diagnostic else {"maxOutputTokens": 64})
    raw_request = json.dumps({
        "contents": [{"role": "user", "parts": [{"text": message}]}],
        "generationConfig": config,
    }, separators=(",", ":"), allow_nan=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        data=raw_request,
        method="POST",
    )
    try:
        client = opener if opener is not None else urllib.request.build_opener(NoRedirect())
        with client.open(request, timeout=60) as response:
            payload = response.read(MAX_RESPONSE_BYTES + 1)
            status_code = response.status
        if len(payload) > MAX_RESPONSE_BYTES:
            return {"status": "PROVIDER_RESPONSE_OVERSIZE", "counted_core_cases": 0}
        envelope = json.loads(payload)
        if not isinstance(envelope, dict):
            return {"status": "PROVIDER_RESPONSE_INVALID", "counted_core_cases": 0}
        candidates = envelope.get("candidates")
        if not isinstance(candidates, list) or len(candidates) != 1:
            return {"status": "PROVIDER_RESPONSE_INVALID", "counted_core_cases": 0}
        candidate = candidates[0]
        if not isinstance(candidate, dict):
            return {"status": "PROVIDER_RESPONSE_INVALID", "counted_core_cases": 0}
        content = candidate.get("content", {})
        parts = content.get("parts", []) if isinstance(content, dict) else []
        if not isinstance(parts, list):
            return {"status": "PROVIDER_RESPONSE_INVALID", "counted_core_cases": 0}
        text = "".join(p.get("text", "") for p in parts
                       if isinstance(p, dict) and isinstance(p.get("text"), str))
        model_version = envelope.get("modelVersion")
        token_usage = envelope.get("usageMetadata")
        safe_usage = {}
        if isinstance(token_usage, dict):
            for name in ("promptTokenCount", "candidatesTokenCount", "totalTokenCount"):
                value = token_usage.get(name)
                if type(value) is int and 0 <= value < 10_000_000:
                    safe_usage[name] = value
        if core_config_diagnostic:
            try:
                parsed_text = json.loads(text)
                returned_ready = (
                    isinstance(parsed_text, dict) and
                    parsed_text.get("status") == "READY"
                )
            except (ValueError, TypeError):
                returned_ready = False
        else:
            returned_ready = text.strip() == "READY"
        return {
            "status": "MODEL_DIAGNOSTIC_RESPONSE_RECEIVED",
            "http_status": status_code,
            "core_config_diagnostic": core_config_diagnostic,
            "requested_model": model,
            "provider_model_version": model_version if isinstance(model_version, str) else None,
            "finish_reason": candidate.get("finishReason") if isinstance(candidate.get("finishReason"), str) else None,
            "returned_ready": returned_ready,
            "usage_metadata": safe_usage,
            "counted_core_cases": 0,
            "independent_acceptance": False,
            "stable_ready": False,
        }
    except urllib.error.HTTPError as err:
        return {"status": "MODEL_DIAGNOSTIC_HTTP_ERROR",
                "http_status": err.code if type(err.code) is int else None,
                "requested_model": model, "counted_core_cases": 0}
    except (OSError, urllib.error.URLError, ValueError, TypeError, RuntimeError):
        return {"status": "MODEL_DIAGNOSTIC_TRANSPORT_OR_PARSE_ERROR",
                "requested_model": model, "counted_core_cases": 0}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", required=True, choices=ALLOWED_DIAGNOSTIC_MODELS)
    p.add_argument("--live", action="store_true")
    p.add_argument("--confirm-free-tier", action="store_true")
    p.add_argument("--core-config-diagnostic", action="store_true",
                   help="tiny PUBLIC text under Core JSON/4096/low-thinking settings; NOT Core")
    args = p.parse_args(argv)
    if not args.live or not args.confirm_free_tier:
        print('{"status":"NOT_AUTHORIZED_NO_API_CALL","counted_core_cases":0}')
        return 2
    key = os.environ.get("GEMINI_API_KEY") or getpass.getpass(
        "Free-tier Gemini API key (hidden): "
    )
    result = probe(model=args.model, key=key,
                   core_config_diagnostic=args.core_config_diagnostic)
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    return 0 if result["status"] == "MODEL_DIAGNOSTIC_RESPONSE_RECEIVED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
