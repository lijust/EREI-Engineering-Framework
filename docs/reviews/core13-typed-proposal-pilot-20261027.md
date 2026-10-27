# EREI typed-proposal pilot — policy-authorized state materialization

**Status: bounded experimental reference implementation, not production.**

This pilot implements the *first executable slice* of Astra's recommendation:
`typed AI proposal → independent caller-supplied policy facts → existing
capability-activation resolver → deterministic state preview → offline test
verification`. It deliberately **does not call Gemini, execute a capability,
write project files, approve changes, adopt candidates or claim independent
operational acceptance**.

## Contract and responsibility split

`tools.learning_proposal_runtime.evaluate_proposal(proposal, initial_state, trusted_context)`

The model-facing proposal carries **only**:

```json
{"contract":"erei-proposal-v1",
 "decision":"capture_task",
 "actions":[{"op":"record_task",
             "occurrence_id":"synthetic-01",
             "outcome":"success",
             "signals":{"rework_cycles":0,"verification_failures":0,
                        "verification_escape":false}}],
 "claimed_state":{"task_events":[]}}
```

The optional `claimed_state` is *untrusted diagnostic input*, NEVER the
authoritative state. The caller owns `initial_state` and **independently
established** `trusted_context`. The model cannot set workflow domain,
activation evidence, project SHA, adoption approval or facts. Candidate activation also requires a caller-attested timezone-aware UTC-comparable clock to make expiry deterministic. The pilot
checks the explicit decision→operation allowlist and typed fields before
authorizing. It permits only three classes of pure changes:

- Task learning capture, omission and sensitive capture rejection; recording
  requires `engineering_execution=true` and exact supplied occurrence,
  outcome and typed signals.
- Authorized review status from an upstream deterministic task-learning
  policy, or feedback→nomination from a supplied review finding. These trusted
  decisions are caller-attested, **not authenticated** by this pilot.
- Candidate/Stable capability resolution by reusing
  `tools.capability_activation.resolve_activation()`. No parallel adoption
  engine or ref checks are introduced. Candidate execution proposal requires
  a matching commit-pinned, unexpired existing adoption; branch pins remain
  rejected. Unknown block causes fail closed.

Materialization is a copy-on-write in-memory reducer. There are **no
external side effects**: even a successful `execute_capability` only appends
to a *simulation* `executions` list; it does not run any real capability.
The original model proposal remains untouched; `claimed_state` mismatch is
reported separately. Denied proposals cannot materialize state.

Example (synthetic only):

```python
from tools.learning_proposal_runtime import evaluate_proposal
result = evaluate_proposal(
    {"contract":"erei-proposal-v1","decision":"omit_task","actions":[]},
    {"task_events":[]},
    {"domain":"task_capture","facts":{"engineering_execution":False}},
)
assert result["status"] == "AUTHORIZED_IN_MEMORY_PREVIEW"
assert result["materialized_state"] == {"task_events":[]}
assert result["executed"] is False
assert result["independently_verified"] is False
```

## Evidence, safety and comparison boundaries

- **Frozen PR98 evaluator remains unmodified.** The unit tests use its
  reducer only as an independent *test reference* for synthetic fixtures.
  The live proposal module never imports the scorer or any case expectation.
- No `reference_actions` or `expected_state` are used for runtime decisions.
  Consequently this cannot and must not change any frozen Core13 PASS/FAIL.
- If the model proposes `persist_sensitive`, `modify_core`, more than
  one allowed domain action sequence, a fabricated fact, wrong block reason
  or unsupported operation, the pilot returns DENIED with no state output.
- Output state is an in-memory preview. It must not be passed to an actual
  project writer until the caller is authenticated, its trusted evidence
  is verified, and a separate execution/verification contract is designed.
- `independently_verified=false`, `stable_ready=false` always, including
  passing tests. A future external verifier must examine independent
  evidence of real task effects; reducer parity alone does not prove
  policy correctness or execution effectiveness.
- No repeated Gemini calls, no new provider credentials or quota changes.
  PR #115's original counterfactual receipts and outputs remain untouched.

## Acceptance for this slice

1. The unit suite demonstrates allow/deny of synthetic task, review,
   feedback and capability proposals, including attempted sensitive writes.
2. Existing `resolve_activation` remains authoritative for Candidate
   adoption, branch pins, expiry, version and Stable status.
3. Model-claimed state never authorizes actions nor overwrites computed state.
4. An authorized preview matches frozen PR98 `simulate_actions` for its
   selected synthetic actions. All data comparisons are strictly typed.
5. Nothing is executed or written; no admission to Stable.
6. CI and an exact-head Codex review must pass before considering local
   evaluation or any downstream connection.

## Deliberate gaps — subsequent P1 tasks

The caller-supplied `trusted_context` is presently an *interface contract*,
not a cryptographically authenticated provider. Review trigger policy and
feedback authority are not recomputed here, to avoid inventing a second
parallel learning policy engine. Before production adoption, integrate their
existing deterministic functions, pin evidence to task IDs, and enforce a
separate read-only runtime verifier with exposure/outcome measurements.

Do not connect this demo to GitHub Issue routing, Google Sheets writers,
project mutation tools or real execution tasks during this experiment.

## Separate read-only reference verification stage

`evals.analysis.core13_pilot_reference_verifier.verify_preview()` is a
**separate module** that compares a successfully authorized preview against a
caller-supplied independent reducer. For trustworthy audits, supply the
immutable PR98 simulation reducer from
`evals.analysis.core13_local_counterfactual_cli.load_frozen()` after pin
verification. This module never executes actions, edits prompts, reports
Stable readiness or turns a hypothetical replay into a model PASS.

Test-only example:

```python
from evals import runner
from evals.analysis.core13_pilot_reference_verifier import verify_preview
check = verify_preview(proposal, initial_state, preview,
                       independent_reducer=runner.simulate_actions)
assert check["status"] == "REFERENCE_STATE_PARITY_PASS"
assert check["real_execution_verified"] is False
```

**Scope:** independent reducer parity of *state transition mechanics* only.
It is not an independent policy/authorization reviewer, model evaluator,
end-to-end execution verifier, or transfer-learning proof. A production
verifier must use authenticated original evidence, independently enforced
permission checks, actual effects and an attested identity.
