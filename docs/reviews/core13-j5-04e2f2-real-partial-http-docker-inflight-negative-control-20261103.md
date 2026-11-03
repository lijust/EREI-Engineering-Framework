# Core13 J5-04E2F2 — real incomplete HTTP CREATE pending during two EMPTY Docker inventories

**3 November 2026 | reusable framework evidence — no worker or model code authorized.**

## Actual observations, with limits

App [Draft #258](https://github.com/lijust/EREI-3.2/pull/258) extends App F1 #257's local queued CREATE negative control to an actual **partially submitted** Docker HTTP request. The controller persistently writes J5-04B PREPARED, establishes a **kernel SO_PEERCRED authenticated AF_UNIX connection to the exact temporary owned secondary rootful dockerd**, and transmits an immutable fixed J4 Python container's HTTP POST headers plus only HALF its expected JSON body. Content-Length announces the correct COMPLETE body length. Docker's request body remains incomplete while **two separate direct peer-bound GET /containers/json?all=1 scans both return EMPTY**. The controller then supplies the remaining JSON bytes and receives an actual HTTP 201 with a full CID, inspects exact approved immutable image/name/label and State.Running=false, removes only that CID with actual 404+empty secondary inventory, and stops the secondary daemon. The host's default Docker remains unchanged. The test never invokes Docker START or runs model/candidate code.

**Actual verified CI:** [Actions #41621174848](https://github.com/lijust/EREI-3.2/actions/runs/41621174848), tested App HEAD a04c5caedf5c940d39cf2269a06a61b6cde923ef, **3/3 JOBS SUCCESS**: Ubuntu **148 PASS**, Windows **147 PASS +1 Linux-only skip**, plus one genuine ephemeral fixed-only Linux secondary Docker HTTP experiment.

Exact real JSON values:
- durable_prepared_before_partial_http_emission=true
- actual_docker_unix_peer_http_header_and_partial_body_sent_before_scans=true
- actual_docker_http_body_complete_before_scans=false
- two_real_private_docker_inventories_empty_during_partial_request=true
- real_cid_created_only_after_http_body_completed=true
- real_fixed_cid_owned_removed_and_inventory_empty=true
- real_fixed_container_never_started=true
- host_primary_docker_unchanged=true
- docker_server_application_timing_independently_attested=false
- exclusive_create_transport_owner_attested=false
- creation_quiescence_barrier_proven=false; late_async_create_excluded=false
- worker_isolation_certified=false; untrusted_code_execution_authorized=false
- independently_verified=false; decision=BLOCK_AI_ACCEPTANCE
- learning_effectiveness=NOT_ESTABLISHED

**Important protocol scope:** It is proven that SOME bytes of the CREATE message were sent over the EXACT Docker-peer Unix socket before both empty inventories, and that a new CID materialized after completion of the body. It is NOT proven that the daemon had processed a COMPLETE valid CREATE request before the scans or would create later if no further bytes were supplied. Docker-side request application time is not independently attested. A partially transmitted request differs fundamentally from a completely submitted, delayed-completion RPC. Do not call this latter case proven.

**Initial test repair:** [Actions #41620873963](https://github.com/lijust/EREI-3.2/actions/runs/41620873963) initially failed one Windows synthetic Unix socketpair refusal test, because the mocked server waited on a deliberately absent body half until timeout. The test fixture was corrected to close the intentionally refused client and classify the resulting EOF as expected; production controller unchanged. [Cross-OS success #41621021272](https://github.com/lijust/EREI-3.2/actions/runs/41621021272) then verified all tests before the live experiment.

**Privilege control:** After the live evidence, App F2 rootful secondary Docker CI restored to manual-only in workflow-only commit fdd187ff615065249874fa5a083c9ed2de78aa75. All PRs Draft/unmerged; the default host daemon was never stopped.

## Negative-control ladder and what remains

| Stage | Where the CREATE exists BEFORE empty scans | Actually proven | Still missing |
|---|---|---|---|
| F1, actual | Admitted in an in-process local queue, NOT sent to Docker | A fixed owned CID can be created AFTER two empty real Docker scans | No Docker request submitted before scans |
| F2, actual | Exact owned Docker Unix socket has received POST headers + INCOMPLETE body | Two empty inventories do not identify pending partial protocol request; valid CID created after request completion | No COMPLETE POST submitted before scans; Docker app/transaction completion time not attested |
| F3, proposed | Entire immutable fixed POST submitted before empty scans; application/response deliberately delayed | Must be independently witnessed with safe controlled transport/server boundary | Not implemented or verified |
| F4, proposed | Sealed old-generation token from a stale async client after a restart | Enforced broker denies request before it reaches Docker | Not implemented or verified |
| L3 trust, proposed | Separately administered verifier process/host and protected key | Independent signed receipt of no CREATE admission and drained in-flight queue | Not implemented or verified |

Only a strict exclusive CREATE transport with OS-enforced denial of bypass routes, durable fsync WAL records, monotonic generation/fencing across daemon restarts and an independently authenticated verifier can potentially prove quiescence. A single user-process flag, a J5-04B PREPARED record, a CRC/hash checksum, or repeated cgroup/inventory emptiness cannot substitute.

## Implementation order without interfering with production

1. Build an EXCLUSIVE fixed-only CREATE broker contract as a separate adapter with statically closed API surface, read/write access controls to temporary Docker Unix socket, protected generation and sealed/drain semantics. Start with negative controls and a disposable secondary daemon; DO NOT change worker execution routes or allow untrusted code.
2. Build a durable in-flight/unknown lifecycle ledger with correct crash recovery behavior. A timeout or half-sent request is UNKNOWN until exact name/CID is reconciled or old generation permanently fenced.
3. Design a fixed-only, bounded real complete-POST delayed-server fixture. Never claim daemon application delay from a partial-body test. Positive outcome must still report noncertifying HOLD.
4. Parallel work: independently administered verifier trust root/protected key and signed epoch/fence receipt, per [Framework ADR #131](https://github.com/lijust/EREI-Engineering-Framework/pull/131) and F1 [ADR #132](https://github.com/lijust/EREI-Engineering-Framework/pull/132).
5. Only after independent acceptance gates: worker sandbox, full process tree/shim accounting and prospective hidden Oracle for AI learning.

Permanent state: independent_verifier_attested=false, creation_quiescence_barrier_proven=false, late_async_create_excluded=false, worker_isolation_certified=false, untrusted_code_execution_authorized=false, independently_verified=false, independent_model_patch_oracle_established=false, decision=BLOCK_AI_ACCEPTANCE, learning_effectiveness=NOT_ESTABLISHED.
