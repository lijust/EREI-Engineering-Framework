# Core13 F5B1G — UNKNOWN-CREATE fault matrix, replay and independent drain contract

**6 November 2026.** Companion to App F5B1G staged on Framework F5B1F #167. [App issue #295](https://github.com/lijust/EREI-3.2/issues/295). The prior owner-manual [F5B1F #42202611269](https://github.com/lijust/EREI-3.2/actions/runs/42202611269) established only one fixed never-started CREATE/inspect/DELETE, local scoped.

## Safety assertion: an UNKNOWN row is not a transport retry permit

The existing raw F5 `submit_static_test_only` checks that a row is `EMITTED_UNKNOWN` before invoking its callback; it does not independently prove the callback was never invoked before. The new F5B1G counterexample explicitly calls it again after one injected failed callback and can observe a second invocation (with fake CID, **not** real Docker).

This is **a discovered remaining guard gap**, not an endorsement of retries and not evidence that the fixed real root Broker auto-retries. Future source-pinned broker must block any uncoordinated re-emission and require separate protected reconciliation of the named intent.

## Negative matrix

Real POSIX SQLite WAL persistence plus reviewed fixed Unix HTTP transport to a local fake Docker server must reproduce: abrupt child death after PRE-SEND commit; unreachable private socket; CREATE applied and reply lost; invalid returned CID; DELETE reply lost both before/after application; foreign ownership labels; local cleanup with unresolved claim; empty inventory then scripted delayed CREATE; and raw F5 re-emission after an uncertain response.

A PASS means a fault was *reproduced and still blocked*. Each case must read back a persisted unresolved row, reject duplicate admission, and reject legacy F5 rotation. No source/mocks may claim independent terminal settlement, daemon-generation quiescence or durable crash proof.

## Separate proof obligations

1. Introduce **send-once** authorization and immutable per-intent dispatch identity bound to the exact source, daemon epoch and fixed configuration. The raw F5 entrypoint must not be reusable as an unrestricted second SEND after unknown.
2. Design separate OS-principal protected verifier with authenticated observations, able to classify known identities and daemon epochs after crash; do not silently interpret empty inventory as terminal.
3. Prove a genuine late-CREATE barrier with adversarial delays and independent daemon control, including process tree and inherited socket FDs; scripted fake delay is only a counterexample.
4. Migrate all J4/J4S Docker paths to reviewed Broker, then independently test global socket exclusivity, retained WAL crash replay and L3.
5. Keep automatic CI **strictly nonroot**. Real Docker fault tests require separate owner-reviewed manual workflow on disposable isolated daemon and must never START model/candidate code.

```text
F5B1G_OFFLINE_NEGATIVE_FAULTS=CI_PENDING
RAW_F5_UNKNOWN_RETRY_GAP=COUNTEREXAMPLE_PROPOSED
REAL_DOCKER_FAULT_MATRIX=NOT_EXECUTED
INDEPENDENT_TERMINAL_SETTLEMENT=NOT_IMPLEMENTED
LATE_CREATE_QUIESCENCE=NOT_ESTABLISHED
GLOBAL_DOCKER_EXCLUSIVITY=NOT_ESTABLISHED
INDEPENDENT_L3=NOT_ESTABLISHED
stable_ready=false
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
```

## Verified CI evidence — 6 November 2026

[App Actions #42204308978](https://github.com/lijust/EREI-3.2/actions/runs/42204308978) completed SUCCESS. Its decoded regression log independently confirms 22 F5B1G + 18 F5B1F + 15 F5B1E + 12 F5B1D + 15 F5B1C + 10 F5B1B + 42 F5 + 28 F5A + 17 F5B0 = **179/179 PASS**, 0 failed.

The 22 F5B1G test assertions include 10 offline deterministic fault cases against actual SQLite WAL and a real AF_UNIX fake Docker HTTP server. Specifically, `unsafe_raw_f5_retry_counterexample` **reproduced** the raw F5 second-callback opportunity after first transport failed. This result exposes an unclosed replay/duplicate CREATE path; it is NOT a safety proof or accepted retry. `late_create_after_empty_counterexample` also deliberately demonstrates that one empty fake inventory observation does not exclude a later accepted create.

No sudo, no privileged Docker workflow, no image pull, no real Docker CREATE/START and no candidate/model execution occurred in this run. F5B1F's prior real Docker owner-manual success remains separately scoped to run #42202611269; no F5B1G real-Docker fault run has been performed.

F5B1G_OFFLINE_REAL_SQLITE_FAULT_MATRIX=LOCAL_SCOPED_PASS
F5B1G_REGRESSIONS=179_PASS
RAW_F5_UNKNOWN_REEMISSION_RISK=COUNTEREXAMPLE_REPRODUCED
ONE_EMPTY_INVENTORY_LATE_CREATE_COUNTEREXAMPLE=REPRODUCED
RAW_F5_SEND_ONCE_GUARD=NOT_IMPLEMENTED
REAL_DOCKER_FAILURE_INJECTION=NOT_EXECUTED
INDEPENDENT_TERMINAL_SETTLEMENT=NOT_IMPLEMENTED
LATE_ASYNC_CREATE_QUIESCENCE=NOT_ESTABLISHED
GLOBAL_DOCKER_EXCLUSIVITY=NOT_ESTABLISHED
INDEPENDENT_L3=NOT_ESTABLISHED
STABLE_READY=false
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
