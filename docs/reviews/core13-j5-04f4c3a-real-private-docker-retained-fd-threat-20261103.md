# Core13 F4C3A — retained pre-authorized Docker FD counterexample contract

**3 November 2026 | Framework scope after App F4C2 manual Docker success #41683597910.**

## Prior milestone and remaining false assurance

[App real Actions #41683597910](https://github.com/lijust/EREI-3.2/actions/runs/41683597910) at source SHA `f7bde5fddf13b8c926692589890ff271e9175825`: controller-only fixed immutable Docker CREATE/inspect/delete via owned root broker **PASS**; restricted worker denied, fixed config and empty private inventory verified, privileged job PASS + offline **120 PASS**. Only bounded broker capability RPC was tested. Neither controller privilege separation nor exclusive worker/daemon transports are proved; the root broker and runner still hold broad authority. F4B fresh-connect EACCES never proved existing FD revocation.

## Exact adversarial counterexample

The source-reviewed App F4C3A test creates one disposable private secondary dockerd with root-owned 0600 socket and does **no Docker mutation**. One exact privileged child opens a single connected private Unix socket, verifies `SO_PEERCRED` for the exact expected daemon PID and root UID, **then drops all supplementary groups and sets restricted UID/GID without closing that FD**. Under restricted credentials, a **new** connection to the same protected socket path must produce OS `EACCES`; the **retained** pre-drop connected FD must be able to issue only immutable `GET /_ping` and receive `200 OK`. A successful run is labeled **`RETAINED_DOCKER_FD_AFTER_UID_DROP_COUNTEREXAMPLE=CONFIRMED`**, not security protection success. Close FD, kill only exact-owned private daemon and verify conventional host Docker baseline. No host API request, candidate code, container creation, project writes or model calls.

PR checks exercise offline code guards and trusted dispatch constraints; only exact owner-branch `workflow_dispatch` runs rootful real Docker. Do not infer privileged Docker behavior from offline CI. Its source-generated real receipt is not an L3 independent verification.

## Threat-model separation

1. **Fresh connect denial**: 0600 Unix pathname + OS principal, proven earlier only for a new `connect()`.
2. **Retained open FD**: capability established before UID drop or chmod can remain usable; F4C3A explicitly checks this on a real private Docker daemon.
3. **Inherited FD across fork/exec**: a distinct boundary requiring source-level `FD_CLOEXEC`, `close_range`, service launcher, and runtime `/proc/*/fd` checks. F4C3A *does not* by itself establish that any real production worker inherited a Docker FD or that inheritance was prevented.
4. **FD passing via `SCM_RIGHTS`**, Docker context and TCP/SSH/alternative Unix aliases: separate adversarial paths; no deny claim without evidence for each supported transport.
5. **Privilege ownership**: a root broker and sudo-capable controller are still broadly privileged even when broker RPC is fixed. Sole service access requires an OS boundary or capability-limited operating account, not just a Python dispatcher allowlist.
6. **F5 in-flight/daemon epoch** and **L3 independent attestation** remain separate final gates, with no AI candidate execution until all required proofs pass.

**Non-promotion flags always false here:** `exclusive_transport_owner_attested`, `external_socket_bypass_denied`, `inherited_or_retained_private_fd_excluded`, `retained_fd_leakage_prevented`, `broker_exclusive_transport_certified`, `worker_isolation_certified`, `creation_quiescence_barrier_proven`, `independently_verified`, `untrusted_code_execution_authorized`; `decision=BLOCK_AI_ACCEPTANCE`, `learning_effectiveness=NOT_ESTABLISHED`.

**Reusable engineering rule:** confirm that a negative test of a new Unix socket connection is not silently promoted to a claim of exclusive transport. Established FDs have their own lifetime and privilege-transfer semantics; test both paths under the same daemon and same restricted principal, and treat a confirmed counterexample as evidence of a boundary the design still needs to close.

## F4C3A implementation and offline evidence — 3 November 2026

App [PR #264](https://github.com/lijust/EREI-3.2/pull/264) and Framework PR #139 are now open as stacked **Draft** PRs. The initial PR CI [#41684378875](https://github.com/lijust/EREI-3.2/actions/runs/41684378875) found one invalid offline test expectation (`SO_PEERCRED` inside the fixed `python -c` child source string, not a standalone argument); corrected without changing live probe logic. App [Actions #41684487897](https://github.com/lijust/EREI-3.2/actions/runs/41684487897) **SUCCESS** with F4C3A 16, F4C2 22, F4C2 root helper 15, F4C1 20, F4B 23 = **96 offline PASS, 0 FAIL**. The privileged real Docker negative control is **SKIPPED** on a PR event, so retained FD against a real private daemon is still **NOT OBSERVED**. A user-authorized owner-only manual run on pinned source is necessary for that scoped counterexample. All broker/global isolation/AI acceptance fields remain FALSE.
