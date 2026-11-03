# EREI Core13 F4C3D1A — live actual J4S host controller runtime observation contract

**4 November 2026 · Framework stacked on D0 contract PR #142.**

## Anchored accepted evidence and why D1A matters

Actual F4C3C [App Actions #41737838052](https://github.com/lijust/EREI-3.2/actions/runs/41737838052) proved a post-exec `SCM_RIGHTS` read-only Docker-socket transfer from a privileged test process to a distinct restricted OS UID. This is a controlled counterexample to assuming `close_fds` alone eliminates all Docker capabilities, **not evidence of production worker leakage or containment**. F4C3D0 [Actions #41738757356](https://github.com/lijust/EREI-3.2/actions/runs/41738757356) source-vetted **53 tests PASS** with actual J4/J4S host Docker CLI source and canary/hostile execution gate review, **no Docker executed**.

D1A is intentionally more specific than an arbitrary new subprocess demonstration: it instruments **the actual existing J4S `probe`** with a temporary observer around **its single unchanged** `subprocess.Popen(["docker", "start", "--attach", exact_CID])`. The test is **only owner-manual** on a reviewed disposable Linux GitHub runner. Source-referenced fixed J4 `timeout` script runs under the exact approved immutable image digest, with original J4S network none, read-only root, nonroot user, caps dropped, bounded timeout and verified cleanup. No model code or candidate patch is authorized.

## Defined evidence

1. D0 source Git-blob and AST pins must match exactly; source drift denies.
2. Manual job verifies GitHub-hosted Linux preflight, default local Unix Docker context with no environment overrides, reviewed source and unchanged host baseline; pinned fixed test image only.
3. Existing J4S `probe(..., case="timeout")` must run and return original `TIMEOUT_STOPPED`, capped stream and container forced removal + absence.
4. Runtime observer must see **one** live Docker CLI child PID under actual original J4S `_attached_stream`, exact `docker start --attach <verified 64hex CID>` /proc cmdline, observed effective host controller UID/GID and bounded /proc FD-type counts. It must not emit actual FD path targets or environmental secrets.
5. Observer errors after spawning a child MUST NOT bypass original J4S process abort and owned cleanup; fail closed after J4S's finally.
6. Require no leftover `core13.j4.probe` containers and unchanged host Docker baseline.
7. The source-generated receipt may prove **only** a host Docker CLI subprocess was actually observed under reviewed fixed source, with a snapshot of UID/GID and FD *types*; it cannot claim those descriptors are free of Docker or that the actual container Python worker/IPC paths were enumerated.

PR CI runs no Docker, while the separate privileged/host live job must remain explicit `workflow_dispatch` by owner and exact ref. If the real job is unrun/skipped, no live observation claim is permitted.

## Security image gate

The user's Docker Scout screenshot showed **34 reported CVEs** on a locally inspected `python:3.12-slim` image with a digest prefix matching the pinned fixed test image. **Never interpret an immutable SHA as vulnerability remediation.** A source-fixed 60-second Python sleeper is a trusted measurement only; any later **untrusted worker** in that image requires fresh full digest match, SBOM/CVE policy review and repair or accountable exception before execution. No candidate code here. The Docker image policy field stays FALSE.

## Next isolated proofs

**D1B**: inspect running fixed J4S container's real Python PID/UID/GID/cgroup/network namespace and OS descriptors while distinguishing it from host CLI; if root inspection is required, allow a separately bounded exact-PID, exact-CID, read-only fixed helper on ephemeral runner, but do not label it independent L3 attestation.

**D2**: enforce real worker broker-only transport, no inherited/SCM_RIGHTS Docker FDs, deny alternative Unix/TCP/SSH endpoints and root/sudo access. **F5**: daemon-epoch and in-flight CREATE/late completion quiescence barrier. **L3**: independently administered verifier and signed evidence.

Until those gates are actually observed, `actual_untrusted_worker_os_process_verified=false`, `actual_container_python_worker_pid_verified=false`, `actual_worker_all_docker_endpoints_denied=false`, `worker_isolation_certified=false`, `exclusive_transport_owner_attested=false`, `creation_quiescence_barrier_proven=false`, `independently_verified=false`, `untrusted_code_execution_authorized=false`, `decision=BLOCK_AI_ACCEPTANCE` and `learning_effectiveness=NOT_ESTABLISHED`.

**Reusable core-framework lesson:** observing the real host-side orchestration subprocess is not evidence about an in-container worker's capabilities. Preserve that distinction in code, tests, receipts and approval gates.
