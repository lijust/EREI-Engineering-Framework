---
name: behavior-first-testing
description: Drive implementation with small behavior-focused red-to-green slices through an approved public test seam while rejecting implementation-coupled or tautological tests. Use for feature/bug work where deterministic automated tests can provide fast feedback during implementation.
---

# Behavior-First Testing

**Status:** Candidate V1

## Objective

Use automated tests as a fast implementation feedback loop without coupling the test suite to private implementation details or inventing architecture solely for test convenience.

This skill complements, and does not replace, `verification-before-completion`.

## Trigger when

Use when:

- a feature or bug can be expressed as deterministic observable behavior,
- a regression guard is required,
- a business/domain rule is changing,
- a contract/interface behavior is being implemented,
- a cross-layer slice can be exercised through an approved public seam,
- the feature workflow reaches implementation and automated feedback is practical.

## Do not force full procedure when

- the change is cosmetic L0 work,
- reliable automation is not practical and another verification method is explicitly justified,
- the required test seam would itself introduce an unapproved architecture decision,
- the test would merely duplicate a stronger existing static/schema/compiler guarantee.

## Core terms

- **Behavior** — externally observable outcome/invariant the requirement needs.
- **Test seam** — approved interface/location through which the behavior is exercised and observed.
- **Tracer slice** — the smallest real vertical behavior that can fail, be implemented, and pass end-to-end through the selected seam.
- **Red** — the new/changed behavior is represented by a test/check that fails for the intended reason.
- **Green** — the smallest implementation makes that behavior pass without introducing unrelated scope.

## Procedure

### 1. State the behavior independently from implementation

Write the expected behavior in terms of requirement/domain outcome.

Examples:

- authorized tenant A can read A's record and cannot read tenant B's record,
- stale request sequence cannot overwrite a newer result,
- a payment plan normalization returns the accepted canonical plan,
- duplicate retry does not create a second durable mutation.

Avoid statements like "private helper X returns Y" unless the helper itself is the accepted public contract.

### 2. Select the test seam

Prefer an existing public interface already used by callers.

Record:

- seam/interface,
- behavior observed there,
- dependencies required,
- why this seam is stable enough to test.

Do not expose private methods or split modules merely to make tests easier.

If no suitable seam exists and creating one would be a material structural decision, route to architecture analysis/approval rather than smuggling the seam in through the test.

### 3. Establish an independent expected result

Expected values must come from an independent source such as:

- accepted requirement,
- worked business example,
- known-good fixture,
- authoritative standard/schema,
- previously verified regression evidence.

Reject tests that recompute the expected result using the same algorithm as the implementation.

### 4. Create one red tracer slice

Add the smallest meaningful test/check for one behavior.

Confirm it fails for the intended missing/incorrect behavior, not because of broken setup, unrelated infrastructure, or stale fixtures.

If it is already green, determine whether behavior already exists or the test is insensitive before adding implementation.

### 5. Implement only enough to turn the slice green

Do not anticipate later slices by adding speculative abstractions/features.

Preserve:

- project architecture,
- authorization/data invariants,
- error semantics,
- compatibility constraints,
- risk/approval boundaries.

### 6. Repeat vertically

Use the last slice to inform the next one.

Prefer:

```text
behavior 1 → red → green
behavior 2 → red → green
behavior 3 → red → green
```

Avoid horizontal batching such as:

```text
all imagined tests → all implementation → late integration
```

when vertical slices are practical.

### 7. Reject implementation-coupled tests

Flag tests that depend on:

- private methods/fields,
- exact internal call order when not contractual,
- mocks of internal collaborators that callers do not know about,
- internal storage layout when the public behavior is the real requirement,
- incidental function/file structure,
- side-channel inspection that bypasses the accepted interface unless the side channel itself is the invariant under test.

A refactor that preserves behavior should not break behavior tests solely because internals moved.

### 8. Keep targeted feedback fast

During implementation run the narrowest relevant checks frequently.

Examples:

- one test file,
- one contract test group,
- static/type/schema check for the touched interface,
- one deterministic local integration fixture.

Do not run the full suite after every tiny edit unless the project specifically requires it.

### 9. Preserve regression evidence

For bug fixes, ensure the test/check represents the original violated invariant strongly enough to fail before the fix and pass after it where practical.

Do not weaken a test just to obtain green.

### 10. Hand off to final review/verification

Passing implementation-time tests are not a completion claim.

After latest material changes continue through:

- regression analysis,
- requirement compliance,
- engineering quality review,
- applicable specialist gates,
- fresh `verification-before-completion`.

## Required output

```text
Behavior under test:
Selected test seam:
Why seam is valid/stable:
Independent expected-result source:
Tracer slice:
Initial red evidence:
Minimal implementation scope:
Green evidence:
Next slice or stop condition:
Implementation-coupling risks:
Architecture decision required: yes | no
Final verification still required:
```

## Anti-patterns

### Implementation-coupled

A test knows private structure that callers do not. Refactoring breaks the test while behavior remains correct.

### Tautological

The test calculates the expected result using the same logic pattern as the implementation, so disagreement is structurally unlikely.

### Horizontal test batch

Many tests for imagined future behavior are written before any real slice is implemented, creating premature test architecture.

### Test-created architecture

Production interfaces/wrappers/adapters are introduced only because a unit test wants a mock point, with no accepted seam or runtime variation justifying them.

### Green-by-weakening

Assertions, fixtures, or scope are relaxed to make a failing implementation appear correct.

## Rationalizations to reject

- "Any test is better than no test."
- "Private-method tests give more coverage."
- "We should mock everything for isolation."
- "The expected value uses the same formula, but that is fine."
- "Write every test first so implementation is faster later."
- "The targeted tests passed, so final verification is unnecessary."
- "Create another adapter so we can mock the dependency."

## Definition of Done

The implemented behavior was driven through an explicit approved seam, expected outcomes were independent from implementation logic, red-to-green evidence exists where practical, slices remained vertical and scope-bounded, tests avoid private implementation coupling, and final Framework review/verification remains required before completion.
