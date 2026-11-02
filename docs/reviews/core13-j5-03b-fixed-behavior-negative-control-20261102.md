# Core13 J5-03B — fixed RED/GREEN behavioral negative-control calibration

**2 Nov 2026 · Draft stacked on J5-03 #129 → J5-02 #128 → J5-01 #127 → J2 #126**

## Purpose

Demonstrate, with **real trusted Python subprocesses**, that the verifier-side oracle comparison detects an intentionally wrong behavior (RED) and distinguishes it from a reviewed correct control (GREEN). This adds a simple behavioral calibration to J5-03's *source-as-data AST witness* but is **not a model patch validation**.

The self-contained **source-controlled literal** function implements a small `price_text_normalization_trusted_fixed` test. It uses four fixed/public inputs, with a deliberate faulty reviewed `red` mode failing to remove a text suffix and a reviewed `green` mode normalizing it. A verifier-only, read-only, SHA256-pinned JSON oracle contains four expected values. Neither generated model code nor caller-controlled source is ever executed, loaded, imported, or applied. Fixed tests use only source-controlled literal snippets.

1. J2 validates task/patch/result claim syntax and identity. Caller-reported PASS never has acceptance authority.
2. J5-01 rebinds clean Git HEAD, source path, raw patch bytes. J5-02 ensures disjoint candidate/source/verifier workspaces and source/oracle/profile digests, rejects mount escape and link aliases.
3. A fresh temporary verifier-owned directory is created. Reviewed fixed code runs in **two actual subprocesses** with `-I -S`, empty stdin and minimal environment. One subprocess observes the intentionally faulty behavior, the other the fixed reference behavior. The worker receives only `red` or `green`, no private oracle path or contents.
4. The controller validates each exit code and tightly bounded JSON trace, exact expected schema and types, checks **RED mismatch >=1** and **GREEN mismatch = 0** against protected expected values, confirms distinct observed PIDs and temporary-directory removal. If RED/GREEN quality control fails, preflight fails closed.
5. The emitted sanitized record includes task/base/patch/oracle/profile identities, SHA256 of each trusted fixed process trace and number of mismatches, but **no raw expected values, source, worker profile, private file path or private bytes**. Hashes and subprocess IDs do not authenticate their own provenance.

## Limits

- **Not an independent evaluation of a candidate patch.** The actual source patch is not applied/executed; two trusted toy programs are used solely to calibrate the verifier's ability to reject a wrong output.
- **Not a sealed prospective behavioral oracle.** Fixture inputs and expected values are published within calibration tests. Real hidden prospective tests must be separately preregistered and not leaked to candidates.
- **Not a malicious-code sandbox or trusted verification channel.** Both subprocesses run as the same host user. No authenticated verifier principal, kernel MAC, signed receipt or enforcement of mount namespaces is claimed.
- Status remains `independently_verified=false`, `independent_model_patch_oracle_established=false`, `worker_isolation_certified=false`, `untrusted_code_execution_authorized=false`, `BLOCK_AI_ACCEPTANCE`, `learning_effectiveness=NOT_ESTABLISHED`.
- Fixed red/green tests are explicitly **reviewed program controls**, not evidence of AI patch efficacy. The code does not use `exec()` on any caller text or source file.

## Reproduction

```powershell
python -m unittest evals.tests.test_core13_repair_evidence_contract evals.tests.test_core13_j5_01_pinned_source_binding evals.tests.test_core13_j5_02_verifier_boundary evals.tests.test_core13_j5_03_source_observation evals.tests.test_core13_j5_03b_fixed_behavior -v
```

21 new tests include actual subprocesses, incorrect/misbound oracle, fake candidate PASS, forged independent provenance, deliberately swapped RED/GREEN known code, process nonzero exit, malformed JSON, wrong Git HEAD, patch tampering, worker profile mutation, symlinked oracle and mount escape. Record exact `Ran N tests OK` and runner OS once CI completes.

## Transition

J5-04 worker security is a separate security engineering gate. Until OS/daemon, mounts, network, lifecycle and verifier-principal constraints are reviewed and approved, do **not** run untrusted/model code even if these trusted toy controls pass.
