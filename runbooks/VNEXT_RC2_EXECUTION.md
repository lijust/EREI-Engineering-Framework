# VNext RC2 Execution Runbook

**Status:** Candidate execution procedure. It does not authorize Stable promotion.

## Preconditions

RC1 remains immutable at `515387e1a1d3e07744d73b9f2d38c6ed9d481d6c` and must not receive behavioral or evidence rewrites.

RC2 may be selected only after all of the following are true:

1. PR #41 (assurance-scope correction) has executable green PR CI and is merged.
2. The Copilot exact-target adapter PR has been rebased/retargeted onto the merged corrected `main`, has executable green PR CI, and is merged.
3. The resulting Framework `main` commit has push-side `Framework Assurance Gate` success and bootstrap success.
4. No unreviewed behavior/schema/eval change is added after that successful `main` revision.

A GitHub job that fails before runner allocation (`runner_id=0`, null/empty `steps`) is **not** executable green CI and does not satisfy any precondition.

## 1. Select the frozen RC2 target

Create `release/vnext-rc2` from the exact post-merge `main` revision that passed push-side assurance.

Add only `releases/VNEXT_TARGET.json`, with:

- `target_id = vnext-rc2`;
- exact Framework commit and tree;
- exact successful push-side Assurance Gate run id;
- current Stable baseline identity;
- `promotion_authorized = false`.

Run:

```bash
python tools/release_target.py --repo-root . --validate-closure
```

The release branch must pass its normal assurance/closure CI before external runtime execution.

## 2. Execute independent behavioral evidence

Configure the dedicated personal-repository Copilot PAT as `EREI_COPILOT_EXACT_TARGET_TOKEN` through the repository secret-management UI. Do not place the PAT in the repository, workflow inputs, command line, issue, PR, or evidence files. The exact-target adapter itself is PAT-only and must not fall back to the workflow `GITHUB_TOKEN`.

Before dispatch, choose one exact published `@github/copilot` npm version and independently record its npm `dist.integrity` value. The pair is part of the runtime identity; do not use `latest`, a mutable tag, a version range, an unbound package version, or a truncated SRI value.

Dispatch `VNext Exact Target Copilot Evidence` with:

- `release_ref = release/vnext-rc2`;
- `expected_carrier_sha =` exact current release-branch HEAD;
- `copilot_cli_version =` one exact npm version;
- `copilot_cli_integrity =` one full SHA-512 npm SRI for that same version.

### 2.1 Verify package bytes before installation

Before installation the workflow must:

1. query `npm view @github/copilot@<version> dist.integrity` and require an exact match with the supplied SRI;
2. download the exact package tarball with `npm pack`;
3. compute SHA-512 from the downloaded tarball bytes and require that SRI to equal the supplied SRI;
4. install only that verified local tarball.

A mismatch at either metadata or downloaded-byte verification stops execution before any model call. Direct registry installation after metadata-only verification is not permitted for governed evidence production.

### 2.2 Verify skill-event telemetry transport before behavioral execution

After the exact CLI version is installed and verified, but **before** any of the 43 behavioral cases are executed, the workflow must run the adapter telemetry probe:

```bash
python evals/adapters/copilot_cli_exact_target.py \
  --target-root . \
  --model=gpt-5.4 \
  --timeout=120 \
  --probe-skill-event skills/impact-analysis
```

The probe:

- runs against the exact frozen target and installed CLI/model path intended for the behavioral evidence run;
- stages exactly one routing skill;
- does not name `impact-analysis` in the probe prompt;
- requires the available project skill to be invoked exactly once;
- accepts only an authoritative observed `skill.invoked` name/path that resolves to the staged skill;
- fails closed if generic `skill` tool activity is visible without an authoritative named skill event;
- fails closed on an out-of-bound skill name/path, conflicting observed request/start correlation, explicitly failed correlated completion, duplicate invocation telemetry, or missing exact trace;
- succeeds only when the normalized trace is exactly `[{"type":"tool","name":"impact-analysis"}]`.

If this probe fails, **do not run the 43 behavioral cases and do not produce an exact-target evidence package**. Changing the CLI version, model, adapter, or telemetry path after the probe invalidates the probe; rerun it on the exact path that will produce evidence.

A successful probe must be retained in the exact runtime provenance as:

```text
copilot-skill-event-transport:skill.invoked-v1
```

The package-identity builder, importer, and Stable/readiness binder require this marker. It is not an optional note.

### 2.3 Execute the behavioral set

Only after the package-byte checks and skill-event telemetry probe pass may the workflow:

- validate the exact release carrier and `VNEXT_TARGET` closure;
- use only exact-commit-pinned GitHub Actions;
- check out the exact frozen target/tree separately;
- execute only the 43 `behavioral_runtime` cases;
- send no `harness_only` case to the model;
- keep real suite ids, case ids, tags, and scorer expectations outside the model boundary;
- use observed runtime routing events only; synthetic trace is forbidden;
- record the Copilot package SRI and `copilot-skill-event-transport:skill.invoked-v1` in runtime identity evidence;
- produce a reconstructible V2 run manifest;
- produce V2 execution evidence;
- build digest-bound V2 `runtime-identity.json` whose governed destination is derived from the run-manifest path;
- validate Framework/adapter/runtime/provenance parity at package-identity build time;
- upload the three-file evidence package only;
- perform no repository write, commit, push, approval, or promotion.

