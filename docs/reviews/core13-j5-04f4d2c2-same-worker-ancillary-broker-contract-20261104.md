# Core13 J5-F4C3D2C2 — actual SAME worker controller-IPC ancillary denial and broker EACCES contract

**4 November 2026 | Framework Draft stacked on D2C1 Framework #148.**

## What has been proven before this change

Owner-dispatched real [App D2C1 #41820521157](https://github.com/lijust/EREI-3.2/actions/runs/41820521157), source `9a59602e55cbefd0213f077e702ff3464236c014`, passed actual disposable root/private Docker and **80 offline tests**. It verified a **second** separate restricted-UID worker detecting and closing exactly one harmless `SCM_RIGHTS` dummy Unix socketpair FD via authenticated controller IPC. Its parent D2B1 source-fixed restricted worker's broker CREATE denial and fresh private+host raw Unix Docker socket EACCES also passed in the same owned disposable session, **but on a different process/PID**. Source-fixed D2B1 owner run [#41817999943](https://github.com/lijust/EREI-3.2/actions/runs/41817999943) had also passed.

Do **not** infer a cross-process combination proves a particular real worker cannot acquire capabilities later. Real F4C3C #41737838052 already proved connected root Docker FD transfer via `SCM_RIGHTS` into a separate restricted process is possible under a controlled counterexample. No completed prior result proves global Docker endpoint exclusivity.

## D2C2 desired narrow invariant

A single real, source-fixed restricted Linux worker OS **PID** must receive and explicitly close one authenticated-controller harmless dummy FD via `recvmsg(MSG_CMSG_CLOEXEC)`; verify the FD is gone before proceeding; receive the next normal fixed controller command with **zero ancillary**; then in the **same PID** perform original F4C2 broker mutation-denial and protected private/host Unix Docker EACCES tests. The existing reviewed D2B1 setup and full owned cleanup remain unchanged.

App code `tools/core13_j5_04f4d2c2_same_worker_ancillary_and_broker_denial.py` pins exact D2B1 worker source Git blob and replaces only its one controller command receive block, preserving D2B1 fixed UID/group/peer checks, broker request, socket attempts and reporting. The input protocol is fixed and source controlled, not an arbitrary worker task or general Docker proxy. Test harness uses one **non-Docker** disposable Unix socketpair FD; no private/host Docker raw FD is ever delivered, and no image/model/user code is started.

Required conditions:
1. **Live identity:** actual restricted worker kernel PID/UID/GID, same source-fixed command and controller Unix `SO_PEERCRED` verified before sending.
2. **First negative:** controller sends exact command + one harmless `SCM_RIGHTS` FD. Worker must parse all ancillary, close delivered FDs immediately, reject unexpected/truncated ancillary and incorrect multiplicity; then verify only authenticated controller socket remains open and acknowledge `ANCILLARY_DENIED`.
3. **Second normal command:** same PID requires exact source-fixed command with **zero ancillary**. Worker continues original fixed broker `DENIED_PRINCIPAL` and protected private+host raw Unix Docker `EACCES`; correct original bounded receipt and exit 0 required.
4. **Original lifecycle:** controller sends only its source-fixed F4C2 allowed/denied requests, never starts its immutable test container, verifies exact create/inspect/delete and empty inventory; private broker+daemon terminated and host baseline unchanged.
5. **Automation constraints:** pull-request checks are offline only. Real root/secondary dockerd requires explicit owner-reviewed `workflow_dispatch` on the exact D2C2 branch, disposable Linux runner, no untrusted executable.
6. **Assurance:** keep `BLOCK_AI_ACCEPTANCE` regardless of a green source-only CI or scoped real run.

**Not in D2C2 scope:** actual privileged raw Docker FD injection, arbitrary/untrusted code execution, other broker/controller IPC peers, lifetime capability acquisition or continuous FD graph, alternate Docker Unix/TCP/TLS/SSH endpoints, old J4/J4S controller's direct host Docker CLI authority, F5 in-flight/late CREATE epoch quiescence and independently governed L3 verification. Docker Scout 34 vulnerabilities on a local pinned-image scan require separate full-digest/current SBOM triage before any untrusted code execution.

```text
d2c1_dummy_fd_closed_second_process=SCOPED_REAL_PASS
d2c2_integrated_primary_fixed_worker=CODE_READY_LIVE_PENDING
actual_worker_privileged_docker_fd_injection_denied=false
all_worker_ancillary_ipc_senders_restricted=false
actual_worker_all_docker_endpoints_denied=false
actual_worker_fd_lifetime_continuous_attested=false
controller_direct_host_docker_access_removed=false
broker_exclusive_transport_certified=false
creation_quiescence_barrier_proven=false
worker_isolation_certified=false
independently_verified=false
untrusted_code_execution_authorized=false
decision=BLOCK_AI_ACCEPTANCE
learning_effectiveness=NOT_ESTABLISHED
```

**General-purpose reusable lesson:** a second worker with the same UID and launch command is still a different security subject. Require the test receipt to bind negative control, normal authorized operation and cleanup to one actual PID and one source hash without implying universal isolation.
