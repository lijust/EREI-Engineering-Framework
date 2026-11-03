# EREI Core13 J5-04F4C1 — scoped OS broker fixed-read-only acceptance contract

**3 November 2026 · Framework successor of F4B Framework PR #136 · App F4C1 implementation source on the stacked branch.**

## Prior pinned F4B evidence

[App real Docker Actions #41676848336](https://github.com/lijust/EREI-3.2/actions/runs/41676848336) established a **restricted UID fresh-socket** EACCES block for direct Docker CREATE after its private daemon socket was changed from permissive to owner-only mode. It also proved the same UID could create a pinned never-started container *before* that chmod, which was removed with evidence. The assurance flags for exclusive transport/inherited FDs/worker isolation remained false.

## F4C1 contract

Goal: test a **separate restricted Linux UID** which cannot connect to Docker directly but can invoke one immutable **read-only** broker operation over a Unix RPC socket.

- Parent is an audited disposable GitHub-hosted Linux runner and its private secondary dockerd identity is kernel verified. No production socket chmod, Docker API writes, host container operations or candidate code.
- Private Docker Unix socket stays `0600`; broker is a **separate root OS process** capable of connecting to private Docker by fixed `GET /_ping`, explicitly bound with daemon `SO_PEERCRED` to reviewed PID/UID.
- Broker listens on a distinct test socket. The socket is open to callers for this experiment; broker **checks kernel SO_PEERCRED**, not caller assertions, and only allows a single exact fixed JSON `{"op":"ping","version":1}` with packet length <=256. Response is a fixed ok/code pair with no arbitrary Docker response forward.
- Authorized restricted UID gets broker-mediated GET success. A restricted `{"op":"create","version":1}` receives `DENIED_OP`; a **foreign** runner UID ping receives `DENIED_PRINCIPAL`. The broker never accepts CREATE, run, bind/mount, untrusted patch or model code.
- Restricted UID direct new connects to private daemon and standard host Docker socket both give kernel `EACCES`; host socket is connect-only, no HTTP.
- Single-use broker exits after the exact three calls; kernel endpoint no longer accepts connections. Only exact-owned broker and private daemon can be terminated. Post-condition: no containers created and original host Docker baseline unchanged.
- Any timeout, principal mismatch, broker process ambiguity, raw direct-connect success, cleanup uncertainty or peer mismatch is HOLD. Explicit manual privileged execution only on reviewed owner/ref, never arbitrary PR code.
- Offline CI can prove only source guards, NOT live kernel broker behavior. The real Docker receipt (if obtained) is source-generated, not independently signed.

## Gates withheld

F4C1 passing would prove **one mediated read-only GET path and two rejected RPC cases**, not a secure exclusive broker. Root broker remains too powerful, GitHub runner controller has sudo and may access Docker, alternate TCP/SSH sockets and inherited/concurrent FDs are unenumerated. A kernel-UID allowlist is not a complete capability-isolation model.

| Gate | Status |
|---|---|
| F4B scoped real Docker DAC test | Proven on Actions #41676848336 |
| **F4C1 broker immutable read-only RPC** | Code/test pending live manual run; do NOT claim actual Docker proof from PR CI |
| F4C2 least privilege sole transport + fixed mutating RPC | Not built |
| F4C3 inherited FD / alternate transport adversarial controls | Not proven |
| F5 daemon epoch / in-flight CREATE quiescence | Not proven |
| L3 independent verifier / signer | Not proven |

`exclusive_transport_owner_attested=false`; `external_socket_bypass_denied=false`; `broker_exclusive_transport_certified=false`; `worker_isolation_certified=false`; `creation_quiescence_barrier_proven=false`; `late_async_create_excluded=false`; `independently_verified=false`; `untrusted_code_execution_authorized=false`. `decision=BLOCK_AI_ACCEPTANCE`; `learning_effectiveness=NOT_ESTABLISHED`.

**Reusable principle:** A broker must be measured separately on both authorization planes: who may connect to broker RPC, who is allowed by its kernel-credential method policy, and what exact operations the broker can perform on the privileged service. A successful read-only mediation alone never proves exclusive transport ownership or safe untrusted execution.

## Offline App verification, not real broker evidence

[App F4C1 Actions #41678597148](https://github.com/lijust/EREI-3.2/actions/runs/41678597148) succeeded with **20 F4C1 + 23 F4B + 40 F3 = 83 PASS, 0 FAIL**, while the privileged real Docker broker job correctly **SKIPPED** for PR trigger. This is an implementation/contract guard, not proof of actual broker mediation, exclusive daemon transport ownership, FD drain, independent verification, or AI acceptance. Remain Draft/HOLD pending distinct owner-authorized manual run and pin exact live receipt if available.