The package-identity builder must fail before upload if the run manifest omits the skill-event marker or its Framework/adapter/runtime provenance differs from the package identity.

The workflow itself is not Stable evidence unless it completes successfully with an allocated runner and an uploaded artifact.

## 3. Governed evidence import

Download the exact Actions artifact from the successful run.

The release branch working tree must still be at the exact `release_carrier_ref` recorded in the package identity. If the carrier moved, do not import the package; rerun the external evidence against the new exact carrier.

Validate without writing:

```bash
python tools/import_exact_target_evidence.py \
  --repo-root . \
  --package-dir <downloaded-package> \
  --validate-only
```

Validation must prove:

- SHA-256 integrity of the run manifest and execution-evidence files against the retained identity;
- exact repository/run/attempt/carrier/model provenance;
- exact requested Copilot CLI version and full SHA-512 package-integrity provenance;
- exact `copilot-skill-event-transport:skill.invoked-v1` runtime-provenance marker;
- exact frozen target id/ref/tree;
- vendored adapter revision equals the frozen target;
- exact 43-case behavioral set with no extras;
- every case is `exact_target_runtime`, independent, and PASS;
- every evidence ref points to the package run-manifest destination;
- the runtime-identity destination is exactly `<run-manifest stem>.identity.json`;
- every retained response digest is valid;
- every PASS can be deterministically reproduced from the published case and authoritative scorer;
- all three destination files are new and closure-allowed.

Only then import:

```bash
python tools/import_exact_target_evidence.py \
  --repo-root . \
  --package-dir <downloaded-package>
```

The importer reserves all three destinations exclusively, writes/fsyncs the validated bytes, and rolls back the whole three-file set on handled partial-write failure. It never commits or pushes. If the import process is interrupted externally, do not commit partial local state; remove the partial uncommitted files, return to the unchanged release carrier, and rerun validation from the original package.

The retained files are:

1. `evals/exact-target-runs/<run>.json` — reconstructible normalized runtime responses;
2. `evals/EXECUTION_EVIDENCE.<run>.json` — case-level assurance rows;
3. `evals/exact-target-runs/<run>.identity.json` — durable repository/run/carrier/model/CLI/SRI provenance plus hashes of the first two files.

## 4. Commit evidence without changing the target

Commit only the three imported evidence paths as one evidence-only closure commit directly on the release branch. This commit is part of the evidence identity, not an administrative detail.

The evidence commit must satisfy all of the following:

- it is a single-parent commit;
- its only three file changes are `A` additions of the retained run manifest, execution-evidence file, and runtime identity;
- its parent is exactly the `release_carrier_ref` recorded by the runtime identity;
- it appears on the release HEAD first-parent history, not on a side branch merged later;
- all three retained blobs remain byte-identical to their first evidence commit for the lifetime of the RC.

Do not modify in that evidence commit:

- `VNEXT_TARGET.json`;
- Framework behavior/tooling/schema/eval cases;
- approval records;
- enforcement state;
- Stable identity;
- notes or any unrelated fourth file.

Split evidence commits, merge-based evidence ingestion, manual side-branch copying, or any later rewrite of any retained evidence file fail the durable history binding and invalidate the RC. Restart from a new RC instead of rewriting evidence.

The release branch must pass the frozen release-closure gate after the evidence commit.

## 5. Recompute Stable readiness

Run:

```bash
python tools/stable_readiness.py --repo-root .
```

Stable/readiness validation must re-open the retained `.identity.json`, re-hash the run manifest and execution-evidence file, confirm the exact execution row comes from that digest-bound evidence file, verify the full runtime provenance including the skill-event transport marker, verify evidence-commit history, and then re-run the published scorers.

For a real Git checkout, the exact-target binder fails unless the three retained files were introduced by the one evidence-only first-parent commit directly above the recorded release carrier. Temporary non-Git staging used by the importer can validate content before commit, but it does not satisfy the later Stable history gate by itself.

Expected after valid 43/43 imported evidence:

- prospective cycle: PASS (6/6);
- exact-target runtime: PASS;
- release enforcement: still PASS or BLOCKED according to the machine-readable enforcement record;
- final Architecture/Security approvals: DEFERRED until all pre-approval gates pass.

Do not write final approvals while enforcement remains unsatisfied.

## 6. Enforcement and final approvals

V2 Stable requires either:

- actual server-side branch/status-check enforcement; or
- an independently verified equivalent enforcement mechanism recorded by the Framework.

Process documentation alone is not equivalent enforcement.

Only after prospective cycle + exact-target runtime + enforcement all PASS may Architecture and Security approvals be written. Each approval must bind the exact frozen target/tree and remain immutable at its first-write commit.

## 7. Stable publication and project adoption

Only after all readiness gates PASS:

1. write the Assurance Contract V2 Stable manifest;
2. validate it with `release_assurance.py` and `stable_release_carrier.py`;
3. merge/publish through the controlled release path;
4. verify the immutable Stable carrier;
5. then and only then plan the EREI-App-Google Framework pin upgrade using the verified Git-object upgrade planner.

Never move the App pin to Framework `main`, an RC branch, or a Candidate commit merely because the code is newer.
