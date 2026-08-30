# Apps Script Cache and Properties

**Source baseline:** official CacheService, PropertiesService, and quota documentation, verified 2026-08-31.

## Scope distinctions

### CacheService
- Script cache: shared by all users of the script.
- User cache: scoped to current user + script.
- Document cache: current document + script; may be unavailable outside containing-document context.

### PropertiesService
- Script properties: shared across all users of the script.
- User properties: current/effective user + script.
- Document properties: documented bound/add-on contexts only.

Current official Apps Script limits include property value/store size constraints; verify current quota docs for numeric capacity decisions.

## Engineering rules

### CP-001 — Cache is an optimization, not source of truth
Correctness must survive cache miss, eviction, expiry, and stale entries.

### CP-002 — Cache scope is part of authorization/data isolation
Never cache user/tenant-sensitive results in shared ScriptCache with a key that omits trusted user/tenant/security scope.

### CP-003 — Security context must come from trusted server state
Do not build a cache key from client-supplied tenant/user IDs unless the server first validates/resolves them.

### CP-004 — Cache keys need version/invalidation strategy
When underlying data or rules change, stale cached objects must not silently violate correctness. Use versioned keys, explicit invalidation, bounded TTL, or another defined strategy.

### CP-005 — Avoid cache stampede where expensive recomputation matters
For highly requested expensive shared values, consider bounded locking/single-flight style recomputation, but do not globally lock unrelated users unnecessarily.

### CP-006 — Properties are small configuration/state metadata
Appropriate examples:
- deployment/runtime config,
- small feature flags,
- small durable checkpoints,
- version markers,
- non-secret identifiers/metadata where scope is correct.

Do not use PropertiesService as a general relational/user-record database.

### CP-007 — Property scope must match semantics
- global script config → ScriptProperties,
- user-specific preference/checkpoint → UserProperties,
- document-bound metadata → DocumentProperties only where supported.

### CP-008 — Shared properties are not private from other script users/executions
Do not treat ScriptProperties as per-user isolation.

### CP-009 — Secrets require deliberate handling
Do not send secrets/property values to client code. Assess whether Apps Script Properties is appropriate for the sensitivity and operational model; use project security model and available secret-management architecture rather than assuming "property" means secret vault.

### CP-010 — Cache invalidation must be tied to writes
If a mutation changes data used by cached reads, define which keys are invalidated/versioned and when. A successful write with stale cached read path is an application defect.

## Cache review checklist

For each cache:
- what is cached,
- source of truth,
- scope (script/user/document),
- trusted scope key inputs,
- TTL,
- invalidation/versioning,
- stale-data tolerance,
- sensitive fields,
- max practical payload,
- miss/recompute cost,
- concurrency behavior.

## Verification scenarios
- user A cache cannot appear for user B,
- tenant A cannot hit tenant B key,
- mutation invalidates/versions relevant result,
- cache miss returns correct result,
- expired/evicted cache is safe,
- stale cache does not bypass authorization/business rule.