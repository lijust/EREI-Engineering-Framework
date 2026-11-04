# Core13 J5-F4C3D2D3B1 — bounded kernel Unix broker IPC and deterministic fake backend acceptance contract

**4 November 2026 | Framework Draft stacked on D2D3A Framework #153.**

## Evidence baseline

App D2D3A [Actions #41881110485](https://github.com/lijust/EREI-3.2/actions/runs/41881110485) **92 offline PASS**, with typed in-memory generation, modeled late CREATE, bounded stdout/stderr, logical timeout and source-fixed stop/remove witnesses. D2D2 demonstrated actual J4/J4S still use host Docker direct create/inspect/start-attach/stream/stop/cleanup; the current root F4C2 broker only handles fixed never-started CREATE and immediate remove. D2D1 [owner real #41872834558](https://github.com/lijust/EREI-3.2/actions/runs/41872834558) scoped PASS for a distinct trusted `www-data` test controller and F4C2 broker, **not** full J4/J4S migration.

## D2D3B1 new contract

App source `tools/core13_j5_04f4d2d3b1_fixed_broker_seqpacket_ipc.py`, dedicated unit tests, **offline-only** PR/push CI. The artifact is a Linux kernel IPC transport fixture with source-fixed fake backend. **It is not a real Docker lifecycle implementation, root broker process, F5 persistent journal or production permission grant.**

**Required source-bound behavior:**
- Pin exact D2D3A Git blob `4b2fb854f4008dabb02cb9ea0fd77b859386735a` and source-gated D2D2 all-DENY migration review. Reject drift and symlink/unreviewed input.
- Create one actual local Linux `AF_UNIX/SOCK_SEQPACKET` listener in a test-owned directory mode 0700, socket 0600. Authenticate actual kernel `SO_PEERCRED` PID/UID/GID. **Client and server run in the same process/OS UID for this nonprivileged test; do not treat the observed identity as separation from root or Docker.**
- Use `recvmsg(...,MSG_CMSG_CLOEXEC)`, inspect ancillary before any fake dispatch. Close all delivered `SCM_RIGHTS` FDs, then deny. Test a harmless **non-Docker pipe FD** injected by the local client. Deny unknown ancillary, truncation, frame >512 bytes, malformed JSON and any extra field. Never receive root Docker/host Docker FDs.
- Exact request keys only `op/version/case/ticket`, with fixed op `run_fixed`, **integer** version 1, four source-fixed non-user cases `normal,timeout,output,late_create` and one fixed per-case ticket. Unknown case, op, type, wrong peer or replayed ticket is always denied; in-memory tickets are not durable capability tokens and do not prove replay resistance after restart.
- Fake in-memory D2D3A backend runs normal exit, logical timeout, output-overflow and late CREATE cleanup-obligation scenarios. **All stop/removal witnesses are synthetic.** It must not run Docker, process, root/privileged code, model, user code, or mutate any project. The parent source-reviewed `authorize()` remains categorical DENY regardless of a passing fake recipe.
- Return sanitized fixed bounded receipts: actual local Unix kernel message count and peer/ancillary checks, fake scenario and modeled quiescence. Explicitly all runtime Docker, real controller separation, durable F5, independent L3 and AI acceptance security gates remain FALSE.
- CI may run as a normal nonroot GitHub pull_request/push job only. No rootful workflow, real image start, host/private Docker or owner-run privileged test is created in D2D3B1.

### Stop conditions and required D2D3B2 integration

D2D3B1 cannot satisfy any real J4S broker lifecycle requirement: no real Docker CREATE, INSPECT, START/ATTACH, bounded streaming, timeout STOP, owned container recovery or durable generation fencing. An actual FIFO/Unix IPC test that returns fake backend evidence is **not** an authorization to run code.

**D2D3B2** must:
1. Bind a *separate* nonroot controller kernel principal to a separately privileged **source-fixed** broker; no raw Docker socket FD to the controller/worker. Preserve old host J4/J4S until a reviewed replacement exists.
2. Implement complete Docker lifecycle parity (fixed reviewed identity/config only), real bounded stdout/stderr during streaming, timeout and output abort, owned STOP/REMOVE and cleanup recovery in an owner-manual disposable root/private daemon.
3. Enforce durable F5 generation and in-flight CREATE intent/daemon epoch and late-response quiescence. A process-local fake ticket or modeled CLEANUP witness does not meet this condition.
4. Independently verify with L3 and clear image full digest/CVE review. Do not run candidate/model-generated code, enable root Docker workflow on PR, grant production authority or claim `stable_ready` before those requirements.

```text
d2d1_separate_fixed_test_controller=SCOPED_REAL_PASS
d2d2_migration_legacy_to_broker=BLOCK
d2d3a_in_memory_lifecycle=OFFLINE_PASS
d2d3b1_local_kernel_seqpacket_fake_backend=SOURCE_PRESENT_CI_PENDING
root_broker_protocol_integrated=false
real_docker_create_start_attach_stop_remove_exercised=false
real_host_streaming_and_timeout_stop_exercised=false
real_kernel_controller_worker_os_uid_separation_verified=false
real_privileged_scm_rights_prevented=false
durable_generation_create_intents_verified=false
real_late_create_epoch_quiescence_proven=false
independent_l3_attestation_proven=false
worker_isolation_certified=false
untrusted_code_execution_authorized=false
stable_ready=false
decision=BLOCK_AI_ACCEPTANCE
learning_effectiveness=NOT_ESTABLISHED
```

**Generalizable architecture lesson:** separate actual kernel transport observations from backend semantics. A real SO_PEERCRED-verified local packet with a fake lifecycle witness cannot be counted as a successful root-broker Docker operation, a distinct-OS authorization boundary or durable epoch fencing.

## Verified D2D3B1 source/kernel IPC fixture CI and failure learning — 4 Nov 2026

[App Actions #41885018536](https://github.com/lijust/EREI-3.2/actions/runs/41885018536), exact tested SHA `ef25eaee455e5f58aa2658c694659eaf0f979501`, **SUCCESS: 105 offline/unprivileged PASS (35 D2D3B1 +38 D2D3A +14 D2D2 +18 D2A), 0 FAIL**. Actual local Linux `SOCK_SEQPACKET` peer/SCM_RIGHTS denial messages were exchanged, the fake fixed backend completed all four model scenarios, and the test client/server shared one OS PID/UID. **NO root broker, Docker daemon/container, separate controller OS principal, privileged FD, real J4S streaming/STOP, durable F5 or L3 acceptance was exercised**.

First CI runs #41884358783, #41884445260, #41884584381 and diagnostic #41884831002/#41884839221 failed because a strict Python helper required `value is True` but was supplied integer `listener.type & socket.SOCK_SEQPACKET` (5). Server refused before `accept()`; clients timed out. Repaired by comparing the socket flag mask to `socket.SOCK_SEQPACKET` explicitly, added behavioral real kernel socket regression, then verified above green CI. Preserve failed runs as evidence. **Portable design insight:** explicit bool normalization is mandatory when passing OS integer masks into strict boolean safety gates; source inspection alone is insufficient without an end-to-end socket accept/reply test.

`D2D3B1_LOCAL_KERNEL_IPC_FAKE_BACKEND=OFFLINE_SCOPED_PASS`, not a real root Docker broker lifecycle. All F5/OS isolation/full Docker transport/AI/CVE gates FALSE, `decision=BLOCK_AI_ACCEPTANCE`, `learning_effectiveness=NOT_ESTABLISHED`. Next D2D3B2 must integrate source-reviewed *real trusted* private Docker lifecycle with controller OS separation and F5 durable in-flight CREATE before asking the owner to run any privileged manual experiment.
