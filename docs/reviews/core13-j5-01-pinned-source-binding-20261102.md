# Core13 J5-01 — Immutable source/pin identity preflight

**2 Nov 2026 | Source-only Draft | Prerequisite: Framework J2 Draft #126 | App J5 issue: lijust/EREI-3.2#235**

This is one narrowly scoped J5-01 sub-gate. It **does not** create an independent verifier, execute a model-generated patch, apply a diff, seal or run a hidden oracle, authenticate a result source, or authorize a worker. Existing Framework J2 `repair_evidence_contract` remains the only schema/patch/claimed-result validator; this module **imports**, never duplicates, J2.

## Inputs and authority

1. `task` and `proposal`: exact J2 contracts. Patch bytes are hashed by **J2**; changed paths must be within the J2 task allowlist.
2. `trusted_pins`: externally supplied and **operator/verifier-controlled** `task_sha256` (SHA256 canonical task JSON), `base_sha`, `oracle_sha256` and `worker_profile_sha256`. These values must not originate from the patch proposer. In J5-01 there is **no proof of origin** for the pins—J5-02/J5-03 must establish that boundary before adoption.
3. `root`: an exact, clean Git working tree with HEAD equal to the pinned baseline commit, no tracked modifications or non-ignored untracked files. Source reads use pinned **Git blobs**, not the model workspace or mutable filesystem.
4. Every allowlisted source path must resolve to exactly one existing, regular, non-executable Git blob (`100644`), not a symlink (`120000`), submodule (`160000`) or executable (`100755`). Emit Git blob ID + observed raw SHA256; do not follow Git symlinks. Only existing files and the conservative J2 path allowlist are supported.
5. A caller may offer `reported_result`, but J2 binds it as **unattested**, and even a fabricated `pass` never grants acceptance. A forged independently verified provenance fails closed.

## Known constraints

- Only SHA-1 Git object repositories (40-hex commit/object ids) are currently supported, matching J2. SHA-256-object repositories are an explicit future compatibility task, **not** silently accepted.
- The source check reads original committed Git blobs and checks current tree cleanliness. It does **not** run `git apply --check`, validate actual patch hunk semantics, verify the post-patch mode/tree or isolate candidate/verifier runtime. Those require a disposable workspace and J5-02 security architecture.
- Read-only Git CLI is a host process; source trust and local Git configuration need independent review before hostile repositories can be handled. This is not a hostile-code sandbox.
- The static task/oracle/profile digests identify provided bytes but provide **no cryptographic attestation** or oracle secrecy. Do not embed hidden oracle content or its answers in candidate input.
- All outputs explicitly preserve `BLOCK_AI_ACCEPTANCE`, `worker_isolation_certified=false`, `untrusted_code_execution_authorized=false`, `independently_verified=false`, `learning_effectiveness=NOT_ESTABLISHED`, `stable_promotable=false`.

## Reproducible tests

```powershell
python -m unittest evals.tests.test_core13_repair_evidence_contract evals.tests.test_core13_j5_01_pinned_source_binding -v
```

J5-01 tests use an actual **local temporary Git repo**, not Docker or AI, to cover correct raw Git blob identity, fake PASS non-authority, wrong task/base/oracle/worker pins, changed HEAD, dirty/untracked checkout, Git-index symlink and executable modes, forbidden test paths, patch-byte swap and fake proposer authority. **Passing these tests proves only a source-binding preflight; do not count as an independent verifier run.**

## Next

Implement J5-02 independent candidate/verifier workspace isolation and a separately protected source of trusted task pins/oracle bytes. Add real `git apply --check` on a disposable clone at pinned base, follow post-apply tree/mode constraints and adversarial worker threat review. Until then, no model-generated Python execution.
