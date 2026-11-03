# J5-04F4B — real private Docker socket restricted UID bypass-denial contract

**3 November 2026. Framework Draft stacked on F4A Framework #135. App F4B pending privileged independent run. NO safety or AI acceptance promotion.**

## F3 → F4A → F4B evidence ladder

- **F3:** SQLite durable local admission/generation records; old local token cannot send via the optional adapter after rotate. This is not exclusive Docker transport.
- **F4A:** real Linux AF_UNIX DAC control demonstrates a separate UID cannot make a **new connection** after socket mode switches to owner-only 0600. Counterexample: an FD accepted under mode 0666 can still write after chmod. The bare socket is not Docker.
- **F4B:** reviewed implementation introduces an actual private secondary dockerd and a **real fixed Docker HTTP CREATE** positive control from a restricted UID while socket is temporarily test-open. It then requires exactly EACCES from a fresh CREATE attempt by that UID after owner-only permissions are restored. Checks the conventional primary host socket via **connect only** with no API writes. This provides real platform evidence for one socket/UID boundary **if and only if the manual trusted Actions job completes and evidence is pinned**.

## Required execution constraints

1. Only use existing exact-owned disposable GitHub Ubuntu secondary daemon infrastructure. Do not chmod or send POST to the original host dockerd socket. No model/patch code, no unknown image, no running test container. Created private fixed container must be inspected and removed before daemon stop.
2. Positive control must **succeed** with a restricted Linux UID, show actual Docker CID and peer-bound daemon PID; a denied connect with a 0700 parent directory does not prove socket-specific restriction.
3. Negative control must fail the attempt to establish a **new** direct raw Docker CREATE connection with EACCES while that same daemon/socket inode stays live. If child can connect, the test fails irrespective of the SQLite journal.
4. Restricted child must not have sudo/docker groups or host daemon write access. Check UID/GID and groups; use raw Unix sockets not the context-sensitive Docker CLI. Treat any reachable host socket path as HOLD, without sending a request to it.
5. No privileged execution of arbitrary pull_request code. Actual rootful private dockerd operation is manual-dispatch on exact trusted branch and actor only. Store runner evidence and exact source SHA; PR CI cannot satisfy F4B.
6. If CID is unknown, owned removal fails, daemon identity changes, primary baseline changes or cleanup becomes ambiguous, retain HOLD. Do not delete UNKNOWN admission history or assert no late creates.
7. F4B success does **not** imply complete Docker path enumeration. Explicitly test alternate endpoints, inherited FDs, group memberships and namespace escapes before proposing exclusive transport. Never conflate chmod with revocation of existing connections.

## Gates remain distinct

| Gate | Required evidence | Status |
|---|---|---|
| F4A Linux AF_UNIX permissions | New-connect EACCES with positive control + retained-FD counterexample | Implemented; local result reported, PR static green, no external privileged proof |
| **F4B actual Docker permission attempt** | Private dockerd fixed CREATE positive, restricted EACCES, exact cleanup, primary baseline unchanged | Implementation prepared; manual real run required |
| F4C OS-separated broker | No raw daemon access from restricted worker over any supported transport; sole controller admission | Not built |
| F5 in-flight/daemon generation barrier | Every accepted/queued/partial CREATE accounted, sealed/retired; no possible late emission | Not proven |
| L3 independently administered verifier | Separate principal, measured evidence, protected receipt, independent signer/oracle | Not established |

## Decisions

`exclusive_transport_owner_attested=false`, `external_socket_bypass_denied=false`, `creation_quiescence_barrier_proven=false`, `late_async_create_excluded=false`, `generation_quiescence_certified=false`, `independent_verifier_attested=false`, `worker_isolation_certified=false`, `untrusted_code_execution_authorized=false`, `independently_verified=false`.

`decision=BLOCK_AI_ACCEPTANCE`; `learning_effectiveness=NOT_ESTABLISHED`.

**Reusable engineering rule:** An OS group/ACL boundary must be proven against a real *configured service* under real alternate credentials, with a successful adversarial positive control. Even then, a prevented **new connection** is a smaller claim than exclusive transport ownership, active-request drain, no late CREATE, or safe execution.

## App F4B test status and reusable Python path lesson

