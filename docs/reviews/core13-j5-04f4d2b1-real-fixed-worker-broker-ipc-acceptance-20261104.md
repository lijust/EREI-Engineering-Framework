# Core13 J5-04F4D2B1 — actual separate-UID trusted worker / F4C2 broker acceptance contract

**4 November 2026 · Framework stacked on D2A #146.**

## Evidence lineage

Owner-manual [D1C actual run #41810374448](https://github.com/lijust/EREI-3.2/actions/runs/41810374448) completed SUCCESS and 85 offline PASS, for exactly one trusted fixed J4S Python container process (net/IPC/PID/mount namespace separation, zero open socket FDs, two known Unix Docker paths absent at snapshot, exact cleanup). This is **not** a global worker isolation certificate. D2A [#41811139884](https://github.com/lijust/EREI-3.2/actions/runs/41811139884) passed 104 offline source denial tests, recording existing F4C2 controller-only fixed broker and legacy J4/J4S direct host Docker CLI authority. F4C3C real #41737838052 separately confirmed post-exec SCM_RIGHTS Docker FD transfer is possible into a restricted process.

## D2B1 new executable scope

App implementation tools/core13_j5_04f4d2b1_real_restricted_worker_fixed_broker_ipc.py uses **the existing F4C2 root broker**, private disposable daemon, immutable never-started fixed container, kernel credential checks and cleanup. New code launches **one real separate restricted-UID source-fixed OS worker** on a reviewed disposable Linux GitHub runner under explicit owner-only workflow_dispatch.

- Require reviewed D2A policy, exact old reviewed J4/J4S source and host Docker endpoint preflight, then create an owned disposable rootful secondary Docker daemon. The private Docker Unix socket stays **root-owned 0600**.
- Start the existing F4C2 root broker under its fixed immutable config. It accepts only one controller identity and the source-fixed create operation; worker identity must be rejected.
- New separate restricted worker runs fixed Python code, verifies actual UID/GID and primary groups, checks for zero inherited socket FDs before first IPC, connects to a controller-owned Unix IPC socket and verifies the **kernel controller SO_PEERCRED PID/UID/GID**.
- Controller receives exact fixed worker-ready message, verifies kernel restricted worker UID/GID and trusted source/pid from procfs and sends only fixed test request. The worker checks broker peer's root UID/GID and fixed PID, requests create_fixed and **must receive DENIED_PRINCIPAL**.
- The same worker attempts fresh connects to protected private root Docker socket and host Docker socket. Both must return **EACCES**; unknown response or connection success blocks the test. This is not a test of every possible Docker endpoint or post-exec FD transfer.
- Controller separately attempts invalid RPC (DENIED_OP) and exact allowed create_fixed, expecting **one never-started container created and deleted by existing F4C2 broker**. Verify empty private inventory, cleanup both broker and owned secondary daemon and preserve host Docker baseline.
- Never execute model/user-generated code, never start the immutable Python Docker image. CI on PR is **offline only**. Real privileged run requires explicit owner, branch and reviewed disposable runner.

## What scoped success can prove

| Evidence | Scope after real success | Not established |
|---|---|---|
| Distinct OS principals | Actual source-fixed restricted worker vs controller vs root broker | Future arbitrary candidate work |
| Controller IPC | Exact kernel peer and fixed message sequence | Host controller's raw Docker privilege removed |
| Restricted broker RPC | Fixed mutation denied to actual worker | Unknown IPC methods, SCM_RIGHTS transfer paths |
| Fresh Docker Unix sockets | Actual worker EACCES on two exact sockets | Alternate Unix, TCP/TLS/SSH, endpoint changes |
| Broker authorized test | Never-started source-fixed container CREATE/inspect/delete | F5 generation/quiescence and late CREATE |
| Worker initial FDs | No inherited socket FD at spawn snapshot | Lifetime FD delivery and process injection |

**D2C** must attack the SAME real worker process: controlled post-exec SCM_RIGHTS from all permitted peers, inherited FDs, other Unix/TCP/SSH Docker endpoints, group and sudo/root escalation and lifetime FD/inventory evidence. **D2D** must replace direct host Docker CLI authority for any future untrusted execution path, bind independent F5 epoch/in-flight CREATE quiescence and L3 independent verifier.

User-supplied Docker Scout screenshot reported 34 issues in locally inspected python:3.12-slim; the full immutable digest and current CVE/SBOM policy remain unverified. An exact digest is not vulnerability remediation. No untrusted container image code is authorized at D2B1.

All runtime/global gates remain FALSE: actual_worker_broker_exclusive_enforced, actual_controller_host_docker_authority_removed, actual_worker_no_possible_scm_rights_transfer_attested, actual_worker_all_alternative_docker_endpoints_denied, worker_isolation_certified, creation_quiescence_barrier_proven, independently_verified, untrusted_code_execution_authorized. Decision BLOCK_AI_ACCEPTANCE; learning_effectiveness NOT_ESTABLISHED.

**Reusable engineering lesson:** show authorization denial on the actual distinct restricted worker and verify both sides of kernel IPC, not only the source of a broker or an auxiliary synthetic process.

## D2B1 code/contract CI verified — no live worker yet

[App #41815627227](https://github.com/lijust/EREI-3.2/actions/runs/41815627227) **SUCCESS**: **81 offline PASS / 0 FAIL** (20 D2B1, 18 D2A, 22 F4C2, 21 F4C3C); privileged real private Docker worker+root broker test **SKIPPED** on PR. Only source/contract tests completed. The distinct UID worker's live PID, denied broker request and fresh Docker EACCES remain **unobserved** until user-reviewed owner-only manual run. D2C/F5/L3/image CVE/untrusted code gate all remain BLOCKED.
