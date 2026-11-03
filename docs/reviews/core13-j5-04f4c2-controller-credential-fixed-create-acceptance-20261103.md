# Core13 J5-04F4C2 — fixed CREATE broker controller/worker credential acceptance

**3 November 2026 · Framework draft stacked on F4C1 contract PR #137.**

## Fixed source baseline

[App F4C1 real Docker #41680080355](https://github.com/lijust/EREI-3.2/actions/runs/41680080355) **SUCCESS**, pinned source `762984ba0ab4f65a73dc76a018059a9cf664e5aa`. Actual broker read-only GET succeeded; authorized worker ping, denied worker CREATE RPC, denied foreign UID, both direct raw Docker socket denials and verified cleanup. Offline 83 PASS, no fail. **This is the F4C1 scoped result only, not global exclusive Docker transport.**

## F4C2 contract for next mutation test

A **root broker** may accept exactly one source-fixed mutation capability from a distinct verified controller UID/GID, with the worker UID/GID fully denied. This is a disposable source-fixed test, **not production least-privilege**:

- Exact reviewed source gate and disposable hosted Linux runner with private secondary Docker daemon; host API baseline pinned and unchanged, no host POST/DELETE or host socket chmod.
- Broker root UID, Docker peer root UID/PID must be independently kernel-bound `SO_PEERCRED`, and controller UID must be nonzero and distinct from restricted worker UID (kernel credentials not user claims).
- `{"op":"create_fixed","version":1}` sent by the restricted worker must return `DENIED_PRINCIPAL`. An unrelated controller operation `{"op":"ping","version":1}` must return `DENIED_OP`. Only controller's exact fixed CREATE request can reach the Docker private API.
- Broker independently validates an immutable pinned J4 image digest, static 60s Python sleeper command (never actually started), network none, read-only filesystem, no bind/mounts, caps dropped and other pinned runtime parameters. There must be no RPC knob for arbitrary image, code, url, body, ports, volumes, privilege or container names.
- One strict `POST /containers/create` to **private** daemon must return validated 64-hex CID, inspect must prove exact expected name/label/config and state Running=false. Broker deletes exact CID and proves empty private inventory before returning minimal `{"ok":true,"code":"FIXED_CREATED_REMOVED"}`.
- Controller independently rechecks inventory; restricted user still receives direct `EACCES` from private and conventional host raw sockets. Host Docker receives no mutating request.
- Uncertain POST, CID or cleanup -> HOLD; recover only exact-name/label/immutable config on private daemon; require zero private inventory and exact broker/daemon termination. No synthetic or inferred success.
- Actual rootful job must remain **manual trusted branch/user only**; PR CI cannot run privileged Docker and cannot certify this new path.

## Precise acceptance ledger

| Claim | Required actual evidence | State |
|---|---|---|
| F4B real Docker restricted fresh socket denial | Actual positive fixed CREATE plus EACCES and exact cleanup | PASS, Actions #41676848336 |
| F4C1 real fixed read-only broker mediation | Authorized ping; denied create op/foreign UID; direct raw denial; cleanup | PASS, Actions #41680080355 |
| **F4C2 controller-only pinned never-started CREATE through broker** | Real positive fixed create→inspect→delete; worker denied; unknown controller op denied; zero private inventory | **Implementation/CI pending; do not promote without real manual receipt** |
| F4C3 exclusive service transport, inherited FD and alternative endpoint control | Independent attack probes over all supported transports/credentials | Not established |
| F5 creation quiescence/daemon epoch and pending creates | In-flight/queued/partial CREATE closure receipts | Not established |
| L3 independently-administered verifier | External measured and signed evidence | Not established |

## Non-promotion and reusable principle

The root broker itself has broader capabilities than its RPC. The runner controller may also have local Docker/sudo rights. Therefore even a successful real F4C2 **does not** establish sole service transport, worker namespace isolation or safe untrusted code execution. The capability shape, the authority of the broker process, the authority of the controller, and the provenance of verification receipts are distinct assurance requirements.

`exclusive_transport_owner_attested=false`, `external_socket_bypass_denied=false`, `broker_exclusive_transport_certified=false`, `trusted_fixed_create_broker_isolated_capability_certified=false`, `controller_only_docker_transport_certified=false`, `worker_isolation_certified=false`, `creation_quiescence_barrier_proven=false`, `independently_verified=false`, `untrusted_code_execution_authorized=false`, `decision=BLOCK_AI_ACCEPTANCE`, `learning_effectiveness=NOT_ESTABLISHED`.

**Cross-country reusable engineering rule:** For privileged mutations, prove identity of calling principal + identity of daemon peer + immutable operation and resources + exact resulting object removal; never conflate RPC allowlist with restricted broker OS powers, daemon transport exclusivity, or replay/drain safety.

## App F4C2 offline CI status — 3 November 2026

[App Actions #41681545174](https://github.com/lijust/EREI-3.2/actions/runs/41681545174) succeeded for 22 F4C2 + 20 F4C1 + 23 F4B + 40 F3 = **105 PASS, 0 FAIL**; privileged owner-only actual secondary-Docker broker test was **SKIPPED** on PR event. The implementation is available but the F4C2 mutating capability acceptance is **NOT ESTABLISHED** pending an explicit trusted manual run and inspected full receipt. Keep global gate flags false.
