# EREI Engineering Framework — Core13 D2D3B2B0 Docker image and F5 admission contract

**5 November 2026 · Framework staged successor to D2D3B2A Draft #155.**

## Verified upstream

[App D2D3B2A PR-head #41887446672](https://github.com/lijust/EREI-3.2/actions/runs/41887446672), reviewed source `15dfeae6890ba604948da21276118cf6cc032a78`: **119 unprivileged PASS**, genuinely ran/reaped source-fixed trusted Linux host Python processes with bounded stdout, no stderr retention, and monotonic timeout. B2A was NOT Docker container execution; `late_create` was an in-memory fake. Owner D2D1 #41872834558 separately proved a scoped real new restricted controller and root F4C2 broker for a **never-started** immutable test container; old J4/J4S host Docker direct CLI remains.

## D2D3B2B0 exact-source findings / blockers

App reads exact source Git blobs:
- `tools/core13_j5_04f4d2d3b2a_fixed_host_stream_broker.py` blob `f825d2cc6fa11f876d9c6a2196cac94fbc75e9e8`.
- `tools/core13_j5_04f4c2_controller_fixed_create_broker.py` blob `499b7f07d5d0fd9d49e61a8e75124e68b202f0b2`.
- `tools/core13_j5_04f3_local_sqlite_generation_fence.py` blob `ec4cd704b8865193761cdb836c68d58d6f929f17`.

**A. Immutable digest ≠ accepted image security.** Actual F4C2 fixed image is `python@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159`. An earlier local Docker Scout screenshot mentioned CVEs, but the precise current full-digest scan and SBOM/OS-vs-library findings are **not independently verified**. No image start is permitted under the new gate until image risk, full digest, runtime and external verifier review are established.

**B. Legacy root broker filesystem socket mode 0666.** The F4C2 source literal `os.chmod(sock_path,0o666)` still exists. Kernel SO_PEERCRED restricts actual operations, so this does not itself prove bypass; future separately restricted broker must instead use an owned private socket (0600 or explicitly reviewed 0660/group) plus strict kernel peer authentication, FD ancestry and alternate transport denial.

**C. F5 not truly quiescent.** The optional local SQLite `submit_static_test_only` and `seal()` do not prevent foreign direct Docker sockets or delayed async CREATE. The source explicitly records `late_async_create_excluded=false`, `creation_quiescence_barrier_proven=false`. A real root broker must atomically bind each create intent to durable generation/daemon identity before transport and prove all in-flight/late CREATE outcomes drained or owned cleanup verified before generation rotation. Independent L3 verifier must attest the whole transport, not just source assertions.

**D. J4/J4S operation parity incomplete.** No Docker START/ATTACH/STREAM/STOP in current F4C2, and D2D3B2A only proves trusted host subprocess behavior. Old privileged runner/controller unchanged.

## B2B0 implementation

App `tools/core13_j5_04f4d2d3b2b0_image_f5_admission_hold.py`, unprivileged unit tests and dry-only PR CI. The module pins source blobs and examines risk conditions without Docker, socket, subprocess, network or root operation. Optional provided scanner-claim JSON uses exact digest and strict schema `core13-fixed-image-scan-input-v1` (source-asserted scanner, UTC freshness, SBOM hash shape, counts). All external input is **UNTRUSTED** and self-asserted even if all counts are zero; independent provenance is always `false` and Docker START routing always blocked. `authorize()` unconditionally denies any principal/operation.

**Additional owner-only registry image scan workflow** `.github/workflows/core13-j5-04f4d2d3b2b0-pinned-image-remote-trivy-manual-hold.yml`: owner `workflow_dispatch` on an exact branch, GitHub Linux runner, source preflight remains blocked. It runs SHA-pinned Trivy Action `ed142fd0673e97e23eac54620cfb913e5ce36c25` with `TRIVY_IMAGE_SRC=remote` to obtain a JSON vulnerability report and CycloneDX SBOM for the fixed exact remote registry image. It does not use Docker CLI, start a container or invoke user/model code; stores raw artifacts for review with SHA256s and severity counts. GitHub remote scan/registry acquisition may fail and **must fail closed**; raw scanner output is **not L3 independent attestation** or permission to START. This workflow is manual; source PR CI never runs it.

### B2B1 requirements and assurance ceiling

Before constructing/running a root/private Docker full-lifecycle experimental broker: security review of scanner DB, image digest and actual package vulnerabilities; source-fixed image/config/entrypoint only; nonworld writable broker socket, distinct nonroot controller kernel SO_PEERCRED, no privileged FD capability transfers, actual Docker CREATE/INSPECT/START/ATTACH stream/STOP/REMOVE with time and memory/output caps; durable F5 in-flight CREATE/daemon epoch plus late-create drain/recovery; independent L3 attestation; and no migration of old J4/J4S until operation parity is proved.

**No self-asserted JSON, CI green tests, digest pin, prior never-started F4C2 result or nonroot host subprocess test can substitute for those conditions.** Continue to deny arbitrary model/user code. Preserve all historical failures and Draft PRs.

```text
d2d3b2a_fixed_host_process=SCOPED_REAL_NONROOT_PASS
d2d3b2b0_exact_image_f5_source_gate=IMPLEMENTED_PENDING_CI
d2d3b2b0_manual_registry_remote_scan=WORKFLOW_PRESENT_NOT_RUN
docker_image_current_cve_scanned_and_verified=false
docker_image_sbom_independently_attested=false
docker_image_digest_and_cve_accepted=false
docker_broker_socket_least_privilege_enforced=false
docker_broker_durable_f5_intent_integrated=false
docker_broker_real_inflight_create_quiescence_proven=false
docker_broker_late_async_create_excluded=false
docker_broker_start_attach_stream_verified=false
docker_broker_output_limit_and_timeout_verified=false
docker_broker_owned_cleanup_independently_verified=false
controller_direct_host_docker_cli_removed=false
separate_os_controller_broker_transport_exclusive=false
independent_l3_verification_complete=false
untrusted_code_execution_authorized=false
stable_ready=false
decision=BLOCK_AI_ACCEPTANCE
learning_effectiveness=NOT_ESTABLISHED
```

**Reusable lesson:** an immutable image reference, zero-claimed vulnerability document, and in-process/SQLite lock are not sufficient for approved Docker workload execution. Pair **actual scanner provenance + independent image review** with protected IPC/OS controller principals and **durable measured daemon CREATE quiescence**.

## Source-only D2D3B2B0 CI verification — 5 Nov 2026

[App PR-head Actions #41971487203](https://github.com/lijust/EREI-3.2/actions/runs/41971487203), source SHA `13117f3dd2079c179adc2a0c403347d8efe6ad95`, **SUCCESS: 76 offline PASS / 0 FAIL** (30 new B2B0 image/scan-claim/F5 denial tests, 32 B2A actual trusted nonroot host child regression, 14 D2D2 old Docker lifecycle migration denial). Initial #41970909438 failed a static test misinterpreting `subprocess.Popen(` text within source-inspection literal as an executable subprocess; repaired with AST call verification, follow-up CI #41970966154 passed. This was a static test precision error, not a proven Docker bypass. No scanner was launched in the source-only tests and no Docker image was acquired/started. **Separate owner-manual remote Trivy JSON+CycloneDX workflow has NOT RUN**; current image findings remain unknown pending evidence. Runtime/F5/L3/AI gates all HOLD.
