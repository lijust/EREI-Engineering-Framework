# Requirement Compliance Review Evals

**Status:** Draft V1

## C-001 — Missing requirement
Spec requires search results plus export. Implementation adds search only.
Expected: search `SATISFIED/NOT_VERIFIED` depending evidence; export `NOT_SATISFIED`; verdict FAIL.

## C-002 — Scope expansion
Spec requests bug fix only. Implementation also rewrites unrelated data layer.
Expected: flag unapproved scope drift even if code is clean.

## C-003 — Constraint violation
Requirement: fill only blank cells. Implementation overwrites existing values when source is newer.
Expected: explicit constraint violation; FAIL.

## C-004 — Code present but unverified
Implementation contains cache invalidation logic but no test/runtime evidence.
Expected: distinguish implementation presence from verified compliance; use `NOT_VERIFIED` where evidence is required.

## C-005 — Explicit deferral
One non-blocking report format is explicitly accepted for later release.
Expected: `PASS_WITH_DEFERRED` only if core requirements are satisfied and deferral is durable/approved.