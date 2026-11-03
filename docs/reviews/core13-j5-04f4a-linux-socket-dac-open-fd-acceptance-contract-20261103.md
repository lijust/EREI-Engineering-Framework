# Core13 J5-04F4A — OS permission denial can be real; socket chmod is NOT creation quiescence

**3 November 2026 | reusable engineering/acceptance rule; no production worker permission.**

## Background
App F1 [Draft #257](https://github.com/lijust/EREI-3.2/pull/257) demonstrated a late local queued CREATE after empty Docker inventories. App F2 [Draft #258](https://github.com/lijust/EREI-3.2/pull/258) demonstrated a partial HTTP request body pending on a real Docker Unix socket before empty scans. App F3 [Draft #259](https://github.com/lijust/EREI-3.2/pull/259) added local durable SQLite generation fencing but explicitly did not deny other Docker socket clients. Framework [Draft #134](https://github.com/lijust/EREI-Engineering-Framework/pull/134) records that boundary.

The new App F4A branch introduces **a deliberately restricted non-Docker kernel proof**:
- On Linux, owner-only AF_UNIX socket mode \`0600\` prevents **new** \`connect()\` from a separate real restricted \`nobody\` UID, with observed EACCES and Linux SO_PEERCRED validating the adversarial positive control.
- A positive control with socket mode \`0666\` verifies the same restricted UID *can* connect when allowed. This rules out a trivial false PASS from inaccessible path or ineffective child identity.
- A restricted client that connected while \`0666\` can still send fixed bytes *after* chmod \`0600\`. **Changing access permissions does not revoke established connections or queued socket bytes.** This is a measured counterexample to ACL-change-as-drain-barrier.
- No actual Docker Unix socket or HTTP CREATE was exercised in F4A. Running the local root fixture is not broker integration, worker isolation or an independent verifier.

## F4 acceptance ladder (never collapse the levels)
| Gate | Required measurable evidence | F4A result |
| --- | --- | --- |
| F4A kernel DAC fixture | Separate OS UID, valid positive control, fresh EACCES, retained FD counterexample | Local Linux test PASS; CI pending independent run |
| F4B actual Docker bypass | Private owned dockerd and protected socket, denied fixed direct HTTP CREATE from restricted worker, host Docker socket paths considered, no leftovers | NOT TESTED |
| F4C exclusive broker | Distinct privileged broker identity, restricted worker permitted broker RPC only, raw daemon transport absent from its FD/mount/network namespace, source and credentials independently measured | NOT IMPLEMENTED |
| F5 in-flight barrier | Existing connections/partial HTTP/detached CREATE fail closed under seal; daemon epoch and durable unresolved intents protected through restart | NOT PROVEN |
| L3 independent verifier | Separate admin/principal, source measurement, protected signing/receipt, independent outside the Controller | NOT ATTESTED |

## Execution contract
1. Keep all F3 records, including EMITTED_UNKNOWN and RETURNED_CLAIM; they cannot be auto-cleared just because Docker inventory is empty or mode changed.
2. A restricted worker must not carry \`docker\` group, sudo, inherited privileged FDs, direct host socket mount, unmediated \`DOCKER_HOST\` TCP/SSH endpoints or other raw CREATE paths. Fail any bypass attempt; record attempted UID, socket inode, daemon epoch and outcome, without exposing secrets in public logs.
3. Broker admission must bind immutable fixed config, generation, daemon epoch and intent ID *at the only Docker transport point*; do not accept a caller-provided attestational Boolean.
4. Do not rely on chmod-based revocation as F5. Terminate or wait on all existing accepted connections, remove/retire old listener/daemon, and independently verify daemon lifecycle and no unresolved sends before considering a quiescence receipt.
5. Keep privileged GitHub Actions tests on trusted, exact-owner branches or explicit reviewed/pinned flows, **never arbitrary PR code under sudo**. Do not use model-generated/unreviewed payloads in a Docker fixture.
6. After every F4 change, preserve FAIL/HOLD evidence; do not silently promote \`worker_isolation_certified\`, \`late_async_create_excluded\` or \`independently_verified\`.

**Acceptance remains:** \`exclusive_transport_owner_attested=false\`, \`external_socket_bypass_denied=false\`, \`creation_quiescence_barrier_proven=false\`, \`late_async_create_excluded=false\`, \`independent_verifier_attested=false\`, \`worker_isolation_certified=false\`, \`untrusted_code_execution_authorized=false\`, \`independently_verified=false\`, \`decision=BLOCK_AI_ACCEPTANCE\`, \`learning_effectiveness=NOT_ESTABLISHED\`.

**Reusable engineering insight:** AF_UNIX DAC protects a *connection establishment event*, not already-open transport state. Distinguish deny-new-connect from drain-open-connections from exclusive runtime transport from independently verified quiescence.
