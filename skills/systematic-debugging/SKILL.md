---
name: systematic-debugging
description: Diagnose software defects through reproducible evidence, boundary tracing, hypothesis testing, and root-cause confirmation before implementing a fix. Use for bugs, intermittent failures, stale/race behavior, performance anomalies with unclear cause, failing tests, integration errors, and incidents where guessing or repeated patching would be unsafe.
---

# Systematic Debugging

## Objective

Find and confirm the root cause of an observed failure before selecting the smallest safe fix.

The skill is designed to prevent patch-by-symptom, random edits, and unverified causal stories.

## Trigger when

Use when:
- a bug/failure is reported or observed,
- a test fails unexpectedly,
- behavior is intermittent/order-dependent,
- an error crosses frontend/backend/data/integration boundaries,
- a prior fix did not hold,
- the cause is not already directly established by evidence,
- the Router selects `bug-fix` and diagnosis is required.

## Do not trigger full procedure when

- the defect and cause are directly established and the fix is truly isolated L0/L1,
- the task is feature work rather than defect diagnosis,
- performance has a known measured bottleneck and a dedicated performance workflow is more appropriate.

Even in abbreviated cases, preserve reproduction and verification evidence.

## Required inputs

Use available:
- exact observed symptom/error,
- expected behavior,
- reproduction conditions,
- recent changes,
- logs/errors/traces,
- affected code/config/data,
- baseline/test evidence,
- architecture and relevant project standards/overlays.

## Procedure

### 1. Define the failure precisely
Record:
- observed behavior,
- expected behavior,
- environment/version,
- frequency,
- affected user/tenant/data scope,
- exact error/result,
- when it started if known.

Avoid debugging a vague statement like "search is broken" when a more precise observable can be established.

### 2. Reproduce or establish equivalent evidence
Prefer a minimal deterministic reproduction.

Classify:
- `REPRODUCED`,
- `INTERMITTENT_REPRODUCED`,
- `EVIDENCE_ONLY`,
- `NOT_REPRODUCED`.

Do not claim a fix when the original failure cannot be meaningfully compared before/after unless an equivalent invariant check is justified.

### 3. Establish baseline and scope
Identify:
- affected path/layers,
- known-good neighboring behavior,
- pre-existing failures,
- recent relevant changes,
- whether issue is local or cross-layer.

Run `impact-analysis` when blast radius is unclear/material.

### 4. Trace from symptom to source
Follow actual data/control flow rather than jumping to likely code.

Trace relevant boundaries such as:
- UI state → client request,
- request → server handler,
- handler → business rule,
- business rule → data/integration,
- returned result → client application/rendering,
- trigger/job → state mutation.

At each boundary ask:
- what value/state entered,
- what should have entered,
- where they diverged,
- whether evidence is direct or inferred.

### 5. Generate bounded hypotheses
Create the smallest useful set of hypotheses connected to observed evidence.

For each:
- predicted observation if true,
- cheapest decisive check,
- evidence result.

Do not edit multiple unrelated causes simultaneously.

### 6. Test hypotheses one variable at a time where practical
Use deterministic checks/logging/tests/runtime inspection before speculative code changes.

Classify hypothesis:
- confirmed,
- rejected,
- still possible,
- untestable with current evidence.

### 7. Confirm root cause
A root-cause statement should explain:
- why the symptom occurs,
- why it occurs under the observed conditions,
- why neighboring cases may work,
- what invariant is violated,
- evidence that distinguishes it from competing hypotheses.

If this cannot be established, say `ROOT_CAUSE_NOT_CONFIRMED` rather than inventing certainty.

### 8. Design the smallest safe fix
Prefer fixing the violated invariant at the correct layer.

Evaluate:
- whether fix treats cause or symptom,
- compatibility,
- security/data impact,
- concurrency/order implications,
- regression surface,
- rollback.

Use refactoring only when needed to fix/test safely and benefit exceeds migration risk.

### 9. Create regression guard
Define a test/check that fails for the original defect and passes after the fix when practical.

For real framework/project failures, preserve the scenario as a durable regression case.

### 10. Implement and verify
After implementation:
- reproduce original scenario,
- run targeted regression check,
- run relevant neighboring/regression checks,
- use `verification-before-completion` for material completion claim.

## Required output

```text
Observed failure:
Expected behavior:
Environment/version:
Reproduction status:
Affected scope/layers:
Baseline/pre-existing failures:
Evidence collected:
Hypotheses tested:
Confirmed root cause:
Violated invariant:
Fix strategy:
Why fix addresses cause:
Regression guard:
Verification plan/result:
Unknowns:
Risk level:
```

## Evidence requirements

Root cause must be evidence-backed. Correlation with a recently edited line is not proof. A passing result after a patch is not by itself proof that the identified root cause was correct unless the reproduction/invariant explains the change.

## Stop / escalate

Escalate when:
- debugging reveals a new L3/L4 architecture/security/data decision,
- reproduction indicates cross-tenant/data corruption risk,
- production evidence must be collected in a sensitive system,
- multiple plausible causes cannot be distinguished with available telemetry,
- fix would require large refactor/platform migration.

## Rationalizations to reject

- "This line looks suspicious, let's change it and see."
- "The error disappeared once, so it is fixed."
- "The last commit caused it because timing matches."
- "Add a retry; intermittent errors happen."
- "Catch the exception so users stop seeing it."
- "Rewrite this subsystem—it is probably the source."
- "The first plausible explanation is good enough."
- "We cannot reproduce it, therefore it is not real."

## Definition of Done

The failure is precisely defined, root cause is confirmed or uncertainty is explicit, the fix targets the violated invariant, a regression guard exists where practical, and fresh evidence verifies the original failure no longer occurs without introducing known blocking regression.