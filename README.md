# EREI Engineering Framework

**Status:** Framework Feedback & Knowledge Promotion V1 Stable  
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
7. **Feedback / Knowledge Promotion**
8. **Optional Integration Contracts**

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
- Framework Feedback Capture V1
- Knowledge Promotion Workflow V1

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
├── PROJECT_RULES.md
└── feedback/
    ├── README.md
    └── FRAMEWORK_FEEDBACK.md
adr/
└── ADR_TEMPLATE.md
```

`FRAMEWORK_FEEDBACK.jsonl` is created only when the first evidence-backed feedback event is captured.

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

## Framework Feedback Capture V1

Material project work now includes a Framework Feedback Check through the Chief Engineer, feature-development workflow and bug-fix workflow.

Capture is triggered only when evidence reveals a plausible Framework limitation or reusable lesson, such as:

- workflow/skill/role/context gaps,
- escaped verification conditions,
- materially incorrect risk classification,
- repeated Framework-related workaround/friction,
- missing reusable patterns,
- useful negative learning.

Ordinary project bugs are not automatically Framework feedback.

Project-local source of truth:

```text
.erei/feedback/FRAMEWORK_FEEDBACK.jsonl
```

Each event records the exact pinned Framework ref, project identity, classification, observation, evidence, suggested improvement, generalizability/confidence and semantic fingerprint.

`tools/capture_framework_feedback.py` captures events and refreshes the human-readable Markdown view. `tools/validate_framework_feedback.py` validates ledgers and recomputes fingerprints. Both use Python standard library only.

Feedback capture never modifies Framework Core and never changes the project's Framework pin.

## Knowledge Promotion Workflow V1

Project feedback becomes Framework knowledge only through a separate controlled workflow:

```text
Project observation
→ evidence-backed project feedback
→ Framework review queue
→ validate root cause
→ classify / deduplicate / cluster
→ remove project-specific assumptions
→ complexity/value gate
→ Framework candidate + evals/tests
→ risk / approval
→ verification
→ Stable promotion or documented rejection
```

Raw project feedback remains owned by the source project. Framework-side review is tracked under `feedback/REVIEW_QUEUE.md`.

A feedback suggestion is a hypothesis, not an accepted solution. L3/L4 changes still require explicit approval regardless of recurrence or confidence.

A promoted Framework improvement reaches an existing project only through the Framework Upgrade Workflow; project pins never move automatically.

## Eval Harness V1

The provider-neutral automated evaluation layer is Stable:

`*.eval.json → EREI runner → CLI adapter → target agent/runtime → normalized result → deterministic scorers`

External eval systems remain optional adapters rather than Framework Core dependencies.

## Optional Runtime Adapter Contract V1

The Framework has a Stable semantic boundary for external execution runtimes, but **projects do not need a Runtime Adapter to use EREI Engineering Framework**.

By ADR-0004, concrete runtime/provider implementations are outside Framework Core. Runtime-specific research may remain under `research/` without placing that runtime on the Framework roadmap.

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
- Project-discovered Framework limitations become evidence-backed feedback, not silent self-modification.
- Raw feedback does not become Framework truth until Knowledge Promotion verifies and promotes it.

## Performance baseline

- UI feedback < 100 ms
- Simple search < 1 s
- Normal search < 2 s
- Heavy operation < 5 s
- Prefer P95 behavior over best-case latency.

## Next architecture / validation targets

1. Exercise Feedback Capture V1 on real project work after projects upgrade to this Stable Framework revision.
2. Add cross-project feedback deduplication/classification tooling once real feedback volume justifies it.
3. Add Framework effectiveness/health metrics from real project evidence.
4. Validate the Framework on additional brownfield projects.
5. Add specialist skills only when evidence shows a distinct reusable procedure is needed.
6. Revisit concrete runtime integration only when a real project requirement demonstrates the need.

`BASELINE.json` is the machine-readable checkpoint for the current framework state.
