# EREI Engineering Framework — Core13 D2D3A typed fixed lifecycle and late CREATE model contract

**4 November 2026 | Framework successor to D2D2 Draft #152.**

## Verified evidence lineage

Actual owner [App D2D1 #41872834558](https://github.com/lijust/EREI-3.2/actions/runs/41872834558): SUCCESS for one test-only nonroot `www-data` controller with NoNewPrivs before Python exec, kernel PID/UID/GID, CapEff=0, denied fresh host/private Unix Docker sockets and exact fixed F4C2 root broker CREATE/INSPECT/REMOVE of a never-started image; 78 offline PASS and private daemon cleanup. **NOT legacy J4/J4S migration.**

App [D2D2 PR CI #41874270769](https://github.com/lijust/EREI-3.2/actions/runs/41874270769): 67 offline PASS, actual J4/J4S still use direct host Docker CLI create/inspect/start-attach/stream/timeout/removal; current F4C2 fixed broker only supports one never-started create/delete source test. D2D2 deny-only migration contract BLOCKS all eight operations, including F5 quiescence and L3.

## D2D3A reviewable state-machine specification

App: `tools/core13_j5_04f4d2d3a_typed_fixed_lifecycle_model.py`. It is a **pure offline in-memory typed prototype**; PR tests may exercise it without Docker, sudo, sockets, subprocess, candidate/model/user code or external privileges. Exact reviewed D2D2 Git blob `7db6499e83d953d31d5a7c635888d3d45cd8e875` and denial matrix must match before running a source-review demo. `authorize()` categorically blocks every caller and all operations, including valid source-fixed ones. Do not wire the prototype to actual untrusted-execution control paths.

**Reviewed immutable names:** exact test-only controller principal string, fixed intent and fixed object identity; one integer generation, initially open acceptance, one CREATE in flight at most. This is **not** Linux `SO_PEERCRED` authentication or a Docker server authorization interface.

**Transition policy:**
- `READY → CREATE_IN_FLIGHT` only on an open generation, exact principal/intent and no pending CREATE.
- Success callback for the one fixed object transitions to `CREATED` only while acceptance remains open; unknown, duplicate, contradictory or other-generation callback is `UNRESOLVED` and must prohibit rotation, not silently erase a possible orphan Docker container.
- If the accept window closes while CREATE is in flight, a matching subsequent successful CREATE must transition **`LATE_CREATE_QUARANTINED → REMOVAL_REQUIRED`**, never START or silently accept. An exact removal witness is required before `REMOVED`. Even a clean exit always requires owned cleanup.
- `CREATED → RUNNING` records a fixed deadline **1–15 logical ticks**; output ingestion counts bytes, retains stdout maximum **4,096**, retains no stderr content and caps stderr **2,048**; excess output or deadline requires STOP. One chunk cannot exceed 8,192. **No real subprocess/Docker lifecycle occurs**; integer logical ticks are not wall-clock or host OS evidence.
- `STOP_REQUIRED → STOP_PENDING → REMOVAL_REQUIRED` requires a caller-provided stop witness, then separately an exact owned-removal witness. Witness boolean in offline model is not independent kernel/Docker attestation.
- `stop_accepting` must fail closed on quarantined state and create stop/removal obligations for ongoing tasks; quiescence requires window closed, no in-flight CREATE, unresolved callback, stop, owned resource or cleanup obligation, then only allows `rotate_generation`.
- Source-only receipt exposes sanitized fixed labels, counts and explicit false global acceptance gates. Streaming payload, mutable image/command/endpoint and Docker secrets must not be emitted.

**Counterexample conditions for the test suite:** late successful CREATE after accept window closure, unknown CREATE ID, duplicate CREATE callback, stale generation, wrong principal/intent, stdout and stderr overflow **during ingestion**, exact timeout, non-monotonic tick, missing stop/removal witness, attempt to rotate with unresolved obligation and attempt to execute candidate code. Every one must fail closed without granting operation.

### Evidence ceiling and follow-ups

An offline `PASS` can show only deterministic Python transition behavior. It **cannot** establish a real typed broker protocol, actual Docker START/ATTACH, subprocess streaming/stop/cleanup, durable SQLite intent journals, broker process crash recovery, daemon generation binding, in-flight late CREATE quiescence, independent L3, controller transport exclusivity, candidate isolation or current full-image digest/CVE clearance.

**D2D3B/F5 next:** implement a narrow source-fixed trusted full lifecycle inside the approved **private disposable Docker broker** using kernel controller peer credentials, bounded actual output streaming, exact source-defined image/config and owned cleanup, plus persistent generation/intent fence. A correct offline model is input for this implementation, not security acceptance. Host J4/J4S direct Docker and its privileges must not be changed or repurposed until a separately reviewed migration proves operation parity. Any privileged Docker manual test remains owner-dispatched exact branch and no AI candidate code executes. L3 independent verification + image CVE review stay hard blockers.

```text
d2d1_fixed_controller_broker=SCOPED_REAL_PASS
d2d2_j4_j4s_migration=BLOCK
d2d3a_offline_typed_state_machine=SOURCE_READY_PENDING_CI
live_docker_broker_lifecycle_implemented=false
real_start_attach_stream_executed=false
real_timeout_stop_verified=false
real_late_create_epoch_fenced=false
durable_generation_intents_verified=false
real_owned_cleanup_independently_verified=false
legacy_j4_j4s_host_docker_cli_removed=false
controller_host_docker_authority_removed=false
broker_transport_exclusivity_verified=false
worker_isolation_certified=false
independently_verified=false
untrusted_code_execution_authorized=false
stable_ready=false
decision=BLOCK_AI_ACCEPTANCE
learning_effectiveness=NOT_ESTABLISHED
```

**Reusable architecture principle:** model the partial CREATE response and pending cleanup obligations explicitly before claiming an epoch is quiescent, but never conflate test-harness booleans with independently measured durable/broker/OS facts.

## D2D3A audited source-only tests — 4 Nov 2026

[App Actions #41881110485](https://github.com/lijust/EREI-3.2/actions/runs/41881110485) on code SHA `7e44f377920720f929dbea202c2460ce6087fbea` **SUCCESS, 92 offline PASS / 0 FAIL**: 38 D2D3A source-fixed lifecycle model +14 D2D2 actual J4/J4S migration-denial +22 D2D1 fixed separate-controller source +18 D2A unconditional deny. Tests cover late CREATE result after accept closes, unknown/duplicate callback quarantine, stop/removal obligations and rotation denial, 4096 stdout/2048 stderr bounds and simulated logical deadline timeout. No live Docker/root/sockets/process or candidate code ran in D2D3A. D2D3A **OFFLINE SOURCE MODEL PASS ONLY**, not F5 real daemon/process quiescence, real J4S attach/stream/stop or L3. AI and stable gates remain FALSE; `BLOCK_AI_ACCEPTANCE`.
