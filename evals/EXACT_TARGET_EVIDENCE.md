# Exact-target runtime evidence

`reference_contract` execution proves the eval definitions and scorer logic. It is not evidence that a real coding-agent/model runtime follows the Framework.

For Assurance Contract V2 Stable, `exact_target_runtime` evidence must be produced by `evals/exact_target_run.py` against an independent adapter implementation. The runner deliberately rejects the Framework reference oracle and mock fixtures as exact-target adapters.

Each run writes two artifacts:

1. a run manifest under `evals/exact-target-runs/` containing the exact Framework revision, adapter identity/revision, runtime identity evidence, a digest of the adapter command, and a response digest for every case;
2. V2 execution evidence whose `evidence_ref` points back to the exact run manifest and case.

The Stable release validator resolves every exact-target `evidence_ref` and fails closed if the run manifest, Framework revision, adapter identity/revision, case identity, or status do not agree.

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

A generated manifest does not authorize Stable promotion by itself. All 44 published cases must pass at `exact_target_runtime`, the prospective cycle must be complete, enforcement must satisfy the Stable gate, and architecture/security approvals must bind the final immutable release candidate.
