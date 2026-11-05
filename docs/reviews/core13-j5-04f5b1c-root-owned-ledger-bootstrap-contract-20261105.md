# Core13 F5B1C — broker-owned WAL bootstrap contract (still HOLD)

**2026-11-05 | Stacked on Framework F5B1B #163. Implementation tracked in App #286 / Framework #161.**

## Contract

F5B1B built a source-fixed AF_UNIX HTTP CREATE/inspect/DELETE path linked to true F5 SQLite PREPARED→EMITTED_UNKNOWN→RETURNED_CLAIM, but the successful tests used a **nonprivileged fake Docker-protocol server** and the real root ledger was not initialized.

F5B1C adds a **root-only prospective bootstrap** to close part of that wiring gap, without executing it in automatic CI:
- Root authority requires actual `euid=egid=0`, owner-manual `workflow_dispatch` on a disposable GitHub Linux runner, exact repository/actor, and pinned reviewed predecessor source. No public CLI root execution route.
- Dedicated `/run/core13-j504e2a-...` directory must be owned by root with `0710` permissions and intended controller group, while only root can modify `root-ledger` (`0700`) and SQLite/WAL (`0600`) created under strict `umask 077`. `RUNNER_TEMP` must resolve to root-owned ledger parent; never re-use mutable runner temp as trusted ledger.
- Independent kernel and filesystem observations required before initialization: expected secondary `dockerd` process argv, root UID, PID start ticks, exact root socket mode `0600`, real `SO_PEERCRED` PID/UID/GID, and boot ID. A local witness is hashed into F5 epoch instead of accepting a caller-supplied epoch. This still does **not independently certify daemon generation or absence of delayed creates**.
- Fail on foreign SQLite files, symlinks, hardlinks, incorrect modes/owners, stale initialized ledgers and any earlier unresolved request. Never quietly reset WAL/intent state.
- A source-fixed one-shot root helper could call existing F5B1B broker after root checks, but **no owner-manual privileged workflow has been attached**. CI runs nonroot POSIX negative tests, not rootful dockerd or separate OS principals.

## Independent acceptance remains absent

Unresolved F5 rows are intentionally permanent blocks until an independently evidenced settlement state and a late-CREATE drain barrier exist. A local CID claim or apparent DELETE cannot complete acceptance or permit rotation. Legacy direct J4/J4S Docker workflows still bypass this new *optional* path; genuine global broker exclusivity and worker/host socket denial need adversarial live tests. Complete separate root/controller/worker role security, L3 and image suitability are not certified.

```text
F5B1C_OFFLINE_LAYOUT=TEST_PENDING
F5B1C_REAL_ROOT_LEDGER_BOOTSTRAP=NOT_EXECUTED
F5B1C_ROOT_DOCKER_INTEGRATION=NOT_EXECUTED
INDEPENDENT_DAEMON_EPOCH=NOT_ESTABLISHED
INDEPENDENT_SETTLEMENT=NOT_IMPLEMENTED
LATE_CREATE_QUIESCENCE=NOT_ESTABLISHED
INDEPENDENT_L3=NOT_ESTABLISHED
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
```
