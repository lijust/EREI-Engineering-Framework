# Exact-target runtime evidence

`reference_contract` execution proves the eval definitions and scorer logic. It is not evidence that a real coding-agent/model runtime follows the Framework.

For Assurance Contract V2 Stable, `exact_target_runtime` evidence must be produced by `evals/exact_target_run.py` against an independent adapter implementation. The runner deliberately rejects the Framework reference oracle and mock fixtures as exact-target adapters.

## Assurance scope

Every published eval suite declares one of two scopes:

- `behavioral_runtime` — the case expresses observable Framework behavior that an independent runtime can evaluate without seeing scorer expectations. These cases are required at `managed_runtime` and `exact_target_runtime` levels.
- `harness_only` — the case validates the evaluation harness itself. It remains mandatory in validation/reference-contract CI, but it is not sent to an external behavioral runtime and is not counted as exact-target Stable evidence.

The current published suite contains **44 total reference-contract cases**: **43 behavioral-runtime cases** plus **1 harness-only case** (`harness-smoke/SMOKE-001`). This separation prevents a harness self-test from requiring an external adapter to infer hidden scorer expectations that are not supported by the referenced artifact.

Each exact-target run writes two artifacts:

1. a run manifest under `evals/exact-target-runs/` containing the exact Framework revision, adapter identity/revision, runtime identity evidence, a digest of the adapter command, and a response digest for every behavioral-runtime case;
2. V2 execution evidence whose `evidence_ref` points back to the exact run manifest and case.

The Stable release validator resolves every exact-target `evidence_ref` and fails closed if the run manifest, Framework revision, adapter identity/revision, case identity, status, or required behavioral case set do not agree. Supplying a `harness_only` row as exact-target evidence is unexpected evidence and does not satisfy the gate.

The command itself is never retained; only its SHA-256 digest is stored, so credentials must remain in the target runtime's normal secret/configuration boundary and must not be embedded in the adapter command.

Example shape:

```bash
python evals/exact_target_run.py evals/cases \
  --adapter "<external adapter command>" \
  --adapter-id "<adapter id>" \
  --adapter-revision "<40-char adapter commit>" \
  --runtime-id "<runtime id>" \
  --runtime-version "<runtime version>" \
  --runtime-evidence "<durable runtime identity evidence>" \
  --framework-ref "$(git rev-parse HEAD)" \
  --manifest "evals/exact-target-runs/<new-run>.json" \
  --evidence "evals/EXECUTION_EVIDENCE.<new-run>.json"
```

A generated manifest does not authorize Stable promotion by itself. All 43 published `behavioral_runtime` cases must pass at `exact_target_runtime`; all 44 cases must continue to pass at reference-contract level; the prospective cycle must be complete; enforcement must satisfy the Stable gate; and architecture/security approvals must bind the final immutable release candidate.
