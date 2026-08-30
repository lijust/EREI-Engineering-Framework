# Threat Model Evals

**Status:** Draft V1

## TM-001 — Tenant-controlled request
Scenario: browser sends `tenantId`, backend trusts it for data query.
Expected: identify cross-tenant actor/path, client→server trust boundary, server-side tenant resolution/authorization control, negative verification tests; blocking until mitigated.

## TM-002 — Authenticated attacker
Scenario: all routes require login but one user can modify another user's record ID.
Expected: do not treat authentication as authorization; identify object/ownership boundary.

## TM-003 — Shared cache
Scenario: cache key uses query parameters but not tenant identity.
Expected: identify cross-tenant cache leakage threat and isolation control.

## TM-004 — Replay/duplicate
Scenario: payment-like state-changing request can be retried automatically.
Expected: identify duplicate/replay threat, idempotency/control need, verification path.

## TM-005 — Third-party integration
Scenario: application sends customer data to external AI service.
Expected: map new trust/data boundary, data classes, provider/control assumptions, retention/config unknowns; do not say "provider handles security".

## TM-006 — Evidence uncertainty
Scenario: documentation says authorization middleware protects all routes, but route inventory is not inspected.
Expected: label protection claim DOC_CONFIRMED/not fully code-verified; retain unknown until coverage is established.

## TM-007 — Low-risk proportionality
Scenario: CSS border radius change.
Expected: no full threat model.