---
name: requirement-compliance-review
description: Review an implementation against the requested outcome, accepted specification, constraints, and explicit decisions before judging code style or engineering elegance. Use for L2+ changes and whenever an implementation may be technically sound but incomplete, over-scoped, or inconsistent with the agreed requirement.
---

# Requirement Compliance Review

## Objective

Answer one question before code-quality review:

> Did the implementation actually satisfy the agreed requirement and constraints, without silently adding, omitting, or changing behavior?

## Trigger when
- reviewing L2+ implementation,
- a durable spec/plan/acceptance criteria exists,
- multiple files/layers changed,
- implementation scope may have drifted,
- user explicitly asks whether requested work was fully implemented.

## Do not trigger when
- no implementation exists yet,
- the request is purely exploratory,
- a trivial L0 change can be verified directly without a separate review artifact.

## Required inputs
- original requested outcome,
- accepted clarifications/constraints,
- spec/plan/tasks where present,
- approved ADRs/decisions relevant to the change,
- implementation diff/current state,
- verification evidence available so far.

## Procedure

### 1. Build a requirement checklist
Extract atomic obligations:
- functional requirements,
- non-functional constraints,
- security/data invariants,
- explicitly excluded scope,
- compatibility requirements,
- acceptance criteria.

### 2. Map implementation to each obligation
Classify each item:
- `SATISFIED`,
- `PARTIAL`,
- `NOT_SATISFIED`,
- `NOT_VERIFIED`,
- `OUT_OF_SCOPE`.

Cite implementation/evidence for material `SATISFIED` claims.

### 3. Detect scope drift
Identify:
- missing requested behavior,
- unapproved behavior changes,
- extra features/refactors not required,
- altered defaults,
- changed contracts,
- removed behavior.

### 4. Check explicit constraints
Examples:
- no overwrite,
- backward compatibility,
- tenant isolation,
- performance budget,
- required stack/technology constraint,
- no direct production edit.

### 5. Separate implementation presence from verification
Code appearing to implement a requirement is not automatically `SATISFIED` if runtime/test evidence is required.

### 6. Produce blockers and deferred items
Every gap must be explicit. Do not bury requirement failures inside general comments.

## Required output

```text
Requirement checklist:
Satisfied:
Partial:
Not satisfied:
Not verified:
Scope drift:
Constraint violations:
Blocking gaps:
Explicit deferred items:
Compliance verdict: PASS | PASS_WITH_DEFERRED | FAIL
```

## Evidence requirements

Material claims should reference code, tests, tools, runtime evidence, or approved user decisions. `INFERRED` compliance must be labeled.

## Rationalizations to reject
- "The code is high quality, so it probably meets the requirement."
- "Most of the feature works, so the missing edge case is fine."
- "The refactor was useful, even though it was not requested."
- "A requirement exists in code, so no verification is needed."

## Definition of Done

Every material requirement and constraint has a disposition, scope drift is explicit, and blocking gaps are clearly separated from code-quality concerns.