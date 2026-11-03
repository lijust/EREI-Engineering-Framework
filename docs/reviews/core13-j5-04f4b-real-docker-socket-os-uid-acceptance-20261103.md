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
