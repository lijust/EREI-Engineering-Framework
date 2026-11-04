# Core13 J5-F4C3D2C1 — restricted-worker controller IPC ancillary FD rejection contract

**4 November 2026 · Framework Draft stacked on D2B1 #147.**

## Verified upstream runtime evidence

Owner-triggered [App D2B1 #41817999943](https://github.com/lijust/EREI-3.2/actions/runs/41817999943), SHA `3af42a207e86703a45ec133171aef0fea6b76f3e`, **SUCCESS** both actual private Docker and offline **81 PASS/0 FAIL**. The new **actual fixed restricted-UID OS process** had controller/worker SO_PEERCRED checked, zero inherited socket FDs before IPC, worker broker mutation `DENIED_PRINCIPAL` and fresh private and host raw Docker Unix socket connect `EACCES`. Trusted controller only created/inspected/deleted a never-started immutable test container via existing F4C2 broker; owned cleanup passed. This is **not** complete worker isolation or full Docker endpoint denial.

Earlier F4C3C real #41737838052 proved that an existing privileged Docker socket FD can be sent through post-exec `SCM_RIGHTS` to a restricted-UID process under controlled root/private Docker. D2B1's `recv(96)` of its controller command does not explicitly inspect ancillary messages; zero socket FD at worker startup cannot prove lifetime capabilities remain absent.

## New precise D2C1 contract

App code: `tools/core13_j5_04f4d2c1_worker_controller_ipc_ancillary_reject.py`. Offline tests and manual-only GitHub Actions workflow are paired on its Draft branch.

- Require exact immutable reviewed D2B1 source Git blob and original D2A source authority policy. No untrusted code, arbitrary Docker operations, generated code or new generic broker.
- Run the actual existing D2B1 fixed root private daemon and restricted worker EACCES/authorized-controller CREATE baseline. D2B1 remains sole owner of daemon, broker and fixed test container lifecycle and full cleanup.
- Launch a **second new real restricted process** through the *same source-fixed D2B1 UID/GID and subprocess pattern*, with the same UID and kernel controller peer checks, but a narrow `recvmsg` based controller input handler. Its PID is **not** the same as the original D2B1 worker; avoid conflating an additional process's evidence with a lifetime proof of the original.
- Authenticated controller sends one fixed command through allowed Unix IPC with one new local **dummy non-Docker Unix socketpair FD** via `sendmsg(SCM_RIGHTS)`. This tests kernel ancillary delivery and whether the worker explicitly detects and closes it, without transferring a Docker credential or any privileged FD to the restricted worker.
- The D2C1 fixed worker accepts only this exact adversarial input as a test: it must call `recvmsg(... MSG_CMSG_CLOEXEC)`, inspect ancillary level/type, close each received FD, deny unexpected or truncated ancillary and never treat it as an authorized task. Exact fixed `ANCILLARY_DENIED` reply and process exit 0 required; other outcomes **BLOCK**. This is a *negative test receipt*, not an authorization for future task execution.
- Normal pull_request CI runs **no root/Docker**. Privileged actual private Docker + restricted UID test is a separately reviewed **owner-only explicit `workflow_dispatch`** on the exact branch, ephemeral runner, source-pinned. Do not automatically run rootful code on PR or push.

### Limits and next gates

A later scoped D2C1 live PASS can prove **one dummy FD injection rejected on one authenticated controller IPC by one fixed restricted worker process**. It cannot prove a privileged raw Docker FD transfer is rejected, that *all* controller/broker IPC paths are hardened, no alternate raw Unix/TCP/TLS/SSH Docker endpoints exist, or that production untrusted worker code is contained. The user-supplied Docker Scout screenshot reports 34 vulnerabilities and the old pinned image has not been current-full-digest/CVE cleared; none of this authorizes untrusted image execution.

**D2C2:** attack the same new worker model with controlled privileged broker/SCM_RIGHTS and alternate endpoint negative controls, all source-defined and cleanup bounded; enforce default `recvmsg` ancillary refusal in the eventual *production* worker IPC. **D2D:** migrate any prospective untrusted path away from legacy J4/J4S host Docker CLI, integrate independently checked F5 daemon-generation/in-flight CREATE quiescence and separate L3 attestation.

```text
d2b1_actual_restricted_fixed_worker=SCOPED_REAL_PASS
d2c1_harmless_ancillary_denial=CODE_PRESENT_LIVE_PENDING
actual_worker_no_privileged_scm_rights_fd_delivery_proven=false
all_controller_and_broker_ipc_ancillary_paths_denied=false
actual_worker_no_fd_injection_for_full_lifetime_certified=false
actual_worker_all_alternative_docker_endpoints_denied=false
broker_exclusive_transport_certified=false
worker_isolation_certified=false
creation_quiescence_barrier_proven=false
independently_verified=false
untrusted_code_execution_authorized=false
decision=BLOCK_AI_ACCEPTANCE
learning_effectiveness=NOT_ESTABLISHED
```

**Generalizable engineering rule:** authenticate kernel peer on every allowed worker IPC, then use `recvmsg` to explicitly inspect and reject FD capabilities rather than equating `recv`, `close_fds` or a prestart snapshot with end-to-end ancillary denial. Even successfully rejecting a dummy FD is not equivalent to certifying all privileged FD delivery paths.

## D2C1 code reviewed and offline CI verified — 4 Nov 2026

[App Actions #41818892284](https://github.com/lijust/EREI-3.2/actions/runs/41818892284) **SUCCESS** with **80 OFFLINE PASS / 0 FAIL** (21 D2C1 +20 D2B1 +21 F4C3C +18 D2A), source SHA `f93cabeb0eedb35995ea0d15020552d487e4f452`. Real owner-manual D2C1 harmless SCM_RIGHTS FD injection into an actual second restricted worker was **SKIPPED** on PR and is therefore not real evidence yet. D2B1 actual owner run #41817999943 remains scoped separate-UID/fixed broker EACCES PASS only. Broad privileged FD transfer, all IPC peers, full Docker endpoints, F5, L3 and AI acceptance remain unproven.

## Verified actual D2C1 owner dispatch — 4 November 2026

Owner-run [App Actions #41820521157](https://github.com/lijust/EREI-3.2/actions/runs/41820521157), source `9a59602e55cbefd0213f077e702ff3464236c014`, **both actual private Docker and offline CI SUCCESS**. Actual second source-fixed separate restricted worker of same D2B1 launcher/UID/GID saw kernel controller peer credentials and **received/detected/closed and did not adopt one harmless non-Docker socketpair FD sent via authenticated controller `SCM_RIGHTS`**. Original D2B1 fixed broker EACCES baseline passed in the same owned session and broker/private Docker cleanup passed. **80 offline PASS** (21+20+21+18), no model calls/writes, no actual privileged Docker capability transferred.

This is **SCOPED_REAL_PASS** for one secondary worker IPC negative control only. The ordinary primary D2B1 worker still reads its fixed controller command via `recv`, not integrated `recvmsg`, and nothing here denies actual privileged SCM_RIGHTS across all peers or future arbitrary worker code. Keep all global worker security, alt-endpoint, F5, L3, Docker image CVE and AI acceptance gates FALSE, decision `BLOCK_AI_ACCEPTANCE`.

**Next reusable design delta:** integrate and test ancillary rejection in the *primary* worker that also executes broker + fresh Docker EACCES probes, instead of treating a second worker's demo as an enforceable default. Explicit source and runtime evidence must refer to the same worker PID/process.
