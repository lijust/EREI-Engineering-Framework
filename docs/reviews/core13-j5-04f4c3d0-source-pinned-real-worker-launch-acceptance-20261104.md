# Core13 J5-F4C3D0 — source-bound actual fixed worker launch inventory before runtime isolation

**4 November 2026 · Framework draft stacked on F4C3C contract PR #141.**

## Pinned real adversarial result

Actual [App owner-manual Actions #41737838052](https://github.com/lijust/EREI-3.2/actions/runs/41737838052), exact SHA `69934a92e7a1e11558ff98ecc6df90ee6c1cc10d`: real secondary Docker and offline **136 PASS**. An already-connected root-origin Docker socket was sent **after exec** via Unix IPC `SCM_RIGHTS` to a separate restricted-UID child and was usable for fixed read-only GET. The no-transfer child had no descriptor and fresh socket connect got EACCES. This is **a confirmed capability-transfer counterexample**, not evidence that deployed Core13 workers leaked or excluded any FDs. All global gates `BLOCK_AI_ACCEPTANCE`.

## F4C3D0 actual source-to-capability mapping

The App F4C3D0 tool directly reads four exact reviewed Git blob versions of existing **actual** known fixed J4/J4S worker control path (not newly invented probe implementations) and statically examines Python AST without imports or running Docker.

- `tools/core13_j4_known_worker_lifecycle.py` `0f655d855898bef0d02fdda36602236b76304252`: J4 host controller runs Docker CLI `create` through subprocess.
- `tools/core13_j4s_streaming_fixed_worker.py` `42e4c879fc7a0b82c963838eb862ade8d6ac8531`: J4S host controller invokes `docker start --attach` through `Popen`; it bounds host-side stream retention for fixed trusted probes.
- `tools/core13_v5v_isolation_canary.py` `9b1d0d6f92ecc7aef0e576e128ec43e84578ba9f`: canary denies Docker endpoint override environment variables; Docker context validation permits `npipe://` or `unix://` **scheme** rather than binding one specific broker/daemon PID/socket.
- `tools/core13_j5_04a_hostile_execution_deny_gate.py` `a591c2e1d68de1c72fd05428f3153158f77ee2d0`: explicit negative untrusted-execution gate remains.

**Important:** J4/J4S are known, source-fixed container experiments controlled by a host Docker-CLI-capable process. They are not proof of a separate least-privileged OS user for AI candidate code; those candidate executions are prohibited. An exact-source finding establishes architectural facts but cannot by itself attest live `/proc/<pid>/fd`, `SCM_RIGHTS`, alt Docker endpoints or actual worker group privileges.

## Non-overlapping acceptance gates

| Phase | Required evidence | State |
|---|---|---|
| F4C3A | Same-process retained preconnected Docker FD works despite fresh EACCES | CONFIRMED read-only counterexample |
| F4C3B | Distinct fork/exec child explicit pass_fds GET positive vs close_fds/EBADF negative | SCOPED real Docker PASS |
| F4C3C | Distinct restricted child SCM_RIGHTS transfer after exec GET positive vs no-transfer EACCES | CONFIRMED real read-only counterexample, Actions #41737838052 |
| **F4C3D0** | Git-pinned actual J4/J4S host controller launcher source and exact gap inventory | Implementation + offline CI; cannot certify runtime |
| F4C3D1 | Instrument actual fixed trusted J4/J4S runtime PID/UID/FD/IPC/endpoint graph in disposable real run | Not established |
| F4C3D2 | Implement/attack-test actual worker isolation, absent inherited & received privileged FDs and alternate transports | Not established |
| F5 | Generation/daemon epoch with in-flight CREATE quiescence/drain | Not established |
| L3 | Independent trusted verifier separate from controller | Not established |

Potential separate pre-execution gate: user-supplied Docker Scout screenshot reported **34 vulnerabilities** for `python:3.12-slim`, truncated digest beginning `aa943ce41142`; this is a version-bound reported scan, **not** confirmed exploitability. Full hash + current SBOM/CVE triage, remediation or approved exceptions are prerequisites for starting untrusted worker code. F4C3 socket probes do not execute that image; F4C2 created but never started a fixed test container.

All global safety booleans remain **FALSE** including `actual_untrusted_worker_os_process_verified`, `actual_worker_runtime_fd_table_audited`, `exclusive_transport_owner_attested`, `external_socket_bypass_denied`, `worker_isolation_certified`, `creation_quiescence_barrier_proven`, `independently_verified`, `untrusted_code_execution_authorized`; `decision=BLOCK_AI_ACCEPTANCE`, `learning_effectiveness=NOT_ESTABLISHED`.

**Reusable engineering insight:** separate three claims: (1) reviewed static source has an execution guard, (2) actual fixed worker OS process is observed, (3) arbitrary candidate code is contained. Only (1) is targeted by the D0 artifact; never infer (2) or (3) from it.
