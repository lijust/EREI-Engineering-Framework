# EREI Engineering Framework

**Status:** Runtime Adapter Contract V1 Stable  
**Date:** 2026-09-01

EREI Engineering Framework is a reusable, cross-project engineering operating system for AI-assisted software development.

It is intentionally **not** a project-specific codebase, **not** a flat prompt/skill library, and **not** a mandatory agent runtime.

The framework separates:

1. **Constitution / Policies**
2. **Agents / Engineering Roles**
3. **Skills / Reusable Procedures**
4. **Workflows / Orchestration**
5. **Project Context / Standards**
6. **Durable Artifacts / Evidence**
7. **Runtime Adapters / Distribution**

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

The Framework has also completed its first real brownfield integration with `lijust/EREI-App-Google`.

Accepted architecture decisions:

- `ADR-0001-EVAL-HARNESS.md`
- `ADR-0002-PROJECT-INTEGRATION-CONTRACT.md`
- `ADR-0003-RUNTIME-ADAPTER-CONTRACT.md`

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

## Framework Upgrade Workflow V1

A Framework pin is treated as a release dependency, not as a string to replace casually.

The Stable upgrade path requires:

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

The previous exact pin remains rollback evidence until the upgraded project baseline is accepted.

## Eval Harness V1

The provider-neutral automated evaluation layer is Stable:

`*.eval.json → EREI runner → CLI adapter → target agent/runtime → normalized result → deterministic scorers`

The runner uses Python standard library only. External systems such as Inspect AI, DeepEval, Promptfoo, Braintrust, or provider-native eval APIs remain optional adapters rather than Framework Core dependencies.

## Runtime Adapter Contract V1

The Framework now has a Stable semantic boundary for real agent/runtime execution.

EREI owns:

- Constitution and governance,
- risk classification,
- workflow/role/skill selection,
- project context and Framework pinning,
- required capabilities,
- mutation and approval policy,
- evidence requirements,
- independent verification,
- release acceptance.

Concrete runtimes own their provider/session/process/shared-workspace lifecycle.

Adapters declare standardized capabilities and translate Framework intent into the runtime without weakening governance. Missing required capabilities fail closed.

Runtime success is evidence, not independent completion proof.

### Runtime capability vocabulary

Runtime Adapter V1 covers capabilities including:

- task execution
- session resume/persistence
- exact cancellation
- workspace read/write
- interactive approval/input
- mutation/tool policy
- trace export
- runtime recovery
- optional shared context
- optional parallel agents
- optional agent handoff

### Tutti

Tutti is a high-priority **experimental adapter candidate**, not a Framework dependency and not yet an enableable Stable adapter.

Research confirmed:

- Apache-2.0 root license,
- provider-neutral Agent Host architecture,
- a versioned local daemon API intended for desktop, CLI and approved local integrations,
- workspace-agent operations for session creation/read, sending input, exact-turn cancellation, interactive responses, plan decisions and related workspace capabilities.

The next step is a narrow Tutti adapter prototype plus conformance testing for policy enforcement, isolation, failure semantics, evidence normalization and version compatibility.

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
- Runtime capability never outranks Framework governance.

## Performance baseline

- UI feedback < 100 ms
- Simple search < 1 s
- Normal search < 2 s
- Heavy operation < 5 s
- Prefer P95 behavior over best-case latency.

## Next architecture / validation targets

1. Build a Tutti experimental runtime adapter against the documented local daemon API.
2. Run single-agent Runtime Adapter conformance.
3. Prove mutation/approval and project-workspace isolation fail closed.
4. Normalize runtime trace/evidence without trusting runtime self-certification.
5. Add multi-agent handoff/parallel execution only after the single-agent trust boundary passes.
6. Build the knowledge-promotion workflow from proven project lessons.
7. Validate the Framework on additional brownfield projects.
8. Add specialist skills only when evidence shows a distinct reusable procedure is needed.

`BASELINE.json` is the machine-readable checkpoint for the current framework state.