---
name: security-review
description: Review a concrete implementation against its threat model, trust boundaries, authorization/tenant invariants, sensitive-data handling, privileged operations, and security controls. Use for L3/L4 security-sensitive changes and whenever implementation could create authorization bypass, cross-tenant exposure, sensitive-data leakage, unsafe privileged/destructive behavior, or a material external trust boundary.
---

# Security Review

## Objective

Determine whether the implemented system enforces the intended security boundaries in code/config/runtime, not merely in design or UI.

## Trigger when
- threat model identifies material security paths,
- auth/authz/tenant logic changes,
- sensitive-data handling/export/logging changes,
- privileged/admin/destructive operations change,
- a new external trust boundary/integration is introduced,
- Security Engineer or Router requires independent review.

## Required inputs
- threat model or explicit security scope,
- architecture/project security model,
- implementation diff/current code/config,
- risk classification,
- relevant tests/runtime evidence,
- project/overlay security standards.

## Procedure

### 1. Reconstruct intended security invariants
Examples:
- authenticated identity comes from trusted provider/session,
- authorization is server-side,
- user cannot select unauthorized tenant scope,
- object ownership is checked,
- privileged action requires explicit authority,
- sensitive data is scoped and not leaked via cache/log/error/export,
- destructive operations have appropriate controls.

### 2. Trace enforcement points
For each invariant locate where it is actually enforced.

Flag controls that exist only in:
- UI visibility,
- client-side validation,
- documentation/comments,
- caller convention,
without authoritative backend/runtime enforcement where required.

### 3. Review input and identity trust
Identify untrusted values used for:
- user identity,
- role,
- tenant/company,
- object ownership,
- permission,
- redirect/destination,
- file/resource path,
- query/filter scope,
- privileged operation parameters.

Confirm trusted derivation/validation appropriate to context.

### 4. Review data/control isolation
Check direct and indirect paths:
- primary query/write paths,
- cache keys/scope,
- exports/reports,
- background jobs,
- logs/errors,
- bulk operations,
- admin tooling,
- retries/replays.

### 5. Review failure behavior
Security-sensitive failures should not accidentally broaden access or bypass controls. Assess fail-open/fail-closed behavior based on operation risk.

### 6. Review dependencies/integrations
For new material dependencies/services inspect:
- privilege/data shared,
- credentials/config,
- provenance/version risk,
- failure/timeout behavior,
- external assumptions from threat model.

### 7. Map implementation to threats
Each blocking/high threat should have:
- control location,
- implementation evidence,
- verification evidence or explicit gap,
- residual risk disposition.

### 8. Run/require targeted negative verification
Examples:
- wrong tenant,
- wrong owner,
- missing role,
- stale/replayed request,
- manipulated client parameter,
- direct endpoint invocation without UI path,
- cache scope crossover.

### 9. Produce findings
Severity:
- `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`.

CRITICAL/HIGH findings should be concrete and evidence-backed.

## Required output

```text
Security scope:
Threat model reference:
Security invariants:
Enforcement points:
Negative paths checked:
Critical findings:
High findings:
Medium/low findings:
Verification evidence:
Residual risks:
Accepted risks/authority:
Security verdict: PASS | PASS_WITH_ACCEPTED_RISK | BLOCK
```

## Stop / block conditions

Return `BLOCK` for unresolved credible critical/high failures such as cross-tenant exposure, authorization bypass, material sensitive-data exposure, or privileged operation without trustworthy authorization.

## Rationalizations to reject
- "The UI never sends that value."
- "Only admins know the endpoint."
- "The route requires login, so it is authorized."
- "The tenant ID is read-only in the form."
- "The cache is internal."
- "The library probably sanitizes it."
- "No scanner warning means no issue."
- "We tested the allowed case, so denied cases are unnecessary."

## Definition of Done

Intended security invariants are traced to real enforcement points, credible negative paths are reviewed/verified, findings have proportional severity and evidence, and blocking residual risks are explicit.