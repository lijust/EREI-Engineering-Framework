# EREI Engineering Framework

**Existing released baseline:** Task Learning & Learning Review V1 Stable (2026-09-02)  
**Current product scope decision:** Evidence-first; **no autonomous learning** (2026-11-10, [ADR-0006](adr/ADR-0006-EVIDENCE-FIRST-NO-AUTONOMOUS-LEARNING.md)). This policy does not repin existing projects or change the Stable baseline.

EREI Engineering Framework is a reusable, cross-project engineering operating system for AI-assisted software development.

It is intentionally **not** a project-specific codebase, **not** a flat prompt/skill library, **not** a mandatory agent runtime, and **not** a repository of provider-specific runtime clients.

## Product objective — evidence-first engineering

Build an AI-assisted engineering system that diagnoses actual defects, proposes bounded repairs, executes only with explicit permission, independently verifies the results, and **records experiments, errors, outcomes and decisions for future human-directed development/release plans**.

**Not an objective or roadmap dependency:** autonomous/self-training agents, automatic behavioral or prompt updates from history, self-modifying workflows, online learning or automatic knowledge promotion. Existing **Task Learning** is a historical name for structured **experience recording and review signals only**. Future version improvements require a human decision, separate validation and ordinary release governance. See [ADR-0006](adr/ADR-0006-EVIDENCE-FIRST-NO-AUTONOMOUS-LEARNING.md) and the [experiment record template](research/EXPERIMENT_RECORD_TEMPLATE.md).

The framework separates:

1. **Constitution / Policies**
2. **Agents / Engineering Roles**
3. **Skills / Reusable Procedures**
4. **Workflows / Orchestration**
5. **Project Context / Standards**
6. **Durable Artifacts / Evidence**
7. **Task experience recording / deterministic review signals (legacy Task Learning naming)**
8. **Evidence-backed feedback / human-approved future versions**
9. **Optional Integration Contracts**

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
- Task Learning Capture V1
- Learning Review / Deterministic Review Trigger V1

The Framework has completed its first real brownfield integration with `lijust/EREI-App-Google`.

Accepted architecture decisions:

- `ADR-0001-EVAL-HARNESS.md`
- `ADR-0002-PROJECT-INTEGRATION-CONTRACT.md`
- `ADR-0003-RUNTIME-ADAPTER-CONTRACT.md`
- `ADR-0004-CONCRETE-RUNTIME-IMPLEMENTATIONS-OUT-OF-SCOPE.md`
- `ADR-0005-TASK-LEARNING-AND-REVIEW-TRIGGERS.md` (original evidence-capture contract)
- `ADR-0006-EVIDENCE-FIRST-NO-AUTONOMOUS-LEARNING.md` (current product scope; no self-learning)

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

The stable project-integration contract now standardizes:

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
├── feedback/
│   ├── README.md
│   └── FRAMEWORK_FEEDBACK.md
└── learning/
    ├── README.md
    └── LEARNING_SUMMARY.md
adr/
└── ADR_TEMPLATE.md
```

Machine ledgers are created on first use rather than as empty files:

```text
.erei/feedback/FRAMEWORK_FEEDBACK.jsonl
.erei/learning/TASK_EVENTS.jsonl
.erei/learning/LEARNING_REVIEWS.jsonl
.erei/learning/LEARNING_STATE.json
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

## Framework Feedback Capture V1

Material project work includes a Framework Feedback Check through the Chief Engineer and delivery workflows.

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

Feedback capture never modifies Framework Core and never changes the project's Framework pin.

## Task Learning Capture V1

Framework Feedback records exceptional Framework lessons. Task Learning is broader: **every routed engineering execution becomes one structured project-local experience event**, including clean success, blocked work and failed execution.

The Router terminal path is now:

```text
Execution
→ review / verification
→ convergence
→ Framework Feedback Check when applicable
→ Task Learning Event
→ deterministic Learning Review Trigger
→ terminal state
```

Task Learning stores observable engineering signals rather than private reasoning:

