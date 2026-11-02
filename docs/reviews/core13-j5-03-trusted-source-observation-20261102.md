# Core13 J5-03 — independent fixed-source observation pilot

**2026-11-02 | Source-only Draft | Stacked on J5-02 #128 → J5-01 #127 → J2 #126 | App issue lijust/EREI-3.2#235**

## Narrow accepted claim

Implement a **verifier-generated** observation from an **actual, reviewed, fixed Python inspector subprocess** operating on raw, source-pinned Git blob bytes in a *fresh disposable verifier-controlled directory*. This is beyond grading a candidate-submitted JSON trace; the caller does not supply the observed source SHA, line/function/class counts or runtime exit status. The verifier controller calculates checks against a verifier-only SHA256-pinned oracle.

**This does NOT verify the candidate patch.** The candidate patch is only bound by original J2 identity, never applied or executed. The trusted inspector reads original baseline source as **data**, performs `ast.parse` (not `compile`/`import`/`exec`) and outputs bounded structural observations. An AST syntax failure currently blocks (not a reported positive outcome). No arbitrary/model-generated Python program is run. This is a calibration of source-derived evidence handling, **not functional verification of a repaired program**, not prospective independent AI acceptance.

## Reused contracts (no parallel authority)

1. J2 `validate_patch` / `bind_reported_result` (only source of truth for patch/result claim schema). A caller-reported PASS or forged provenance cannot authorize anything.
2. J5-01 pinned source: exact verified baseline HEAD, clean worktree, regular mode 100644 Git blobs; inspect `git cat-file blob` again and compare SHA256 to J5-01's source receipt.
3. J5-02 workspace: nonintersecting source/candidate/verifier roots, bounded read-only regular oracle/profile files with correct pinned SHA, no candidate mount escape, symlink or hardlink fixture aliases.
4. J5-03 fixed case `baseline_python_ast` requires exactly one pre-approved existing source path. Verifier-only JSON oracle contains `contract=erei-j5-03-trusted-source-oracle-v1`, `case=baseline_python_ast`, and the expected exact six fixed fields (`source_sha256`, `source_bytes`, `line_count`, `function_count`, `class_count`, `syntax_valid`). Oracle content and expected values never enter the candidate task projection.
5. A fresh temporary verifier folder contains a **data-only source copy**, which the fixed Python inspector reads and parses; source content is **not executed**. Controller checks actual subprocess success, strict bounded JSON schema, exact source hash/size, and verifier-controlled oracle comparisons. Temp folder must be removed before returning evidence.
6. Receipt includes pinned task/base/patch/oracle/worker identities, bounded per-check match booleans, SHA256 of the observed fixed trace, confirmed fixed-process exit code and sanitized source-only provenance `TRUSTED_FIXED_INSPECTOR_PROCESS_OBSERVED`. No raw oracle, verifier paths or expected values are returned. No model, live project or production writes.

## Explicit security and effectiveness non-claims

- **No trusted attestation channel:** a malicious same-UID process or external caller could forge a JSON receipt; no separate OS user, IPC credential, HMAC, kernel policy or signed protected log is implemented. Even an outcome `J5_03_FIXED_SOURCE_OBSERVATION_MATCH` means only this **fixed baseline AST** comparison matched.
- **No independent AI patch verification:** `independently_verified=false`, `independent_model_patch_oracle_established=false`, `model_patch_applied=false`, `candidate_code_executed=false`. Passing oracle checks must not trigger any Task Learning success or `ACCEPTED_FOR_REVIEW`.
- **No sandbox security certification:** J5-02 filesystem topology is not isolation against malicious code of the same host principal. Parsing trusted pinned source as data is not authorization to handle hostile content. `worker_isolation_certified=false` and `untrusted_code_execution_authorized=false`.
- This does **not** replace the prospective independent behavioral tests and the J5-04 code-execution security review. No J6 effectiveness or Stable promotion.

## Reproduction

```powershell
python -m unittest evals.tests.test_core13_repair_evidence_contract evals.tests.test_core13_j5_01_pinned_source_binding evals.tests.test_core13_j5_02_verifier_boundary evals.tests.test_core13_j5_03_source_observation -v
```

20 new tests use a **real local temporary Git repository** and an actual fixed Python subprocess, with wrong oracle, forged PASS, malformed/forged inspector trace, actual child nonzero exit, corrupted source/profile, changed Git HEAD, J2 patch swap and cleanup checks. All negative controls are labeled by their origin. Run on Windows and Ubuntu; record `Ran N tests / OK` per exact branch head before claiming pass.

## Next work

J5-04 must independently establish actual untrusted-code isolation and a trusted verifier principal/channel before the system may evaluate model-produced repairs. J5-05 must cover malicious child trees, mount escape, truncated logs, worker crash, oracle leakage, fake evidence and cleanup races. J5-06 preregisters truly new tasks and blinded private behavior oracles; no historical fixed calibration counts as learning effectiveness.
