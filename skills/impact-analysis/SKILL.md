---
name: impact-analysis
description: Analyze the cross-layer blast radius, boundaries, invariants, risks, and required engineering roles before a material software change. Use for cross-layer changes, uncertain scope, architecture/security/data/performance-sensitive work, and before selecting a workflow for L2+ changes.
---

# Impact Analysis

## Trigger when

Use this skill when any of the following is true:
- a change may affect more than one engineering layer,
- a frontend change alters backend/API expectations,
- data shape, persistence, ownership, or migration may change,
- authentication, authorization, tenant isolation, or trust boundaries may change,
- concurrency/consistency may change,
- performance-sensitive paths may change,
- a dependency/platform/service boundary may change,
- the true blast radius is uncertain,
- the Router needs evidence to classify L2+ risk.

## Do not trigger when

Do not require full impact analysis for clearly isolated L0 cosmetic changes with no functional contract, security, data, performance, or deployment effect.

For L1 changes, use a lightweight version unless evidence suggests broader impact.

## Required inputs

- Requested outcome.
- Explicit constraints/acceptance criteria.
- Relevant project context.
- Current architecture or affected code/runtime evidence where material.
- Applicable Constitution and project rules.

## Procedure

### 1. Normalize the requested change
Separate:
- intended outcome,
- proposed implementation,
- explicit constraints,
- assumptions,
- unknowns.

### 2. Identify touched components
List concrete affected components/files/services/data stores where known.

If unknown, identify what must be inspected before implementation.

### 3. Map affected layers
Assess each as `NONE`, `POSSIBLE`, or `CONFIRMED`:
- frontend/UI state,
- backend/business logic,
- API/contracts,
- authentication,
- authorization/tenant isolation,
- data/storage/schema,
- concurrency/consistency,
- performance/resource use,
- observability/error handling,
- deployment/release,
- external integrations/dependencies,
- governance/documentation.

### 4. Identify boundaries and invariants
For every affected layer, identify properties that must remain true.

Examples:
- tenant A cannot read tenant B data,
- request/response contract remains backward compatible,
- existing data is not overwritten unintentionally,
- stale requests cannot supersede newer state,
- performance budget remains within target,
- rollback remains possible.

### 5. Estimate blast radius
Classify:
- local,
- module,
- cross-layer,
- project-wide,
- tenant/user-wide,
- production-wide.

### 6. Identify failure modes
Ask what could fail even if the happy path works:
- unauthorized access,
- cross-tenant exposure,
- data corruption/loss,
- race/stale-state behavior,
- contract mismatch,
- latency regression,
- quota/resource exhaustion,
- deployment/config drift,
- partial migration,
- unobservable failure.

### 7. Identify verification needs
Map each important invariant to evidence:
- test,
- deterministic tool,
- runtime check,
- benchmark,
- review,
- approval.

### 8. Recommend roles and skills
Activate only those with material responsibility.

### 9. Recommend provisional risk level
Use the Risk Contract. Explain which factors raise the risk.

### 10. Surface unknowns
Do not fill missing architecture facts with assumptions when they can change risk or implementation correctness.

## Required output

```text
Outcome:
Proposed implementation (if any):
Affected components:
Affected layers:
Key boundaries:
Key invariants:
Blast radius:
Primary failure modes:
Performance implications:
Security implications:
Data implications:
Rollback implications:
Unknowns requiring discovery:
Recommended roles:
Recommended skills:
Evidence plan:
Provisional risk level:
Risk rationale:
```

## Stop / escalate

Escalate to discovery or architecture review when:
- current-state architecture is materially unknown,
- a new trust/security/data boundary is introduced,
- irreversible state change is possible,
- the request conflicts with the Constitution,
- safe verification cannot be defined.

## Rationalizations to reject

- "The diff will be small, so the impact is small."
- "Only frontend code changes, so backend contracts cannot be affected."
- "The happy path works, so edge boundaries are safe."
- "We can find out in production if performance regresses."
- "Existing data probably matches the new assumption."

## Definition of Done

Impact analysis is complete when affected layers, boundaries, invariants, blast radius, major failure modes, verification needs, unknowns, required roles/skills, and provisional risk are explicit enough for the Router to choose a safe workflow.