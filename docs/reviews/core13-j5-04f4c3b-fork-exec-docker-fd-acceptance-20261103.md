# Core13 J5-04F4C3B — audited fork/exec raw Docker FD boundary acceptance contract

**3 November 2026 | Framework successor of retained-FD counterexample contract Draft #139.**

## Evidence basis

Real private Docker [App F4C3A Actions #41685370694](https://github.com/lijust/EREI-3.2/actions/runs/41685370694), source SHA `1d18b7097219c15c4a1595ba3252d264ab6604b2`: both jobs SUCCESS, 96 offline PASS. With 0600 raw Docker Unix socket and restricted UID, fresh connect was OS **EACCES**, yet same-process pre-drop connected FD supported fixed read-only GET /_ping after UID drop. This is a **confirmed retained capability counterexample**, not isolation or deployed-worker leak proof. Keep `BLOCK_AI_ACCEPTANCE` and global exclusive transport fields FALSE.

## F4C3B measured fork/exec controls

The App F4C3B code is a fixed read-only Docker test on one disposable private secondary dockerd. It uses **one root process as the controlled launcher**, which binds exact ephemeral socket path and `SO_PEERCRED` to the real private daemon PID and runs **two distinct OS-restricted Python exec children**, both `user=<restricted uid>`, `group=<restricted gid>`, `extra_groups=[]`:

- **Positive explicit descriptor transfer:** `subprocess.run(..., close_fds=True, pass_fds=(exact_socket_fd,))` allows a previously root-opened Unix Docker socket into a distinct restricted exec child. The child must verify kernel peer identity and succeed in a single immutable **GET /_ping**. No POST or mutation.
- **Negative sealed launch:** `subprocess.run(..., close_fds=True, pass_fds=())` for the same restricted principal must produce **EBADF** on the prior privileged descriptor number and **EACCES** for fresh raw private daemon connect. A negative success without matching live positive control does **not** prove the detector works.

Root launcher may accept only exact pinned scratch owner `SUDO_UID`, canonical root-owned 01777 parent `/tmp`, random 0711 scratch root, root-owned 0600 private dockerd socket and /proc-bound daemon PID/argv. No user-supplied Docker URL or endpoint, no container create/start, no host API, no model code, no project writes. Owner-reviewed manual-only `workflow_dispatch`; PR unprivileged tests cannot certify live FD inheritance.

## Gate semantics and no false assurance

If real Docker test passes, call it **`F4C3B_FORK_EXEC_FD_POSITIVE_AND_SEALED_NEGATIVE_SCOPED=PASS`**. Only the exact test launcher and child prove explicit pass_fd can leak a Docker socket and zero-pass close_fds denies that specific connected FD while new connects are blocked by DAC. No claim that deployed untrusted worker inherits no descriptors, or that `SCM_RIGHTS` transport, alternate Unix/TCP/SSH Docker endpoints, global broker/control privileges or concurrency/F5 have been eliminated. The root controller is not independent of the root daemon; source-generated evidence is not L3 attestation.

```text
inherited_or_retained_private_fd_excluded=false
worker_fork_exec_fds_fully_isolated=false
retained_fd_leakage_prevented=false
scm_rights_raw_docker_fd_transfer_excluded=false
exclusive_transport_owner_attested=false
broker_exclusive_transport_certified=false
external_socket_bypass_denied=false
worker_isolation_certified=false
creation_quiescence_barrier_proven=false
independently_verified=false
untrusted_code_execution_authorized=false
decision=BLOCK_AI_ACCEPTANCE
learning_effectiveness=NOT_ESTABLISHED
```

## Further necessary controls

F4C3C: restricted actual worker/child FD inventory and `SCM_RIGHTS` transfer controls. F4C3D: enumerate alternative daemon transports and remove root/sudo controller bypass to satisfy **exclusive** transport. F5: generation/daemon-epoch and in-flight or queued Docker CREATE drain even across process crashes/timeouts. L3: independently administered and signed evidence outside worker/controller privileges.

**Reusable lesson:** distinguish (i) pathname permissions on fresh connect, (ii) retained FD after UID change, (iii) FD inheritance across exec, (iv) descriptor passing via Unix messages, and (v) alternative endpoint/privileged actor routes. For each boundary require an actual positive and negative control tied to the same immutable service and caller identity before making any security assertion.
