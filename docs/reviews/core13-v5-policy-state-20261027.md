# Core13 V5 — 27 Oct 2026: diagnose policy routing and state replay

## Actual V4 owner-local structural evidence (already evaluated, no new provider requests)

| Private issue | Case | Model-reported decision / operation | Frozen scorer category |
| --- | --- | --- | --- |
| #7 | TLR-007 | `block_capability` / `block_capability(reason=mutable_pin)` | `state_mismatch` |
| #8 | CCA-006 | `block_capability` / `block_capability(reason=expired_or_mismatched)` | `wrong_block_reason` |
| #9 | TLR-001 | `capture_task` / `record_task` (all required keys present) | `state_mismatch` |
| #15 | CCA-003 | `block_capability` / `block_capability(reason=pin_upgrade_without_adoption)` | `state_mismatch` |

The user's local redacted report is the evidence. It contains neither
raw provider values nor scorer-private expectations. In particular,
**state_mismatch** does NOT by itself prove whether the underlying
operation's factual values, the emitted claimed state, or both are wrong.

V4 frozen Core13 experiment produced **9/13 scored PASS**, **4 scored FAIL**
with case-level regressions. Original baseline was also 9/13 PASS.
There is no demonstrated overall gain and no independent acceptance.

## Intervention: model's POLICY reasoning, not additional hardcoded case answers

V4 `anyOf` action schema solved the missing required `status` field;
it cannot force the *right operation*, correct blocked reason or faithful
post-operation state. V5 keeps the **exact same V4 JSON Schema** and
generation settings and appends one static, case-blind checklist:

- Route to the Framework workflow supported by the supplied state/facts,
  instead of treating all operations as interchangeable.
- Do not confuse evidence-feedback/candidate nomination with authorized
  Core mutation.
- Check immutable reference and adoption/approval/identity/expiry
  preconditions independently, using only the supplied artifact.
- Copy every observed action parameter, nested signal and its type from
  facts, never invent zero values or occurrence IDs.
- Deep-copy the initial state and replay operation effects **in order**;
  preserve unrelated entries and use the public reason-to-state mapping.
- Check resulting state against model-proposed actions before output.

These are general transferable process controls derived from the
**already model-visible** `SIMULATION_INSTRUCTIONS` and public Framework
artifacts, not leakage of benchmark expected outputs. No case ID, expected
decision, fingerprint, secret scorer value, threshold or correct
case-specific blocking reason appears in V5's model-facing coaching.

V5 is a fixed prompt-engineering experiment, **NOT** continuous learning,
online self-modification, weight updates, or an independently admitted
Framework improvement.

## Controlled next steps

1. V5 offline test and Codex review. Do not edit frozen PR98 or older receipts.
2. New opt-in locally SHA-pinned V5 bridge route, preserving V2/V3/V4 and
   450/day shared local budget. No real calls in GitHub Actions.
3. Owner-authorized one-shot V5 four-failure comparison; classify each
   status as scored PASS, scored FAIL, INVALID, or NOT SCORED.
4. Whole thirteen-case V5 rerun; detect regressions before promoting.
5. Unseen policy/state stress cases with independent assessment. No
   Stable/independent acceptance until separate evidence.

For more precise V4 root cause, the owner can run a *read-only local*
property-level comparison of the claimed state to the official reducer,
without exporting values or private scorer expectations. This does not
change the hypothesis or require an API call.
