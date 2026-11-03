# Core13 J5-04F4C3C — SCM_RIGHTS post-exec transfer of Docker capabilities

**3 November 2026 · Framework Draft stacked on F4C3B framework #140.**

## Verified upstream

Owner-dispatched real App [Actions #41687102623](https://github.com/lijust/EREI-3.2/actions/runs/41687102623) at source `5ba1097b0fd8bea2e91a0a86db6bf273b567efe1` confirmed with Docker that **`pass_fds` leaks a pre-connected root-origin Unix Docker socket into a restricted fork/exec child**, while `close_fds=True` with no passed descriptors gives **EBADF** on that known FD and **EACCES** on new connect; **115 offline PASS**. No Docker API mutation. This was one test launcher only, not deployed worker isolation.

## New threat boundary: descriptor transfer *after* exec

A safe fork/exec launch does **not** prevent a privileged sender from **transferring an already-connected file descriptor later** over a permitted Unix IPC channel using Linux `sendmsg` with `SCM_RIGHTS`. F4C3C introduces two fixed real-private-Docker experimental controls, both on one root-owned 0600 secondary daemon on a reviewed disposable hosted Linux runner:

1. One root source-fixed launcher opens a private Docker socket and checks exact daemon `SO_PEERCRED` and /proc-owned private instance. The launcher creates a `SOCK_SEQPACKET` local IPC socketpair and spawns a fixed restricted child with `user=restricted uid`, `group=restricted gid`, `extra_groups=[]`, `close_fds=True`; the only `pass_fds` item is the IPC socket, **never the Docker connection**.
2. **Positive transfer**: sender uses `sendmsg(..., SCM_RIGHTS, <one private Docker FD>)` and bounded fixed protocol `ALLOW_FD`. Restricted child receives with bounded `recvmsg`, validates sender's kernel PID/UID/GID and transferred Docker peer PID/root identity; only fixed **GET /_ping** is sent through the transferred raw socket. No CREATE/start, mounts, user-chosen API or host Docker API.
3. **Negative no-transfer**: a second identically restricted child receives `NO_FD` **without ancillary data** and must fail a fresh connect to root-owned private Docker socket with **EACCES**. There is no mutation or image execution.
4. On timeout, peer mismatch, unexpected descriptor number, wrong response, nonempty ancillaries, unknown process/scratch, uncertain shutdown or changed host Docker baseline, **HOLD** with sanitized reason. Only own disposable daemon and test child are touched.
5. PR CI unprivileged, root real Docker `workflow_dispatch` owner/branch only. Source-generated runner JSON is not independently signed L3 evidence.

If both real controls succeed, `F4C3C_REAL_SCM_RIGHTS_TRANSFER_COUNTEREXAMPLE=CONFIRMED` **means a dangerous transfer mechanism was demonstrated**, NOT prevention. None of `scm_rights_raw_docker_fd_transfer_prevented`, `scm_rights_raw_docker_fd_transfer_excluded`, `exclusive_transport_owner_attested`, `external_socket_bypass_denied`, `worker_isolation_certified`, `creation_quiescence_barrier_proven`, `independently_verified` or `untrusted_code_execution_authorized` may be true; `decision=BLOCK_AI_ACCEPTANCE`, `learning_effectiveness=NOT_ESTABLISHED`.

## Actual worker, alternate transport and generation coverage are still missing

F4C3D must examine the **real** untrusted-worker launch and runtime `/proc/<pid>/fd`, permitted IPC and `SCM_RIGHTS` peers, inherited sockets, Docker contexts, other Unix socket aliases, TCP/TLS/SSH Docker access, and broad root/sudo controller capability. Only then can a credible exclusive broker boundary be designed and measured. F5 must handle in-flight/late Docker CREATE across stop/cancel/epoch; L3 independently governed verifier/signing remains required.

**Reusable principle:** `close_fds` affects initial process capabilities; `SCM_RIGHTS` is an independent post-exec capability acquisition channel. A positive demonstration and a matched no-transfer negative are both needed for a valid threat probe.

## Docker image security observation from user-provided Docker Scout screenshot

The user supplied a **3 November 2026 screenshot** displaying a locally scanned `python:3.12-slim` image: **34 reported vulnerabilities, 127 packages**, and a visible truncated digest beginning `aa943ce41142`. The pinned test-only image used for F4C2's **never-started** fixed CREATE/inspect/delete shares that prefix; compare the **full SHA256 digest** before equating the two. The image was **never started** in that F4C2 test; F4C3A/B/C do not create or start Docker containers, so these read-only socket tests do not execute vulnerable Python image code.

An immutable digest guards reproducibility only, not exploitability or security of a future worker. Any decision to start a container to execute untrusted/candidate code requires a separate digest-bound, current SBOM + vulnerability scan/triage gate, remediation of unacceptable findings (especially reported HIGH/CRITICAL), approved documented exceptions if any, refreshed pinned image and repeat independent OS/daemon/lifecycle verification. Do not confuse Docker Scout's **reported** CVE count with confirmed exploitability, and never grant `worker_isolation_certified` based solely on green create/inspect/remove tests.
