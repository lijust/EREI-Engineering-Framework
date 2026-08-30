# EREI Engineering Framework

**Status:** Eval Harness V1 Stable  
**Date:** 2026-08-31

EREI Engineering Framework is a reusable, cross-project engineering operating system for AI-assisted software development.

It is intentionally **not** a project-specific codebase and **not** a flat prompt/skill library.

The framework separates:

1. **Constitution / Policies**
2. **Agents / Engineering Roles**
3. **Skills / Reusable Procedures**
4. **Workflows / Orchestration**
5. **Project Context / Standards**
6. **Durable Artifacts / Evidence**
7. **Runtime Adapters / Distribution**

## Current state

Foundation V1, Phase 2 Core, Google Apps Script / Google Sheets Overlay V1, Specialist Roles V1, Delivery Workflows V1, and **Eval Harness V1** are stable.

`adr/ADR-0001-EVAL-HARNESS.md` is accepted and defines the provider-neutral automated evaluation architecture.

## Engineering roles

The framework defines distinct accountability roles for:
- Chief Engineer
- System Architect
- Frontend Engineer
- Backend Engineer
- Security Engineer
- Data Engineer
- Performance Engineer
- QA Engineer
- Release Engineer

Roles own perspective, accountability, authority, escalation and evidence obligations. Reusable procedures remain in Skills and cross-role execution remains in Workflows.

## Delivery workflows

### Feature development
`workflows/feature-development/` implements:

Outcome/acceptance → impact/risk → structural gates → technical plan → implementation slices → regression analysis → compliance review → engineering review → specialist gates → fresh verification → convergence → release.

### Bug fixing
`workflows/bug-fix/` implements:

Precise defect → baseline/reproduction → systematic debugging/root cause → impact/risk → smallest safe fix → regression guard → regression analysis → reviews → fresh verification → convergence → release.

## Eval Harness V1

The framework now includes a provider-neutral automated evaluation layer:

- `research/EVAL_HARNESS_BENCHMARK.md`
- `adr/ADR-0001-EVAL-HARNESS.md`
- `evals/README.md`
- `evals/schema/eval-case.schema.json`
- `evals/adapters/PROTOCOL.md`
- `evals/runner.py`
- `evals/tests/test_runner.py`
- deterministic mock/self-test fixtures
- `evals/cases/harness-smoke.eval.json`
- `evals/cases/impact-analysis.eval.json`
- `.github/workflows/framework-evals.yml`

Core design:

`*.eval.json → EREI runner → CLI adapter → target agent/runtime → normalized result → deterministic scorers`

The runner uses Python standard library only. External systems such as Inspect AI, DeepEval, Promptfoo, Braintrust, or provider-native eval APIs remain optional adapters rather than Framework Core dependencies.

## Stable core capabilities

- Engineering Constitution
- Agent / Skill / Workflow / Evidence / Risk contracts
- Workflow Router and impact analysis
- New-project discovery and brownfield onboarding
- Requirement compliance / engineering quality / verification baseline
- Threat modeling, security review and security-critical workflow
- Google Apps Script / Google Sheets technology overlay
- Full specialist engineering role set
- Feature and bug delivery workflows
- Provider-neutral automated eval harness

## Operating principles

Key approved principles include:
- Hybrid autonomy: safe changes may execute automatically; new architecture/security/data structural decisions require approval.
- Enterprise-grade SaaS security mindset.
- Frontend is never trusted for authorization.
- Tenant boundaries are hard boundaries.
- Durable project state beats conversational memory.
- Evidence beats claims.
- Deterministic verification precedes probabilistic judgment.
- Refactor only when measurable benefit exceeds migration risk.
- DEV → Candidate → QA → Stable release flow with rollback.
- Dependencies should be minimized and security-reviewed.
- Framework Core stays technology-neutral; technology expertise lives in overlays.

## Performance baseline

- UI feedback < 100 ms
- Simple search < 1 s
- Normal search < 2 s
- Heavy operation < 5 s
- Prefer P95 behavior over best-case latency.

## Next architecture targets

1. Project integration/bootstrap adapters.
2. EREI APP Google project-specific overlay/context.
3. Runtime adapters for supported agent environments.
4. Add specialist skills only when evidence shows a distinct reusable procedure is needed.

`BASELINE.json` is the machine-readable checkpoint for the current framework state.
