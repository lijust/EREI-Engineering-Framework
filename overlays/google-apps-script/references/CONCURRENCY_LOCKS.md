# Apps Script Concurrency and Locking

**Source baseline:** official Google LockService and Apps Script quota docs, verified 2026-08-31.

## Lock scopes

### Script lock
Serializes the guarded code across all users/executions of the script.

Use when the protected resource is truly global to the script, such as a shared sequence or shared mutable structure that cannot tolerate concurrent mutation.

### User lock
Serializes guarded code only for the current user while allowing different users to proceed concurrently.

Use for per-user mutable resources when cross-user serialization is unnecessary.

### Document lock
Serializes within the current containing document. It may return `null` outside supported containing-document contexts such as standalone scripts/web apps.

## Critical fact

Calling `getScriptLock()`, `getUserLock()`, or `getDocumentLock()` does **not** acquire the lock. The code must successfully call `tryLock(timeout)` or `waitLock(timeout)`.

## Engineering rules

### C-001 — Lock the resource, not the function name
Define what mutable invariant is protected before choosing lock scope.

### C-002 — Keep critical sections small
Do expensive reads/network work before entering the lock when correctness permits. Hold the lock only around operations that must be serialized.

### C-003 — Avoid global locks for tenant/user-local work
A script-wide lock can turn independent users into a single queue and destroy throughput.

### C-004 — A user lock is not tenant isolation
If multiple users modify one tenant-shared resource, a user lock is too narrow. Security tenant scope and concurrency resource scope are separate questions.

### C-005 — Locking does not replace idempotency
Retries, duplicate browser calls, trigger re-execution, and client timeouts can cause repeated operations. State-changing APIs should consider idempotency even when locks are used.

### C-006 — Lock acquisition failure is an explicit outcome
Use bounded wait/try behavior and return/record a clear conflict/busy error. Do not spin or silently continue without the required lock.

### C-007 — Establish write protocol
For shared Sheets state, define a consistent pattern such as:
1. acquire appropriate lock,
2. re-read authoritative state inside lock if stale reads matter,
3. validate invariant/precondition,
4. perform batched write,
5. flush/read-back only when required for correctness,
6. release lock in guaranteed cleanup path.

### C-008 — Sequence/order controls need monotonic semantics
For stale-request protection, define whether ordering is per browser session, user, tenant, or global. A request counter reset after refresh can conflict with server-stored sequence state; timestamp/random/request IDs have different collision/order properties and must match the invariant.

## Failure modes
- requested lock but never acquired,
- wrong lock scope,
- long external API call while holding global lock,
- stale pre-lock read used for post-lock write,
- duplicate operation after client retries,
- global serialization used as substitute for tenant-aware data design,
- swallowed timeout causing partial/silent failure.

## Verification

Concurrency-sensitive changes should include targeted tests/simulations for:
- two simultaneous writers,
- duplicate request,
- stale request/order inversion,
- lock timeout,
- retry after ambiguous client failure,
- different users/tenants operating concurrently.