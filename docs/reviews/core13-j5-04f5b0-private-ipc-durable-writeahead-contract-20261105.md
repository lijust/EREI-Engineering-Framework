# EREI Engineering Framework F5B0 — real local private IPC + durable CREATE write-ahead contract

**2026-11-05 | Verification scope: nonprivileged, source-fixed, NO Docker transport.**

## Background and concrete implementation

F5A [App PR #284](https://github.com/lijust/EREI-3.2/pull/284) introduced a strict additive SQLite WAL generation rotation method that blocks when any historical `PREPARED`, `EMITTED_UNKNOWN`, or `RETURNED_CLAIM` exists. **Legacy `f5.rotate()` remains callable and allows rotation with outstanding rows**. A strict local database guard is necessary but not sufficient for real Docker creation quiescence.

New F5B0 [App staged successor] adds `tools/core13_j5_04f5b0_private_ipc_durable_presend_hold.py`: nonroot Linux **AF_UNIX/SOCK_SEQPACKET** kernel messenger with real user-owned directory mode **0700**, socket mode **0600** (unlike legacy F4C2 source mode `0666`), exact source literal request `{"op":"prepare_fixed","version":1}`, kernel `SO_PEERCRED` PID/UID/GID check, bounded framing and ancillary SCM_RIGHTS FD rejection with actual received FD closure. No arbitrary image, config, command, name or Docker endpoint is accepted. Both sides of the test are **same-UID/same-process**; this does not certify OS controller vs root broker separation.

The local handler sources and SHA1-Git-blob pins exact F5 prototype `ec4cd704b8865193761cdb836c68d58d6f929f17` and F5A guard `2b69ab0284571bac826c8d65bfc268670c1c6ef5`, then calls existing real local SQLite F5 `admit()` and `prepare_dispatch_unknown()` on a deterministic fixed name, committing `PREPARED` then `EMITTED_UNKNOWN` before *any future hypothetical* Docker send. It never invokes a Docker API; **`EMITTED_UNKNOWN` is pessimistic pre-send uncertainty, not evidence an API request was actually emitted**. Subsequent F5A guarded local rotation is denied, while original legacy F5 rotate bypass is separately demonstrated and remains an obstacle.

## Direct verified CI / evidence ceiling

[App nonprivileged Actions #42046395930](https://github.com/lijust/EREI-3.2/actions/runs/42046395930), reviewed push source SHA `886a29e4a31b097b3baa7c3ce2dc727902d0605a`, actual fixture **SUCCESS: 84 PASS / 0 FAIL**: **16 new real Linux source-fixed Unix IPC/0700-0600 socket/peer/SQLite WAL pre-send tests +28 F5A SQLite zero-pending/all-generation transaction tests +40 unmodified F5 local prototype tests**. Source logic genuinely sends/reads a kernel socket message and writes/reads SQLite/WAL, unlike purely in-memory lifecycle fixtures. There was **no Docker, container, root, remote endpoint, model/user code, or production write**. If later PR-head documentation changes occur, record fresh exact SHA/source CI separately.

## Required integration/acceptance sequence

1. Only the **root/private broker** may hold the actual Docker socket; private controller identity must be verified as a **different nonroot OS principal**, and neither controller nor restricted worker can access Docker Unix/TCP/TLS/SSH or inherited FD capabilities. Replace/disable old world-accessible F4C2 test socket and any unreviewed alternative RPC route.
2. Every allowed fixed Docker CREATE must durably record an intent before bytes can be sent. Validate daemon epoch/boot identity, transport lifecycle and untrusted late/unknown daemon responses under a *single* exclusive broker authority. The broker must own and independently verify cleanup for returned, ambiguous and orphaned CIDs.
3. Generation rotation must be an atomic zero-unresolved all-generation action, under the broker's **exclusive** transport. Legacy `f5.rotate()` must be retired or made unreachable; a new wrapper alongside it does not enforce production policy. A zero-row local SQLite snapshot is not global quiescence.
4. Use independently approved, current SHA-pinned SBOM/CVE image and fixed runtime compatibility tests before any container START/ATTACH. Alpine 3.24 remote scan showed 0 HIGH but six pip CVEs and no runtime/ABI verification; F4C2 currently uses a different Debian digest with 47 HIGH package matches. Do not silently replace that digest.
5. Independently prove real Docker lifecycle (CREATE→INSPECT→START/ATTACH/STREAM→STOP/REMOVE), late async CREATE + crash/restart, actual owned cleanup and L3 verification before relaxing `BLOCK_AI_ACCEPTANCE`. Prior J4/J4S host Docker CLI remains unmigrated.

```text
f5b0_local_sourcefixed_private_seqpacket_ipc_0700_0600=SCOPED_PASS
f5b0_real_sqlite_wal_presend_unknown=SCOPED_PASS
f5a_local_zero_unresolved_rotation_denies_unknown=SCOPED_PASS
f5_legacy_rotate_unresolved_bypass_present=true
broker_exclusive_docker_create_transport_proven=false
distinct_privileged_broker_controller_principals_proven=false
real_docker_api_send_or_create_tested=false
late_async_daemon_create_excluded=false
owned_docker_container_absence_verified=false
independently_protected_generation_ledger=false
image_security_approved=false
independent_l3_verified=false
untrusted_code_execution_authorized=false
stable_ready=false
decision=BLOCK_AI_ACCEPTANCE
learning_effectiveness=NOT_ESTABLISHED
```

**Reusable source-engineering lesson:** successful IPC kernel framing and real SQLite WAL persistence can be tested as a component without privileged Docker, but distinguishing **write-ahead prepared/unknown** from **actual external emission and verified cleanup** prevents false claims of generation quiescence. Tight socket filesystem permissions are useful, not a substitute for peer isolation and exclusive broker transport.
