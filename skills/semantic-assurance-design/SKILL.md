---
name: semantic-assurance-design
description: Reduce repeated verification/rework caused by brittle assurance mechanics while preserving or strengthening the invariants being checked. Use when CI/review repeatedly fails on stale bindings, source-layout regexes, allowlists, duplicated provenance checks, or environment-specific process handling rather than product behavior.
---

# Semantic Assurance Design

**Status:** Candidate V1

## Objective

Lower avoidable assurance rework **without lowering assurance strength**.

The goal is not fewer failing tests. The goal is fewer failures caused by duplicated/incidental harness mechanics while keeping the same or stronger protected invariants.

## Trigger when

Task Learning or CI history shows recurring pre-acceptance rework caused by:

- stale predecessor/successor bindings;
- exact-head/provenance logic duplicated across workflows;
- allowlists copied into many workflows and drifting;
- regex/source-text assertions tied to incidental layout;
- shell/native-process behavior inconsistently handled;
- fixtures repeatedly missing new semantic dependencies;
- completed predecessor workflows continuing to enforce obsolete successor write sets.

## Do not trigger when

- verification is catching genuine product/security/data defects;
- the proposed simplification removes an invariant rather than encoding it better;
- there is only one isolated harness failure with no reusable mechanism;
- the easiest "fix" is to skip checks.

## Procedure

### 1. Name the protected invariant

For each brittle check, state what must remain true independently of how the source currently looks.

Examples:
- exact reviewed commit is the one executed;
- no file outside an authorized scope changed;
- a predecessor artifact remains immutable;
- a successor workflow no longer inherits a consumed predecessor write set;
- a native command failed only when its exit semantics indicate failure.

### 2. Separate semantic proof from incidental representation

Prefer:
- parsed machine-readable contracts over grep/regex on layout,
- exact Git object/blob identity over line-position assumptions,
- reusable path-policy composition over duplicated allowlists,
- shared process wrappers that preserve stdout/stderr/exit status explicitly,
- successor-aware applicability metadata over frozen workflow assumptions.

Keep source-text assertions only when textual form itself is the invariant.

### 3. Deepen repeated assurance seams

When the same safe lifecycle appears repeatedly, centralize the reusable primitive behind a small tested interface.

Do not create a shared abstraction from one isolated check.

### 4. Preserve fail-closed behavior

Any replacement must be at least as strict for:

- unknown state,
- identity mismatch,
- missing evidence,
- stale predecessor state,
- unauthorized path/mutation,
- ambiguous native-process result.

### 5. Measure effect

Before/after measurement must include:

Primary:
- verification escape recurrence for the target mechanism,
- final failed-task rate.

Secondary:
- rework cycles per comparable task,
- repeated pre-merge catch count for the target mechanism,
- verification-clean/rework-free rates.

A reduction in failures is not accepted if verification coverage was weakened.

## Required output

```text
Assurance hotspot:
Repeated evidence:
Protected invariant:
Current brittle mechanism:
Proposed semantic mechanism:
Shared seam justified?:
Fail-closed behavior preserved:
Checks removed/replaced:
Regression/eval plan:
Before metrics:
Target after metrics:
Risk/approval:
```

## Rationalizations to reject

- "Delete the flaky test to lower rework."
- "Allow every learning/feedback file everywhere."
- "Regex is simpler, so representation drift is acceptable."
- "Centralize all verification into one giant script."
- "A lower verification-failure rate proves improvement."

## Definition of Done

The invariant is explicit, incidental harness coupling is reduced, negative/adversarial cases remain covered, and effectiveness is measured without gaming the verification system.
