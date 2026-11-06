# Core13 F5B1H — send-once SQLite WAL commit-before-callback acceptance contract

**6 November 2026 | successor to Framework Draft F5B1G #168.**

App F5B1G [Actions #42204308978](https://github.com/lijust/EREI-3.2/actions/runs/42204308978) reproduced the raw F5 `EMITTED_UNKNOWN` re-emission gap using actual SQLite WAL and fake Unix Docker transport. Issue [#298](https://github.com/lijust/EREI-3.2/issues/298) tracks a durable send-once repair. F5B1F [real manual #42202611269](https://github.com/lijust/EREI-3.2/actions/runs/42202611269) remains local-scoped and does not prove unknown-response safety.

## Requirements

- An attempt to send a fixed Docker CREATE must consume a **durable DB claim before entering the transport callback**. All later calls on that row must reject even if the callback never returned, threw an exception, returned malformed CID, or died with `os._exit()`.
- Concurrency must be serialized by SQLite immediate transactions. At most one caller may enter a transport callback for a specific intent. Seal/rotate must remain protected from in-flight callback and must reject unresolved rows.
- **Legacy rows** without a send-once column have uncertain history: migrate conservatively to dispatch-consumed, including historical PREPARED. Do not infer never-sent from `PREPARED` without independent evidence; never grant retroactive SEND authority.
- A committed claim preceding transport is an upper bound on dispatch count, **not** proof that Docker received the request. Lost response and unknown callback must remain `EMITTED_UNKNOWN`; local success is `RETURNED_CLAIM` without independent terminal certification.
- The new F5 core blob changes source-chain hashes. Re-pin and re-run every dependent guard and regression; do not mutate historical successful F5B1F and F5B1G PR evidence. All automatic tests remain nonprivileged and require no Docker.
- No supplementary `candidate_execution`, no generic Docker API and no fallback to unprotected raw transport are authorized.

## Independent approval remains blocked

Even if all 197 scoped nonroot tests pass, this only establishes an F5 **local** durable send-once property and not exclusive Docker transport or terminal settlement after daemon crash. A separately protected terminal witness, late-CREATE barrier, adversarial inherited-FD/capability tests, global J4/J4S broker migration and independent L3 are outstanding.

```text
F5B1H_LOCAL_SEND_ONCE_REGRESSION=CI_PENDING
F5B1H_REAL_DOCKER_FAULT_INJECTION=NOT_EXECUTED
GLOBAL_DOCKER_EXCLUSIVITY=NOT_ESTABLISHED
INDEPENDENT_SETTLEMENT=NOT_IMPLEMENTED
LATE_ASYNC_CREATE_QUIESCENCE=NOT_ESTABLISHED
INDEPENDENT_L3=NOT_ESTABLISHED
stable_ready=false
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
```

## Verified GitHub Actions — 6 November 2026

[F5B1H scoped Actions #42206075573](https://github.com/lijust/EREI-3.2/actions/runs/42206075573) completed SUCCESS; decoded job logs confirm 18 F5B1H + 22 updated F5B1G + 18 F5B1F + 15 F5B1E + 12 F5B1D + 15 F5B1C + 10 F5B1B + 42 original F5 + 28 F5A + 17 F5B0 = **197 PASS / 0 FAIL**.

After re-pinning four inherited workflow SHA assertions (D, E, F and G) to the newly reviewed source blobs, **all 11 PR check workflow runs on commit 3cec005b0f64d200d9a35e0c8cb83b6b942736b1 completed SUCCESS**, including [F5B1H #42206263178](https://github.com/lijust/EREI-3.2/actions/runs/42206263178), [F5B1G #42206263190](https://github.com/lijust/EREI-3.2/actions/runs/42206263190), [F5B1F #42206263179](https://github.com/lijust/EREI-3.2/actions/runs/42206263179), and [F5B1E #42206263189](https://github.com/lijust/EREI-3.2/actions/runs/42206263189). The owner-root/real-Docker jobs in inherited E/F/D workflows were explicitly **SKIPPED**, so this stage did not run a real Docker CREATE.

The formerly reproduced raw F5 second-callback counterexample is now **DENIED by the revised SQLite WAL implementation** after a committed durable per-intent dispatch claim. The test includes direct second-call refusal after response loss, process death during transport, concurrent callers, migration of historical UNKNOWN and PREPARED rows as non-dispatchable, and blocked seal/rotate. This is a **LOCAL_SEND_ONCE_SCOPED_PASS** for the reviewed F5 adapter; it is not an independent settlement certificate or host-wide Docker sandbox.

F5B1H_LOCAL_SEND_ONCE=SCOPED_PASS
F5B1H_NONROOT_REGRESSION=197_PASS
F5B1H_INHERITED_CI=11_SUCCESS
F5B1H_REAL_DOCKER_FAULT_INJECTION=NOT_EXECUTED
LEGACY_UNKNOWN_REPLAY=FAIL_CLOSED
GLOBAL_DOCKER_EXCLUSIVITY=NOT_ESTABLISHED
INDEPENDENT_TERMINAL_SETTLEMENT=NOT_IMPLEMENTED
LATE_CREATE_QUIESCENCE=NOT_ESTABLISHED
INDEPENDENT_L3=NOT_ESTABLISHED
STABLE_READY=false
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
