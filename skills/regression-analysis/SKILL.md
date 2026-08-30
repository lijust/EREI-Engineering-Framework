---
name: regression-analysis
description: Determine what existing behavior can be affected by a change and define proportional regression coverage using dependency, boundary, invariant, and historical-failure evidence. Use after impact analysis or bug/feature implementation, especially for L2+ changes, shared code, contract changes, state/data changes, and fixes to previously escaped defects.
---

# Regression Analysis

## Objective

Identify the smallest credible set of existing behavior that must remain correct after a change, then map that risk to targeted verification.

Regression analysis is not "run every test" and is not "test only the changed line".

## Trigger when
- material code/data/config behavior changes,
- shared module/API/contract changes,
- bug fix can affect neighboring cases,
- refactor changes implementation while behavior should remain stable,
- security/data/concurrency invariant changes,
- a real escaped defect should become permanent regression protection.

## Do not trigger full analysis when
- confirmed L0 cosmetic change has no functional impact,
- no implementation/state change is occurring.

## Required inputs
- change intent/diff,
- impact analysis,
- architecture/module dependencies,
- requirements/invariants,
- current test/eval suite,
- known incidents/bugs,
- risk level,
- relevant platform/project standards.

## Procedure

### 1. Define changed behavior and implementation surface
Separate:
- intended behavior change,
- implementation-only change,
- affected files/modules/data/contracts/config.

### 2. Build regression surface
Identify behavior connected through:
- callers/callees,
- shared functions/components,
- API consumers,
- data/schema relationships,
- cache/state/concurrency behavior,
- authorization/tenant rules,
- deployment/config assumptions,
- exports/reports/integrations.

### 3. Identify invariants that must remain unchanged
Examples:
- users outside scope remain denied,
- existing data values are preserved,
- old API clients still work where compatibility is required,
- unrelated filters still return same semantics,
- retries do not duplicate writes,
- performance stays within budget.

### 4. Use historical evidence
Include:
- previous bugs/incidents,
- flaky/fragile areas,
- prior regressions,
- production-specific failure modes.

A real escaped defect should normally create a durable regression check if practical.

### 5. Prioritize by risk
Classify candidate regression areas:
- `CRITICAL` — security/data/production invariant,
- `HIGH` — core workflow/shared contract,
- `MEDIUM` — meaningful neighboring behavior,
- `LOW` — low-impact adjacent behavior.

### 6. Select verification type
For each important area choose the cheapest reliable evidence:
- unit/domain test,
- integration/contract test,
- negative authorization test,
- UI/e2e check,
- data reconciliation/read-back,
- static/schema validation,
- performance benchmark,
- deployment smoke check.

### 7. Detect unnecessary breadth
Do not require full-system regression when dependency evidence shows isolation. Conversely, do not use a narrow unit test when the risk crosses layers.

### 8. Record coverage gaps
If a high-risk regression area cannot be tested, make the gap explicit and route to approval/blocking as required.

## Required output

```text
Change surface:
Intended behavior changes:
Behavior intended to remain stable:
Regression surface:
Critical/high regression risks:
Historical failures relevant:
Selected checks:
Checks executed/results:
Coverage gaps:
Residual regression risk:
Risk level:
Recommendation:
```

## Evidence requirements

Regression scope should be tied to actual dependencies/contracts/invariants rather than generic test lists. Claims of isolation require architecture/code evidence. Claims of no regression require executed evidence with bounded scope.

## Stop / escalate

Escalate when:
- change affects unknown shared consumers,
- high-risk behavior has no credible verification path,
- a refactor unexpectedly changes contract/data/security behavior,
- regression analysis reveals broader architecture impact than original risk classification.

## Rationalizations to reject
- "Only one file changed, so only one test is needed."
- "Run the full suite and we don't need impact analysis."
- "The unit tests pass, so the cross-layer contract is safe."
- "This bug was rare, so no regression test is needed."
- "The refactor should be behavior-preserving, so verification is unnecessary."
- "No existing test means the behavior is not important."

## Definition of Done

The credible regression surface is explicit, high-value invariants map to proportional checks, historical escaped failures are preserved where practical, gaps are visible, and completion claims are scoped to evidence actually executed.