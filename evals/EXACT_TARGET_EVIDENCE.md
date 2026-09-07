# Exact-target runtime evidence

`reference_contract` execution proves the eval definitions and scorer logic. It is not evidence that a real coding-agent/model runtime follows the Framework.

For Assurance Contract V2 Stable, `exact_target_runtime` evidence must be produced by `evals/exact_target_run.py` against an independent adapter implementation. The runner deliberately rejects the Framework reference oracle and mock fixtures as exact-target adapters.

## Assurance scope

Every published eval suite declares one of two scopes:

- `behavioral_runtime` — the case expresses observable Framework behavior that an independent runtime can evaluate without seeing scorer expectations. These cases are required at `managed_runtime` and `exact_target_runtime` levels.
- `harness_only` — the case validates the evaluation harness itself. It remains mandatory in validation/reference-contract CI, but it is not sent to an external behavioral runtime and is not counted as exact-target Stable evidence.

The current published suite contains **44 total reference-contract cases**: **43 behavioral-runtime cases** plus **1 harness-only case** (`harness-smoke/SMOKE-001`). This separation prevents a harness self-test from requiring an external adapter to infer hidden scorer expectations that are not supported by the referenced artifact.

## Reconstructible run evidence

Each exact-target run writes two target artifacts:

1. a **V2 run manifest** under `evals/exact-target-runs/` containing the exact Framework revision, adapter identity/revision, runtime identity evidence, a digest of the adapter command, and for every behavioral-runtime case:
   - retained normalized adapter response;
   - SHA-256 digest of that response;
   - recorded PASS/FAIL status;
   - explicit `adapter_error` state;
2. V2 execution evidence whose `evidence_ref` points back to the exact run manifest and case.

The controlled Copilot workflow packages those two files with a third **V2 runtime-identity record**. The package identity binds:

- source repository;
- frozen target id/ref/tree;
- exact release-carrier ref used to run the evidence;
- adapter/runtime/model identities;
- exact GitHub Actions run id and attempt;
- requested exact CLI version;
- requested npm `dist.integrity` sha512 SRI for that CLI package;
- original governed destination paths;
- run id;
- SHA-256 digests of both evidence files.

Before installation, the controlled workflow compares `npm view @github/copilot@<version> dist.integrity` with the supplied exact SRI. A mismatch stops the run before any model call. The same SRI is retained in run-manifest runtime identity evidence and package identity, and the importer requires them to agree exactly.

All external GitHub Actions in the controlled runtime workflow are pinned to exact commit SHAs rather than mutable major-version refs.

Digest-only run manifests are not sufficient for V2 Stable because a later reviewer cannot reconstruct the scorer result from a digest alone.

The Stable/readiness validators resolve every exact-target `evidence_ref`, load the corresponding published behavioral case, revalidate the retained adapter response using the same authoritative eval runner, rerun every published scorer, and compare the recomputed status with both the run manifest and execution-evidence row. They fail closed if the retained response digest, Framework revision, adapter identity/revision, case identity, scorer result, status, or required behavioral case set do not agree.

Supplying a `harness_only` row as exact-target evidence is invalid and does not satisfy the gate.

The adapter command itself is never retained; only its SHA-256 digest is stored. Credentials must remain in the target runtime's normal secret/configuration boundary and must not be embedded in the adapter command.

## Governed import into the release closure

The downloaded Actions artifact must **not** be copied manually into a release branch.

At the exact release-carrier commit that was used to execute the runtime evidence, validate first:

```bash
python tools/import_exact_target_evidence.py \
  --repo-root . \
  --package-dir <downloaded-evidence-package> \
  --validate-only
```

The importer verifies the frozen `VNEXT_TARGET`, current carrier HEAD, package hashes, repository/run/attempt/carrier/model provenance, exact CLI version/package-integrity provenance, complete behavioral case set, exact assurance level, immutable destinations, retained response digests, and deterministic rescoring for every case using a temporary staging root. No release file is written during validation.

Only after validation succeeds may the same tool write the two governed evidence files:

```bash
python tools/import_exact_target_evidence.py \
  --repo-root . \
  --package-dir <downloaded-evidence-package>
```

The importer reserves both destination paths exclusively before writing, writes/fsyncs the validated bytes, and rolls back both newly created files on handled partial-write failure. It does not commit, push, modify `VNEXT_TARGET`, write approvals, alter enforcement state, or authorize promotion. Existing destination files are never overwritten. The subsequent evidence commit must still pass the release-closure CI; the closure validator rejects later rewrites of the evidence files.

## Producer shape

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

A generated or imported manifest does not authorize Stable promotion by itself. All 43 published `behavioral_runtime` cases must pass at `exact_target_runtime`; all 44 cases must continue to pass at reference-contract level; the prospective cycle must be complete; enforcement must satisfy the Stable gate; and architecture/security approvals must bind the final immutable release candidate.
