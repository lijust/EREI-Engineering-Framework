# Core13 F5B1J — distinct OS principal, kernel-gated observer and custody contract

**6 November 2026 | companion to App F5B1J, stacked on Framework F5B1I #170.**

The previous F5B1I [Actions #42209572291](https://github.com/lijust/EREI-3.2/actions/runs/42209572291) validated a same-UID child and fake-Docker read-only contradictions (218 PASS). It did not establish security independence. App [Issue #302](https://github.com/lijust/EREI-3.2/issues/302) requires the first genuinely separated OS principal and protected receipt-custody proof.

## Narrow acceptance (kernel only, synthetic mock)

- **Manual owner-only** workflow with exact reviewed Git source blob and real Linux root, and with `python3 -I -S` stdlib-only source to avoid importing repository modules before root source gate. PR/push tests remain nonprivileged.
- Real kernel UID/GID separation: nonroot controller `runner`, verifier `nobody`, root-only proxy/evidence owner; dropped supplemental groups, zero effective capabilities and no inherited root/broker socket descriptors in children.
- Root-owned `0710` key vault group-scoped to verifier (key `0440`); root-owned `0600` evidence journal inaccessible to controller. Root-owned `0660` UNIX SOCK_SEQPACKET proxy checks **exact PID+UID+GID** using kernel `SO_PEERCRED`; rejects mutation request and only returns two synthetic fixed GET snapshots.
- A 32-byte secret, never printed or returned, authenticates an exact-schema nonce-bound `UNRESOLVED` observation with HMAC-SHA256; root verifies and fsyncs only a disposable local receipt. Stale nonce, forged MAC, changed CID/body or different principal cannot pass. Controller cannot read key/receipt or connect proxy.

## What this is NOT

A successful real kernel/manual test would establish **protected verifier principal against controller**, and a local root-owned verified HMAC receipt from a simulated read-only proxy. It cannot establish verifier independence *against root*, because root provisions and can read HMAC key; nor does it prove independent authenticated Docker terminal receipts, immutable crash-durable append-only evidence, true Docker kernel peer identity, no asynchronous late CREATE, globally exclusive Docker transport, J4/J4S migration, or L3. The two snapshots are intentionally `[]` then a present fixed CID to demonstrate why an empty snapshot can be misleading.

Actual Docker read-only proxy tests, durable cross-crash journal, distinct independent custody external to root, and causal quiescence must be staged separately. Never create a terminal F5 `SETTLED` row or rotate an unresolved generation from this evidence. No model/candidate execution.

```text
F5B1J_OS_PRINCIPAL_REAL_ROOT_TEST=NOT_EXECUTED
F5B1J_HMAC_ROOT_LOCAL_CUSTODY=NOT_EXECUTED
F5B1J_NONROOT_TESTS=CI_PENDING
INDEPENDENT_TERMINAL_SETTLEMENT=NOT_IMPLEMENTED
LATE_CREATE_QUIESCENCE=NOT_ESTABLISHED
EXTERNAL_L3=NOT_ESTABLISHED
stable_ready=false
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
```

## Verified nonprivileged CI — 6 November 2026

[App F5B1J Actions #42293589700](https://github.com/lijust/EREI-3.2/actions/runs/42293589700) completed **SUCCESS**. Decoded logs show **24 F5B1J + 21 F5B1I + 18 F5B1H + 22 F5B1G + 18 F5B1F + 15 F5B1E + 12 F5B1D + 15 F5B1C + 10 F5B1B + 42 F5 + 28 F5A + 17 F5B0 = 242/242 PASS / 0 FAIL**.

The first CI run [#42293513068](https://github.com/lijust/EREI-3.2/actions/runs/42293513068) failed exclusively in a **negative test race**: the kernel-denied SOCK_SEQPACKET peer closed before the test client could send, resulting in an expected `BrokenPipeError`. The test was corrected to accept either an early `EPIPE/ECONNRESET` or a completed send, while still requiring the server's kernel-peer rejection. The production module and its source Git blob were **not changed for this correction**. The second full run [#42293589700](https://github.com/lijust/EREI-3.2/actions/runs/42293589700) passed all 242 cases.

The privileged owner-only job was **SKIPPED** during automatic PR/push CI. The real root offline distinct UID/GID and HMAC custody proof is therefore **NOT_EXECUTED**. No real Docker daemon, CREATE, DELETE, START, or AI/model invocation occurred. F5B1J is currently **NONROOT_SOURCE_AND_NEGATIVE_REGRESSIONS_PASS**, not a root-kernel-principal acceptance.

F5B1J_NONROOT_REGRESSIONS=242_PASS
F5B1J_OWNER_REAL_ROOT_OFFLINE=NOT_EXECUTED
INDEPENDENT_TERMINAL_SETTLEMENT=NOT_IMPLEMENTED
ROOT_INDEPENDENT_VERIFIER_CUSTODY=NOT_ESTABLISHED
LATE_CREATE_QUIESCENCE=NOT_ESTABLISHED
INDEPENDENT_L3=NOT_ESTABLISHED
stable_ready=false
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
