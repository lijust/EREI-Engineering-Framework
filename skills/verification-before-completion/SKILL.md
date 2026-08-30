---
name: verification-before-completion
description: Verify material completion claims with fresh, appropriate evidence before a task, fix, feature, migration, or release is declared complete. Use after implementation and reviews, before convergence/release, and whenever someone claims that code is fixed, tests pass, performance improved, data is safe, or a requested outcome is complete.
---

# Verification Before Completion

## Objective

Replace confidence with evidence.

A completion claim is valid only when the relevant property has been checked at the level required by its risk.

## Trigger when
- implementation is believed complete,
- a bug is claimed fixed,
- tests/build/lint are claimed passing,
- performance is claimed improved,
- a migration is claimed successful,
- security/data behavior is claimed safe,
- a candidate is considered for release.

## Do not trigger when
- no completion claim is being made,
- work is clearly still exploratory/in progress.

## Required inputs
- requested outcome/spec,
- risk level,
- implementation/review results,
- evidence plan from impact/workflow,
- available deterministic/runtime checks,
- known pre-existing failures.

## Procedure

### 1. Enumerate material claims
Examples:
- feature works,
- bug no longer reproduces,
- tests pass,
- build succeeds,
- no regression in targeted behavior,
- performance meets budget,
- data migration preserved invariants,
- authorization boundary holds,
- release artifact is deployable.

### 2. Map each claim to a verification method
Prefer, in order where appropriate:
- deterministic test/script/schema/static check,
- direct runtime observation,
- benchmark/measurement,
- source inspection,
- independent review,
- inference only when no stronger method is available and the claim permits uncertainty.

### 3. Run fresh verification
Use evidence produced after the relevant implementation state. Do not rely on stale checks from before the latest material change.

### 4. Record exact result and scope
For each check record:
- command/tool/check,
- result,
- what it proves,
- what it does not prove,
- version/commit/runtime scope when material.

### 5. Separate pre-existing failures
If baseline already failed:
- identify which failures predate the change,
- verify the change did not introduce new relevant failure,
- never re-label unknown failures as pre-existing without evidence.

### 6. Verify negative claims carefully
Claims such as "no cross-tenant leak", "no regression", or "no data loss" require scoped evidence. Avoid universal claims from narrow tests.

### 7. Check risk-proportional coverage
Minimum posture:
- L0: direct visual/local check may suffice.
- L1: targeted functional verification.
- L2: targeted tests + relevant regression/review evidence.
- L3: independent security/data/architecture evidence as applicable.
- L4: strongest available deterministic/runtime verification plus rollback/post-change checks.

### 8. Produce verification verdict
Use:
- `VERIFIED` — required evidence supports the scoped completion claim.
- `VERIFIED_WITH_LIMITATIONS` — core claim supported; limitations explicitly bounded and non-blocking.
- `NOT_VERIFIED` — evidence insufficient.
- `FAILED` — verification contradicts completion claim.

## Required output

```text
Claims verified:
Checks executed:
Observed results:
Evidence types:
Pre-existing failures:
New failures/regressions:
Coverage limitations:
Unverified claims:
Verification verdict:
Release/completion recommendation:
```

## Evidence requirements

A statement like `tests pass` must include fresh observed test evidence. A statement like `performance improved` needs before/after measurement with comparable scope. A statement like `bug fixed` needs reproduction-oriented evidence or equivalent targeted verification.

## Stop / block conditions

Block a material completion claim when:
- required checks were not executed,
- evidence is stale relative to latest material change,
- a blocker/high finding remains unresolved,
- verification fails,
- critical negative claims are broader than the evidence supports.

## Rationalizations to reject
- "The code is obvious, so running the check is unnecessary."
- "It passed before the last edit."
- "The agent is confident."
- "Most tests passed, so the feature is fine."
- "The user can test it after release."
- "No error was returned, so data integrity is proven."

## Definition of Done

Every material completion claim has current, scoped evidence appropriate to risk, limitations are explicit, and the final verdict does not overstate what was actually verified.