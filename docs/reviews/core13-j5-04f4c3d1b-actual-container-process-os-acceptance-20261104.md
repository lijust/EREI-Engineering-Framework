# EREI Engineering Framework — Core13 J5-F4C3D1B actual in-container Python /proc audit

**4 November 2026 · successor to D1A Framework Draft #143.**

## Prior pinned real evidence

[Owner/manual App J5-F4C3D1A #41740996507](https://github.com/lijust/EREI-3.2/actions/runs/41740996507) on pinned App SHA `a95df4f536a7291d58c4580ab4cec82bdb062018`: actual trusted J4S `docker start --attach` **host CLI process** PID/UID/GID and FD type counts (`socket=0, pipe=2, other=1`) observed, original fixed timeout and container cleanup succeeded. 49 offline tests PASS. **This was not the container Python process.** Before that, [actual F4C3C #41737838052](https://github.com/lijust/EREI-3.2/actions/runs/41737838052) showed **post-exec `SCM_RIGHTS`** could transfer an existing privileged Docker Unix FD to a separate restricted process. It was a risk demonstration, not a deployed worker leak/denial certificate.

## D1B contract

**Target claim:** observe one **actual running, source-fixed** Python process *inside* the immutable J4S trusted timeout container, as host `/proc/<PID>` and Docker `State.Pid`, while keeping full lifecycle and any AI execution authority blocked.

App implementation: `tools/core13_j5_04f4c3d1b_actual_j4s_container_python_proc_audit.py`. PR unprivileged tests: `tests/unit/test_core13_j5_04f4c3d1b_actual_j4s_container_python_proc_audit.py`. Manual-only live workflow: `.github/workflows/core13-j5-04f4c3d1b-actual-j4s-container-python-proc-hold.yml`.

1. Exact Git-blob source review from D0, unchanged original J4S `probe` lifecycle, trusted source-fixed `timeout` Python `time.sleep(60)`, original complete immutable image digest, approved ephemeral Linux GitHub runner and conventional host Docker baseline/no env overrides required.
2. Temporarily observe the **real existing** `j4s._attached_stream` call with an overlapping thread, not a new synthetic workload. The original J4S remains sole owner of Docker create/start/attach/timeout/forced removal and absence verification.
3. Read-only `sudo -n python -I -S -c <fixed source>` root helper (disposable reviewed runner only) may call **only** exact `docker --host unix:///var/run/docker.sock container inspect <64hex-CID>` and read the corresponding running host `/proc` entries. It validates `SUDO_UID`, exact `core13.j4.probe` label/name, **full** pinned image digest, source fixed command and nonroot/caps/read-only/no-network/no-bind limits. No arbitrary Docker endpoint, user code or mutation RPC.
4. Require exact `State.Pid>1` from running container, four Linux UID/GID fields = 65534, effective capability set 0, `NoNewPrivs=1`, argv exact fixed Python `-I -S -c`, and a network namespace distinct from host pid1. Sample **FD TYPES only** (socket/pipe/other counts <=128); do not log raw targets, env or secret content. Double-check same CID and running PID immediately after sampling. Source helper is not independently administered L3 verifier.
5. Require J4S source-generated `TIMEOUT_STOPPED`, exact container removal+absence, zero leftover `core13.j4.probe` containers and unchanged original Docker host baseline. Any issue yields HOLD; do not synthesize missing process facts.
6. PR CI must execute **only static/offline tests**. Rootful actual Docker test remains an exact owner + branch `workflow_dispatch`, and runs only the fixed known trusted script; it is not authorization of untrusted AI candidate execution.

## Assurance ledger

A successful *live* D1B would prove **only** the sampled actual source-fixed in-container Python process PID / UID / effective caps / NoNewPrivs / network namespace / FD *type* counts with exact cleanup. It is not a sample of an AI-generated or user-controlled worker, and FD-type counts do not prove the absence of a raw Docker socket peer, IPC `SCM_RIGHTS` or alternate Docker transports over time. The root helper is not independent.

| Security dimension | D1B state |
|---|---|
| Host Docker CLI process source-bounded runtime observation | D1A scoped real PASS #41740996507 |
| Actual running fixed J4S container Python `/proc` observation | **D1B implementation, live run pending** |
| Production untrusted worker OS authority and executable | NOT VERIFIED / no authorization |
| Raw Docker backend FD peer graph, SCM_RIGHTS and endpoint coverage | NOT VERIFIED |
| Broker sole transport, controller root/sudo boundary | NOT VERIFIED |
| F5 in-flight CREATE quiescence and daemon-epoch | NOT VERIFIED |
| L3 independently administered verifier | NOT VERIFIED |

### Vulnerable-image gate is separate

Docker Scout screenshot supplied by the user reports **34 CVEs** in local `python:3.12-slim` with truncated digest matching the test image prefix; the full scanned image digest and current CVE status have **not** been verified or remediated. Only source-trusted fixed-sleeper tests are considered on ephemeral owner-approved hosts; no model/user code execution. Before any untrusted image work: full digest, current SBOM, applicable CVEs, patch/exception policy and real isolation evidence. The pinned digest is not a security fix.

**All global gates remain FALSE:** `actual_untrusted_worker_os_process_verified`, `actual_worker_all_docker_endpoints_denied`, `worker_isolation_certified`, `broker_exclusive_transport_certified`, `exclusive_transport_owner_attested`, `creation_quiescence_barrier_proven`, `independently_verified`, `untrusted_code_execution_authorized`; `decision=BLOCK_AI_ACCEPTANCE`, `learning_effectiveness=NOT_ESTABLISHED`.

**Reusable framework rule:** separate *host controller*, *container's real fixed process* and *untrusted worker with privileged endpoint denial*, without treating proof of the first two as automatic certification of the third. Source-generated process observations are a necessary diagnostic step, not an independent security certificate.
