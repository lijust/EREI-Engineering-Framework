# Core13 F5B1D — actual Linux root/controller/worker OS principal isolation (HOLD)

5 November 2026. Stacked on Framework F5B1C #164. This is a stage-scoped **acceptance contract, not a certificate**.

## Scope

App F5B1D introduces a manual-owner-only Unix filesystem/socket fixture:
- A genuine root process must create a random private `/run/core13-j504e2a-*` namespace with mode `0710`, controller group, an inaccessible root-ledger `0700` and test marker `0600`; root-owned broker Unix SOCK_SEQPACKET `0660`.
- Real, distinct nonroot controller and worker principals must have credentials dropped via Linux `setgroups([])/setgid()/setuid()`. Controller can connect to broker socket; kernel `SO_PEERCRED` proves expected PID/UID/GID, but controller cannot read ledger. Worker must be denied the broker socket and root ledger.
- The manual privileged job may only run on `workflow_dispatch` from owner `lijust` on an exact reviewed branch with explicit `root_fs_no_docker` input, reviewed Git blob, and successful nonroot gate. Ordinary push/PR tests must never invoke `sudo`.
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

## Verified local CI and manual-proof status — 5 November 2026

[App GitHub Actions #42060987806](https://github.com/lijust/EREI-3.2/actions/runs/42060987806) completed **SUCCESS** with `12+15+10+42+28+17 = 124/124 nonroot PASS`. The manually gated `owner-manual-real-root-posix-probe` job was **SKIPPED**, as intended for ordinary push/PR events. Therefore the real root controller/worker POSIX proof is **NOT EXECUTED**, and no claim is made about actual broker isolation or Docker exclusivity. All acceptance booleans remain false.

## Verified OWNER-MANUAL real-root Linux OS experiment — 2026-11-05

**Evidence:** [App workflow_dispatch #42069248000](https://github.com/lijust/EREI-3.2/actions/runs/42069248000), at reviewed head `9354d38a81d078ee7b51b2ab42072811b9c2cfd8`.

The GitHub connector independently re-read both jobs. Both **completed SUCCESS**:
- `nonroot-review-and-negative-regressions` — job `127392209717`, all scoped test steps PASS (124 regression cases from preceding baseline).
- `owner-manual-real-root-posix-probe` — job `127392374192`, source-Git-blob and owner/context preflight PASS, then **actual sudo-root Linux kernel proof PASS**. The run's decoded job log includes the exact assertion marker `F5B1D_REAL_ROOT_POSIX_KERNEL_NEGATIVE_PASS_BUT_NO_DOCKER_OR_AI_AUTHORITY` after the fixture's explicit JSON assertions.

**Scope supported by the manual script + passing job:** a real root-owned ephemeral `/run` directory/marker; separate controller/worker UID/GID drops; controller can connect to root-owned group-restricted 0660 broker `SOCK_SEQPACKET`, kernel `SO_PEERCRED` PID/UID/GID matches; controller cannot read root-only ledger; worker cannot read root-only ledger or connect to broker socket. The manually gated job ran once on owner dispatch, not on PR or push.

**Not established:** actual broker-to-dockerd authorization, host Docker bypass resistance, inherited FD/capability confinement, actual root F5 SQLite WAL initialization, independent daemon epoch/quiescence, independently verified terminal settlement, late asynchronous CREATE barrier, full J4/J4S broker-only lifecycle, L3, stable readiness or AI execution authorization.

```text
F5B1D_NONROOT_REGRESSION=LOCAL_SCOPED_PASS
F5B1D_ACTUAL_ROOT_CONTROLLER_WORKER_KERNEL_POSIX=MANUAL_SCOPED_PASS
F5B1C_REAL_ROOT_F5_SQLITE_INITIALIZE=NOT_EXECUTED
REAL_DOCKER_CREATE=NOT_EXECUTED
BROKER_EXCLUSIVITY=NOT_ESTABLISHED
INDEPENDENT_SETTLEMENT=NOT_IMPLEMENTED
LATE_CREATE_QUIESCENCE=NOT_ESTABLISHED
INDEPENDENT_L3=NOT_ESTABLISHED
STABLE_READY=false
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
```
