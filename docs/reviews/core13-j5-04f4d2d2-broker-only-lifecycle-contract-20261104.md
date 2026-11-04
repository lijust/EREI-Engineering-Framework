# EREI Engineering Framework — Core13 D2D2 broker-only real lifecycle migration HOLD contract

**4 November 2026 | Framework successor to D2D1 PR #151.**

## Actual verified input and remaining authority gap

[App D2D1 owner-manual real #41872834558](https://github.com/lijust/EREI-3.2/actions/runs/41872834558), exact reviewed source `6598d18d1dc5a8611865d4a474ec7a3c6a6a239b`: **SUCCESS** for real source-fixed *test-only* separate `www-data` controller with `NoNewPrivs=1` before Python exec, UID/GID/PID/CapEff verified, no inherited socket FDs, EACCES for fresh host/private Unix Docker connections, and only fixed allowed F4C2 root broker IPC `create_fixed` (create/inspect/remove one never-started test container). `nobody` worker and unknown method denied, owned private daemon cleanup passed. 78 source-only PASS, 0 model calls/writes. The privileged supervising GitHub runner and legacy J4/J4S remain able to issue host Docker CLI directly; there is **no production controller migration** yet.

## Source-verified operations needing replacement

Exact reviewed J4/J4S source blobs:
- `tools/core13_j4_known_worker_lifecycle.py`: `0f655d855898bef0d02fdda36602236b76304252`, direct Docker CLI **create, inspect, start --attach, cleanup rm** and subprocess state/timeout handling.
- `tools/core13_j4s_streaming_fixed_worker.py`: `42e4c879fc7a0b82c963838eb862ade8d6ac8531`, **subprocess.Popen(["docker","start","--attach",cid])**, fixed trusted streaming with output threshold, timeout and cleanup.
- `tools/core13_j5_04f4c2_controller_fixed_create_broker.py`: `499b7f07d5d0fd9d49e61a8e75124e68b202f0b2`, only `create_fixed` for **never-started container, immediate inspect/remove**, with fixed principal check; no general start/attach streaming or stop/recovery contract.
- `tools/core13_j5_04f4d2d1_separate_controller_fixed_broker.py`: `d972be45f43cf16389b1e2839848f52bf43382b9`, restricted *test-only* controller with broker-only fixed operation, not installed into J4/J4S.

New App `tools/core13_j5_04f4d2d2_broker_only_lifecycle_migration_contract.py`, source-pinned review and migration matrix, unprivileged source-only tests plus PR CI. New `authorize()` **never grants capabilities**. All source-bound operations remain `BLOCK`:

| Required future broker operation | Existing fixed F4C2 coverage | D2D2 decision |
|---|---|---|
| CREATE intent / exact owned identity | Fixed never-started CREATE and immediate removal only | BLOCK |
| INSPECT lifecycle state | Internal fixed identity only | BLOCK |
| START/ATTACH stream | None | BLOCK |
| STREAM cap / timeout | None | BLOCK |
| STOP and owned cleanup/recovery | Fixed create/delete test only | BLOCK |
| F5 daemon epoch + in-flight late CREATE quiescence | Not bound to broker | BLOCK |
| L3 independent review | Not bound to broker | BLOCK |

**Required follow-up architectural work:** implement a tested *typed* broker lifecycle strictly for source-fixed trusted code, with kernel-verified controller OS principal, no raw Docker FD/host CLI in restricted controller; enforce immutable source-defined image, exact owned container identity, output and timeout caps, durable generation fence and quiescent cancellation across late CREATE, cleanup verification and independent L3 verifier. Never reinterpret success of F4C2's `create_fixed` as equivalence to full J4/J4S lifecycle. No arbitrary model/user code and no Docker image start under these Draft changes. PR CI remains offline only; any root-private Docker run requires explicit user manual review and dispatch. Docker image full digest/current SBOM CVE approval still missing.

**Invariant:** `old_j4_j4s_host_docker_cli_removed=false`, `new_broker_supports_start_attach=false`, `new_broker_supports_host_streaming=false`, `new_broker_supports_full_lifecycle_inspect_cleanup=false`, `new_broker_late_create_epoch_quiescence=false`, `controller_host_docker_permissions_removed=false`, `restricted_worker_arbitrary_code_isolated=false`, `independently_verified=false`, `untrusted_code_execution_authorized=false`, `stable_ready=false`, `decision=BLOCK_AI_ACCEPTANCE`, `learning_effectiveness=NOT_ESTABLISHED`.

**Reusable engineering lesson:** isolate controller OS authority **and** match all required lifecycle capabilities before migration. A successful broker-only fixed CREATE/REMOVE toy is not a tested substitute for actual streaming, cancellation, cleanup or generation quiescence.
