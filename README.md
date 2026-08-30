# EREI Engineering Framework

**Status:** Research-to-Architecture Baseline V0.1  
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

## Current phase

The framework is currently in the **Research → Architecture** phase.

The first formal research artifacts are under `/research`, and the initial target architecture is under `/architecture`.

## Current artifacts

- `research/LANDSCAPE.md`
- `research/BENCHMARK_MATRIX.md`
- `research/PATTERN_CATALOG.md`
- `research/ANTI_PATTERNS.md`
- `research/RESEARCH_LEDGER.md`
- `architecture/EREI_ARCHITECTURE_V1.md`

## Foundation decisions already approved

- Hybrid autonomy: safe changes may execute automatically; architecture/security/data migrations require approval.
- Enterprise-grade SaaS security mindset.
- One tenant/company per user in the current EREI APP Google project.
- Frontend is never trusted for authorization.
- Refactor only when measurable benefit exceeds migration risk.
- DEV → Candidate → QA → Stable release flow with rollback.
- Performance budgets:
  - UI feedback < 100 ms
  - Simple search < 1 s
  - Normal search < 2 s
  - Heavy operation < 5 s
- Current EREI APP Google stack remains Vanilla JS + HTML + CSS + Apps Script unless migration/build tooling is technically justified.
- Dependencies should be minimized and security-reviewed.
- Framework is reusable across future EREI projects.
