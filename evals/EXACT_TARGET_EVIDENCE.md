# Exact-target runtime evidence

`reference_contract` execution proves the eval definitions and scorer logic. It is not evidence that a real coding-agent/model runtime follows the Framework.

For Assurance Contract V2 Stable, `exact_target_runtime` evidence must be produced by `evals/exact_target_run.py` against an independent adapter implementation. The runner deliberately rejects the Framework reference oracle and mock fixtures as exact-target adapters.

## Assurance scope

Every published eval suite declares one of two scopes:

- `behavioral_runtime` — the case expresses observable Framework behavior that an independent runtime can evaluate without seeing scorer expectations. These cases are required at `managed_runtime` and `exact_target_runtime` levels.
- `harness_only` — the case validates the evaluation harness itself. It remains mandatory in validation/reference-contract CI, but it is not sent to an external behavioral runtime and is not counted as exact-target Stable evidence.

The current published suite contains **44 total reference-contract cases**: **43 behavioral-runtime cases** plus **1 harness-only case** (`harness-smoke/SMOKE-001`). This separation prevents a harness self-test from requiring an external adapter to infer hidden scorer expectations that are not supported by the referenced artifact.

## Routing-trace transport assurance

Routing-sensitive exact-target evidence must not infer a skill invocation from the declared artifact or from generic tool activity alone.

For the controlled Copilot CLI adapter, `skill.invoked` is the authoritative name-bearing runtime signal. The adapter validates the observed skill name/path against the one staged routing skill before normalizing it into eval trace. When generic `skill` tool requests/starts are observed without a corresponding authoritative `skill.invoked`, the adapter fails closed rather than treating the trace as empty. Conflicting request/start IDs, an out-of-bound skill name/path, an explicitly failed correlated completion, duplicate invocation telemetry, or a skill event in direct semantic mode also fail closed.

Before the governed 43-case run starts, the workflow executes a skill-event telemetry probe against the exact installed CLI/model/adapter path. The probe stages exactly one routing skill, does not name that skill in the probe prompt, requests that the available project skill be invoked once, and requires the normalized trace to be exactly:

```json
[{"type":"tool","name":"impact-analysis"}]
```

If the chosen runtime transport does not expose a usable authoritative skill event, the workflow stops before behavioral evidence is produced.

A successful probe is retained in the run manifest's exact runtime provenance as:

```text
copilot-skill-event-transport:skill.invoked-v1
```

The package-identity builder, governed importer, and Stable/readiness binder require that marker as part of the exact runtime-evidence set. An older or manually assembled package that did not pass this governed probe is not accepted as V2 Stable evidence merely because its other hashes or runtime fields match.

## Reconstructible run evidence

Each exact-target execution initially produces two target-checkout outputs:

1. a **V2 run manifest** under `evals/exact-target-runs/` containing the exact Framework revision, adapter identity/revision, runtime identity evidence, a digest of the adapter command, and for every behavioral-runtime case:
   - retained normalized adapter response;
   - SHA-256 digest of that response;
   - recorded PASS/FAIL status;
   - explicit `adapter_error` state;
2. V2 execution evidence whose `evidence_ref` points back to the exact run manifest and case.

The controlled Copilot workflow then packages those two files with a third **V2 runtime-identity record**. The identity binds:

- source repository;
- frozen target id/ref/tree;
- exact release-carrier ref used to run the evidence;
- adapter/runtime/model identities;
- exact GitHub Actions run id and attempt;
- exact requested Copilot CLI version;
- exact full npm SHA-512 SRI for that CLI package;
- original governed destination paths for all three retained files;
- run id;
- SHA-256 digests of the run manifest and execution-evidence files.

The runtime-identity destination is derived deterministically from the run-manifest path:

```text
evals/exact-target-runs/<run>.json
→ evals/exact-target-runs/<run>.identity.json
```

Digest-only run manifests are not sufficient for V2 Stable because a later reviewer cannot reconstruct the scorer result from a digest alone. Likewise, discarding `runtime-identity.json` after import is not permitted because that would discard the structured repository/run/carrier/model/CLI/SRI provenance used to authenticate the retained evidence set.

The package-identity producer validates the run manifest before writing the identity and requires the manifest's Framework revision, adapter/runtime identity, and exact runtime-evidence set—including the skill-event transport marker—to match the package identity. Provenance drift therefore stops the producer before artifact upload.

