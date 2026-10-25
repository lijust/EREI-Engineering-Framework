#!/usr/bin/env python3
"""Bounded Gemini 3.8 Flash adapter for one EREI V2 blind Core request.

Explicit local --live only. NO unattended CI calls, no API key on disk, no
billing-tier assumptions, no tool calls, and no independently authenticated
model release/adoption claim. Only synthetic/public Framework inputs allowed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    from . import copilot_cli_exact_target as contract
except ImportError:
    import copilot_cli_exact_target as contract

MODEL = "gemini-3.8-flash"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/" + MODEL + ":generateContent"
EXPECTED_TARGET_HEAD = "31d4e518b9e71a9585df9097e7ca07a7e25af916"
EXPECTED_TARGET_TREE = "913c6a0daaa7a6efa7d6d2148aa0294812fab360"
MAX_REQUEST_BYTES = 200_000
MAX_RESPONSE_BYTES = 512_000
PUBLIC_CORE_ARTIFACTS = {
    "skills/task-learning-capture + workflows/learning-review",
    "workflows/candidate-capability-adoption",
}


class GeminiAdapterError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GeminiAdapterError("API redirect rejected")


def verify_frozen_target(root: Path) -> None:
    """Binding is to candidate #98; do not silently evaluate modified source."""
    root = root.resolve()
    isolated = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    try:
        head = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
            stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=10, env=isolated, text=True,
        ).strip()
        tree = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD^{tree}"],
            stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=10, env=isolated, text=True,
        ).strip()
        top = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=10, env=isolated, text=True,
        ).strip()
        dirty = subprocess.check_output(
            ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
            stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=10, env=isolated, text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as ex:
        raise GeminiAdapterError("frozen target identity unavailable") from ex
    if Path(top).resolve() != root or head != EXPECTED_TARGET_HEAD or tree != EXPECTED_TARGET_TREE:
        raise GeminiAdapterError("frozen #98 HEAD/tree mismatch; no API request")
    if dirty:
        raise GeminiAdapterError("frozen target worktree is dirty; no API request")


def prepare_one(request: dict, root: Path) -> str:
    request = contract.validate_request(request)
    if request["artifact"] not in PUBLIC_CORE_ARTIFACTS:
        raise GeminiAdapterError("only public frozen Core13 artifact declarations allowed")
    case_input = request["input"]
    if case_input.get("response_contract") != contract.SIMULATION_CONTRACT:
        raise GeminiAdapterError("only action-simulation Core13 is permitted")
    # No scorer-private expectations, real tool traces or credential material.
    if set(case_input) != {"prompt", "response_contract", "initial_state", "facts"}:
        raise GeminiAdapterError("unexpected Core input fields (may leak scorer/private content)")
    if request["context"]:
        raise GeminiAdapterError("nonempty context not allowed in synthetic-only pilot")
    artifacts = contract.resolve_artifact(root, request["artifact"])
    prompt = contract.build_direct_prompt(artifacts, case_input, {})
    if len(prompt.encode("utf-8")) > MAX_REQUEST_BYTES:
        raise GeminiAdapterError("bounded synthetic prompt exceeded")
    return prompt


def parse_gemini_result(payload: bytes) -> dict:
    try:
        def unique_object(pairs):
            value = {}
            for key, item in pairs:
                if key in value:
                    raise ValueError("duplicate provider response key")
                value[key] = item
            return value

        def no_nonfinite(value):
            raise ValueError("non-finite provider value")

        envelope = json.loads(
            payload, object_pairs_hook=unique_object, parse_constant=no_nonfinite
        )
        candidates = envelope["candidates"]
        if not isinstance(candidates, list) or len(candidates) != 1:
            raise ValueError("expected one candidate")
        candidate = candidates[0]
        if candidate.get("finishReason") != "STOP":
            raise ValueError("candidate not normally finished")
        parts = candidate["content"]["parts"]
        if not isinstance(parts, list) or len(parts) != 1 or set(parts[0]) != {"text"}:
            raise ValueError("expected exactly one plain-text JSON part")
        text = parts[0]["text"]
        if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_RESPONSE_BYTES:
            raise ValueError("oversize or invalid text")
        # Reuse the exact existing typed output parser, rather than weakening
        # the model response contract for a different API provider.
        result = contract._parse_final_json(text)
        if not isinstance(result["output"], dict):
            raise ValueError("Core13 requires typed action-simulation output")
        return result
    except (KeyError, TypeError, IndexError, ValueError, contract.CopilotExactTargetError) as ex:
        raise GeminiAdapterError("invalid/incomplete model response; do not count as passed") from ex


def generate_once(prompt: str, *, key: str, timeout: float) -> dict:
    if not isinstance(key, str) or not key.strip():
        raise GeminiAdapterError("GEMINI_API_KEY missing from process environment")
    if not 5 <= timeout <= 120:
        raise GeminiAdapterError("timeout out of bounded 5–120 second range")
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens": 4096,
            "temperature": 0,
        },
    }
    raw = json.dumps(body, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(raw) > MAX_REQUEST_BYTES:
        raise GeminiAdapterError("API body exceeds allowed bound")
    req = urllib.request.Request(
        API_URL,
        headers={
            "x-goog-api-key": key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        data=raw,
        method="POST",
    )
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=timeout) as response:
            content = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as ex:
        # Never print provider response body or API key (could contain request).
        raise GeminiAdapterError(f"Gemini API request blocked: HTTP {ex.code}") from None
    except (OSError, urllib.error.URLError) as ex:
        raise GeminiAdapterError("Gemini API transport unavailable; no automatic retries") from None
    if len(content) > MAX_RESPONSE_BYTES:
        raise GeminiAdapterError("Gemini response exceeds byte limit")
    return parse_gemini_result(content)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target-root", type=Path, required=True)
    p.add_argument("--live", action="store_true", help="explicit single Gemini API call")
    p.add_argument("--timeout", type=float, default=90)
    args = p.parse_args(argv)
    try:
        if not args.live:
            raise GeminiAdapterError("explicit --live required; no synthetic answer will be fabricated")
        # Strictly one stdin request per process; CI tests never pass --live.
        payload = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        if len(payload) > MAX_REQUEST_BYTES:
            raise GeminiAdapterError("oversized blind request")
        request = json.loads(payload)
        if not isinstance(request, dict):
            raise GeminiAdapterError("blind request must be a JSON object")
        verify_frozen_target(args.target_root)
        prompt = prepare_one(request, args.target_root)
        key = os.environ.get("GEMINI_API_KEY", "")
        result = generate_once(prompt, key=key, timeout=args.timeout)
    except (ValueError, json.JSONDecodeError, GeminiAdapterError,
            contract.CopilotExactTargetError) as ex:
        # Do not print provider response content or exception containing secrets.
        print("GEMINI_ADAPTER_BLOCKED: " + str(ex)[:220], file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
