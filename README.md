# EREI Engineering Framework

**Status:** Google Apps Script Overlay V1 Candidate  
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

Foundation V1 and Phase 2 Core are stable. The first technology overlay—Google Apps Script / Google Sheets—is now implemented as a candidate.

### Stable foundation and core

- `constitution/ENGINEERING_CONSTITUTION.md`
- Agent / Skill / Workflow / Evidence / Risk contracts
- Chief Engineer + Workflow Router
- Project discovery and brownfield onboarding
- Requirement compliance / engineering quality / verification baseline
- Security Engineer + threat model + security review + security-critical workflow

### Google Apps Script / Google Sheets overlay

- `overlays/google-apps-script/OVERLAY.md`
- `overlays/google-apps-script/SOURCES.md`
- Quotas/runtime
- Concurrency/LockService
- HTML client/server and `google.script.run`
- CacheService/PropertiesService scopes
- Google Sheets data access/batching
- Web app deployment/execute-as identity
- Apps Script-specific eval cases

The overlay uses progressive, tag-based loading so a CSS/UI task does not automatically load quota, lock, database, and deployment guidance.

### Research and architecture

- `research/LANDSCAPE.md`
- `research/BENCHMARK_MATRIX.md`
- `research/PATTERN_CATALOG.md`
- `research/ANTI_PATTERNS.md`
- `research/RESEARCH_LEDGER.md`
- `architecture/EREI_ARCHITECTURE_V1.md`

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

1. Remaining specialist engineering roles.
2. Feature-development and bug-fix workflows.
3. Automated eval harness.
4. Project integration/bootstrap adapters.
5. EREI APP Google project-specific overlay/context.

`BASELINE.json` is the machine-readable checkpoint for the current framework state.
