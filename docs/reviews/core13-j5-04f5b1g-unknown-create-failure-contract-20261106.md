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
