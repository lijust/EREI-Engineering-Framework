"""Offline observational analysis of state-only failure versus policy errors.

Never rewrites a provider receipt, model answer, frozen benchmark or scorer.
The replayed-state scenario is a *counterfactual*, not a second model result.
"""
from __future__ import annotations

import copy
import json

from evals import runner

ALLOWED_STATE_FIELDS = frozenset({
    "task_events", "review_status", "feedback", "promotion_queue",
    "core_modified", "capability_status", "executions",
})


def _identity(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def classify(expectation, response, case_input, *,
             score_fn=runner.score_simulation,
             replay_fn=runner.simulate_actions):
    """Perform read-only analysis using the unchanged scorer and reducer.

    Call only from an owner-local process with original input/expectation.
    A counterfactual pass must NEVER be reported as a model/harness PASS.
    Output contains no prompts, expected states, actions, or private values.
    """
    raw_pass, _ = score_fn(expectation, response, case_input)
    report = {
        "raw_model_pass": bool(raw_pass),
        "counterfactual_replay_pass": None,
        "failure_class": "ORIGINAL_PASS" if raw_pass else "UNCLASSIFIED",
        "replayed_state_equals_model_claim": None,
        "different_state_fields": [],
        "independently_accepted": False,
        "stable_ready": False,
        "provider_calls": 0,
    }
    if raw_pass:
        return report
    try:
        actions = response["output"]["actions"]
        initial = case_input["initial_state"]
        claimed = response["output"]["state"]
        # Validate actions FIRST. A malformed claimed state must not be
        # misreported as an invalid/forbidden action.
        calculated = replay_fn(initial, actions)
        state_shape_valid = isinstance(claimed, dict)
        report["claimed_state_shape_valid"] = state_shape_valid
        if state_shape_valid:
            fields = sorted({
                field if field in ALLOWED_STATE_FIELDS else "UNKNOWN_STATE_FIELD"
                for field in set(calculated) | set(claimed)
                if field not in calculated or field not in claimed or
                _identity(calculated[field]) != _identity(claimed[field])
            })
        else:
            fields = []
        report["different_state_fields"] = fields
        report["replayed_state_equals_model_claim"] = (
            state_shape_valid and not fields
        )
        # Counterfactual constructed in-memory, NEVER persisted or fed to model.
        alternative = copy.deepcopy(response)
        alternative["output"]["state"] = calculated
        cf_pass, _ = score_fn(expectation, alternative, case_input)
        report["counterfactual_replay_pass"] = bool(cf_pass)
        if not state_shape_valid:
            report["failure_class"] = (
                "MALFORMED_STATE_ONLY_COUNTERFACTUAL" if cf_pass else
                "MALFORMED_STATE_AND_POLICY_OR_ACTION_FAILURE"
            )
        else:
            report["failure_class"] = (
                "STATE_ONLY_COUNTERFACTUAL" if cf_pass else
                "POLICY_OR_ACTION_FAILURE" if not fields else
                "STATE_AND_POLICY_OR_ACTION_FAILURE"
            )
    except (ValueError, KeyError, TypeError, IndexError, OverflowError):
        report["failure_class"] = "INVALID_OR_FORBIDDEN_ACTION"
    return report
