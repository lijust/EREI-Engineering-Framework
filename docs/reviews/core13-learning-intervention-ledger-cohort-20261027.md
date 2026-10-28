# Core13 P1-B — source-bound Learning Intervention cohort accounting

**Candidate-only, offline, no operational dispatch.** This is a narrow next
slice of the preexisting Learning Intervention V1 contract in
`learning/LEARNING_INTERVENTION_CONTRACT.md`, NOT a new learning engine.
It depends on draft PR #118 → #117 → #116 → #115.

## What was implemented

`tools.learning_intervention_sources.assess_intervention_against_ledger(
project_root, intervention_v1, selection_v1)`

The original `tools.learning_effectiveness.assess_intervention()` remains
the authoritative implementation for declared intervention exposure and
recurrence accounting, and its schema, metrics, and restrictions are NOT
changed. This binding adds read-only **local source consistency** checks:

1. Validate the preexisting Intervention V1 schema and its declared tasks.
2. Read the authoritative Task Learning V2 snapshot using
   `task_learning.authoritative_snapshot` and existing event/review validation.
3. Require `cohort.ledger_sha256` to equal SHA-256 of exact bytes in the
   project `.erei/learning/TASK_EVENTS.jsonl` event projection; do not confuse
   this digest with the combined multi-file ledger-generation digest.
4. Check every locally stored event belongs to the declared project repository,
   and determine exactly which occurrences belong to the declared current
   epoch or a closed V2 review. Reject legacy V1 review cutoffs here instead of
   inferring historical membership.
5. Compute *every* eligible material task under one strict declared selector.
   Match that complete source set to the intervention's declared cohort IDs.
   Missing failures, escapes, retries, and unexpected IDs DENY the accounting
   instead of producing a deceptively improved rate.
6. Keep the existing prospective-vs-legacy designation. Never promote
   an event with schema_version 1 to prospective.
7. Report descriptive source-ledger outcomes (verified successes, failures,
   blocked tasks, assessed verification escapes and verification failures),
   without treating an unassessed signal as a zero. Cross-check a second
   ledger generation after assessment and deny if it changed.

This does **not** verify intervention exposure, recurrence of the same root
cause, adoption authenticity, version ancestry, prospective pre-registration,
or cause-and-effect. A new event's EOCC ID is not proof of prospective design.
All those flags remain false, even when source membership matches.

## Explicit selection input (synthetic example)

The existing intervention's `cohort.eligibility_rule` must equal
`all_material_workflow_risk_time_v1`. The separate selector supplied by
the project owner has exactly:

```json
{
  "schema_version": 1,
  "rule_id": "all_material_workflow_risk_time_v1",
  "selection_ref": "dddddddddddddddddddddddddddddddddddddddd",
  "workflow": "bug-fix",
  "risk": "L2",
  "material_only": true,
  "from_inclusive": "2026-10-27T14:00:00Z",
  "to_exclusive": "2026-10-27T15:00:00Z"
}
```

`risk: null` selects all risks. Windows use RFC3339 timestamps with
timezones, start-inclusive/end-exclusive. The selection ref must match the
ref declared by intervention V1, but **no Git ancestry or publication-time
authentication** is performed. The selector itself is a caller-supplied
declared scope; local set completeness is not proof that the chosen scope was
unbiased or precommitted.

## Output meaning

- `LOCAL_COHORT_MEMBERSHIP_MATCHED`: exact local source ledger digest and
  exact cohort membership for declared selector; **not** proof of
  independent source authenticity.
- `DENIED`: malformed contract, missing/extra occurrences, wrong ledger,
  wrong repository, unsupported epoch, bad selector or observed concurrent
  mutation. No success ratio is returned on denial.
- `intervention_accounting`: existing descriptive V1 exposure / recurrence
  accounting, which remains `effectiveness=NOT_ESTABLISHED` and
  `causation=NOT_ESTABLISHED`.
- `source_outcomes`: locally stored task outcomes only; no assertion that
  an exposure prevented errors or that the declared root cause recurred.
- `source_binding`: local event-projection hash, combined ledger-generation
  hash, and *declared*, **not authenticated**, Git ref metadata.

## Synthetic checks

```text
python -m unittest evals.tests.test_learning_intervention_sources -v
```

Tests cover omitted failed occurrences, mismatched digest, corrupted
selection, extra/foreign tasks, strict selection windows, valid closed V2
epoch, concurrent mutation, and absence of causal/adoption/exposure claims.

## Next required evidence before effectiveness

A project-controlled, precommitted eligibility and observation-window
declaration must be independently verified against a real commit.
Independently authenticate intervention implementation/adoption ancestry
and the complete source evidence set; link each eligible task to observed
runtime version, actual intervention exposure, and separately adjudicated
same-root-cause recurrence. Compare a prospective holdout/control cohort
under equal verification rigor before asserting benefit.

**Do not merge this as Stable, connect it to project mutation dispatch,
auto-upgrade a pin, make Gemini calls, or treat CI as proof of actual
engineering-task improvement.** The optional read-only source-binding
function has no project write or adoption side effects.
