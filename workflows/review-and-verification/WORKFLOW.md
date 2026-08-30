# Review and Verification Workflow

**Type:** Engineering quality workflow  
**Status:** Draft V1

## Objective

Provide a standard post-implementation quality path that keeps three questions separate:

1. **Compliance:** Did we build what was agreed?
2. **Engineering quality:** Is the implementation technically sound?
3. **Verification:** What evidence proves the scoped completion claims?

## Entry conditions

Use after material implementation and before convergence/release. Default for L2+ changes; use abbreviated form for L0/L1 where justified.

## Required skills
- `requirement-compliance-review`
- `engineering-quality-review`
- `verification-before-completion`

## Conditional specialist reviews
Activate based on impact/risk:
- security-review,
- data/integrity review,
- performance analysis,
- dependency review,
- migration verification,
- release verification.

## Stage 1 — Requirement compliance

Run requirement compliance first.

If verdict is `FAIL`, return to implementation unless the gap is explicitly deferred/accepted by authorized decision.

Do not use code quality to compensate for missing requirements.

## Stage 2 — Engineering quality

Review the intended implementation for correctness, architecture fit, complexity, boundaries, failure modes, and project standards.

BLOCKER/HIGH findings must be resolved or explicitly dispositioned according to risk and governance.

## Stage 3 — Specialist gates

Run only those materially required by impact analysis and risk.

Security/data blocking findings may veto progression under the Constitution.

## Stage 4 — Fresh verification

Run `verification-before-completion` after the latest material fixes/review changes.

Evidence generated before a later material edit is stale for the affected claim.

## Stage 5 — Convergence handoff

Produce a durable review package:

```text
Compliance verdict:
Engineering verdict:
Specialist verdicts:
Verification verdict:
Resolved blockers:
Remaining non-blocking findings:
Explicit deferred items:
Evidence summary:
Residual unknowns:
Recommended terminal state:
```

Recommended terminal states follow the Router contract:
- `COMPLETE_VERIFIED`
- `COMPLETE_WITH_EXPLICIT_DEFERRED_ITEMS`
- blocker states when applicable.

## Independence rules

For L2+ work:
- prefer compliance/quality review that is not simply the authoring context repeating its own judgment,
- for L3/L4 security/data-critical changes, independent specialist review is expected where practical.

## Risk proportionality

### L0
Direct local/visual verification; separate formal reviews usually unnecessary.

### L1
Targeted verification; lightweight combined review acceptable.

### L2
Separate compliance + engineering review + fresh verification.

### L3
L2 baseline plus applicable independent specialist review and stronger evidence.

### L4
Strongest applicable review/verification plus explicit execution/release gates and rollback/post-change evidence.

## Rationalizations to reject
- "The same reviewer can just say everything looks good in one sentence."
- "Code quality is excellent, so a missing requirement is acceptable."
- "Compliance passed, so security review is unnecessary."
- "Tests passed before review fixes, so they remain current."
- "A non-blocking style issue should prevent release."

## Definition of Done

Compliance, engineering quality, applicable specialist gates, and fresh verification each have explicit verdicts; blockers/deferred items are durable; evidence scope is clear; and convergence can determine a truthful terminal state.