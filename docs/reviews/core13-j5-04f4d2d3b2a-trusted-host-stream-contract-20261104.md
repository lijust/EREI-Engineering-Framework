# Core13 D2D3B2A — verified trusted host process streaming over fixed kernel IPC (not Docker)

**4 November 2026 | Framework staged successor to D2D3B1 Draft #154.**

## Prior verified boundary

[App D2D3B1 PR-head Actions #41885152565](https://github.com/lijust/EREI-3.2/actions/runs/41885152565) **105 offline/nonprivileged PASS** (35 B1 Unix SEQPACKET/peer/ancillary and in-memory fixed backend, 38 D2D3A modeled lifecycle, 14 D2D2 migration-denied, 18 D2A authority-denied). Its kernel socket messages were real but **both principals shared OS UID/PID and backend was fake**. Real [D2D1 owner run #41872834558](https://github.com/lijust/EREI-3.2/actions/runs/41872834558) scoped success for NEW separate controller and never-started F4C2 root broker, not J4/J4S streaming.

## D2D3B2A new behavioral boundary

App module `tools/core13_j5_04f4d2d3b2a_fixed_host_stream_broker.py`, tests and unprivileged Linux PR/push workflow. It pins the exact reviewed D2D3B1 Git blob `00b719de5f41a37a8447da7fee845bb6e8d94e08` and its upstream D2D3A/D2D2 denial policy. Requests still use actual B1 `AF_UNIX/SOCK_SEQPACKET`, kernel `SO_PEERCRED`, strict exact fixed typed `run_fixed` case/ticket, one-shot replay rejection, ancillary-denied before dispatch, frame <=512B. Neither client nor broker receives mutable image, code, Docker URL, command, shell flags or user/model instructions.

**New verified execution target is a source-defined trusted host Python child, NOT a Docker container.** Fixed scripts only:
- `normal`: real small stdout/stderr and natural zero exit.
- `output`: real stdout write of 20,000 bytes; bounded 512B reads and 4,096B retention limit, stop obligation at overflow.
- `timeout`: real fixed `time.sleep(10)` but enforced actual 0.25s monotonic deadline, followed by process-group SIGKILL and wait/reap.
- `stderr` direct test: real stderr 20,000 bytes, count max 2,048 and **zero stderr payload retained**.
- `late_create` is explicitly fake modeled D2D3A only and **MUST NOT START a child**.

Launch: fixed `sys.executable,-I,-S,-u,-c,<source literal>`, DEVNULL stdin, stdout/stderr pipes, fixed PATH/LANG env, `close_fds=True`, `start_new_session=True`. The process stream uses `selectors` and actual monotonic wall time, not only synthetic D2D3A ticks. On abort, send SIGKILL to the trusted child's dedicated process group if still alive, wait/reap and close pipes. Modeled `FixedLifecycle` stop/owned removal witnesses are **still boolean synthetic**, never an independently verified Docker resource deletion. Real process-tree isolation is NOT certified by the single PID/reap test.

**Credential ceiling:** B2A requires nonroot current Linux UID/GID but does **not** prove the GitHub runner OS account lacks membership in Docker group, passwordless sudo, alternate endpoints or inherited capabilities. Socket client/server remain within same host process UID. No production root broker, private daemon, Docker image container, Docker API, privileged SCM_RIGHTS or real generation journal is used.

## Source CI / acceptance scope

Unprivileged PR/push CI runs B2A's 32 real trusted child/IPC/stream/timeout tests plus B1 (35), D2D3A (38), D2D2 (14). One initial green push [App Actions #41886983678](https://github.com/lijust/EREI-3.2/actions/runs/41886983678) reported **119 PASS / 0 FAIL**: B2A 32, B1 35, D2D3A 38, D2D2 14, on source SHA `630b3410350a067553adb33c84ee2c0f9dd5e4ac`. It used **real trusted host child processes**, but no Docker or privileged operations. Do not confuse a green B2A run with full Docker broker lifecycle, F5 process epoch or independent L3.

### Follow-on D2D3B2B and hard security gates

D2D3B2B must complete a separately controlled owner-reviewed root **private Docker** broker with distinct OS controller, kernel authenticated peer, fixed immutable image/config, **real** CREATE/INSPECT/START/ATTACH/stream/STOP/REMOVE and real owned private daemon cleanup, under bounded timeout/output and crash recovery. **Before starting any Docker image**, verify exact current image digest and full SBOM/CVE risk and bind durable F5 daemon generation, in-flight CREATE transport and late CREATE drain/quiescence. A previously noted vulnerable image remains an unresolved gate; its precise current advisories are not yet independently established. Independent L3 governance is also required. None of these are proved by B2A.

Existing J4/J4S direct host Docker CLI remains unmigrated. D2D2 migration policy and B2A public `authorize()` unconditionally DENY candidate execution. No code/user/model output is authorized and Draft PRs remain unmerged.

```text
d2d3b1_kernel_ipc_fake_model=OFFLINE_SCOPED_PASS
d2d3b2a_fixed_trusted_host_child_streaming=SCOPED_NONPRIVILEGED_REAL_PROCESS_PASS
real_docker_lifecycle_exercised=false
real_docker_start_attach_stream_exercised=false
docker_image_digest_and_cve_accepted=false
real_docker_owned_cleanup_verified=false
real_broker_controller_os_separation_verified=false
broker_host_docker_authority_removed=false
root_broker_transport_exclusive=false
durable_f5_create_intent_fenced=false
late_create_daemon_quiescence_proven=false
independent_l3_attested=false
real_worker_isolation_certified=false
untrusted_code_execution_authorized=false
stable_ready=false
decision=BLOCK_AI_ACCEPTANCE
learning_effectiveness=NOT_ESTABLISHED
```

**Generalizable lesson:** output streaming and timeout should be proved with real bounded OS child pipe reads and observed process cleanup rather than synthetic stop events; a successful trusted host process test is not a Docker sandbox, production controller boundary, F5 epoch or AI authorization certificate.

## Verified final App PR-head regression — 4 November 2026

[App Actions #41887290661](https://github.com/lijust/EREI-3.2/actions/runs/41887290661), exact App source SHA `1e8c334ee18c3f0ab4ceddffc2e15f40c3c64448`: **SUCCESS, 119 nonroot Linux PASS / 0 FAIL** (32 new D2D3B2A genuine source-fixed trusted host child PIPE/Unix IPC/monotonic deadline/kill/reap tests; 35 B1 kernel Unix IPC+fake model; 38 D2D3A in-memory lifecycle; 14 D2D2 migration-denial). Runtime child streaming and timeout **ARE REAL host process measurements**; Docker daemon, Docker container image/start/attach, controller-root-broker separation, durable F5 quiescence, independent L3 and image CVE clearance **are NOT tested**. The late CREATE example remains modeled/synthetic only. Existing J4/J4S remains direct host Docker. Gate `BLOCK_AI_ACCEPTANCE` unchanged.