- exact Framework ref,
- workflow and risk,
- terminal/outcome class,
- task materiality,
- rework cycles,
- verification failures / verification escape,
- Framework-feedback linkage,
- manual workaround/context-gap/scope-growth signals,
- critical security/data signal,
- coarse duration class.

Canonical project-local files:

```text
.erei/learning/TASK_EVENTS.jsonl
.erei/learning/LEARNING_REVIEWS.jsonl
.erei/learning/LEARNING_STATE.json
.erei/learning/LEARNING_SUMMARY.md
```

`TASK_EVENTS.jsonl` and `LEARNING_REVIEWS.jsonl` are append-only evidence. State and Markdown summary are deterministic derived views.

`tools/task_learning.py` uses only Python standard library and provides:

- `capture`
- `status`
- `validate`
- `review-close`

Task-event semantic fingerprints and review-cutoff/epoch validation detect malformed or inconsistent ledgers.

## Deterministic Learning Review Trigger V1

Every project Learning Epoch returns one state:

- `LEARNING_HEALTHY`
- `LEARNING_WATCH`
- `REVIEW_RECOMMENDED`
- `REVIEW_DUE`
- `IMMEDIATE_REVIEW`

Initial transparent thresholds:

- **Immediate:** verification escape or critical security/data event.
- **Due:** 40 material tasks, same Framework-feedback fingerprint 3 times, or 5 Framework-feedback tasks.
- **Recommended:** 20 material tasks; or elevated rework/verification-failure rates after minimum sample; or 3 manual workarounds/context gaps.
- **Watch:** 10 material tasks or 2 Framework-feedback tasks.

These thresholds are an initial calibration to be tested against real projects, not permanent truth.

A Learning Review validates the accumulated evidence, records findings/decision/actions, closes the exact event cutoff and starts the next epoch. A review trigger is not a release state and never authorizes Framework self-modification.

## Knowledge Promotion Workflow V1

Project feedback becomes Framework knowledge only through a separate controlled workflow:

```text
Project execution
→ Task Learning
→ Learning Review when enough evidence accumulates
→ Framework limitation/reusable lesson?
→ evidence-backed Framework Feedback
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

Raw project feedback/task-learning evidence remains owned by the source project. Framework-side feedback review is tracked under `feedback/REVIEW_QUEUE.md`.

A promoted Framework improvement reaches an existing project only through Framework Upgrade Workflow; project pins never move automatically.

Future Task Learning epochs provide before/after evidence for whether a promoted Framework change actually improved outcomes.

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
- Every routed engineering execution produces structured learning data, including success.
- Task Learning stores structured observable signals, not private chain-of-thought or secrets.
- Learning metrics are evidence signals, not automatic proof of causation.
- Raw learning/feedback does not become Framework truth until controlled review/promotion verifies it.

## Performance baseline

- UI feedback < 100 ms
- Simple search < 1 s
- Normal search < 2 s
- Heavy operation < 5 s
- Prefer P95 behavior over best-case latency.

## Next validation priorities — no autonomous learning roadmap

1. **Demonstrate practical value** on fresh, source-backed bug diagnosis and repair proposals with preregistered acceptance and independent human/replay evidence. The E1 retrospective six-case trial is exploratory and did not establish model effectiveness.
2. **Reuse existing isolation and verification**, only as needed for a demonstrably useful and explicitly authorized repair workflow. Do not expand privileged execution complexity as a substitute for model quality.
3. **Record experiments and operational outcomes** using existing Task Learning/feedback ledgers plus the lightweight [experiment record](research/EXPERIMENT_RECORD_TEMPLATE.md). Preserve negative results and uncertainty.
4. **Maintain a human-owned future-release backlog:** convert validated findings into specific possible changes, prioritize by impact and evidence, implement only after separate authorization.
5. **Retain compatibility:** existing learning-named files, review triggers, pinned Framework refs and old evidence remain unchanged. No automated memory injection, training, self-modification or self-promotion is planned.

`BASELINE.json` is the machine-readable checkpoint for the existing Stable Framework version. This new scope statement is not a Stable promotion, permission grant, project upgrade or new runner acceptance.
