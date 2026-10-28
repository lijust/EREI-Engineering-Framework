# Core13 P1-B — per-task learning-reuse marker reconciliation (source-only)

**Status: offline, read-only Candidate pilot. No real runtime execution or independently authenticated exposure.**

This slice extends the PR #119 source-ledger cohort membership gate by reconciling
**every** eligible occurrence with an explicit structured task trace supplied by
a caller. It does **not** infer that the intervention actually ran; it is an
intermediate audit of claimed runtime markers, not genuine exposure measurement.

## Contract

`tools.learning_exposure_traces.reconcile_learning_trace_claims(
project_root, intervention_v1, selector_v1, trace_bundle_v1)`

Example **synthetic** bundle with one task:

```json
{
  "schema_version": 1,
  "intervention_id": "fixture-intervention",
  "epoch_id": "EPOCH-001",
  "ledger_generation_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "traces": [
    {
      "occurrence_id": "EOCC-20261027T140000Z-12345678",
      "task_fingerprint": "exact fingerprint from original Task Learning event",
      "framework_ref": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "trace_ref": "cccccccccccccccccccccccccccccccccccccccc",
      "capture_complete": true,
      "steps": [
        {
          "op": "learning_reuse",
          "intervention_id": "fixture-intervention",
          "implementation_ref": "dddddddddddddddddddddddddddddddddddddddd"
        }
      ]
    }
  ]
}
```

The sample ledger generation and fingerprints are placeholders, not real evidence.

Only two step forms are accepted: `{"op":"other_operation"}` and
`{"op":"learning_reuse", "intervention_id":..., "implementation_ref":...}`.
A reported reuse marker must reference the exact existing intervention and
implementation ref. Receipt occurrence ID, fingerprint and framework revision
must match an existing validated Task Learning event. There must be
**exactly one receipt per eligible task**, without extra, missing or repeated
occurrences. The underlying PR #119 gate first checks the full task
denominator, including failed and blocked tasks.

The existing Intervention V1 `exposed` declaration must equal the result of
**parsing the trace claims**:

| Reported trace content | Required existing `exposed` value | Interpretation |
| --- | --- | --- |
| matching `learning_reuse` marker | `true` | matching reuse **claimed** by trace |
| no matching marker, `capture_complete=true` | `false` | complete capture **claimed**, no marker |
| no marker, `capture_complete=false` | `null` | unknown, never counted as not exposed |

`recurred` remains independent, unverified V1 input. **No reviewer may infer
same-root-cause recurrence from successful/failed task outcome.**

The result includes descriptive Task Learning outcomes separately for the
three prospective trace groups, preserving assessment coverage. Their rates
must not be interpreted as causal effects: exposure groups can differ in
risk, task type and verification, and their evidence is not authenticated.

## Evidence boundaries

- The `ledger_generation_sha256` binds to an existing local stable snapshot;
  rechecked after joining. No files are written.
- `trace_ref` is a syntactically valid declared commit SHA, **not** resolved
  against GitHub, a signed attestation or a verified Git ancestry proof.
- The trace bundle's canonical SHA-256 provides local reproducibility, **not**
  provenance or tamper resistance.
- `capture_complete` is supplied by the caller and remains unauthenticated;
  therefore even `exposed=false` cannot be advertised as verified absence.
- A valid `learning_reuse` marker is a structured **claim**, not proof that a
  deployed program loaded or used an approved knowledge artifact.
- `trace_identity_attested=false`,
  `trace_capture_authenticated=false`,
  `learning_exposure_independently_verified=false`,
  `effectiveness=NOT_ESTABLISHED` and
  `causation=NOT_ESTABLISHED` remain unchanged on successful joining.

## Testing and dependency

```text
python -m unittest evals.tests.test_learning_exposure_traces -v
```

Tests must cover positive, negative, unknown capture; missing failed
occurrences; forged fingerprint/ref and marker; duplicate receipts; unsupported
step; malformed booleans; stale generation; unchanged files.

Stacked draft dependency: **PR #120 → PR #119 → #118 → #117 → #116 → #115**.
No Frozen PR98 scorer, V4/V5 provider output or existing intervention V1
schema changes.

## Next step to real effectiveness

Instrument one project-approved runtime to create immutable
task-specific evidence, and **independently authenticate** its identity,
exact deployed commit, trace completeness and reused knowledge ref. Require
prospectively committed eligibility/observation windows, root-cause adjudication
and control/holdout. Only after those gates can system-level improvement be
measured without relying on the AI's own declarations. Keep Stable blocked.
