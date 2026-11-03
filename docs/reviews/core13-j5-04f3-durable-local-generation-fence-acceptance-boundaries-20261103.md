# Core13 J5-04F3 — local durable generation fencing: test evidence vs enforceable CREATE barrier

**3 November 2026 | reusable engineering contract and evidence record. NO runtime or model acceptance promotion.**

## Why this stage is needed

The actual source-reviewed Docker negative controls established:
- App F1 [Draft #257](https://github.com/lijust/EREI-3.2/pull/257), [Actions #41619674881](https://github.com/lijust/EREI-3.2/actions/runs/41619674881): a fixed locally admitted queued CREATE appeared as a real Docker CID *after* two peer-bound empty inventories.
- App F2 [Draft #258](https://github.com/lijust/EREI-3.2/pull/258), [Actions #41621174848](https://github.com/lijust/EREI-3.2/actions/runs/41621174848): actual private Docker Unix HTTP POST header + INCOMPLETE request body went to exact kernel-peer-verified dockerd *before* two empty inventories; the remaining body then produced a real CID. This DOES NOT prove a fully submitted complete POST delayed at the daemon application layer.
- App E1/E1B [Drafts #255](https://github.com/lijust/EREI-3.2/pull/255), [#256](https://github.com/lijust/EREI-3.2/pull/256): two different same-UID Linux OS processes produced matching CID-scoped kernel cgroup observations, NOT independent security principals.

These observations explain why a merely empty Docker inventory or closed local queue cannot certify no late creates. New App [Draft #259](https://github.com/lijust/EREI-3.2/pull/259) implements **durable LOCAL generation admission fencing** with a real SQLite WAL database and source-reviewed immutable fixed J4 config only.

## What the local source actually enforces

Module: tools/core13_j5_04f3_local_sqlite_generation_fence.py. This is a deliberately unconnected research adapter, **not** the production worker path or the primary Docker transport.

- Private scratch root must match reviewed secondary daemon root name and be a direct child of RUNNER_TEMP. Refuse symlinks in root/database/WAL/SHM and fixed-config identity changes. Original source gate is checked at initialization.
- SQLite WAL + synchronous FULL are **requested**. Every state mutation uses BEGIN IMMEDIATE and bounded lock acquisition; this is observed durable local-process behavior, NOT independently attested power-loss resilience or tamper resistance.
- Generation 1 receives a random 256-bit token and current reviewed daemon epoch+host boot identity. New admission stores exact fixed config SHA256 in PREPARED. A separate explicit preparation commits EMITTED_UNKNOWN **before a send attempt**. If process crashes, timeout occurs, or callback throws, UNKNOWN remains, never inferred as absent.
- submit_static_test_only rechecks OPEN generation/current token, exact source-fixed name/hash, and EMITTED_UNKNOWN under the SQLite write transaction lock. The fixed-only *test callback* runs while that transaction lock remains held. A concurrent seal cannot successfully commit until callback returns or times out into HOLD; no success-with-active-sync-transport race *within the adapter*. Callback failure retains the committed UNKNOWN record. A valid full CID result is named RETURNED_CLAIM — **not** verified Docker creation/removal.
- SEALED local generation denies all new intents and sends. Rotation requires old SEALED, changed daemon process epoch, same host boot; increments monotonic generation and issues a new token. Old-generation intents remain in the ledger, including unresolved PREPARED/EMITTED_UNKNOWN; old token can no longer submit through this adapter. Zero outstanding local records still never grants quiescence.
- Same-UID user can modify local ledger; any Docker CLI, raw Unix socket client, alternate host daemon, async callback that returns early, daemon restart ambiguity or rootful process can BYPASS the local enforcement. This is not exclusive CREATE transport, protected verifier, host isolation or process-tree closure.

## Verified cross-platform execution

**Actual tested App source HEAD 3f7e7ffd16697c0ffba635b78c8a9e82d69c15cc**, [GitHub Actions #41625228367](https://github.com/lijust/EREI-3.2/actions/runs/41625228367) **2/2 jobs SUCCESS**. Ubuntu **188 PASS**, Windows **187 PASS +1 Linux-only skip**; no rootful Docker job or candidate code. Includes:
- 40 new F3 tests: actual SQLite WAL reopening and separate real Python interpreter reading committed EMITTED_UNKNOWN records, contending threads, real lock-held callback/seal denial, stale token across rotation, falsified CID/config, source mutation and symlink refusal.
- F2 real offline socketpair protocol tests (27 Linux, 26 Windows+1 skip), F1 queued thread negative tests (27), source gate (30), durable journal (39), fixed-private-container owner-denial suite (25).

Two earlier CI runs were not all green and are retained as engineering evidence: [#41624948046](https://github.com/lijust/EREI-3.2/actions/runs/41624948046) failed a Linux **test-only** pinned source dict index; test changed to iterate actual path keys. [#41625053536](https://github.com/lijust/EREI-3.2/actions/runs/41625053536) failed two Windows **test teardown** cases: Python SQLite connection context managers commit but DO NOT close the handle, so Windows cannot remove a still-open database. Both test tamper fixtures now explicitly close connections with contextlib.closing, while production F3 module already used try/finally close. Final CI 188/187 green.

## What is NOT established

The F3 local callback is injectable by tests and is **not** an OS-enforced exclusive Docker create RPC broker. A callback that spawns a detached async CREATE and returns early can bypass the lock. The local token is stored in the same-user SQLite database, not an external signing secret; source or DB can be tampered with by a same-UID attacker. A request that was already sent before the lock is acquired may still complete. SQLite WAL FULL synchronous requested does not independently prove power-loss durability on host filesystems.

All F3 reports permanently set FALSE: exclusive_transport_owner_attested, external_socket_bypass_denied, independent_verifier_attested, generation_quiescence_certified, creation_quiescence_barrier_proven, late_async_create_excluded, full_process_tree_cleanup_certified, worker_isolation_certified, untrusted_code_execution_authorized, independent_model_patch_oracle_established, independently_verified. Decision remains BLOCK_AI_ACCEPTANCE, learning_effectiveness NOT_ESTABLISHED.

## Decision and next milestones

**Accept F3 only as a RESEARCH FIXTURE for local generation fencing** (subject to independent code review); keep App #259 and Framework review PR Draft/unmerged. Do not merge a production CREATE transport rewrite under this claim.

Next F4 must establish externally enforced exclusive create transport, e.g. a dedicated broker/OS principal with the Docker Unix socket accessible only to that principal, and a deterministic adversarial attempt to bypass it. Broker code and its source must be measured independently; all clients, including stale retries, must be unable to send raw Docker HTTP outside the broker. A real controlled Docker test under disposable hosted Ubuntu should demonstrate denied direct bypass, not just a Python Boolean.

Next F5 needs durable daemon-epoch/generation-fenced in-flight ledger with actual no-pending-create barrier and server-side or independently witnessed timing. One successful stale token denial in an optional local adapter does NOT exclude late Docker creates by other clients.

In parallel build L3 separate independently administered verifier identity, code measurement and protected signer (Framework #131), and independent hidden behavior Oracle for actual AI patch efficacy. Do not authorize untrusted AI code or change Stable readiness.

**Engineering lesson to reuse across countries:** Persist caller intent BEFORE transmission; distinguish PREPARED, EMITTED_UNKNOWN, returned unverified CID, verified owned cleanup, and truly independently fenced no-more-work. A database lock and same-user signature-like token are diagnostics, not authority. On Windows, explicitly close SQLite connections; context manager alone does NOT close file handles.
