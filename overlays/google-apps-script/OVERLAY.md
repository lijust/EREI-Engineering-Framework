# Google Apps Script / Google Sheets Overlay

**Status:** Draft V1  
**Scope:** Apps Script web applications and Google Sheets-backed application/data workflows.

## Purpose

Provide platform-specific engineering rules that augment EREI Framework Core without contaminating the technology-neutral Constitution, roles, or generic skills.

This overlay is loaded only when a project uses Google Apps Script, HTML Service, `google.script.run`, SpreadsheetApp/Sheets API, Apps Script web deployments, CacheService, LockService, PropertiesService, or related Google Workspace runtime constraints.

## Routing tags

Load only the relevant modules:

| Tag | Module |
|---|---|
| `apps-script:quotas` | `references/QUOTAS_RUNTIME.md` |
| `apps-script:concurrency` | `references/CONCURRENCY_LOCKS.md` |
| `apps-script:client-server` | `references/CLIENT_SERVER.md` |
| `apps-script:cache` | `references/CACHE_PROPERTIES.md` |
| `apps-script:sheets` | `references/SHEETS_DATA_ACCESS.md` |
| `apps-script:deployment` | `references/WEBAPP_DEPLOYMENT_IDENTITY.md` |
| `apps-script:performance` | quotas + client-server + sheets + cache modules as relevant |

Do not load the full overlay for every Apps Script task.

## Platform invariants

### G-001 — Service calls are expensive relative to in-memory JavaScript
Minimize calls to Google/external services; batch spreadsheet reads/writes and compute in memory where practical.

### G-002 — Runtime and quota limits are architecture constraints
Design operations to finish within current platform limits with headroom. Never hard-code quota assumptions into Framework Core because Google states quotas/limits may change.

### G-003 — `google.script.run` is asynchronous and unordered
Client calls may complete/run in a different order than issued. State-sensitive flows require explicit request identity/order semantics rather than assuming call order.

### G-004 — Client/server calls need explicit failure handling
Material UI operations should define success and failure behavior. Silent console-only failure is insufficient for production workflows.

### G-005 — Frontend remains untrusted
Every top-level server function callable by the client is an API surface. Hidden buttons, private UI state, or JavaScript variables do not authorize server actions.

### G-006 — Cache scope is a security/data boundary
Script cache is shared by all users of the script. User-specific or tenant-sensitive values must not be placed in a shared cache without an explicit scope-safe key/design.

### G-007 — Lock scope must match the protected resource
Choose user/script/document lock based on the actual shared mutable resource. Acquiring a lock broader than necessary harms concurrency; narrower than necessary fails correctness.

### G-008 — Locks are not acquired merely by requesting a Lock object
`getScriptLock()`, `getUserLock()`, or `getDocumentLock()` return a lock object; code must call `tryLock()` or `waitLock()` to acquire it.

### G-009 — Properties stores have different scopes and finite capacity
Script properties are shared across script users; user properties are user-scoped; document properties are context-dependent. Treat properties as configuration/small metadata, not a general database.

### G-010 — Web app execute-as choice is a security architecture decision
Executing as deployer/owner and executing as accessing user create different authority models. The choice must be explicit in the project security model and threat model when permissions matter.

### G-011 — Never expose server OAuth tokens to the client
OAuth tokens obtained server-side may grant access to protected resources and must not be transmitted to browser code.

### G-012 — Stable deployment uses versions/deployments, not saved editor state
Development/test deployment and stable production deployment are separate concepts. Production promotion must retain version/deployment identity and rollback path.

### G-013 — Spreadsheet data access must be batched and scoped
Prefer range/batch reads and writes. Avoid alternating per-cell reads/writes in loops. Read only required data when scale is material.

### G-014 — Success response does not prove persistence/invariants
For critical writes, verify expected persisted state/read-back when the workflow requires it.

### G-015 — Sheets is not an unlimited database
As dataset size, formula complexity, concurrent writes, or relationship/query complexity grows, explicitly evaluate whether Sheets remains fit for purpose rather than masking architectural limits with caching.

## Usage with Framework Core

Examples:

- Performance investigation → load quotas, client-server, sheets, cache.
- Stale request bug → load client-server + concurrency.
- Multi-user write race → load concurrency + sheets + security context.
- Auth/deployment change → load webapp deployment identity + Security Core.
- Search cache optimization → load cache + tenant security + performance.
- Configuration bug → load properties module.

## Freshness rule

For decisions dependent on numeric quotas, authorization behavior, deployment behavior, or current APIs, verify the current official Google documentation. `SOURCES.md` records the baseline references used to create this overlay.