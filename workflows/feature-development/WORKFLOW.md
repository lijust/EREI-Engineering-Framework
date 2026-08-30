# Feature Development Workflow

**Type:** Engineering workflow  
**Status:** Draft V1

## Objective

Turn an approved product/engineering outcome into a proportionate, traceable implementation that preserves architecture/security/data invariants, controls scope, verifies behavior, and converges against the original requirement before release.

## Entry conditions

Use when:
- adding or materially changing functional capability,
- Router classifies request as feature work,
- work is more than an isolated cosmetic/local adjustment.

L0/L1 features may use abbreviated stages. L3/L4 security/data/architecture decisions require their dedicated approval/specialist workflows.

## Default roles

- Chief Engineer for L2+ routing/integration.
- Implementing specialist role(s) for affected layers.
- QA Engineer for material verification.

## Conditional roles

Activate by impact:
- System Architect
- Frontend Engineer
- Backend Engineer
- Security Engineer
- Data Engineer
- Performance Engineer
- Release Engineer

## Required skills

For L2+:
- `impact-analysis`
- `regression-analysis`
- `requirement-compliance-review`
- `engineering-quality-review`
- `verification-before-completion`

Conditional:
- `project-standard-discovery`
- `threat-model`
- `security-review`
- technology overlay references

## Stage 1 — Normalize outcome and acceptance

Separate:
- desired user/business outcome,
- explicit constraints,
- suggested implementation,
- acceptance criteria,
- explicitly excluded scope,
- unknowns.

Do not treat a suggested technical solution as mandatory unless explicitly required/approved.

For material work persist a feature spec or equivalent durable record.

## Stage 2 — Impact and risk

Run `impact-analysis`.

Identify:
- affected layers/components,
- contracts/boundaries,
- security/tenant implications,
- data/schema/state implications,
- performance implications,
- dependencies/integrations,
- rollout/rollback implications,
- provisional risk.

If current project truth is insufficient, route to discovery/onboarding before planning.

## Stage 3 — Architecture/security/data gate

Before implementation, determine whether the feature introduces a new L3/L4 structural decision.

If yes:
- produce the applicable architecture/security/data analysis/ADR,
- obtain explicit approval,
- use `security-critical-change` when security boundary is material.

If no, remain inside existing approved architecture.

## Stage 4 — Technical plan

Create a plan proportional to risk. For L2+ include:
- components/files/modules expected to change,
- API/contract changes,
- data changes,
- frontend/backend responsibilities,
- error/failure behavior,
- concurrency/idempotency where relevant,
- test/verification plan,
- migration/deployment notes,
- ordering/dependencies among tasks.

Prefer small independently verifiable tasks.

## Stage 5 — Baseline and branch/candidate preparation

Where applicable:
- establish current test/build baseline,
- preserve known pre-existing failures,
- use isolated branch/workspace,
- record version/reference point.

Do not attribute existing failures to the feature later without baseline evidence.

## Stage 6 — Implement by vertical/risk-aware slices

Implement the smallest coherent slice that can be verified.

For cross-layer functionality, prefer completing a real path through required layers rather than creating large disconnected frontend/backend batches that drift from contracts.

During implementation:
- obey project standards/overlays,
- keep server authorization authoritative,
- preserve data invariants,
- keep errors explicit,
- instrument critical operations where needed,
- avoid unrelated refactors/features.

## Stage 7 — Local verification during implementation

After meaningful slices:
- run targeted tests/checks,
- verify contracts/interfaces,
- catch integration drift early.

Evidence during implementation does not replace final fresh verification after latest material changes.

## Stage 8 — Regression analysis

Run `regression-analysis` against actual implementation.

Protect behavior intended to remain stable, including shared consumers, security/data boundaries, configuration, exports/integrations, and historical failures as applicable.

## Stage 9 — Requirement compliance review

Ask independently:
- were all accepted requirements implemented?
- did scope drift occur?
- are explicit constraints/exclusions respected?
- are any items only present in code but not verified?

A technically elegant feature that misses the requirement fails this gate.

## Stage 10 — Engineering quality review

Review correctness, architecture fit, complexity, state/concurrency, errors, performance implications, testability, and project standards.

Route specialist findings rather than stretching generic review beyond its competence.

## Stage 11 — Specialist gates

Run only when impact/risk requires:
- Security review/threat-model convergence,
- Data integrity/migration review,
- Performance measurement,
- Deployment/release checks.

Security/data blockers retain veto authority.

## Stage 12 — Fresh verification

After the latest material changes:
- execute acceptance-critical checks,
- targeted integration/negative/regression checks,
- performance/security/data evidence where required,
- candidate runtime checks.

Use `verification-before-completion` to produce scoped verdict.

## Stage 13 — Convergence

Compare durable outcome/spec/plan against:
- implementation,
- reviews,
- verification evidence,
- unresolved/deferred items.

No material requirement may disappear simply because implementation moved on.

## Stage 14 — Release/exit

If release is required, hand off verified candidate to Release Engineer.

Use Router terminal states:
- `COMPLETE_VERIFIED`
- `COMPLETE_WITH_EXPLICIT_DEFERRED_ITEMS`
- relevant BLOCKED state.

## Required durable record for L2+

```text
Feature outcome/spec:
Acceptance criteria:
Explicit exclusions:
Impact/risk:
Approved structural decisions:
Technical plan:
Implementation summary:
Regression analysis:
Compliance verdict:
Engineering verdict:
Specialist verdicts:
Fresh verification evidence:
Deferred/residual items:
Release/terminal state:
```

## Low-risk abbreviated path

For clear L0/L1 features inside existing architecture:
1. confirm requirement,
2. lightweight impact/risk,
3. implement,
4. targeted regression/verification,
5. truthful completion.

Do not manufacture architecture documents or activate all roles for trivial work.

## Rationalizations to reject

- "We know what they meant; no acceptance criteria needed."
- "Build the frontend first and figure out server contract later" for a cross-layer feature.
- "We can add authorization after the feature works."
- "The tests pass, so scope compliance is guaranteed."
- "This refactor is cleaner, so include it while implementing the feature."
- "It's an MVP, so data/security boundaries can be temporary and undocumented."
- "We can verify on Stable."

## Definition of Done

The accepted feature outcome is durably represented, impact/risk and structural gates are satisfied, implementation remains within justified scope, regression/compliance/quality/specialist reviews are complete as applicable, fresh evidence verifies the actual candidate, and convergence produces a truthful terminal/release state.