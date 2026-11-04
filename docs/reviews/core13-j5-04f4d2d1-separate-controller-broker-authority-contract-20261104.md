# EREI Engineering Framework — D2D1 separate restricted trusted controller through existing root broker

**4 November 2026 | Framework successor to D2C3A #150.**

## Verified upstream
Owner-dispatched D2C3A [App run #41836538195](https://github.com/lijust/EREI-3.2/actions/runs/41836538195), exact source `bad618dc42f71593f24dd6781d95cc8d63e654fa`, both actual private Docker and 76 offline tests SUCCESS. Fixed restricted worker same PID passed source-defined harmless ancillary FD closure, F4C2 broker CREATE denial, protected host/private Unix Docker EACCES and specifically named alias/loopback negative controls, CapEff zero, expected groups and self-applied NoNewPrivs. **Not** a production untrusted-worker or complete transport isolation certificate.

## D2D1: isolate trusted controller OS identity, not just the worker

App implementation `tools/core13_j5_04f4d2d1_separate_controller_fixed_broker.py`, paired unit tests and owner-manual workflow. Reuse exact F4C2 source-reviewed root broker, private disposable daemon and never-started immutable test-container lifecycle, **without introducing a generic Docker proxy**.

The existing historical J4/J4S test launcher and GitHub runner still have direct host Docker CLI and sudo rights. D2D1 builds a **new source-fixed test-only controller process** at distinct nonroot account `www-data`, separate from the restricted `nobody` worker, the supervising runner and the F4C2 root broker; no user/model code. This actor receives only fixed broker socket/daemon socket paths, expected broker PID and exact controller UID/GID.

**Required real experiment:**
- Reviewed disposable GitHub Linux runner, no Docker context override, exact secondary owned private rootful daemon and root-owned **0600** Docker socket; preserve host Docker baseline and original F4C2 source-defined fixed config.
- Broker expects exact `www-data` controller UID/GID; kernel `SO_PEERCRED` denies `nobody` worker's fixed CREATE and unknown operations, allows only `{"op":"create_fixed","version":1}` from controller. No arbitrary image, endpoint, container command or generic RPC input.
- Launch controller with `sudo -n -u www-data -g <verified group> /usr/bin/setpriv --no-new-privs <fixed Python> -I -S -c <source-fixed code>`; **NoNewPrivs is set before Python exec**. Fixed minimal environment.
- Controller verifies all UID/GID values, groups, `CapEff=0`, `NoNewPrivs=1`, no inherited socket FD and no Docker redirect env; parent separately checks the **live** controller `/proc/PID` and source-fixed cmdline/credentials before releasing a fixed GO message.
- Same actual controller PID must obtain EACCES from direct fresh `/var/run/docker.sock`, `/run/docker.sock` and root-owned private Unix Docker socket attempts. Only then may it authenticate kernel root broker PID/UID/GID and ask exact unrecognized `ping` (DENIED_OP), followed by exact `create_fixed` (FIXED_CREATED_REMOVED); broker alone creates/inspects/removes one **never-started** fixed test container.
- Verify empty private Docker inventory, exact process/daemon cleanup and unchanged original host Docker daemon baseline. Fail closed on every uncertain stage and leak no privileged paths in error output.
- PR CI **offline only**. The real root/private Docker/sudo experiment requires explicit user-approved owner-only `workflow_dispatch` on the exact D2D1 branch. No automatic rootful reruns.

### Distinguish narrow outcome from global claim

If live D2D1 succeeds: only **new source-fixed separate controller** has demonstrated protected raw host/private Unix Docker denial while still successfully issuing a typed broker-only fixed operation under kernel peer checks. **This is not removal of Docker privileges from the supervising runner or legacy J4/J4S**; no remote/other Docker alias or pre-connected privileged FD transport exhaustivity; no full future orchestrator isolation. No F5 epoch/in-flight late CREATE quiescence or independent L3, no AI candidate code and no current Docker image CVE clearance. The previously reported Docker Scout 34 vulnerabilities were a local screenshot, not a current verified full-digest SBOM.

**D2D2:** migrate only a new prospective controller orchestration path away from host-Docker CLI, with broker-only source-fixed lifecycle and explicit generation fencing, and then attack the **actual** controller/worker principal graph. Separate F5 cleanup from late-CREATE accept window and L3 governed acceptance before any untrusted execution.

```text
d2c3a_actual_fixed_worker=SCOPED_REAL_PASS
d2d1_separate_controller_source=CODE_PRESENT_RUNTIME_PENDING
legacy_j4_j4s_direct_host_docker_cli_removed=false
supervisor_docker_group_and_sudo_authority_removed=false
all_controller_docker_tcp_tls_ssh_endpoints_denied=false
all_controller_alternate_unix_docker_endpoints_denied=false
broker_transport_globally_exclusive=false
controller_future_task_code_safe=false
worker_isolation_certified=false
creation_quiescence_barrier_proven=false
independently_verified=false
untrusted_code_execution_authorized=false
decision=BLOCK_AI_ACCEPTANCE
learning_effectiveness=NOT_ESTABLISHED
```

**Reusable boundary principle:** broker-only security must apply to the *actual OS controller principal*, not simply to a source-defined job label. Kernel-backed credentials, before-exec NoNewPrivs, direct socket denial and typed broker acceptance must all refer to the same live controller process. These diagnostic tests still do not certify a future arbitrary-code system.

## D2D1 offline source implementation checkpoint — 4 Nov 2026

[App Actions #41869115855](https://github.com/lijust/EREI-3.2/actions/runs/41869115855) at reviewed source `37e1d3bd7f767426d318da18afdc247502d4a760`: **SUCCESS, 78 offline PASS/0 FAIL** (22 new D2D1 +22 existing F4C2 +18 D2A +16 D2C3A). Rootful owner-only real private Docker controller test **SKIPPED** on PR. Therefore this is a **source-reviewed authority design checkpoint**, not real `www-data` separate controller proof. No removal of legacy runner/J4S host Docker authority, no global broker exclusivity, no F5 late CREATE or L3 and no untrusted code acceptance. `BLOCK_AI_ACCEPTANCE`.
