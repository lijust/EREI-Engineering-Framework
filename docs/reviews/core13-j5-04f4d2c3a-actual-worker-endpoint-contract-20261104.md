# Core13 J5-F4C3D2C3A — same restricted fixed worker endpoint/OS negative scope

**4 November 2026 · Framework staged contract, successor of D2C2 Draft #149.**

## Previously verified source-bound baseline

Owner-manual actual [D2C2 Actions #41823943354](https://github.com/lijust/EREI-3.2/actions/runs/41823943354), pinned App SHA `6ae3344ee318c201b58e9e608dd43528970c513a`, completed SUCCESS with **78 offline PASS**. In one genuine **fixed, separate nonroot Worker OS process**, controller IPC received/closed one harmless SCM_RIGHTS dummy FD using recvmsg, accepted the next exact command with zero ancillary data, rejected a fixed Docker CREATE through the reviewed root F4C2 broker, and received EACCES on protected private and host Unix Docker sockets. The fixed controller could create/inspect/delete one never-started container, and original private broker/daemon cleanup passed. Not an AI or broad isolation certificate.

## New D2C3A exact-scope proof obligation

App module `tools/core13_j5_04f4d2c3a_same_worker_alt_endpoint_os_guard.py`, offline unit tests, and owner-only runtime workflow. The script pins D2C2 source Git blob and D2A source policy, composes **one existing actual D2C2 fixed worker**, and inserts explicit OS/endpoint negative checks before original broker/host/private Docker-denial logic. No model/user code, no arbitrary Docker commands, no new privileged broker.

The single live source-fixed restricted worker must verify: (1) four UIDs/GIDs restricted to the same principal and CapEff=0; supplementary groups only expected primary GID. (2) `prctl(PR_SET_NO_NEW_PRIVS,1)` and `PR_GET_NO_NEW_PRIVS=1` self-applied inside worker **after** exec, not an inherited/before-exec guarantee. (3) no Docker env redirection through DOCKER_HOST, DOCKER_CONTEXT, DOCKER_CERT_PATH or DOCKER_TLS_VERIFY. (4) fresh Unix Docker socket connection EACCES for **`/run/docker.sock` and one exact source-fixed symlink alias inside the owned private dockerd directory** (private endpoint root-owned 0600). (5) fresh TCP connections to **loopback `127.0.0.1:2375` and `:2376` must yield ECONNREFUSED**, not a successful connection or ambiguous timeout. (6) source-fixed D2C2 same process dummy-FD closure + zero-ancillary command, reviewed F4C2 broker mutation denial and protected private/host Docker EACCES continue unaltered.

The alias is source-created and source-removed inside the disposable test root. Original D2B1 source maintains only one owned private daemon/broker, never-started test container creation/deletion, empty inventory verification, broker/daemon cleanup and baseline preservation.

PR CI **never runs root or Docker**. Only exact owner-reviewed manual workflow_dispatch on source-pinned branch may attempt privileged Docker, on disposable Linux GitHub runner.

### Assurance ceiling and remaining work

A future live D2C3A PASS would show only these exact local endpoints and OS checks in one source-fixed real worker. It does **not** prove all remote TCP/TLS/SSH Docker, other Unix aliases, privileged SCM_RIGHTS delivery denial, a lifetime FD graph, removal of controller's direct host Docker rights, worker exposure to arbitrary model/user code, F5 in-flight/late CREATE quiescence or L3 independently governed verification.

The user's Docker Scout screenshot reported 34 CVEs on a local python:3.12-slim image with partial hash matching the fixed test image; current full digest applicability and remediation are unverified. The immutable test image is never started in this experiment.

**Next:** D2C3B should evaluate privileged FD-transfer capabilities in a precisely scoped reviewed test, but do not treat a self-closing recipient as prevention of kernel delivery. D2D should prioritize real broker-only controller migration and F5/L3 independent acceptance over repeated fixed-worker diagnostics.

```text
d2c3a_source_and_offline_tests=IMPLEMENTED_PENDING_CI
d2c3a_real_disposable_docker_evidence=NOT_YET_RUN
production_worker_no_new_privs_enforced_from_exec=false
worker_privileged_docker_fd_scm_rights_delivery_prevented=false
worker_all_unix_socket_docker_aliases_denied=false
worker_all_remote_docker_tcp_tls_ssh_denied=false
controller_direct_host_docker_access_removed=false
broker_exclusive_transport_certified=false
worker_isolation_certified=false
creation_quiescence_barrier_proven=false
independently_verified=false
untrusted_code_execution_authorized=false
decision=BLOCK_AI_ACCEPTANCE
learning_effectiveness=NOT_ESTABLISHED
```

**Reusable design rule:** a checked set of local Unix aliases and loopback TCP ports cannot be generalized into an all-endpoint Docker denial. Every source-generated negative test must specify exact identity, address, expected errno, and cleanup.

## Source CI checkpoint — 4 November 2026

[App Actions #41826673140](https://github.com/lijust/EREI-3.2/actions/runs/41826673140) **SUCCESS**: 12 D2C3A + 19 D2C2 + 21 D2C1 + 20 D2B1 = **72 offline PASS / zero FAIL**, exact source SHA `4ef65ffe32a589a1d06389c37e2c770de64eaf96`. Real root/private Docker owner-manual D2C3A workflow job was **SKIPPED** on PR, so same-worker alternate endpoint/NoNewPrivs checks are source-ready but not runtime-verified. Scoped D2C2 real #41823943354 remains valid separately; no worker isolation or full endpoint/FD lifetime/AI acceptance is promoted.

## Final source review/CI (4 November 2026)

[App Actions #41826916946](https://github.com/lijust/EREI-3.2/actions/runs/41826916946) at App SHA `6f4227f6c8d6277e1e7115da6ba45b25eaf70be6` **SUCCESS**, 15 D2C3A + 19 D2C2 + 21 D2C1 + 20 D2B1 = **75 offline PASS / zero FAIL**. Actual privileged private Docker workflow job SKIPPED on PR. The source composition callback was corrected to the original exact seven arguments with one source-owned evidence list; negative wrong-arity tests were added. No live endpoint proof or broader security certification is implied by source CI. Explicit owner-reviewed manual run remains required to establish any D2C3A OS/endpoint sampled result. `BLOCK_AI_ACCEPTANCE` unchanged.
