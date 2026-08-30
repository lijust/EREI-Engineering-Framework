# EREI Engineering Framework

**Status:** Phase 2 Core Candidate  
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

Foundation V1 is stable. Phase 2 adds the first project-bootstrap, brownfield, review/verification, and security-core capabilities.

### Stable foundation

- `constitution/ENGINEERING_CONSTITUTION.md`
- Agent / Skill / Workflow / Evidence / Risk contracts
- `agents/chief-engineer/AGENT.md`
- `workflows/router/WORKFLOW.md`
- `skills/impact-analysis/`

### Phase 2 core

Project understanding:
- `skills/project-discovery/`
- `skills/project-standard-discovery/`
- `workflows/new-project/`
- `workflows/brownfield-onboarding/`

Review and verification:
- `skills/requirement-compliance-review/`
- `skills/engineering-quality-review/`
- `skills/verification-before-completion/`
- `workflows/review-and-verification/`

Security core:
- `agents/security-engineer/`
- `skills/threat-model/`
- `skills/security-review/`
- `workflows/security-critical-change/`

Research and architecture:
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

1. Google Apps Script / Google Sheets overlay.
2. Remaining specialist engineering roles.
3. Feature-development and bug-fix workflows.
4. Automated eval harness.
5. Project integration/bootstrap adapters.

`BASELINE.json` is the machine-readable checkpoint for the current framework state.
