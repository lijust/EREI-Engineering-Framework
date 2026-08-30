# Engineering Quality Review Evals

**Status:** Draft V1

## Q-001 — Real blocker
Scenario: backend endpoint accepts tenant_id from request and queries that tenant without verifying server-side membership.
Expected: BLOCKER/HIGH depending context; explicit cross-tenant failure mode; route Security review.

## Q-002 — Refactor temptation
Scenario: correct 40-line function follows project pattern; reviewer prefers a new abstraction hierarchy.
Expected: do not block or recommend large refactor without measurable benefit.

## Q-003 — Concurrency
Scenario: duplicate retry may execute the same state-changing operation twice.
Expected: identify idempotency/duplicate execution risk; severity based on data impact.

## Q-004 — Performance inference
Scenario: reviewer notices repeated sheet reads in a loop but no benchmark exists.
Expected: identify plausible performance risk and request measurement; do not claim a measured regression.

## Q-005 — Vague style complaint
Scenario: code differs from reviewer's personal naming preference but matches project standards.
Expected: no finding solely based on personal preference.

## Q-006 — Test-count fallacy
Scenario: 100 tests pass but none exercise the changed authorization branch.
Expected: identify verification gap; do not infer coverage from test count.