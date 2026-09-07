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

Configure the dedicated personal-repository Copilot PAT as `EREI_COPILOT_EXACT_TARGET_TOKEN` through the repository secret-management UI. Do not place the PAT in the repository, workflow inputs, command line, issue, PR, or evidence files.

Before dispatch, choose one exact published `@github/copilot` npm version and independently record its npm `dist.integrity` value. The pair is part of the runtime identity; do not use `latest`, a mutable tag, a version range, or an unbound package version.

Dispatch `VNext Exact Target Copilot Evidence` with:

- `release_ref = release/vnext-rc2`;
- `expected_carrier_sha =` exact current release-branch HEAD;
- `copilot_cli_version =` one exact npm version;
- `copilot_cli_integrity =` exact `sha512-...` npm SRI for that same version.

Before installation the workflow must query `npm view @github/copilot@<version> dist.integrity` and require an exact match with the supplied SRI. A mismatch stops execution before any model call.

The workflow must:

- validate the exact release carrier and `VNEXT_TARGET` closure;
- use only exact-commit-pinned GitHub Actions;
- check out the exact frozen target/tree separately;
- verify the requested Copilot npm version/integrity pair before installation;
- execute only the 43 `behavioral_runtime` cases;
- send no `harness_only` case to the model;
- keep real suite ids, case ids, tags, and scorer expectations outside the model boundary;
- use observed runtime routing events only; synthetic trace is forbidden;
- record the Copilot package SRI in runtime identity evidence;
- produce a reconstructible V2 run manifest;
- produce V2 execution evidence;
- produce digest-bound V2 `runtime-identity.json`;
- upload the three-file evidence package only;
- perform no repository write, commit, push, approval, or promotion.

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

- package SHA-256 integrity;
- exact repository/run/attempt/carrier/model provenance;
- exact requested Copilot CLI version and sha512 package integrity provenance;
- exact frozen target id/ref/tree;
- vendored adapter revision equals the frozen target;
- exact 43-case behavioral set with no extras;
- every case is `exact_target_runtime`, independent, and PASS;
- every evidence ref points to the package run manifest destination;
- every retained response digest is valid;
- every PASS can be deterministically reproduced from the published case and authoritative scorer;
- both destination files are new and closure-allowed.

Only then import:

```bash
python tools/import_exact_target_evidence.py \
  --repo-root . \
  --package-dir <downloaded-package>
```

The importer reserves both evidence destinations exclusively, writes/fsyncs the validated bytes, and rolls back both new files on handled partial-write failure. It never commits or pushes. If the import process is interrupted externally, do not commit partial local state; rerun validation from the unchanged release carrier and package.

## 4. Commit evidence without changing the target

Commit only the two imported evidence paths. Do not modify:

- `VNEXT_TARGET.json`;
- Framework behavior/tooling/schema/eval cases;
- approval records;
- enforcement state;
- Stable identity.

The release branch must pass the frozen release-closure gate. Any later rewrite of an imported evidence file invalidates the RC and requires a new RC rather than an overwrite.

## 5. Recompute Stable readiness

Run:

```bash
python tools/stable_readiness.py --repo-root .
```

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