The Stable/readiness validators resolve every exact-target `evidence_ref`, derive and load the retained `.identity.json`, re-hash both bound data files, confirm the caller execution row is present exactly in the digest-bound execution-evidence file, verify runtime provenance, load the corresponding published behavioral case, revalidate the retained adapter response using the same authoritative eval runner, rerun every published scorer, and compare the recomputed status with both the run manifest and execution-evidence row.

On a real Git checkout the same binder also validates the evidence-introduction history. The manifest, execution evidence, and runtime identity must have one shared first-add commit; that commit must be single-parent, must be on the release HEAD first-parent history, must add exactly those three files and nothing else, and its parent must equal the identity's recorded `release_carrier_ref`. Current blobs must remain identical to the blobs first introduced by that evidence commit.

Supplying a `harness_only` row as exact-target evidence is invalid and does not satisfy the gate.

The adapter command itself is never retained; only its SHA-256 digest is stored. Credentials must remain in the target runtime's normal secret/configuration boundary and must not be embedded in the adapter command.

## Controlled runtime supply chain

The exact-target workflow uses exact commit SHAs for all third-party GitHub Actions. Mutable major tags are not acceptable for Stable evidence production.

For `@github/copilot`, both an exact npm version and its exact full `dist.integrity` SHA-512 SRI are required. The workflow first verifies registry metadata for the exact requested version. It then downloads the exact package tarball with `npm pack`, computes SHA-512 from the downloaded tarball bytes, requires that byte-derived SRI to match the approved SRI, and installs only the verified local tarball. A metadata match alone is not sufficient. Direct registry installation after metadata-only verification is not permitted for governed evidence production.

The same SRI is retained in the run manifest's runtime identity evidence and in the durable runtime-identity record.

The Copilot adapter itself requires `COPILOT_GITHUB_TOKEN`; it does not fall back to the workflow `GITHUB_TOKEN`. The child process inherits only the explicit Copilot credential plus the narrow process/network/certificate allowlist.

## Governed import into the release closure

The downloaded Actions artifact must **not** be copied manually into a release branch.

At the exact release-carrier commit that was used to execute the runtime evidence, validate first:

```bash
python tools/import_exact_target_evidence.py \
  --repo-root . \
  --package-dir <downloaded-evidence-package> \
  --validate-only
```

The importer verifies the frozen `VNEXT_TARGET`, current carrier HEAD, package hashes, repository/run/attempt/carrier/model/CLI/SRI/skill-transport provenance, deterministic identity destination, complete behavioral case set, exact assurance level, immutable destinations, retained response digests, digest-bound execution rows, and deterministic rescoring for every case using a temporary staging root. No release file is written during validation.

Only after validation succeeds may the same tool write the governed evidence set:

```bash
python tools/import_exact_target_evidence.py \
  --repo-root . \
  --package-dir <downloaded-evidence-package>
```

The importer atomically reserves and writes the original three package files to the destination paths bound in the identity:

- `evals/exact-target-runs/<run>.json`;
- `evals/EXECUTION_EVIDENCE.<run>.json`;
- `evals/exact-target-runs/<run>.identity.json`.

It does not commit, push, modify `VNEXT_TARGET`, write approvals, alter enforcement state, or authorize promotion. Existing destination files are never overwritten. A handled partial-write failure rolls back the entire three-file set.

The next repository commit must add exactly those three retained files directly on the release first-parent chain. Its parent must be the recorded release carrier. Split commits, side-branch/merge ingestion, an unrelated fourth file, or any later rewrite fail durable evidence history validation. Temporary non-Git importer staging can prove content before commit, but cannot by itself satisfy the later Stable Git-history gate.

## Producer shape

For the governed Copilot path, the telemetry probe must have passed before this producer is invoked and the runtime provenance must include the probe marker:

```bash
python evals/exact_target_run.py evals/cases \
  --adapter "<external adapter command>" \
  --adapter-id "<adapter id>" \
  --adapter-revision "<40-char adapter commit>" \
  --runtime-id "<runtime id>" \
  --runtime-version "<runtime version>" \
  --runtime-evidence "<durable runtime identity evidence>" \
  --runtime-evidence "copilot-skill-event-transport:skill.invoked-v1" \
  --framework-ref "$(git rev-parse HEAD)" \
  --manifest "evals/exact-target-runs/<new-run>.json" \
  --evidence "evals/EXECUTION_EVIDENCE.<new-run>.json"
```

A generated or imported evidence set does not authorize Stable promotion by itself. All 43 published `behavioral_runtime` cases must pass at `exact_target_runtime`; all 44 cases must continue to pass at reference-contract level; the prospective cycle must be complete; enforcement must satisfy the Stable gate; and architecture/security approvals must bind the final immutable release candidate.
