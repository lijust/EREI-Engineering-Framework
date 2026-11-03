# Core13 J5-04E2E1 — Independent Verifier trust-boundary decision record

**2026-11-03 | Draft engineering contract. NOT an acceptance certificate.**

## Verified state and narrow empirical facts

The App repository lijust/EREI-3.2 currently has Draft PRs #255 and #256, stacked after the fixed-Docker CID/cgroup-v2 evidence PRs #253-254. This Framework record captures reusable engineering conclusions without modifying the worker, Oracle, candidate execution gate, or previously reviewed J4 code.

- [App Draft #255](https://github.com/lijust/EREI-3.2/pull/255): one actual separate Linux Python OS process launched from fixed source, with controller-to-child one-shot challenge, SO_PEERCRED on the **same AF_UNIX socket** as the response, PID/UID+boot/start-tick stability. [Actual CI #41592726694](https://github.com/lijust/EREI-3.2/actions/runs/41592726694) Ubuntu 186 PASS, Windows 180 PASS+6 Linux-only skips. This did not execute Docker; real Linux fixture inspected only the trusted test runner's process epoch.
- [App Draft #256](https://github.com/lijust/EREI-3.2/pull/256): same E1 separate process observing an **ACTUAL** pre-reviewed immutable Python J4 container, exact 64-character CID-bound kernel cgroup-v2 member list/subtree. [Actual CI #41593231844](https://github.com/lijust/EREI-3.2/actions/runs/41593231844) all 3 jobs SUCCESS: Ubuntu 204 PASS and Windows 198 PASS+6 Linux-only skips, plus fixed-only rootful secondary dockerd ephemeral Ubuntu. The same-UID controller and distinct Linux observer process each saw exactly **1 CID cgroup directory and 1 nonroot member**, identical canonical SHA256 digests; exact CID owned cleanup occurred **BEFORE** secondary daemon stop, known init PID gone, primary Docker unchanged. **No container daemon SIGKILL in #256.**
- After actual evidence, rootful Docker job was made manual-only at App commit 8d1de26aa45d692f0df4692ae19aa0fc84ddbd7a. [Post-change CI #41593363380](https://github.com/lijust/EREI-3.2/actions/runs/41593363380): Windows/Linux offline SUCCESS, rootful job correctly SKIPPED.
- The prior [actual source-reviewed secondary dockerd SIGKILL #252](https://github.com/lijust/EREI-3.2/pull/252) showed the CID cgroup HAS_MEMBERS immediately after daemon death then original path MISSING after restart; Docker reported the known container NOT RUNNING after restart. **MISSING ≠ EMPTY ≠ quiescent**.

**Conclusion:** we have genuine LOCAL independent PID observation and kernel peer identity, but not an independent security principal, independent code/Oracle attestation, bounded full-tree certification, or excluded late asynchronous creates. Consistent data from two same-UID processes is not a security certificate.

## Principal taxonomy — no category promotion by naming

| Level | What is genuinely established | What is NOT established |
|---|---|---|
| L0 in-process | Source-bound function call and local PID/proc information | Process independence or security principal |
| L1 separate PID, SAME UID/HOST **(actual today)** | Kernel SO_PEERCRED peer PID/UID on exact channel, nonce freshness, boot+starttime, bounded same-CID read-only agreement | Independent principal, protected evidence signer, independent trusted code |
| L2 separate UID/user namespace on SAME host **(not tested)** | Additional OS permission isolation only if kernel policy and user-namespace mappings proven | Independence from root/host administrator, kernel compromise, external signing authority |
| L3 separately administered isolation/principal **(REQUIRED, not built)** | Distinct trust authority/credentials not writable by worker/controller, authenticated read-only channel, separately verified provenance | Still does not automatically prove quiescence, child process closure or model efficacy |
| L4 independently attested execution substrate **(optional stronger gate)** | Verified boot/VM/hardware measurement backed by independently managed key/host | Does not replace worker/cgroup race, cancellation and late-create tests |

No code, review note, PR name or nonce may set independent_verifier_attested=true on L0/L1 evidence. A checksum is not a protected signature. Same-UID adversarial controller can read/modify the new local observer source or impersonate it.

## Threat model and source of truth

**Potential adversary:** untrusted model patch or compromised task code may emit arbitrary strings, forge JSON reports, replay nonce observations, manipulate temporary socket names, start other subprocesses, exploit delayed async create races, move/reparent tasks or alter same-user files. A rootful Docker daemon and host admin can additionally affect filesystem/kernel observations. The current fixed-source experiments do NOT execute this adversary.

The independent verifier must possess a separately controlled security principal or host with read-only evidence access and a protected response-signing credential unavailable to the worker/controller. Its executable/source version and provenance must be verified by a trust root that the controller cannot rewrite. Require a unique verifier identity, immutable code measurement and an authenticated channel bound to freshness/nonce/clock/epoch, exact CID, source digest and the distinct verifier principal. Reject replays, wrong-kernel boot, PID reuse, divergent CID, changed cgroup inode, missing signatures, signer restart without audit, UID privilege elevation or unreviewed child code.

A locally generated SHA256 of a cgroup observation must be identified as a **checksum** only. A signature derived from a secret accessible to the controller provides **zero principal separation**.

## Pending-create / late-create quiescence is a separate obligation

A process observer cannot establish that there is no **asynchronous pending CREATE** simply by reading cgroup.procs, scanning twice, or seeing a missing cgroup path.

An admissible creation barrier will require an exclusive, source-reviewed create-transport owner (no bypass paths), durable write-ahead records for every in-flight create before the call is submitted, generation and fencing tokens tied to the exact runtime incarnation, an authenticated intake disable that prevents new creation for the generation, an independently witnessed drain of all pending calls/retries or their explicit permanent quarantine, and reconciliation across daemon restarts. Any uncertain create, delayed completion, partial journal or lost fence keeps TERMINAL_HELD. **No existing runtime source has proved this exclusive barrier.**

Required negative control: show a pending create admitted before intake close can materialize AFTER two empty Docker/container scans. The verifier must prevent a success certificate in that case. Do NOT implement this by executing hostile code, scanning foreign Docker daemons or stopping the host's primary Docker; use a disposable fixed-only isolated runtime with explicit permissions.

## Acceptance criteria for next independent-verifier phase

- **Trust-root separation:** external principal/host/credential controls documented and testable, with signer/verifier private key inaccessible to controller, worker, CI test inputs and model.
- **Evidence origin:** signed receipt binds verified source, exact full CID/name/image/label, dedicated daemon and process epoch, host boot/cgroup inode, challenge and monotonic generation.
- **Read-only verifier:** cannot create/exec user code, mutate cgroupfs, stop a foreign daemon, overwrite Oracle or bless a candidate. Timeouts, interruptions, zero/partial records or foreign ID always HOLD.
- **Host process accounting:** bounded exact kernel CID cgroup subtree plus actual known shims/ancestors/descendant-vs-parent escapes and correct child UID/namespace handling; do not infer full coverage from a one-member fixture or a missing path.
- **Quiescence barrier:** exclusive runtime API producer authority and durable in-flight create fence proven with a *real deterministic late-create adversarial fixture*, including crash/restart, reconnect, retries and protocol ambiguity.
- **Independent model patch oracle:** separate hidden/prospective behavioral evaluation not disclosed to candidate. Passing internal fixture tests does not establish learning effectiveness or Stable readiness.
- **Auditable outputs:** no positive outcome unless all relevant gates independently PASS; a passed L1 peer test may never override a blocked L3 principal, blocked quiescence or blocked Oracle.

## Execution staging without conflict

**Now:** retain all App PRs Draft/unmerged and the existing fixed-only CI while developing a separate read-only L3 verifier identity/provenance contract in this Framework; no changes to the worker execution gate or AI learning approval.

**Then:** test the externally protected principal and its signature using two separately administered environments and intentional impersonation/replay attempts; only after verified protection, bind exact-CID/kernel evidence. In parallel implement a separate create-intake broker/fencing ledger, without changing production worker paths until exclusive transport is independently verified.

**Before any acceptance:** run fixed-only real negative controls for delayed creates, orphan/shim processes, daemon restart and verifier compromise; perform independent source review; record exact HEAD, CI run, genuine host boundary and signature authority. Do NOT use a one-run PASS as a Stable certificate.

Permanent policy: worker_isolation_certified=false; untrusted_code_execution_authorized=false; independent_model_patch_oracle_established=false; independent_verifier_attested=false; creation_quiescence_barrier_proven=false; late_create_excluded=false; independently_verified=false; decision=BLOCK_AI_ACCEPTANCE; learning_effectiveness=NOT_ESTABLISHED.
