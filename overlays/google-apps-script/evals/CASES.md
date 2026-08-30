# Google Apps Script Overlay Evals

**Status:** Draft V1

These cases test whether applicable Core roles/skills load the correct overlay modules and avoid Apps Script-specific failure modes.

## GAS-001 — Stale request after refresh
Scenario: frontend request sequence resets to 0 after refresh while server/workspace remembers a higher sequence.
Expected:
- load client-server + concurrency references,
- identify ordering invariant rather than blindly incrementing local counter,
- design monotonic/request-identity semantics appropriate to scope,
- verify refresh + first request + out-of-order response cases.

## GAS-002 — Search latency
Scenario: normal search takes 14 seconds and repeatedly reads multiple sheet columns in loops.
Expected:
- load sheets + quotas/runtime + client-server references,
- measure service-call count/rows/payload and server duration,
- recommend batching/in-memory indexing where evidence supports it,
- compare against framework performance budget,
- do not optimize blindly by adding cache first.

## GAS-003 — Tenant-sensitive script cache
Scenario: cache key is only query text, ScriptCache is used by multi-tenant web app.
Expected:
- identify ScriptCache shared-user scope,
- raise security/data risk,
- require trusted tenant/user scoping or safer cache design,
- negative cross-tenant test.

## GAS-004 — Wrong lock scope
Scenario: each broker uses UserLock while all brokers increment one shared company sequence in the same sheet.
Expected:
- user lock is too narrow for shared resource,
- choose resource-appropriate serialization or redesign,
- do not call user lock tenant isolation.

## GAS-005 — Lock object not acquired
Scenario: code calls `LockService.getScriptLock()` and immediately writes without `tryLock`/`waitLock`.
Expected:
- identify that no lock was acquired,
- require bounded acquisition and failure behavior.

## GAS-006 — Per-cell write loop
Scenario: 1000 rows updated with one `setValue` call per cell.
Expected:
- load Sheets data-access reference,
- recommend batched range write when semantics permit,
- measure improvement rather than assume target latency.

## GAS-007 — Execute as owner
Scenario: public/internal web app executes as deployer and accepts `userEmail`/`tenantId` from client to determine data access.
Expected:
- load deployment identity + Security Core,
- treat client identity/scope as untrusted,
- require authoritative application identity/membership resolution,
- classify at least L3 for auth/tenant boundary.

## GAS-008 — Execute as user
Scenario: app executes as accessing user and team assumes Google login automatically enforces CEO/Broker roles.
Expected:
- distinguish Google identity from application authorization,
- require server-side project role/tenant checks.

## GAS-009 — Properties as database
Scenario: app stores thousands of customer records in ScriptProperties.
Expected:
- identify scope/capacity/architecture mismatch,
- route toward appropriate persistent data model instead of treating PropertiesService as database.

## GAS-010 — Ambiguous retry
Scenario: browser times out after save call and automatically retries; first call may have already committed.
Expected:
- load client-server + concurrency references,
- require idempotency/request identity for sensitive writes,
- verify duplicate execution behavior.

## GAS-011 — Development deployment confusion
Scenario: `/dev` test URL passes but production deployment still points at previous version.
Expected:
- do not declare release verified,
- require deployment/version identity and production-target verification.

## GAS-012 — Large Sheets workload
Scenario: growing application relies on ever larger full-sheet reads, many formulas, concurrent users, and frequent timeouts.
Expected:
- identify architectural fit question,
- measure current limits/cost,
- consider database/hybrid migration boundary rather than endless micro-optimizations.