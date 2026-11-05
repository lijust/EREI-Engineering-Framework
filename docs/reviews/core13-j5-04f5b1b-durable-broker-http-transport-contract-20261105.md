# Core13 F5B1B — protected broker and durable pre-SEND Docker transport acceptance contract

5 November 2026. Successor to Framework F5B1A PR #162, scoped App implementation after #287. Tracking: Framework #161, App #286.

## Narrow technical progress

App F5B1B introduces a concrete `submit_fixed_with_local_wal` path that sequences real F5 SQLite `admit`, `EMITTED_UNKNOWN` write-ahead, an **AF_UNIX HTTP CREATE request** to an exact Docker-compatible endpoint, CID claim storage, local inspect/DELETE, and local inventory read. No caller-driven image/code/endpoint. A prospective `root_socket_once` has 0660 group-bound broker socket, kernel PID/UID/GID check, SCM_RIGHTS rejection and root-protected daemon/ledger prerequisites. This is **code coverage and integration design**, not evidence of runtime root/daemon authority: ordinary CI tests talk to a deliberately fake Docker-protocol server over a real Unix socket, not to dockerd.

In particular the newly returned CID and locally observed cleanup are **not independently settled**; the F5 record remains `RETURNED_CLAIM` and still blocks F5A/legacy rotation. An invalid CID or interrupted transport leaves durable `EMITTED_UNKNOWN`, which is correct fail-closed behavior but does not clear possible late CREATE.

## Non-negotiable acceptance gates

- Root-only dedicated private dockerd is a separate *verified* daemon principal, never host dockerd alias.
- Root-owned protected persistent SQLite WAL and exact source-fixed ledger, with no same-UID controller modifications.
- Root broker and controller are separate OS accounts; controller and restricted worker both denied all raw host and private Docker paths, inherited FDs and alternative TCP clients. Prove `0660` is accessible only to intended controller group, never broad `0666`.
- Privileged root broker must be launched only via manual owner-dispatched disposable runner and source-reviewed pin; no arbitrary PR code privileges. Immutable test image must independently pass applicable CVE/runtime review before any START.
- Real root broker CREATE/inspect/DELETE and crash/timeout/unknown CID recovery must be verified with a dedicated dockerd. No false claim from the fake server tests.
- Late async CREATE drain/epoch fencing with persistent independent terminal receipt must be proven before enabling rotation or AI acceptance.
- Complete broker-only J4/J4S lifecycle migration (START/attach/stream/timeout/cleanup/recovery) or keep those untrusted execution paths disabled.
- Independent L3 signoff still mandatory; do not infer effect on model learning from test counts.

## Gates

```text
f5b1b_nonroot_unix_http_to_fake_daemon=TEST_PENDING
f5b1b_actual_root_dockerd_create=NOT_ESTABLISHED
broker_only_docker_authority=NOT_ESTABLISHED
late_create_quiescence=NOT_ESTABLISHED
terminal_settlement=NOT_IMPLEMENTED
independent_l3=NOT_ESTABLISHED
untrusted_code_execution_authorized=false
stable_ready=false
decision=BLOCK_AI_ACCEPTANCE
```
