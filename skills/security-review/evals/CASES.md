# Security Review Evals

**Status:** Draft V1

## SR-001 — Hidden admin button
Implementation hides admin button for brokers but endpoint lacks role check.
Expected: HIGH/CRITICAL depending impact; BLOCK; UI is not enforcement.

## SR-002 — Direct tenant manipulation
Backend accepts tenant ID from request and checks only that user is logged in.
Expected: identify authorization/tenant bypass; BLOCK.

## SR-003 — Allowed-path-only tests
Tests verify manager can view reports; no test verifies broker cannot access manager report endpoint.
Expected: require negative authorization test; verification gap.

## SR-004 — Cache isolation
Authorization query is correct but shared cache key excludes tenant/user scope.
Expected: identify indirect cross-tenant leakage path.

## SR-005 — Logging leak
Error logger records full authentication token or sensitive customer payload.
Expected: sensitive-data finding with evidence and remediation.

## SR-006 — Fail-open permission service
Permission lookup error defaults to allowed access.
Expected: serious finding for sensitive operation; recommend fail-closed or justified bounded behavior.

## SR-007 — Scanner false comfort
Static scanner reports zero issues but route-level ownership checks were not reviewed.
Expected: scanner is evidence input, not proof; continue boundary review.

## SR-008 — Proportionality
Low-risk public static page change with no auth/data path.
Expected: no full security review unless other evidence raises risk.