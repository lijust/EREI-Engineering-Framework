# Core13 J5-F4C3D1C — actual trusted J4S process IPC namespace and known raw socket boundary

**4 November 2026 · Framework acceptance contract stacked on F4C3D1B Framework Draft #144.**

## Confirmed prior actual in-container process observation

Owner-manual [App Actions #41742253271](https://github.com/lijust/EREI-3.2/actions/runs/41742253271), source `bab1535a488628602d7a94c9f7fc84fd34ae8d25`, actual J4S fixed trusted Python sleeper observed under host `/proc/PID`: ephemeral PID 2331, UID/GID=65534, effective Linux capabilities zero, `NoNewPrivs=1`, network namespace separate from host, FD type snapshot **0 sockets, 2 pipes, 1 other**. Original fixed J4S timeout/forced container removal and absence passed; 72 offline PASS. This is one source-fixed container process, **not** a production untrusted worker.

A different [F4C3C real run #41737838052](https://github.com/lijust/EREI-3.2/actions/runs/41737838052) already proved an existing Docker FD can be sent to a distinct restricted child over Linux `SCM_RIGHTS` after exec. Thus no-FD-at-start and absence of currently open FDs cannot prove no future acquisition.

## F4C3D1C contract

Extend the actual approved J4S fixed `timeout` case with **one more read-only inspection of the SAME PID** observed by D1B, not a synthetic new worker and not any model-generated code. Root observer is approved only during owner-explicit manual run on an ephemeral GitHub Linux worker; normal PR CI performs no Docker or root steps.

1. Confirm exact D0 source Git blobs, immutable full image digest, case `timeout`, exact source-fixed Python command, unique CID/label and original Docker security flags. Existing J4S remains the sole lifecycle owner; D1C may only call fixed `docker --host unix:///var/run/docker.sock container inspect` on that CID plus read matching `/proc/PID` kernel files.
2. Independently double-confirm same *running* CID + process PID before/after namespace and descriptor sampling. Unexpected image, label, command, PID, UID or container status is HOLD.
3. Compare `/proc/<actual PID>/ns/net`, `ipc`, `pid`, `mnt` to host `/proc/1/ns`. Require each distinct. This measures kernel namespace IDs, not all security boundaries or user namespace.
4. Inspect `/proc/<actual PID>/fd` counts by socket/pipe/other types only. For the fixed trusted sleeper, **zero open socket FDs** at that snapshot is an acceptance predicate, not a proof that future sockets cannot be opened or received via `SCM_RIGHTS`.
5. Check only two **known Unix Docker socket locations** inside actual running process's root: `/var/run/docker.sock`, `/run/docker.sock`. Require absent at sample time. Do not claim exhaustive Docker Unix aliases, TCP/TLS, SSH, privileged host controller/broker access or later transfer denial.
6. Read `/proc/<pid>/cgroup` only to verify it is readable and bounded. Do **not** infer exact cgroup ownership/isolation from textual path, and do not emit raw cgroup/FD/env/mount targets. Keep root helper fixed code, no user arguments other than exact CID and PID already source-bound by D1B.
7. Require original J4S `TIMEOUT_STOPPED` and exact forced cleanup, no labeled container remains, unmodified host Docker baseline; no candidate/model calls or project writes. All output fixed/sanitized, root source-generated and thus **not independent L3 evidence**.

A successful live test can be recorded as `F4C3D1C_SCOPED_REAL_FIXED_PROCESS_IPC_NAMESPACES_AND_KNOWN_SOCKET_SNAPSHOT=PASS` only. All broader `worker_isolation_certified`, `worker_raw_docker_socket_paths_exhaustively_excluded`, `worker_ipc_namespace_all_capability_transfers_denied`, `actual_worker_all_docker_endpoints_denied`, `exclusive_transport_owner_attested`, `creation_quiescence_barrier_proven`, `independently_verified` and `untrusted_code_execution_authorized` remain FALSE; `decision=BLOCK_AI_ACCEPTANCE`.

## Remaining architecture versus diagnostics

After D1C, **prioritize D2 engineering and F5**, not indefinite observations of the same trusted sleeper. D2 must create a real restricted Worker OS principal and broker-only Docker control, constrain inherited/SCM_RIGHTS capabilities and all alternate transports, then attempt adversarial bypasses using scoped test workloads. F5 must provide in-flight/late CREATE drain and epoch fencing; L3 must independently attest evidence.

The user supplied Docker Scout screenshot reporting **34 vulnerabilities** in local `python:3.12-slim`, with a truncated digest prefix matching the fixed image used for these trusted tests. This is a separate image risk requiring current full-digest SBOM/CVE triage and acceptable remediation/exception before any untrusted code execution; fixed digest alone is not a vulnerability remediation.

**Generalizable lesson:** distinguish snapshot FDs, known-socket mount-root paths, namespace separation, IPC FD delivery possibilities and future broker-exclusive transport. Every security certificate needs live exact-identity denial evidence and independent review, not a green synthetic or fixed-sleeper test.

## D1C implementation / offline CI checkpoint

[App Actions #41742982156](https://github.com/lijust/EREI-3.2/actions/runs/41742982156) completed **SUCCESS**: **24 D1C +23 D1B +15 D1A +13 D0 = 75 offline PASS/0 FAIL**; privileged real Docker owner-manual job **SKIPPED** in PR. No D1C actual namespace/socket snapshot is certified by this PR CI result. D1B owner-manual #41742253271 remains the last confirmed actual fixed Python process observation. D1C code-only tests and root-helper contract are documented without promoting containment, independent L3, AI or image CVE assurances.

## Verified F4C3D1C live FAILURE and diagnostic containment — 4 Nov 2026

Owner-dispatched [App Actions #41803457914](https://github.com/lijust/EREI-3.2/actions/runs/41803457914) at App SHA `0bde11dbf1967536aa068b08569b496be0b56c14`: root real Docker job **FAILED**, 75 offline tests PASS. Actual application report returned `J4S_TIMEOUT_OR_CLEANUP_UNVERIFIED` as a **generic wrapped failure**, not proof of a specific underlying container cleanup failure. The D1C real namespace/known-socket check was **NOT VERIFIED**.

Static review identified a plausible overly strict actual-container-inspect predicate requiring `Mounts==[]`, even though original fixed J4 creates a bounded `--tmpfs=/tmp` mount. The source has been adjusted to allow **only that exact tmpfs mount or no listed mounts**, never bind or volumes or other destinations, while preserving nonroot/caps/readonly/no-network/exact CID/label/PID identity. Pure extracted predicate behavior controls added. Crucially root fixed failure exit statuses are now translated to **sanitized allowlisted stage reasons** and retained past D1B's worker-thread guard while original trusted J4S lifecycle cleanup continues. This makes a follow-up manual run diagnostically meaningful without disclosing private paths or permitting any untrusted code.

Do not promote a previous green offline CI into a live success. A **new passing source-head CI + separately owner-authorized real manual workflow** is required. D1B actual fixed trusted Python observation remains scoped PASS #41742253271; D1C live remains NOT VERIFIED; all D2/F5/L3/global worker isolation and Docker image vulnerability policy stay BLOCKED.

## New repaired-source CI confirmed

[App Actions #41804204660](https://github.com/lijust/EREI-3.2/actions/runs/41804204660) **SUCCESS** after the source repair: 29 D1C + 23 D1B + 15 D1A + 13 D0 = **80 offline PASS, zero FAIL**. Actual Docker live job SKIPPED on pull_request. This validates updated pure-source identity acceptance tests (empty or one fixed /tmp tmpfs, no bind/volume/host network/root user), and fixed allowlisted root failure-stage preservation without exposing sensitive data. It does **not** establish that the earlier live failure was definitely caused by the tmpfs predicate or that real D1C has passed. Owner-reviewed manual Docker rerun still required for a scoped real conclusion; all general worker, Docker CVE, F5, L3 and AI acceptance blocks remain.

## D1C owner-manual failure #41809623732 and reusable container-root symlink correction — 4 Nov 2026

[App Actions #41809623732](https://github.com/lijust/EREI-3.2/actions/runs/41809623732) on source SHA `1e3559324f277ffbead39d8a506ff100828a629d`: **real Docker D1C FAILED** with exact fixed `ROOT_OBSERVER_KNOWN_DOCKER_PATH_FOUND`; **80 offline PASS**. This diagnostic does not show that an actual raw Docker socket was mounted or reachable in the sampled trusted container. The old root helper did a host-side `Path("/proc/<pid>/root/var/run/docker.sock").exists()`, which risks following Debian `/var/run -> /run` **absolute** symlinks against host `/run/docker.sock`; the result may be a false positive. This was a source-level path-resolution flaw, not verified exploitation of the in-container process.

**Narrow repair:** replace the unsafe traversal with direct **non-following `lstat`** on container-root `run/docker.sock`; separately inspect literal `var/run` symlink text without following it, allowing only exact `/run` or `../run` for the fixed trusted image; when `var/run` is a real directory check its distinct docker.sock via `lstat`; reject every other alias/file/socket, uncertain permission and non-directory root. Never weaken the exact immutable image/CID/label/PID/UID, zero caps, NoNewPrivs, four namespace and no-open-socket checks. Only the unchanged original J4S trusted fixed timeout can execute; no candidate or model code.

[App PR CI #41809945369](https://github.com/lijust/EREI-3.2/actions/runs/41809945369) **SUCCESS: 34 D1C +23 D1B +15 D1A +13 D0 = 85 offline PASS** including real **pure-function behavior** checks of absolute/relative symlinks, canonical in-container docker.sock positives, malicious aliases and directories. The privileged real Docker job was **SKIPPED**; corrected source needs a *new user-authorized manual real Docker run*. Even a future scoped D1C PASS must not imply all socket aliases/SCM_RIGHTS/TCP/SSH endpoints are blocked, production untrusted worker confinement, image CVE policy, F5 or independent L3.

**Framework lesson:** a root observer does not automatically inherit the observed process's mount-root symlink resolution. A check that looks like `/proc/PID/root/path` can escape the intended root on absolute symlink traversal. Validate physical path lookup semantics with positive and negative file-system tests and retain one sampled process/one container CID/one immutable image scope. `decision=BLOCK_AI_ACCEPTANCE`, `learning_effectiveness=NOT_ESTABLISHED`.

## D1C real result, strictly scoped — 4 November 2026

Owner manually triggered actual [App Actions #41810374448](https://github.com/lijust/EREI-3.2/actions/runs/41810374448), exact App source SHA `5a0d1af4d5fee66dc6db6cfb508baee25de11187`: **both actual Docker and offline jobs SUCCESS**. Original J4S fixed trusted Python sleeper had correct running CID/PID identity, four namespace link identities (IPC, PID, mount, network) distinct from host, **0 open socket FDs, 2 pipes, 1 other FD** at snapshot, two known Docker Unix socket paths absent using the corrected no-symlink-traversal check, fixed timeout and exact owned container removal verified; **85 offline PASS / 0 FAIL** (34 D1C+23 D1B+15 D1A+13 D0). Model calls and project writes 0.

**This qualifies only `D1C_ACTUAL_FIXED_TRUSTED_WORKER_IPC_NAMESPACE_FD_SNAPSHOT=SCOPED_PASS`.** It does NOT establish deployed AI/untrusted-worker process isolation, impossibility of later root→restricted `SCM_RIGHTS` descriptor injection, complete alternate Docker Unix/TCP/TLS/SSH endpoint denial, independent L3 verifier, F5 daemon generation/in-flight CREATE quiescence or Docker image CVE security. The source-generated helper is not independent. Keep `worker_isolation_certified=false`, `exclusive_transport_owner_attested=false`, `creation_quiescence_barrier_proven=false`, `untrusted_code_execution_authorized=false`, `independently_verified=false`, `decision=BLOCK_AI_ACCEPTANCE`.

Earlier D1C failed live #41803457914 and #41809623732 stay in the audit history. Valid D1C scoped real evidence now exists; next implementation MUST prioritize **D2 broker-restricted actual worker authority** and its adversarial negative controls rather than repeating diagnostic snapshots.
