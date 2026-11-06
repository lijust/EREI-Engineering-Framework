# Core13 F5B1F — owner-reviewed never-started real CREATE via exclusive *local* broker path (HOLD)

**6 November 2026 | companion to App F5B1F, stacked on Framework F5B1E #166.**

F5B1E [manual run #42198897241](https://github.com/lijust/EREI-3.2/actions/runs/42198897241) has local scoped PASS for root F5 WAL initialized against a real disposable dockerd with zero CREATE. This F5B1F contract is a narrow proposed next proof, NOT an independent acceptance.

## Required observations

- Privileged operation ONLY on owner `workflow_dispatch`, exact source-reviewed Git branch, nonroot regression completed, explicit `fixed_create_no_start` selection. Never privileged Docker on PR/push.
- Genuine two distinct nonroot child principals must be unable to `AF_UNIX.connect()` directly to root-only private dockerd. Not just deny `os.open()` of the socket pathname. Controller must connect to `SOCK_SEQPACKET` broker with kernel PID/UID/GID verification and exact fixed packet, worker must lack broker credentials. Children close inherited nonstandard FDs before testing.
- Actual root broker must initialize protected F5 SQLite, require immutable source-reviewed pinned image and exact fixed J4 config, durably record `EMITTED_UNKNOWN` before actual single Docker CREATE; never START a container or execute the sleeper. On success, verify exact stopped CID ownership and DELETE plus empty private inventory.
- Persisted `RETURNED_CLAIM` remains unresolved even when local DELETE was observed; sealed generation must refuse legacy F5 rotation with `GENERATION_UNRESOLVED_INTENTS`. No unverified terminal row or fabricated daemon epoch.
- Verify private dockerd stopped, disposed root removed, host default daemon baseline unchanged. Any partial/unknown send or cleanup fails closed.
- Nonroot tests are source/negative regressions, not substitutes for actual root manual Docker result; image unpacking via root dockerd is a real elevated manual operation.

## No premature promotion

Even fully successful owner-manual F5B1F would show **one fixed known-source never-started container through one local broker**, not global exclusive Docker transport, proof against all late CREATE requests, crash replay/independent terminal settlement, J4/J4S migration, hostile model-code containment or L3. All remaining gates must remain false.

```text
F5B1F_REAL_BROKER_DOCKER_CREATE=NOT_EXECUTED
DOCKER_CONTAINER_START=FORBIDDEN
INDEPENDENT_TERMINAL_SETTLEMENT=NOT_IMPLEMENTED
LATE_ASYNC_CREATE_QUIESCENCE=NOT_ESTABLISHED
GLOBAL_DOCKER_EXCLUSIVITY=NOT_ESTABLISHED
J4_J4S_MIGRATED=NOT_ESTABLISHED
INDEPENDENT_L3=NOT_ESTABLISHED
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
```

## Verified automatic regression — 6 November 2026

[GitHub Actions #42200690837](https://github.com/lijust/EREI-3.2/actions/runs/42200690837) **SUCCESS**. Decoded job logs show 18 F5B1F + 15 F5B1E + 12 F5B1D + 15 F5B1C + 10 F5B1B + 42 F5 + 28 F5A + 17 F5B0 = **157 PASS / 0 FAIL** in nonprivileged Linux. The separate owner-manual real fixed CREATE job was deliberately **SKIPPED** on this automatic run; no actual real Docker CREATE happened in F5B1F. Real Docker START and AI code execution remain forbidden. Owner dispatch and independent evidence are required before any broader scoped claim.

## Observed 6 November 2026 owner-manual run

[GitHub Actions #42202611269](https://github.com/lijust/EREI-3.2/actions/runs/42202611269): both nonroot regression (157/157 PASS) and manually dispatched root broker job completed SUCCESS. The decoded privileged job log includes F5B1F_REAL_ROOT_BROKER_FIXED_CREATE_DELETE_NO_START_LOCAL_SCOPED_PASS_BUT_AI_BLOCKED, after executing Python assertion checks for one fixed never-started Docker CREATE/inspect/DELETE through root broker, private Docker socket access denial for controller/worker, persisted unresolved RETURNED_CLAIM, blocked F5 rotation, daemon cleanup and unchanged host baseline.

Scope is MANUAL_LOCAL_SCOPED_PASS, not an independent verifier or globally exclusive transport. The single successful fixed CREATE cannot establish terminal settlement after daemon/transport crashes, late async CREATE exclusion, multi-generation quiescence, legacy J4/J4S exclusivity, L3 or stable readiness.

F5B1F_MANUAL_FIXED_CREATE=LOCAL_SCOPED_PASS
DOCKER_START=NOT_EXECUTED
INDEPENDENT_TERMINAL_SETTLEMENT=NOT_IMPLEMENTED
LATE_CREATE_QUIESCENCE=NOT_ESTABLISHED
GLOBAL_DOCKER_EXCLUSIVITY=NOT_ESTABLISHED
INDEPENDENT_L3=NOT_ESTABLISHED
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
