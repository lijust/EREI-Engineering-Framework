# EREI Engineering Framework — F5A atomic zero-outstanding CREATE intent rotation contract

**5 November 2026 | Framework Draft successor to Alpine B2B2 #158.**

## The actual flaw in local F5

The source-pinned original EREI-3.2 module `tools/core13_j5_04f3_local_sqlite_generation_fence.py` (Git blob `ec4cd704b8865193761cdb836c68d58d6f929f17`) persists one durable SQLite/WAL table with three unresolved CREATE-intent phases:
- `PREPARED`: valid reviewed config and requested name committed, no known Docker send yet.
- `EMITTED_UNKNOWN`: write-ahead record committed before optional transport; response could be delayed or unknown.
- `RETURNED_CLAIM`: optional callback returned a CID, **not a verified container state or cleanup**.

Old `seal()` correctly disclaims generation quiescence but old `rotate()` can advance the generation after seal **even if any of these unresolved rows remain**. This is specifically covered in original F5 tests (#16/#17/#39): it is an observational test fixture, not a production-safe CREATE drain gate. Source-only methods that simply inspect `pending_unresolved_count` or check only the current generation would miss historical intents.

## F5A verified improvement

New App module `tools/core13_j5_04f5a_atomic_no_unresolved_generation_rotation.py` is an **additive, reviewed, locally durable strict alternative**, NOT a replacement for the old f5.rotate entrypoint. It verifies the exact original F5 Git source blob, invokes the original private-root and SQLite WAL/full-sync configuration, and performs **one `BEGIN IMMEDIATE` transaction** containing:
1. Validate current sealed generation token, source-bound ledger, host boot consistency and changed daemon epoch label; no caller-supplied configuration/command.
2. Check `PRAGMA quick_check` and `PRAGMA foreign_key_check` for local structural errors (not cryptographic integrity, not protection against same-UID tamper).
3. Count **all rows across all historical generations** with phase `PREPARED`, `EMITTED_UNKNOWN` or `RETURNED_CLAIM`. Reject all transitions while any unresolved rows exist, even CID-claim-only histories and older generation rows.
4. When and only when pending total is zero, create new unpredictable token and new generation and **compare-and-swap** `control.current_generation` within that same transaction. A racing old-token caller must fail as stale.
5. Audit/read-only CLI returns no tokens, no file path secrets, explicitly false for daemon socket exclusivity/late async CREATE/L3/AI authority and `decision=BLOCK_AI_ACCEPTANCE`. Public execution authority always DENY.

### Real SQLite test evidence, precisely scoped

[App Actions #42041135621](https://github.com/lijust/EREI-3.2/actions/runs/42041135621), reviewed SHA `072e04ca8af1aec027acaf09d405797a30b93a5b`, completed **SUCCESS**: **28 new F5A actual SQLite/WAL tests + 40 original F5 tests + 14 D2D2 migration-deny tests = 82 PASS / 0 FAIL**. Includes:
- Real local generation rotation with zero rows; stale old token and duplicate rotation denied.
- PREPARED/EMITTED_UNKNOWN/RETURNED_CLAIM each block rotation; returned CID is not cleanup.
- Historical outstanding rows deliberately carried by legacy `f5.rotate()` still block new strict guard.
- Real threads race on a single old token; only one successful rotation.
- Real trusted fixed callback holds the SQLite write lock; a concurrent seal cannot finish and subsequent strict rotation still denies unresolved intent.
- DB foreign key corruptions, wrong host boot/daemon epoch, wrong tokens, real separate Python-process read of persistent WAL, missing source and drift, all fail closed.
- No Docker operation, image START, root Docker privilege, user/model code or project write.

**Do not call this full F5 or Docker quiescence.** It is an optional local adapter; the old `f5.rotate()` still exists and bypasses this new policy, any same-UID editor can mutate SQLite, foreign Docker sockets and async daemon callbacks are not covered, daemon epoch is only a local label and no independently observed container cleanup exists. Source pinning and atomicity are real properties; external exclusive transport and L3 attestation remain FALSE.

## Mandatory next integration

F5B must refactor the fixed root Docker broker so **ALL** CREATE paths are routed through a single source-reviewed journal pre-send and root-only socket with strict SO_PEERCRED; no alternate raw Docker endpoints or SCM_RIGHTS capability. The broker must register actual in-flight create intents, bind daemon identity/generation, complete actual CREATE/inspect/stream/STOP/REMOVE and verify absence. A sealed state and DB zero count only become a generation quiescence condition after verified owned resource cleanup, late daemon callbacks, daemon crash/restart and independent read-only verifier are handled. Old `f5.rotate()` must be removed/disabled for that integration; keeping the new strict wrapper alongside it is insufficient.

Independent image CVE/risk approval still required: Alpine candidate has 0 HIGH/CRITICAL in owner Trivy but 5 MEDIUM+1 LOW pip issues, musl compatibility not tested; F4C2 currently pins a different 47 HIGH-match Debian image. No Docker START, model-generated code, production credentials, independent L3 or `stable_ready` in this F5A PR.

```text
f5a_zero_unresolved_all_generation_atomic_sqlite_rotation=SCOPED_LOCAL_PASS
f5_legacy_rotate_unresolved_bypass_still_present=true
f5a_exclusive_runtime_adopted=false
global_docker_create_exclusivity_verified=false
foreign_docker_socket_bypass_excluded=false
late_async_daemon_create_excluded=false
real_docker_owned_cleanup_verified=false
independent_daemon_epoch_identity_verified=false
durable_f5_daemon_quiescence_proven=false
independent_l3_verification_complete=false
image_security_approved=false
untrusted_code_execution_authorized=false
stable_ready=false
decision=BLOCK_AI_ACCEPTANCE
learning_effectiveness=NOT_ESTABLISHED
```

**Reusable contract:** CREATE-intent *phase*, receipt of a CID claim, and verified resource cleanup are distinct states. All-generation unresolved counts and generation CAS must be checked **inside the same database write transaction**. Never certify external Docker quiescence from only local SQLite consistency, and never deploy a strict wrapper while leaving an alternative legacy rotate path active.

## Final PR-head source and SQLite WAL verification

[App PR-head #42041535218](https://github.com/lijust/EREI-3.2/actions/runs/42041535218), exact SHA `74dd27c9aca2b8cd0e242a831e1285c5f3ae260e`, **SUCCESS: 28 F5A +40 original F5 +14 D2D2 = 82 PASS, 0 FAIL**. Push [#42041280196](https://github.com/lijust/EREI-3.2/actions/runs/42041280196) on the same SHA also succeeded. These are local SQLite WAL/threads/real read-only second Python process and source-migration denials, **not** real Docker daemon creation or root privilege. The original `f5.rotate()` allowing unresolved rows remains active, requiring a future exclusive broker-side migration; local new-API success cannot certify F5 or L3. `BLOCK_AI_ACCEPTANCE`.
