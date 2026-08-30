# Regression Analysis Evals

**Status:** Draft V1

## R-001 — Shared API contract
Scenario: backend changes error response shape used by web UI and export integration.
Expected:
- include both consumers in regression surface,
- verify compatibility/updated consumers,
- do not scope testing only to backend unit.

## R-002 — Security fix
Scenario: ownership check added to record update endpoint.
Expected:
- verify allowed owner path,
- wrong-owner/tenant negative paths,
- neighboring privileged/admin behavior if applicable,
- preserve regression test for original bypass.

## R-003 — Blank-only data write
Scenario: enrichment logic changes batching implementation but must still write only blank cells.
Expected:
- preserve populated values,
- verify blank writes,
- include identity/row mapping and read-back where risk warrants.

## R-004 — Isolated CSS
Scenario: border radius changes in scoped component.
Expected:
- classify regression surface narrowly,
- no full backend/security suite by default.

## R-005 — Refactor without intended behavior change
Scenario: search filtering logic is reorganized into modules.
Expected:
- identify representative filters/edge combinations and contract outputs,
- test behavior preservation,
- do not assume refactor is safe because public signature is unchanged.

## R-006 — Stale request fix
Scenario: request ordering mechanism changes after `STALE_REQUEST` bug.
Expected:
- original refresh regression,
- out-of-order responses,
- rapid requests,
- normal sequential requests,
- no need to retest unrelated static UI.

## R-007 — Full suite false confidence
Scenario: full suite passes but no test invokes newly changed export path.
Expected:
- identify coverage gap despite green suite.

## R-008 — Unknown consumers
Scenario: shared function has dynamic callers that cannot be fully enumerated.
Expected:
- surface uncertainty, raise regression risk, use broader verification or discovery rather than claiming isolation.