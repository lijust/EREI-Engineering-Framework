# Core13 J5-02 — Candidate/Verifier placement and fixed process topology

**2026-11-02 · Draft source-only on Framework J5-01 Draft #127 · App J5 tracked in lijust/EREI-3.2#235**

## Scope and exact security boundary

Implements a **fail-closed topology preflight**, not a hostile-code sandbox and not an independent verifier. All inputs are local, supplied by the operator/test harness, with no provider or model invocation. J5-02 directly imports J5-01 `bind_pinned_source`, which imports the original J2 `validate_patch`; it does not implement a second authority engine.

- A **clean, pinned Git source checkout** is separate from both workspaces; two additional existing **disjoint** candidate/verifier directories are required.
- The candidate-facing projection has **only** `contract`, `task_id`, `base_sha`, `allowed_paths` and `max_patch_bytes`. It contains no hidden oracle bytes, expected outputs, oracle/profile digest, private keys, verifier directory or verifier capability.
- Verifier-only oracle and worker-profile fixtures must each be different, **existing regular files** inside the verifier tree, read-only by file mode, bounded in size and SHA256-equal to the previously pinned J2 task values. Symlinked files (including traversed symlink components beneath the verifier directory) are prohibited. A fixture's lexical absolute path must also be under the verifier root **before symlink resolution**, rejecting aliases placed outside the verifier tree.
- Every explicitly declared candidate host mount must resolve **inside the candidate workspace**. No candidate mount can point to the verifier workspace or pinned source checkout. The candidate workspace tree is scanned for symlinks, nonregular objects, too many entries and same-filesystem **hardlink aliases** to protected fixtures. On Windows, portable inode comparisons were insufficient, so any candidate regular file or verifier fixture with a link count other than exactly one is rejected.
- Optional fixed-process probe launches **two separate, literal reviewed Python programs** with separate `cwd` and minimal environment. Candidate probe has no verifier fixture path in argv, env or stdin. Only verifier probe receives the two private fixture paths and checks their SHA256. The two host Python process IDs must differ.
- No file or source from a candidate patch is **ever** executed. Fixtures and the output use no confidential live data. Processes are intentionally fixed source-controlled diagnostics only.

## Evidence and limits

- Topology alone does **not** prevent a malicious process sharing the same host UID from opening the verifier filesystem by an independently discovered path. File mode is not an ACL-based isolation boundary. No kernel/container sandbox or separate principals are configured in this sub-gate. Any preflight result expires when mounts or files are modified; this design is **not** race-free/TOCTOU-proof.
- The filesystem scan and file digest identify a snapshot, not a signed attestation or a guarantee against concurrent symlink/hardlink replacement. Windows junction/reparse behavior and hardlink identity must be reviewed separately before hostile-code approval. Preflight does not enforce a Docker mount namespace, network policy, CPU/PID budget or containment of grandchildren.
- Probe creation of distinct host processes is **not evidence of independent acceptance**. This is a fixed-only local demonstration, not a real patch run or verification of arbitrary user code.
- The J5-02 result keeps `worker_isolation_certified=false`, `untrusted_code_execution_authorized=false`, `trusted_verifier_channel_established=false`, `independently_verified=false`, `acceptance_authorized=false`, `BLOCK_AI_ACCEPTANCE`, `learning_effectiveness=NOT_ESTABLISHED`.

## Reproduction / acceptance evidence

```powershell
python -m unittest evals.tests.test_core13_repair_evidence_contract evals.tests.test_core13_j5_01_pinned_source_binding evals.tests.test_core13_j5_02_verifier_boundary -v
```

31 new J5-02 test cases cover actual temporary Git metadata and two real trusted fixed Python subprocesses; candidate projection redaction, nested workspace rejection, mount crossing, symlink and hardlink alias denial, changed oracle/profile contents, writable fixture, unauthorized patch, forged task pins and fake subprocess reports. **Record CI/local PASS only after the command actually runs**. Windows symlink tests may explicitly skip if the current OS account lacks symlink creation privileges and such skips must never be described as verified.

## Next required gate

J5-03 must implement *source-derived independent observations* in a fresh disposable verifier-controlled checkout with protected oracle and a genuine trusted result channel, then J5-04 separately reviews host/container threat model and grants or denies executing genuinely untrusted code. J5-02 alone does **not** permit J5-03 to run model code. Stable and Task Learning promotion remain blocked.

## Windows negative-control learning (same day)

An initial Ubuntu-only 70-test run passed, but adding a Windows CI job exposed a real cross-platform security gap: GitHub-hosted Windows did not match a hardlink alias through the original `st_dev/st_ino` check. It is not safe to treat that Ubuntu result as cross-platform verification. We now fail closed on `st_nlink != 1` for protected fixtures and all candidate regular files, retaining inode matching as defense-in-depth. New 31st regression covers an unrelated hardlink; the exact-head Windows+Ubuntu matrix must pass before reporting cross-platform J5-02. This still does not establish hostile-code isolation.