The App [Draft #261](https://github.com/lijust/EREI-3.2/pull/261) PR offline CI final [#41633231900](https://github.com/lijust/EREI-3.2/actions/runs/41633231900): **17 F4B PASS, 5 F4A PASS + 2 root-only SKIP, 40 F3 PASS** = **62 PASS, 2 SKIP**. Actual privileged Docker manual job SKIPPED. Prior first [#41632837445](https://github.com/lijust/EREI-3.2/actions/runs/41632837445) had two test failures due an incorrectly strict `type(path) is Path` check (on Linux `Path(...)` produces `PosixPath`). Fixed to `isinstance(path, Path)`; final CI includes isolated immutable child Python source compilation. Keep initial failure history and DO NOT promote from offline green.

Reusable requirement: path-class validation must respect OS-specific `Path` subclasses, but accepting a Path must not replace canonical path traversal checks, no-symlink checks, owner/inode checks, or kernel authority proofs.

## Actual F4B manual run: failure recorded, NOT bypass-denial proof

[App Actions #41638651676](https://github.com/lijust/EREI-3.2/actions/runs/41638651676), 3 November 2026, `workflow_dispatch`, source `a3247ce793636b90e832a72a244b78712d55b09f`: **overall FAILURE**. The offline job passed; the privileged real private dockerd job passed its disposable Linux/host baseline preflight, then probe exited 2 with sanitized `PRIVATE_CONTAINER_REMOVE_UNVERIFIED`. This must remain a HOLD, not be counted as success or negative CREATE denial.

**Review finding:** The F4B cleanup path could overwrite any preceding error (e.g., restricted UID cannot access private socket or positive control did not produce CID) with `PRIVATE_CONTAINER_REMOVE_UNVERIFIED` when no CID was recovered. That code path makes the immediate failure cause ambiguous; the historical report does **not** prove a container was created, removed, left behind, or that the kernel denied a new Docker CREATE. The run's ephemeral runner termination is not independent cleanup certification.

App source now includes a pre-CREATE connect-only positive control plus an explicit sanitized stage and first-failure reason preserved even when cleanup is uncertain; a final cleanup problem remains the top-level denial. Added offline tests for no raw paths/secrets leaked and no acceptance promotion. No privileged automatic retry was enabled. Keep all F4B/F4C/F5/L3 certification fields false pending a new reviewed and explicitly authorized real run.

**Diagnostic fix verification:** [App Actions #41639307722](https://github.com/lijust/EREI-3.2/actions/runs/41639307722) = **65 PASS, 2 root-only SKIP**, including 20 F4B offline guards; real private Docker manual job was skipped. This does not convert the failed actual run #41638651676 into success or establish any live bypass-denial receipt.

## Second live-run negative result and general path-DAC lesson — 3 November 2026

User-dispatched [App Actions #41674697531](https://github.com/lijust/EREI-3.2/actions/runs/41674697531) at App SHA `225d57720616cf29d4bab614cff13effb7db046d`: offline job PASS; privileged actual Docker job FAILURE. The sanitized failure now discriminates `failed_stage=RESTRICTED_POSITIVE_CONNECT`, `first_failure_reason_code=RESTRICTED_POSITIVE_CONNECT_UNVERIFIED`, and cleanup `PRIVATE_CONTAINER_REMOVE_UNVERIFIED`. The positive connect was not proven, so neither Docker HTTP CREATE nor bypass denial may be inferred.

**Generalizable OS principle:** permission on the final Unix socket is not sufficient; every ancestor directory must be searchable by the restricted UID. A 0666 test socket under a 0700 runner ancestor makes the permissive positive control fail even though the socket inode is permissive. App branch correction creates the **disposable PRIVATE daemon/socket only** under an exact verified root-owned 01777 sticky canonical `/tmp` and sets the random child scratch directory to 0711; it never chmods RUNNER_TEMP ancestors or host Docker and retains original runner and source security preflight. The specific blocked ancestor was *not directly measured* in #41674697531; this is a design-level hypothesis resolved via a controlled traversable-parent fixture, not a claim of an observed exact parent mode. Do not promote acceptance. F4B needs a new real manual run with fixed positive CREATE, EACCES negative, exact removal and unchanged host daemon.

## **Later outcome: F4B scoped real private-Docker proof PASS — 3 November 2026**

This later outcome supersedes the preceding historical F4B HOLD checkpoint **within the narrowly defined real-Docker DAC experiment only**. User-dispatched [App Actions #41676848336](https://github.com/lijust/EREI-3.2/actions/runs/41676848336) at reviewed App SHA `4cf0893e62ccf924d4d47d75fe8164ecf3518a7a`: overall SUCCESS, **privileged actual-Docker job SUCCESS**, offline tests SUCCESS (F4B 23 PASS, F4A 5 PASS + 2 legitimate root-only SKIP, F3 40 PASS: **68 PASS, 2 SKIP**).

The actual rootful private-dockerd receipt confirms the same restricted UID successfully sent an approved immutable fixed Docker CREATE over the disposable private socket in permissive mode and returned a peer-verified CID; that specific never-started container was inspected, removed, checked absent. The same restricted UID then received exact **EACCES for a NEW direct Docker CREATE connection** after the private socket was chmodded 0600. A **connect-only** host-socket attempt also received EACCES; no host Docker API CREATE, no untrusted code and no model calls occurred. The source-owned private daemon cleanup and host baseline passed in the same job. The source-generated receipt is **not an independently signed verifier attestation**.

**Acceptance ledger:** mark only `F4B_REAL_DISPOSABLE_DOCKER_SOCKET_UID_NEGATIVE_CONTROL=PASS`. **DO NOT** set `external_socket_bypass_denied`, `exclusive_transport_owner_attested`, `creation_quiescence_barrier_proven`, `late_async_create_excluded`, `worker_isolation_certified`, `independent_verifier_attested`, `independently_verified` or `untrusted_code_execution_authorized` true. Unenumerated Docker endpoints and inherited/pre-connected FDs remain unresolved. Proceed to F4C OS-separated broker and F5 in-flight drain, followed by L3 independent verifier. `decision=BLOCK_AI_ACCEPTANCE`; `learning_effectiveness=NOT_ESTABLISHED`.

**Reusable rule:** Require one real, successful fixed-operation positive control and one real operating-system-denied adversarial negative control against the SAME service instance and OS principal, on an actually traversable socket path, plus exact owned resource removal. Claim no more than the precise daemon/socket/UID/fresh-connect security boundary tested.
