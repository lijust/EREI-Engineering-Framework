# EREI Engineering Framework

**Status:** Project Integration Bootstrap V1 Stable  
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

Foundation V1, Phase 2 Core, Google Apps Script / Google Sheets Overlay V1, Specialist Roles V1, Delivery Workflows V1, **Eval Harness V1**, and **Project Integration Bootstrap V1** are stable.

`adr/ADR-0001-EVAL-HARNESS.md` and `adr/ADR-0002-PROJECT-INTEGRATION-CONTRACT.md` are accepted.

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

## Stable delivery and evaluation

- Feature-development workflow
- Bug-fix workflow
- Systematic debugging
- Regression analysis
- Requirement compliance review
- Engineering-quality review
- Verification-before-completion
- Security-critical workflow
- Provider-neutral Eval Harness V1

## Project Integration Bootstrap V1

The stable project-integration contract standardizes:

```text
AGENTS.md
.erei/
├── framework.json
├── PROJECT_PROFILE.md
├── ARCHITECTURE.md
├── SECURITY_MODEL.md
├── DATA_MODEL.md
├── PERFORMANCE_BUDGET.md
└── PROJECT_RULES.md
adr/
└── ADR_TEMPLATE.md
```

### Pin model

`.erei/framework.json` declares:
- Framework repository,
- Framework baseline,
- exact Framework ref,
- project context paths,
- enabled overlays,
- runtime adapter preferences.

Candidate/Stable project state should pin the Framework using an immutable commit SHA or immutable tag rather than relying only on a mutable branch such as `main`.

### Bootstrap tooling

`tools/bootstrap_project.py` is a Python-standard-library-only, fail-closed generator:
- dry-run supported,
- no overwrite by default,
- explicit conflict reporting,
- explicit `--force` required for replacement,
- no execution of target project code,
- no third-party package dependency.

Generated files are scaffolding, not completed facts. Greenfield projects compose integration with project discovery/new-project workflow; brownfield projects compose it with brownfield onboarding and project-standard discovery before project context is treated as confirmed.

## Eval Harness V1

The provider-neutral automated evaluation layer is stable:

`*.eval.json → EREI runner → CLI adapter → target agent/runtime → normalized result → deterministic scorers`

The runner uses Python standard library only. External systems such as Inspect AI, DeepEval, Promptfoo, Braintrust, or provider-native eval APIs remain optional adapters rather than Framework Core dependencies.

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

1. Apply Project Integration Bootstrap V1 to a real brownfield project.
2. Build the EREI APP Google project-specific context/overlay only from confirmed repository evidence.
3. Runtime adapters for supported agent environments.
4. Framework upgrade workflow.
5. Add specialist skills only when evidence shows a distinct reusable procedure is needed.

`BASELINE.json` is the machine-readable checkpoint for the current framework state.
