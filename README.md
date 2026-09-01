# EREI Engineering Framework

**Status:** Framework Scope Boundary V1 Stable  
**Date:** 2026-09-02

EREI Engineering Framework is a reusable, cross-project engineering operating system for AI-assisted software development.

It is intentionally **not** a project-specific codebase, **not** a flat prompt/skill library, **not** a mandatory agent runtime, and **not** a repository of provider-specific runtime clients.

The framework separates:

1. **Constitution / Policies**
2. **Agents / Engineering Roles**
3. **Skills / Reusable Procedures**
4. **Workflows / Orchestration**
5. **Project Context / Standards**
6. **Durable Artifacts / Evidence**
7. **Optional Integration Contracts**

## Current state

The following layers are Stable:

- Foundation V1
- Phase 2 Core
- Google Apps Script / Google Sheets Overlay V1
- Specialist Roles V1
- Delivery Workflows V1
- Eval Harness V1
- Project Integration Bootstrap V1
- Framework Upgrade Workflow V1
- Runtime Adapter Contract V1
- Framework Scope Boundary V1

The Framework has completed its first real brownfield integration with `lijust/EREI-App-Google`.

Accepted architecture decisions:

- `ADR-0001-EVAL-HARNESS.md`
- `ADR-0002-PROJECT-INTEGRATION-CONTRACT.md`
- `ADR-0003-RUNTIME-ADAPTER-CONTRACT.md`
- `ADR-0004-CONCRETE-RUNTIME-IMPLEMENTATIONS-OUT-OF-SCOPE.md`

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

## Stable delivery and verification

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

`.erei/framework.json` declares the Framework repository, exact immutable Framework ref, project context paths, enabled overlays and optional runtime adapter preferences.

Candidate/Stable project state should pin the Framework using an immutable commit SHA or immutable tag rather than relying only on a mutable branch such as `main`.

`tools/bootstrap_project.py` is Python-standard-library-only and fail-closed: dry-run supported, no overwrite by default, explicit conflict reporting, explicit `--force`, no target-project execution and no third-party dependency.

## Framework Upgrade Workflow V1

A Framework pin is treated as a release dependency, not as a string to replace casually.

```text
current immutable pin
→ exact target resolution
→ revision comparison
→ compatibility/risk classification
→ project impact review
→ approval when required
→ candidate pin
→ project verification
→ convergence
→ promote or rollback
```

Projects can continue working on their current Stable pin while Framework development happens independently. Candidate Framework work is not project truth until it becomes Stable and the project explicitly upgrades.

## Eval Harness V1

The provider-neutral automated evaluation layer is Stable:

`*.eval.json → EREI runner → CLI adapter → target agent/runtime → normalized result → deterministic scorers`

External eval systems remain optional adapters rather than Framework Core dependencies.

## Optional Runtime Adapter Contract V1

The Framework has a Stable semantic boundary for external execution runtimes, but **projects do not need a Runtime Adapter to use EREI Engineering Framework**.

EREI owns governance, risk, workflow/role/skill selection, project context, required capabilities, approval policy, evidence requirements, independent verification and release acceptance.

An external runtime may own provider/session/process/shared-workspace lifecycle. Runtime capability never authorizes work by itself and runtime success is evidence, not independent completion proof.

By ADR-0004, concrete runtime/provider implementations are outside Framework Core. Tutti-, Codex-, Claude-, OpenCode- or other provider-specific clients, credentials, lifecycle logic and CI are created only when a real project requirement justifies them and live outside this repository.

Runtime-specific research may remain under `research/` as architectural evidence without placing that runtime on the Framework roadmap.

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
- Optional integration capability never outranks Framework governance.
- Do not build infrastructure before a demonstrated project requirement exists.
- Project-discovered Framework limitations should become evidence-backed feedback, not silent self-modification.

## Performance baseline

- UI feedback < 100 ms
- Simple search < 1 s
- Normal search < 2 s
- Heavy operation < 5 s
- Prefer P95 behavior over best-case latency.

## Next architecture / validation targets

1. Build Framework Feedback Capture V1 for project-discovered limitations and friction.
2. Build Knowledge Promotion Workflow V1 from evidence-backed project observations.
3. Add cross-project deduplication/classification of Framework feedback.
4. Add Framework effectiveness/health metrics based on real project evidence.
5. Validate the Framework on additional brownfield projects.
6. Add specialist skills only when evidence shows a distinct reusable procedure is needed.
7. Revisit any concrete runtime integration only when a real project requirement demonstrates the need.

`BASELINE.json` is the machine-readable checkpoint for the current framework state.
