# Core13 J5-F4C3D2A — broker-only worker trust contract and executable authorization denial

**4 November 2026 | Framework Draft stacked on D1C #145.**

## Verified evidence and essential distinction

Owner dispatched actual [App D1C Actions #41810374448](https://github.com/lijust/EREI-3.2/actions/runs/41810374448) on pinned SHA `5a0d1af4d5fee66dc6db6cfb508baee25de11187`, yielding **real Docker SUCCESS** and **85 offline PASS**. One genuine **trusted fixed J4S container Python sleeper** had distinct IPC/PID/mount/net namespaces, zero currently open socket FDs, only 2 pipes + 1 other FD, two known Docker Unix socket paths absent at sample, and original J4S fixed timeout/owned cleanup. **This is not evidence that every future untrusted worker lacks Docker capabilities.** The source-generated root observer is not L3 independent.

Previously [F4C2 App PR #263](https://github.com/lijust/EREI-3.2/pull/263) source-fixed controller-only root Docker broker allowed only a very narrow `create_fixed` against a disposable private daemon, while denying restricted workers. [F4C3C actual Actions #41737838052](https://github.com/lijust/EREI-3.2/actions/runs/41737838052) separately confirmed raw Docker socket capabilities may be transferred via `SCM_RIGHTS` **after exec** to a restricted child. This means neither `close_fds` nor a zero-socket snapshot alone is a lifetime guarantee.

## D2A — authority matrix is a source-bound deny gate, not a deployed security boundary

App module: `tools/core13_j5_04f4d2a_worker_broker_authority_policy.py`. Source-pinned F4C2, F4C1, hostile-deny and D1C plus real J4/J4S (via D0) inspected **without Docker, root privilege, dynamic code or model calls**. Strict unchanged Git source snapshots and AST ensure presence of reviewed F4C2's controller kernel credential binding and deny behaviors. Reject symlink/hardlink replacement and source drift.

Its public `authorize(principal, operation, request)` **denies every operation for every principal**, including controller `create_fixed`. This is a deliberate fail-closed **pre-authorization design gate**, not a generic Docker proxy, runtime principal verifier or a worker launcher. Any source/test green result MUST NOT change `untrusted_code_execution_authorized=false`.

| OS actor | Required final capability boundary | Evidence still needed |
|---|---|---|
| Broker (one dedicated privileged OS principal) | Exclusive owner of root/private-Docker API socket; only controller `SO_PEERCRED` may request reviewed fixed operation | Authenticated broker process, socket inode/daemon epoch, exact RPC + cleanup, no alternate roots |
| Controller (separate trusted UID) | Typed schema validation, fixed job lifecycle; **no** unmediated Docker CLI or raw private/host socket, root/sudo or arbitrary Docker APIs | Actual replacement of legacy J4/J4S direct Docker CLI in new path and adversarial attempts |
| Worker (separate restricted UID) | Only fixed bounded work IPC; no Docker-group membership, socket capability inheritance/SCM_RIGHTS injection, root escalation or alternate Unix/TCP/TLS/SSH transport | Live kernel PID/UID/groups/FD/IPC graph and negative bypass probes in actual new worker launch |
| Independent verifier (separate trusted principal) | Read-only independently governed attestation with authenticated receipts, not controlled by worker/controller | L3 protocol, source/epoch verification and signed/validated evidence |

**Important existing architectural gap:** legacy J4/J4S *trusted host controller* runs `docker create` and `docker start --attach` directly. Passing a fixed test there does **not** establish controller Docker exclusivity. D2 needs a **new, isolated worker path**, not a premature claim that this legacy test route became broker-only.

## Explicit phases / non-overlapping proof obligations

**D2A — this branch:** immutable authority-matrix specification and deny-only tool, source drift checks, offline unit regressions on F4C2 and hostile-deny. Zero Docker execution, zero AI code and zero runtime security certificate.

**D2B — real fixed new restricted worker launcher:** use existing narrow F4C2 broker concepts rather than duplicating a general-purpose Docker proxy. One separate limited worker UID, no supplementary groups, closed child descriptors, no env Docker redirects, fixed task code only, exactly authorized IPC; root broker owns single private daemon socket and checks exact controller `SO_PEERCRED`. The worker must not acquire controller or broker credentials, and no raw Docker descriptor may be passed or received. Owner-explicit reviewed ephemeral Linux Docker test only.

**D2C — attack the actual D2B process graph:** prove denial of fresh private and host Docker socket connects, pre-connected inherited FDs, post-exec `SCM_RIGHTS` from each allowed IPC peer, arbitrary broker RPC, Docker socket aliases and TCP/TLS/SSH endpoints, docker-group membership and accidental sudo privileges. One bypass = `BLOCK`; keep container/daemon cleanup and host baseline forensic evidence. The kernel runtime process must be the **same actual worker** under test, not a standalone proxy test.

**D2D — integration:** migrate prospective (not existing fixed historical) execution to broker-only job lifecycle, bind epoch/owned CREATE intent and late completion to F5 drain before accepting any operation, and independent L3 principal for receipts. Then separately review an actual sandbox image's full digest and current SBOM/CVEs before any candidate/user/model code.

### Keep these distinct gates closed

```text
d2a_source_bound_authority_matrix=IMPLEMENTED
actual_worker_new_launcher_implemented=false
actual_worker_broker_exclusive_enforced=false
actual_worker_no_docker_group_attested=false
actual_worker_no_inherited_docker_fd_attested=false
actual_worker_scm_rights_delivery_denied=false
actual_worker_other_docker_endpoints_denied=false
controller_host_docker_authority_removed=false
in_flight_create_epoch_quiescence_proven=false
worker_isolation_certified=false
independently_verified=false
untrusted_code_execution_authorized=false
decision=BLOCK_AI_ACCEPTANCE
learning_effectiveness=NOT_ESTABLISHED
```

Docker Scout screenshot from user reports **34 vulnerabilities** on a local `python:3.12-slim` with partial hash matching legacy pinned test image; current full digest, actual applicability and remediation are not yet independently established. **Pinned digest != secure image** and no untrusted code is approved. F5 in-flight CREATE quiescence and L3 independently governed verifier remain separate blockers.

**Reusable engineering rule:** distinguish four claims: (1) fixed J4S source contains security flags, (2) a fixed trusted container's Linux namespaces/FDs were observed, (3) the future actual restricted worker cannot reach Docker through *any* allowed peer or alternate transport, (4) untrusted code may safely execute. D2A documents (1) and the historic (2); only future D2B/C + F5/L3 can potentially support (3)/(4).

## D2A App implementation evidence — 4 November 2026

[App GitHub Actions #41811139884](https://github.com/lijust/EREI-3.2/actions/runs/41811139884) at source SHA `506a1fdda2b278019c3f9f3650d92070b1d18f8c` **SUCCESS**: **104 offline PASS, zero FAIL** (18 D2A, 34 D1C, 22 F4C2, 30 J5-04A). Source-only receipt authenticated to exact reviewed source snapshot, contains `existing_f4c2_fixed_broker_controller_only_policy_detected=true`, `existing_j4_and_j4s_host_docker_cli_authority_present=true`, `actual_worker_new_launcher_implemented=false`, `actual_worker_broker_exclusive_enforced=false`, `untrusted_code_execution_authorized=false`, `decision=BLOCK_AI_ACCEPTANCE`. D2A job ran **no real Docker**; this is only a source policy/review checkpoint. D2B actual separate-UID worker/broker and D2C attacks remain unimplemented. The separate image CVE, F5, L3 gates are not promoted.
