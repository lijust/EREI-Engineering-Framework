# EREI Engineering Framework

**Status:** Specialist Roles V1 Stable  
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

Foundation V1, Phase 2 Core, Google Apps Script / Google Sheets Overlay V1, and Specialist Roles V1 are stable.

## Engineering roles

The framework now defines distinct accountability roles for:

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

## Stable core capabilities

- Engineering Constitution
- Agent / Skill / Workflow / Evidence / Risk contracts
- Workflow Router and impact analysis
- New-project discovery and brownfield onboarding
- Requirement compliance / engineering quality / verification baseline
- Threat modeling, security review and security-critical workflow
- Google Apps Script / Google Sheets technology overlay
- Full specialist engineering role set

## Google Apps Script / Google Sheets overlay

The first technology overlay includes routable references for:
- quotas/runtime,
- concurrency/LockService,
- HTML client/server and `google.script.run`,
- CacheService/PropertiesService scopes,
- Google Sheets batching/data access,
- web app deployment/execute-as identity,
- platform-specific eval cases.

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

## Next implementation targets

1. Feature-development and bug-fix workflows.
2. Systematic debugging and regression skills.
3. Automated eval harness.
4. Project integration/bootstrap adapters.
5. EREI APP Google project-specific overlay/context.

`BASELINE.json` is the machine-readable checkpoint for the current framework state.
