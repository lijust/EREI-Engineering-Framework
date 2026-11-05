# Core13 F5B1D — actual Linux root/controller/worker OS principal isolation (HOLD)

5 November 2026. Stacked on Framework F5B1C #164. This is a stage-scoped **acceptance contract, not a certificate**.

## Scope

App F5B1D introduces a manual-owner-only Unix filesystem/socket fixture:
- A genuine root process must create a random private `/run/core13-j504e2a-*` namespace with mode `0710`, controller group, an inaccessible root-ledger `0700` and test marker `0600`; root-owned broker Unix SOCK_SEQPACKET `0660`.
- Real, distinct nonroot controller and worker principals must have credentials dropped via Linux `setgroups([])/setgid()/setuid()`. Controller can connect to broker socket; kernel `SO_PEERCRED` proves expected PID/UID/GID, but controller cannot read ledger. Worker must be denied the broker socket and root ledger.
- The manual privileged job may only run on `workflow_dispatch` from owner `lijust` on an exact reviewed branch with explicit `ROOT_FS_NO_DOCKER` input, reviewed Git blob, and successful nonroot gate. Ordinary push/PR tests must never invoke `sudo`.
- **No real Docker daemon, F5 SQLite initialization, AI model code or container execution is involved.** The OS fixture only proves a narrow kernel-owned access-control boundary on the selected runner.

## Acceptance gaps

Even if the manual kernel test passes, the complete exclusive Docker broker is not ready. Next steps require root-only F5 SQLite initialize against a real independently identified secondary daemon, pinning all privileged code, inherited FD/alternate socket bypass tests, crashed/unknown CREATE repair, independently protected terminal receipts, a proven late-CREATE quiescence barrier and J4/J4S broker-only migration. Independent L3 and image approval are separate requirements.

```text
F5B1D_NONROOT_REGRESSION=CI_PENDING
F5B1D_REAL_ROOT_POSIX_TEST=NOT_EXECUTED
REAL_DOCKER_CREATE=NOT_EXECUTED
BROKER_EXCLUSIVITY=NOT_ESTABLISHED
INDEPENDENT_SETTLEMENT=NOT_IMPLEMENTED
LATE_CREATE_QUIESCENCE=NOT_ESTABLISHED
INDEPENDENT_L3=NOT_ESTABLISHED
STABLE_READY=false
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
```
