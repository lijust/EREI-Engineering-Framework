"""Separate read-only verifier for EREI proposal state previews.

Unlike the proposal runtime, this module may use a separately pinned,
previously reviewed simulation reducer. It verifies ONLY state transition
parity and never attests policy correctness, real execution or Stable status.
It does not import model outputs from test fixtures or use expected answers.
"""
from __future__ import annotations
import json
from typing import Any, Callable


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def verify_preview(proposal: Any, initial_state: Any, preview: Any,
                   *, independent_reducer: Callable[[Any, Any], Any]) -> dict:
    """Verify a deterministic preview with a separate reference reducer.

    The reference reducer must be supplied by a verified, immutable source,
    e.g. the exact PR98 Git blob loaded by existing local audit tooling.
    Success is independent **state parity only**, not policy authorization.
    """
    result = {
        "kind": "EREI_PILOT_REFERENCE_REPLAY_CHECK",
        "independently_accepted": False,
        "stable_ready": False,
        "real_execution_verified": False,
        "model_original_score_changed": False,
        "provider_calls": 0,
    }
    if (type(preview) is not dict or
            preview.get("status") != "AUTHORIZED_IN_MEMORY_PREVIEW" or
            preview.get("executed") is not False):
        return {**result, "status": "NOT_AUTHORIZED_FOR_REPLAY"}
    try:
        if (type(proposal) is not dict or type(initial_state) is not dict or
                type(preview.get("materialized_state")) is not dict):
            raise ValueError("invalid input shape")
        if not callable(independent_reducer):
            raise ValueError("reference reducer missing")
        reference = independent_reducer(initial_state, proposal["actions"])
        same = _canonical(reference) == _canonical(preview["materialized_state"])
        return {
            **result, "status": "REFERENCE_STATE_PARITY_PASS" if same
            else "REFERENCE_STATE_PARITY_FAIL",
            "state_parity": same, "policy_correctness": "NOT_ASSESSED",
        }
    except (ValueError, TypeError, KeyError, OverflowError):
        return {**result, "status": "REFERENCE_REPLAY_REJECTED",
                "state_parity": False, "policy_correctness": "NOT_ASSESSED"}
