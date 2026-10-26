#!/usr/bin/env python3
"""Metadata-only Gemini project/key/model diagnostic. NO generateContent POST.

Asks invisibly for a Free-tier key. Prints only a status code and allowed
model metadata; never provider error text, header values, or token.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.request

from evals.adapters import gemini_core13_exact_target as adapter

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/" + adapter.MODEL
MAX_METADATA_BYTES = 128 * 1024


def metadata_check(key: str, *, timeout: int = 15,
                   opener=None) -> dict:
    if not isinstance(key, str) or not key or key != key.strip():
        return {"result": "KEY_FORMAT_INVALID", "http_status": None}
    if not key.isascii() or any(x in key for x in ("\r", "\n", "\x00")):
        return {"result": "KEY_FORMAT_INVALID", "http_status": None}
    if not 5 <= timeout <= 30:
        return {"result": "PROBE_TIMEOUT_INVALID", "http_status": None}
    req = urllib.request.Request(
        API_URL,
        headers={
            "x-goog-api-key": key,
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        handler = opener if opener is not None else urllib.request.build_opener(adapter.NoRedirect())
        with handler.open(req, timeout=timeout) as response:
            raw = response.read(MAX_METADATA_BYTES + 1)
            status = response.status
        if len(raw) > MAX_METADATA_BYTES:
            return {"result": "METADATA_OVERSIZE", "http_status": status}
        metadata = json.loads(raw)
        if not isinstance(metadata, dict):
            return {"result": "INVALID_METADATA", "http_status": status}
        methods = metadata.get("supportedGenerationMethods", [])
        if not isinstance(methods, list):
            methods = []
        name = metadata.get("name")
        return {
            "result": "MODEL_METADATA_AVAILABLE",
            "http_status": status,
            "model": adapter.MODEL,
            "model_identity_matches": name == f"models/{adapter.MODEL}",
            "generate_content_listed": "generateContent" in methods,
            "does_not_prove_free_tier_or_generation_quota": True,
        }
    except urllib.error.HTTPError as exc:
        return {"result": "MODEL_METADATA_HTTP_ERROR",
                "http_status": int(exc.code)}
    except (OSError, urllib.error.URLError, ValueError, adapter.GeminiAdapterError):
        return {"result": "MODEL_METADATA_TRANSPORT_ERROR", "http_status": None}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--metadata-only", action="store_true", required=True)
    args = p.parse_args(argv)
    key = os.environ.get("GEMINI_API_KEY") or getpass.getpass(
        "Gemini API key (hidden, never logged): "
    )
    result = metadata_check(key)
    print(json.dumps(result, sort_keys=True))
    return 0 if (result["result"] == "MODEL_METADATA_AVAILABLE"
                 and result["generate_content_listed"]
                 and result["model_identity_matches"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
