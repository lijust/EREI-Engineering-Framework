---
name: engineering-quality-review
description: Review an implementation for technical quality after requirement compliance is established. Use to assess correctness risks, maintainability, complexity, error handling, data/security boundaries, concurrency, testability, performance implications, and project-standard adherence without re-litigating product scope.
---

# Engineering Quality Review

## Objective

Answer:

> Assuming this is the intended change, is the implementation technically sound, maintainable, appropriately simple, and safe for its risk level?

## Trigger when
- requirement-compliance review passes or the intended scope is otherwise clear,
- L2+ change is ready for engineering review,
- code quality/correctness review is explicitly requested,
- a risky implementation needs independent technical judgment.

## Required inputs
- accepted requirement/scope,
- implementation diff/current code,
- project standards,
- architecture/ADRs,
- risk classification,
- available tests/verification evidence.

## Procedure

### 1. Check correctness and invariants
Look for logical defects, edge cases, invalid state transitions, incorrect assumptions, and broken project invariants.

### 2. Check architecture fit
Assess:
- module/layer boundaries,
- coupling/cohesion,
- contract compatibility,
- duplication vs justified abstraction,
- project-local patterns.

Do not demand a refactor merely because another architecture is aesthetically preferable.

### 3. Check security/data implications
Within the implementation scope inspect obvious boundary failures such as:
- trusting client authorization,
- scope/tenant leakage,
- unsafe input handling,
- secret exposure,
- unintended writes/overwrites,
- weak transaction/consistency behavior.

Route to full security/data specialist review when risk warrants it.

### 4. Check concurrency/state behavior
When applicable inspect:
- race conditions,
- stale state,
- idempotency,
- duplicate execution,
- lock/atomicity assumptions,
- ordering assumptions.

### 5. Check performance implications
Look for obvious regressions:
- repeated I/O,
- N+1 behavior,
- excessive serialization,
- unbounded loops/data loads,
- cache-scope mistakes,
- unnecessary network/runtime calls.

Performance-sensitive findings should route to measurement, not guesswork.

### 6. Check error and failure handling
Assess:
- fail-open/fail-closed appropriateness,
- bounded retries,
- actionable error taxonomy,
- cleanup/rollback behavior,
- partial failure handling,
- observability.

### 7. Check testability and verification coverage
Ask whether meaningful failure modes are covered, not merely whether tests exist.

### 8. Check simplicity and change scope
Flag:
- unnecessary abstraction,
- dependency inflation,
- speculative generalization,
- large refactor without measurable benefit,
- dead/unreachable code introduced by change.

### 9. Rank findings
Use:
- `BLOCKER` — must resolve before release,
- `HIGH` — serious correctness/security/data/reliability concern,
- `MEDIUM` — meaningful maintainability/performance/testability concern,
- `LOW` — minor improvement,
- `NOTE` — observation without requested change.

Do not inflate severity to force stylistic preferences.

## Required output

```text
Review scope:
Risk level:
Blockers:
High findings:
Medium findings:
Low findings:
Positive/verified properties:
Required specialist follow-up:
Verification gaps:
Engineering verdict: PASS | PASS_WITH_NONBLOCKING_FINDINGS | FAIL
```

## Evidence requirements

Each BLOCKER/HIGH finding must identify concrete code/path/behavior and explain the failure mode. Avoid vague assertions.

## Rationalizations to reject
- "It works on the happy path, so the implementation is correct."
- "This is cleaner, therefore the refactor is justified."
- "There are tests, so concurrency/security/data edge cases are covered."
- "It's only internal code, so input boundaries do not matter."
- "Performance looks fine from reading the code, so measurement is unnecessary."

## Definition of Done

Findings are concrete, severity is proportional, project standards and architecture are considered, specialist escalation is explicit, and technical quality is judged independently from requirement compliance.