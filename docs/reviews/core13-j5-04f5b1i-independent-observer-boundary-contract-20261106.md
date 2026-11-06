# Core13 F5B1I — Observer/terminal-authority separation contract

**6 November 2026.** Companion to App F5B1I; stacked on Framework F5B1H #169.

## Background and objective

F5B1F [real root fixed CREATE/DELETE #42202611269](https://github.com/lijust/EREI-3.2/actions/runs/42202611269) has `MANUAL_LOCAL_SCOPED_PASS`. F5B1G [offline fault matrix #42204308978](https://github.com/lijust/EREI-3.2/actions/runs/42204308978) reproduces ambiguity and delayed CREATE. F5B1H [local send-once #42206476167](https://github.com/lijust/EREI-3.2/actions/runs/42206476167) blocks low-level raw resend. Independent terminal settlement remains missing.

The first F5B1I engineering deliverable is a **separately executed read-only observer**, not a settlement authorizer. It re-opens F5 protected-schema SQLite WAL read-only from a separate OS process, checks the exact reviewed fixed intent, and issues two kernel-peer-pinned **GET-only** requests to a local Unix fake Docker daemon. It must classify contradictory observations including an empty inventory preceding late CREATE, wrong CID, foreign labels, UNKNOWN with present container, and an apparently absent returned claim. Every result remains unresolved and non-authoritative.

## Correct trust split

| Evidence | What it can establish | What it does NOT establish |
|---|---|---|
| Actual distinct observer PID | A separate process ran | A separate protected principal, trustworthy external witness |
| SQLite `mode=ro` + `query_only=ON` | This reader did not intentionally mutate F5 | Source WAL integrity against a same-UID attacker, terminal settlement |
| Linux `SO_PEERCRED` on test socket | The fake Unix peer has expected OS credentials | A genuine protected dockerd or all possible endpoints |
| Fixed name/CID/config + two GETs | Snapshots and contradictions visible in the test | A barrier against future asynchronous CREATE |
| Denied `settle()` and AI authorization | This module is not an acceptance entrypoint | System-wide exclusive control of unrelated Docker entrypoints |

**A signed-looking self-generated JSON object cannot graduate to independently attested terminal state.** Actual protected verifier must have its *own* OS principal/authority and source binding, use a separately authenticated evidence journal, and avoid trusting mutable controller-provided termination flags. Root privilege and Linux FDs must be contained, and late daemon requests drained before any generation promotion.

## Review/acceptance ladder

1. **Offline classifier** (this phase): PASS means reproducible observations and continued HOLD, never terminal acceptance. Nonroot tests only, expected 21 new +197 inherited = **218**.
2. **Protected independent witness** (future): distinct UID/GID, no inherited root/daemon FD, kernel peer validation and separately controlled receipt signing/append-only logs. Can authoritatively attest observations, **not** end-to-end quiescence yet.
3. **Terminal settlement** (future): reviewed state transitions that require approved independent receipt, exact daemon epoch+boot+fixed name/CID, proven terminated stopped container and no outstanding async request with a verified drain barrier.
4. **Cross-incident and adversarial holdouts** (future): real disposable Docker with owner-manual fault windows, stale receipt, delayed CREATE, race and crash replays. Then separately independently accepted L3.

Until all required proof obligations pass, F5 intents stay unresolved and rotation fails closed. Never reinterpret the same-UID observation as signed, cryptographically independent evidence.

```text
F5B1I_OFFLINE_CLASSIFIER=CI_PENDING
DISTINCT_PROTECTED_VERIFIER_PRINCIPAL=NOT_IMPLEMENTED
VERIFIER_AUTHENTICATED_TERMINAL_RECEIPT=NOT_IMPLEMENTED
INDEPENDENT_DOCKER_TERMINAL_SETTLEMENT=NOT_ESTABLISHED
LATE_CREATE_QUIESCENCE=NOT_ESTABLISHED
GLOBAL_DOCKER_EXCLUSIVITY=NOT_ESTABLISHED
J4_J4S_MIGRATION=NOT_ESTABLISHED
INDEPENDENT_L3=NOT_ESTABLISHED
stable_ready=false
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
```

## Verified execution — 6 November 2026

[App Actions #42209572291](https://github.com/lijust/EREI-3.2/actions/runs/42209572291) completed **SUCCESS**. The decoded logs confirm **21 F5B1I + 18 F5B1H + 22 F5B1G + 18 F5B1F + 15 F5B1E + 12 F5B1D + 15 F5B1C + 10 F5B1B + 42 F5 + 28 F5A + 17 F5B0 = 218/218 PASS, zero failures**. The new 21 cases include actual separate-PID Linux child, read-only SQLite WAL, fake Unix GET-only two-snapshot observations, CID/label mismatch, initial empty inventory followed by late CREATE, peer PID mismatch, no terminal-settlement/AI path, and no real Docker authority.

**Evidence scope:** `F5B1I_SAME_UID_OBSERVER_LOCAL_SCOPED_PASS`, NOT independent terminal attestation. The observer is a separate PID but shares the parent's UID/GID and still trusts a local fake Docker daemon. All success reports explicitly assert independent protected verifier, authenticated terminal settlement, real Docker, global exclusive transport, late-create quiescence, L3 and AI authorization FALSE.

F5B1I_NONROOT_REGRESSIONS=218_PASS
F5B1I_SEPARATE_PID_READONLY_WAL=LOCAL_SCOPED_PASS
F5B1I_SAME_UID_NOT_INDEPENDENT=true
INDEPENDENT_TERMINAL_SETTLEMENT=NOT_IMPLEMENTED
PROTECTED_VERIFIER_PRINCIPAL=NOT_IMPLEMENTED
LATE_ASYNC_CREATE_QUIESCENCE=NOT_ESTABLISHED
GLOBAL_DOCKER_EXCLUSIVITY=NOT_ESTABLISHED
INDEPENDENT_L3=NOT_ESTABLISHED
STABLE_READY=false
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
