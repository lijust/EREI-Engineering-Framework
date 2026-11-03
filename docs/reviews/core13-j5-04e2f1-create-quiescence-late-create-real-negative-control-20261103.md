# Core13 J5-04E2F1 — actual late Docker CREATE after empty inventories: negative-control ADR

3 November 2026 | Reusable Framework evidence and next-stage engineering contract.

## Actual evidence, not hypothetical

App [Draft #257](https://github.com/lijust/EREI-3.2/pull/257) implements a fixed-source, locally queued Docker CREATE. Its source-reviewed J5-04B PREPARED intent is persisted before a one-process AdmissionFence admits the exact fixed J4 name. The one-shot queue is SEALED while one request is still pending. A real worker thread is held BEFORE issuing HTTP POST. Two genuine Linux SO_PEERCRED-bound private Docker inventory scans return exactly empty. Only then the queued fixed request is released, causing a real, full 64-hex CID to appear.

Actual evidence: [GitHub Actions #41619674881](https://github.com/lijust/EREI-3.2/actions/runs/41619674881), tested code HEAD a2f565693d6dadee9879fe8d7aeaf3f455e2bb7f. ALL 3 jobs SUCCESS: Ubuntu 121 PASS and Windows 121 PASS offline, plus one fixed-only disposable hosted Ubuntu rootful SECONDARY dockerd. The source-approved immutable image was validated; the created container was never started. Exact CID/name/label/image verified. The one owned CID was removed with real inspect 404/empty private inventory BEFORE stopping secondary daemon; host primary Docker unchanged.

The actual result explicitly confirmed:
- durable_prepared_intent_written_before_local_admission=true
- fixed_create_admitted_to_local_queue_before_two_empty_scans=true
- two_peer_bound_private_docker_inventory_scans_empty=true
- real_fixed_container_created_only_after_empty_scans=true
- real_fixed_container_never_started=true
- real_exact_owned_cid_removed_and_private_inventory_empty=true
- broker_queue_was_local_only_not_exclusive=true
- actual_docker_inflight_request_preceded_scans=false
- creation_quiescence_barrier_proven=false; late_async_create_excluded=false
- worker_isolation_certified=false; untrusted_code_execution_authorized=false
- decision=BLOCK_AI_ACCEPTANCE; learning_effectiveness=NOT_ESTABLISHED

Following the one actual run, rootful Docker was made manual-only in App commit f66dd6de78d27bfb39a9b4a0276a8ef2a17dc490. [Post-reset Actions #41619867181](https://github.com/lijust/EREI-3.2/actions/runs/41619867181) shows both OS offline jobs SUCCESS and rootful job SKIPPED.

IMPORTANT: the local queue admitted the create BEFORE scans, but Docker had NOT been sent the request. This is NOT a Docker-in-flight request finishing late. It is a real Docker counterexample to reasoning that two correct empty inventories exclude future creations by an already admitted LOCAL producer. The AdmissionFence is neither exclusive over all Docker transports nor independently authenticated; an emptied or sealed local queue does not certify runtime quiescence.

## Required global creation-quiescence invariants (not met)

1. Exclusive authority over ALL worker CREATE/START/retry paths. Raw daemon socket and Docker context bypass must be denied at OS permission/namespace boundary. Local Python convention is not sufficient.
2. Durable write-ahead PREPARED record, fsync before HTTP emission: exact source-reviewed fixed image/code digest, request id, daemon identity, host boot, monotonic generation/epoch, expected name and immutable config. Unknown write -> no send.
3. Fencing: a SEALED generation must reject old-generation requests at the enforced transport (including delayed threads, retries, reconnects). Cannot depend only on local in-memory flags.
4. In-flight drain: every PREPARED, EMITTED and CREATE_UNKNOWN request must be shown completed and reconciled to an exact owned CID, or securely fenced against all later completion. Empty inventory is not a substitute.
5. Daemon restart: preserve old generation ledger, bind new daemon epoch, reject/reconcile old delayed calls; do not turn lost socket or connection timeout into success.
6. Independent verifier L3: separately administered principal and trust root protecting source measurement and signing key inaccessible to worker/controller, signed fresh generation-close and drained-inflight receipts. Same-UID SO_PEERCRED and SHA digest agreement from App #255/#256 provide local peer consistency only.
7. Full owned workload/process/cgroup accounting, including child groups, shims, reparented processes and creation races. A missing cgroup path is not a complete closure proof.
8. Model patch acceptance and stable readiness remain blocked until separate hidden behavioral Oracle and all isolation gates independently pass.

## Required RED negative controls and ownership

F1 ACTUAL COMPLETE: locally queued fixed request admitted before seal, TWO empty real private Docker inventories, release and real late owned fixed CID. Expected RED for quiescence, PASS for counterexample witness.

F2 NOT ESTABLISHED: actual Docker HTTP POST bytes already sent before the two empty reads; carefully controlled delayed server acceptance/application/response. Different from F1; requires a deterministic and safe scoped transport experiment, not guessed sleeps.

F3 NOT ESTABLISHED: sealed generation N with stale token released after generation N+1 restart; broker/OS transport MUST refuse before reaching Docker.

F4 NOT ESTABLISHED: foreign direct socket create bypass; permissions MUST block before dispatch.

F5 NOT ESTABLISHED: daemon crash during EMITTED/UNKNOWN operation; journal stays TERMINAL_HELD until independently reconciled.

F6 NOT ESTABLISHED: escaped/reparented/shim process or child cgroup after daemon stop; separately authenticated observer detects it.

F7 NOT ESTABLISHED: replay/forgery of same-UID verifier nonce/hash cannot elevate an external protected-principal signature.

## Next conflict-free execution

Start F2 with a fixed reviewed local-transport fixture proving HTTP request bytes are transmitted before an empty observation, while explicitly distinguishing local proxy reception from Docker request processing. Develop the enforceable transport/generation ledger in parallel but do not wire it into production worker paths until bypass denial is verified. Develop L3 verifier identity/independently protected signing authority separately, per [Framework Draft #131](https://github.com/lijust/EREI-Engineering-Framework/pull/131).

Keep every PR Draft/unmerged. Permanent flags: worker_isolation_certified=false, untrusted_code_execution_authorized=false, independent_model_patch_oracle_established=false, independent_verifier_attested=false, creation_quiescence_barrier_proven=false, late_async_create_excluded=false, independently_verified=false, decision=BLOCK_AI_ACCEPTANCE, learning_effectiveness=NOT_ESTABLISHED.
