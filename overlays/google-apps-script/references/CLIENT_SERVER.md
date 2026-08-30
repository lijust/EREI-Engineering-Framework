# Apps Script HTML Client / Server Boundary

**Source baseline:** official HTML Service communication documentation, verified 2026-08-31.

## Current platform facts

- `google.script.run` calls server-side Apps Script asynchronously.
- Concurrent calls may execute/complete in an order different from the order issued.
- The page can have up to 10 concurrent `google.script.run` server calls; excess calls wait for capacity.
- Success and failure handlers are the response/error mechanisms.
- Parameters/return values must use supported serializable types; arbitrary functions, DOM nodes, Dates, circular structures, etc. are restricted.
- Top-level callable server functions are an API surface. Functions ending in underscore are private from `google.script.run` under the documented behavior.

## Engineering rules

### CS-001 — Every state-sensitive call gets request identity
For search/autocomplete/save flows where old responses can overwrite new state, attach a request identity/sequence and reject/ignore stale results according to a documented invariant.

### CS-002 — Never infer ordering from call order
Two calls fired in order A then B do not establish server completion order A then B.

### CS-003 — Bound client concurrency intentionally
Do not flood `google.script.run` with one server call per UI element/row/keystroke. Debounce/coalesce/batch where appropriate.

### CS-004 — Use success and failure handlers for production flows
UI state must transition explicitly for success/failure. A failure visible only in the browser console is not adequate for critical user operations.

### CS-005 — Separate transport DTOs from internal objects
Return compact serializable DTOs. Do not expose server objects or unnecessary raw Sheet rows merely because serialization permits objects/arrays.

### CS-006 — Client parameters are untrusted
Validate and authorize server-side:
- user identity/role claims,
- tenant IDs,
- row/project/client IDs,
- filters that affect data scope,
- operation names/commands,
- values used for writes.

### CS-007 — Public server functions should be deliberate
Keep helper/internal functions private where possible and expose a small explicit application API surface.

### CS-008 — Retry semantics must be designed
A browser/server transport failure can leave the client uncertain whether a state-changing call executed. Retrying blindly can duplicate writes; use idempotency/request IDs for sensitive operations.

### CS-009 — Loading and stale-response state are separate concerns
A UI can finish request B while older request A is still running. Loading indicators and response application should track the active/current request, not a single global boolean when concurrent operations are possible.

## Recommended client call wrapper behavior

A project may standardize a wrapper that provides:
- generated request ID,
- start timestamp,
- success handler,
- failure handler,
- timeout/user feedback policy,
- stale-response check,
- normalized error mapping,
- optional telemetry duration.

The wrapper must not hide authorization errors or automatically retry non-idempotent operations.

## Verification scenarios
- rapid repeated search input,
- response B returns before A,
- refresh/reset then first request,
- failure handler path,
- 10+ concurrent calls/burst,
- client manipulates tenant/role/ID,
- retry after ambiguous failure.