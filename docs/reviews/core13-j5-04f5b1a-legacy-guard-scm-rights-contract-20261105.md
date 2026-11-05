# Core13 F5B1A — close local unsafe legacy rotate and exercise real FD rejection

**2026-11-05 | Draft security contract. Does not approve Docker or model code.**

Predecessors: F5B0 App #285; Framework #160; implementation tracker App #286, Framework #161.

## Required invariants and acceptance evidence

1. The original F5 `rotate()` is a publicly callable local entrypoint. It must **atomically** refuse any existing unresolved F5 intent across **all** generations inside the same `BEGIN IMMEDIATE` transaction that advances the control row. The original F5A-only guard is insufficient if unguarded F5 remains callable. Use SQLite `quick_check` + `foreign_key_check`, fail-closed on mismatch/corrupt state.
2. `PREPARED`, `EMITTED_UNKNOWN`, `RETURNED_CLAIM` are still unresolved because **no independent verified terminal settlement phase exists**. In particular, a returned CID or locally emitted marker does not authorize rotation, removal or a new generation. Never erase the record to make tests pass.
3. Preserve the earlier F5A all-generation guard as a separate regression and repin exact reviewed F5/F5A source blobs in F5B0 IPC. Label all local guards **LOCAL_SCOPED_PASS** only if GitHub actions are green; never infer production/daemon exclusivity.
4. A real test must transmit an actual Linux `SCM_RIGHTS` ancillary FD through the F5B0 Unix SOCK_SEQPACKET socket. Receiving server must reject, close any received FDs and not create a SQLite intent.
5. Expected regression scope: **F5 42 + F5A 28 + F5B0 17 = 87**. These are suite sizes, not a PASS claim until run evidence is checked. Tests must be Linux nonroot, with no Docker calls, privileged setup, candidate code or AI execution.

## F5B1B conditions not met by F5B1A

Real separate root broker and limited controller/worker principals; broker-only protected WAL with true pre-SEND; root-only dedicated Docker socket and no alternative raw caller; real immutable fixed CREATE/inspect/DELETE under manual owner-dispatched disposable runner; crash/late async CREATE recovery; independent terminal reconciliation preserving audit history; fencing against all pending across generations; migration of J4/J4S start/stream/timeout/cleanup; independent L3.

**Acceptance state:**

```text
F5B1A=LOCAL_OFFLINE_TEST_PENDING
F5B1B=NOT_IMPLEMENTED
INDEPENDENT_TERMINAL_SETTLEMENT=NOT_ESTABLISHED
EXCLUSIVE_DOCKER_TRANSPORT=NOT_ESTABLISHED
LATE_CREATE_QUIESCENCE=NOT_ESTABLISHED
IMAGE_SECURITY_ACCEPTANCE=NOT_ESTABLISHED
INDEPENDENT_L3=NOT_ESTABLISHED
STABLE_READY=false
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
```

The old F5 API may remain callable on an empty local ledger, but must never permit rotation across unresolved rows. This is **not** proof that a live Docker daemon changed epoch or that all late creates have drained.

## Observed Actions evidence — 2026-11-05

- [F5B1A nonprivileged Linux Actions #42051673810](https://github.com/lijust/EREI-3.2/actions/runs/42051673810): **SUCCESS**.
- Test steps completed successfully: **42 original F5 + 28 F5A + 17 F5B0 (including real SCM_RIGHTS) = 87 tests, 0 failed**.
- The checked step also confirmed no Docker backend present and `BLOCK_AI_ACCEPTANCE`. This is **local regression scope**, not live Docker exclusivity, daemon quiescence or independent L3.
- Ancillary pre-existing [F5B0 workflow #42051673719](https://github.com/lijust/EREI-3.2/actions/runs/42051673719) and [F5A workflow #42051673798](https://github.com/lijust/EREI-3.2/actions/runs/42051673798) also completed successfully on the same PR head.
- DO NOT advance `F5B1B` acceptance without actual broker-only Docker lifecycle, independent receipt settlement, and a tested late-create drain barrier.
