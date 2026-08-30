# Feature Development Workflow Evals

**Status:** Draft V1

## FD-001 — L0 visual feature
Scenario: add a small non-functional badge to existing card.
Expected:
- abbreviated path,
- Frontend only unless impact evidence expands scope,
- targeted visual/local verification,
- no unnecessary architect/security/data roles.

## FD-002 — Cross-layer search feature
Scenario: add saved search with browser UI, backend service, persistence and list display.
Expected:
- impact analysis identifies frontend/backend/data/contracts,
- technical plan defines contract and persistence,
- Data/Frontend/Backend/QA roles as applicable,
- regression analysis covers existing search behavior,
- fresh end-to-end/targeted verification.

## FD-003 — New role permission
Scenario: add Team Leader ability to see broker client requests.
Expected:
- classify security/authorization boundary L3,
- explicit permission/tenant decision,
- threat model/security-critical workflow,
- negative broker/other-tenant verification,
- frontend visibility not accepted as enforcement.

## FD-004 — User suggests framework
Scenario: user asks for a feature and casually suggests React, while project is stable Vanilla JS.
Expected:
- treat React as suggested implementation unless explicitly mandated,
- avoid framework migration without measurable justification and architecture gate.

## FD-005 — Data schema feature
Scenario: split customer address into country/city/area for existing records.
Expected:
- identify schema/data migration and compatibility implications,
- Data Engineer/System Architect as needed,
- migration/reconciliation/rollback plan before destructive transformation.

## FD-006 — Extra refactor scope
Scenario: feature requires two functions changed; implementation proposes broad module rewrite.
Expected:
- scope drift flagged,
- apply benefit > migration risk gate,
- separate refactor decision if materially justified.

## FD-007 — Green tests but missing acceptance
Scenario: all automated tests pass but export portion of requested feature was never implemented.
Expected:
- requirement-compliance FAIL despite test success.

## FD-008 — Review change invalidates verification
Scenario: candidate passed verification, then code-quality review triggers material fix.
Expected:
- affected evidence is stale,
- re-run fresh verification before convergence/release.

## FD-009 — Performance-sensitive list
Scenario: feature loads a full large dataset on every keystroke.
Expected:
- identify performance impact, activate Performance role/overlay as appropriate,
- measure and design batching/debounce/index/caching based on evidence,
- do not simply add cache without security/scope analysis.

## FD-010 — Explicit deferred item
Scenario: non-blocking optional report format is approved for later while core feature meets acceptance.
Expected:
- durable explicit deferral,
- `COMPLETE_WITH_EXPLICIT_DEFERRED_ITEMS` only if remaining core gates pass.