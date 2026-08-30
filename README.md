# EREI Engineering Framework

**Status:** Delivery Workflows V1 Candidate  
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

Foundation V1, Phase 2 Core, Google Apps Script / Google Sheets Overlay V1, and Specialist Roles V1 are stable. Delivery Workflows V1 is the current candidate.

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
`workflows/feature-development/` implements a proportional lifecycle:

Outcome/acceptance → impact/risk → structural gates → technical plan → implementation slices → regression analysis → compliance review → engineering review → specialist gates → fresh verification → convergence → release.

### Bug fixing
`workflows/bug-fix/` implements:

Precise defect → baseline/reproduction → systematic debugging/root cause → impact/risk → smallest safe fix → regression guard → regression analysis → reviews → fresh verification → convergence → release.

### Supporting skills
- `skills/systematic-debugging/`
- `skills/regression-analysis/`

Both include specifications and eval cases.

## Stable core capabilities

- Engineering Constitution
- Agent / Skill / Workflow / Evidence / Risk contracts
- Workflow Router and impact analysis
- New-project discovery and brownfield onboarding
- Requirement compliance / engineering quality / verification baseline
- Threat modeling, security review and security-critical workflow
- Google Apps Script / Google Sheets technology overlay
- Full specialist engineering role set

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

1. Automated eval harness.
2. Project integration/bootstrap adapters.
3. EREI APP Google project-specific overlay/context.
4. Add specialist skills only when evidence shows a distinct reusable procedure is needed.

`BASELINE.json` is the machine-readable checkpoint for the current framework state.
