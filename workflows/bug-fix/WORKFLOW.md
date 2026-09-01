# Bug Fix Workflow

**Type:** Engineering workflow  
**Status:** Draft V1

## Objective

Resolve a software defect by confirming the failure and root cause, applying the smallest safe fix at the correct layer, protecting against regression, and verifying the original symptom plus affected neighboring behavior before completion.

## Entry conditions

Use when:
- observed behavior differs from expected behavior,
- a test/runtime/production failure requires correction,
- the Router classifies the work as a bug/defect,
- an incident has been contained and remediation enters normal engineering flow.

For a security-critical defect, this workflow composes with or routes into `security-critical-change` as required.

## Default roles

- Chief Engineer for L2+ routing.
- Implementing specialist role based on affected layer.
- QA Engineer for material regression/verification.

## Conditional roles

Activate based on impact:
- System Architect
- Frontend Engineer
- Backend Engineer
- Security Engineer
- Data Engineer
- Performance Engineer
- Release Engineer

Do not activate every role by default.

## Required skills

- `systematic-debugging`
- `regression-analysis`
- `verification-before-completion`

For L2+ also use:
- `impact-analysis`
- `requirement-compliance-review`
- `engineering-quality-review`

Conditional:
- `threat-model`
- `security-review`
- `framework-feedback-capture`
- technology overlay references

## Stage 1 — Capture defect

Create a precise defect record:
- observed behavior,
- expected behavior,
- environment/version,
- reproduction/evidence,
- user/tenant/data impact,
- severity/urgency,
- known recent changes if relevant but not assumed causal.

## Stage 2 — Establish baseline

Before changing code where practical:
- reproduce defect or preserve equivalent evidence,
- record known pre-existing test/runtime failures,
- identify current version/commit,
- preserve rollback/reference point for material changes.

## Stage 3 — Systematic debugging

Run `systematic-debugging`.

Exit this stage with:
- confirmed root cause and violated invariant, or
- explicit `ROOT_CAUSE_NOT_CONFIRMED` with enough evidence to justify the next diagnostic step.

Do not patch symptoms merely to progress the workflow.

## Stage 4 — Impact and risk

Determine:
- affected layers,
- blast radius,
- security/data/concurrency/performance implications,
- likely regression surface,
- risk level.

If diagnosis reveals a new L3/L4 structural decision, stop at approval gate.

## Stage 5 — Fix design

Choose the smallest safe fix that addresses the confirmed cause.

Check:
- correct enforcement/layer,
- compatibility,
- data preservation,
- auth/tenant behavior,
- concurrency/idempotency,
- performance implications,
- rollback.

A refactor may be included only when needed or measurably justified relative to migration risk.

## Stage 6 — Regression guard first where practical

Create/update a deterministic regression check that demonstrates the original defect or violated invariant before/with the fix.

When a test-first sequence is practical:
1. make the regression check fail against defective behavior,
2. implement minimal fix,
3. make it pass.

This is preferred for reproducible bugs but is not ritualistically required when the failure can only be verified through another stronger mechanism.

## Stage 7 — Implement fix

Implement using project standards and relevant overlays. Avoid unrelated cleanup/scope expansion.

If new evidence contradicts the root cause, return to debugging rather than forcing the patch.

## Stage 8 — Regression analysis

Run `regression-analysis` against the actual fix.

Map affected invariants/consumers to targeted checks and preserve the escaped defect as regression protection where practical.

## Stage 9 — Reviews

For L2+:
1. requirement/defect compliance: does the fix address the agreed failure without unwanted behavior change?
2. engineering quality: is the fix technically sound?
3. conditional security/data/performance specialist review.

For L0/L1 use proportional abbreviated review.

## Stage 10 — Fresh verification

After latest material edit:
- re-run original reproduction,
- run regression guard,
- run selected neighboring checks,
- confirm no new relevant failures,
- verify performance/security/data claims where applicable.

Use `verification-before-completion` for the final evidence verdict.

## Stage 11 — Convergence

Compare:
- original defect,
- root cause,
- violated invariant,
- implemented fix,
- regression coverage,
- verification evidence,
- remaining findings.

Every unresolved item is blocking, accepted/deferred explicitly, or out of scope.

## Stage 12 — Framework Feedback Check

After convergence, determine whether the defect/rework exposed a limitation or reusable lesson in the pinned Framework itself.

Capture project-local feedback when evidence shows, for example:
- the applicable workflow/skill missed a material condition,
- verification allowed an escaped defect,
- risk was materially misclassified,
- a repeated workaround outside Framework guidance was necessary,
- useful negative learning should be preserved.

Do not capture an ordinary project defect if Framework behavior was adequate.

When triggered, use `framework-feedback-capture` and store the event under `.erei/feedback/`. Feedback capture does not modify Framework Core or the project pin.

## Stage 13 — Release/exit

Use Router terminal states.

For production-impacting changes, route through Release Engineer and applicable deployment procedure.

## Required durable bug record for L2+

```text
Defect:
Expected behavior:
Reproduction/evidence:
Root cause:
Violated invariant:
Affected layers/risk:
Fix:
Regression guard:
Regression surface/checks:
Review verdicts:
Verification evidence:
Residual/deferred items:
Framework feedback: none | captured <feedback-id>
Release/terminal state:
```

## Hotfix path

Urgency may abbreviate planning but does not erase security/data/verification gates.

For a true production hotfix:
- minimize change,
- preserve before/after evidence,
- retain rollback/recovery posture,
- run the strongest practical targeted verification,
- document skipped non-critical checks,
- create follow-up regression/postmortem work if needed,
- run the Framework Feedback Check after containment when the incident exposed a reusable Framework lesson.

## Rationalizations to reject

- "Just make the error disappear."
- "The fix is one line so root cause does not matter."
- "Add retry and move on."
- "We can test after deploying."
- "Since the bug is urgent, tenant/data checks can wait."
- "While we're here, rewrite the module."
- "The original symptom stopped once, so we're done."
- "Every project bug must be a Framework bug."

## Definition of Done

The defect/root cause relationship is evidence-backed, the fix addresses the violated invariant with proportional scope, regression protection exists where practical, reviews/gates are satisfied, fresh evidence verifies the original defect plus credible regression surface, the Framework Feedback Check has been performed for material work, and a truthful terminal state is reached.