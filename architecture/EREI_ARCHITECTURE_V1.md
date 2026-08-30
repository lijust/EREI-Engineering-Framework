# EREI Engineering Framework Architecture V1

**Status:** Draft Architecture Baseline V0.1  
**Decision state:** Proposed from approved foundation decisions + landscape research.

---

# 1. Mission

Build a reusable engineering operating system that allows an AI coding environment to act with the combined discipline of:

- Principal/Chief Engineer
- System Architect
- Frontend Engineer
- Backend Engineer
- Security Engineer
- Data Engineer
- Performance Engineer
- QA Engineer
- Release/DevOps Engineer

while preserving:
- cross-layer reasoning,
- durable project context,
- evidence-based verification,
- risk-proportional rigor,
- portability across agent runtimes.

The framework must improve with project experience without becoming contaminated by project-specific assumptions.

---

# 2. Architectural thesis

EREI is **not a skill library**.

EREI is a layered engineering system:

```text
                 Constitution / Policies
                          |
             +------------+------------+
             |                         |
      Project Context             Framework Standards
             |                         |
             +------------+------------+
                          |
                   Chief Engineer
                          |
          +---------------+---------------+
          |                               |
     Engineering Roles                Workflow Router
          |                               |
          +---------------+---------------+
                          |
                     Reusable Skills
                          |
                     Tools / Scripts
                          |
                  Evidence / Verification
                          |
                      Convergence
                          |
                        Release
```

---

# 3. Core layers

## 3.1 Constitution

Highest-authority engineering rules.

Candidate principles:

1. Frontend is untrusted.
2. Never cross tenant boundaries.
3. Durable state beats conversational memory.
4. Evidence beats claims.
5. Deterministic verification precedes probabilistic judgment.
6. Security correctness beats convenience.
7. Data correctness beats apparent success.
8. Measure before optimizing.
9. Complexity requires justification.
10. Refactor only when measurable benefit exceeds migration risk.
11. Critical operations must be observable.
12. Architectural decisions must be explainable and durable.
13. Process rigor increases with risk.
14. Stable is modified through controlled release, not direct edits.
15. Project-specific assumptions must not silently enter Framework Core.

Constitution changes require explicit approval.

---

## 3.2 Agents / Engineering Roles

Roles define **accountability and perspective**, not step-by-step procedures.

Initial roles:

- `chief-engineer`
- `system-architect`
- `frontend-engineer`
- `backend-engineer`
- `security-engineer`
- `data-engineer`
- `performance-engineer`
- `qa-engineer`
- `release-engineer`

### Chief Engineer responsibilities

- Interpret request.
- Classify risk.
- Determine affected layers.
- Select workflow.
- Select required roles.
- Select required skills.
- Ensure cross-layer impact analysis.
- Escalate approval-required decisions.
- Require evidence before completion.
- Coordinate convergence/release recommendation.

Chief Engineer is not a giant universal implementation prompt.

---

## 3.3 Skills

Skills define reusable procedures.

Initial candidates:

- `project-discovery`
- `architecture-design`
- `impact-analysis`
- `threat-model`
- `security-review`
- `code-review`
- `systematic-debugging`
- `root-cause-analysis`
- `performance-analysis`
- `test-design`
- `regression-analysis`
- `refactoring-analysis`
- `data-migration`
- `observability-design`
- `incident-analysis`
- `release-verification`
- `dependency-review`
- `project-standard-discovery`

### Skill standard

Substantial skills should support:

```text
skill-name/
├── SKILL.md
├── SPEC.md
├── SOURCES.md          optional
├── references/         optional
├── scripts/            optional
├── evals/              recommended
└── fixtures/           optional
```

`SKILL.md`
- Runtime instructions.
- Trigger conditions.
- Procedure.
- Required outputs.
- Stop/escalation rules.

`SPEC.md`
- Purpose.
- Scope/non-scope.
- Design rationale.
- Required evidence.
- Failure modes.
- Evaluation strategy.
- Maintenance expectations.

`SOURCES.md`
- External provenance.
- Currentness expectations.
- License notes when relevant.

---

## 3.4 Workflows

Workflows compose roles + skills + tools + gates + artifacts.

Initial workflow set:

### `new-project`
Discovery → constraints → architecture baseline → risk model → standards → initial ADRs → project profile.

### `brownfield-onboarding`
Inspect code → runtime → tests → data → deployment → security → conventions → risks → baseline verification.

### `feature-development`
Requirement → risk → impact → spec → plan → implementation → review → verification → convergence → release decision.

### `bug-fix`
Reproduce → classify → root cause → minimal fix plan → implement → regression check → verify.

### `security-critical-change`
Threat model → design → approval gate → implementation → independent security review → adversarial verification → release gate.

### `performance-investigation`
Measure → decompose latency/resource use → identify bottleneck → hypothesis → controlled optimization → benchmark → regression check.

### `migration`
Current state → desired state → invariants → compatibility plan → backup/rollback → dry run → execute → verify.

### `release`
Candidate evidence → QA → security/data gates → performance checks → rollback point → Stable.

### `incident-response`
Detect → contain → preserve evidence → diagnose → remediate → verify → postmortem → promote reusable lesson.

---

# 4. Risk model

```text
L0 — cosmetic / isolated
L1 — normal local feature
L2 — cross-layer change
L3 — auth / data / security / architecture
L4 — destructive / production-critical / irreversible
```

## Autonomy

- L0/L1: autonomous implementation allowed when inside approved architecture.
- L2: autonomous only when no new architectural/security/data boundary is introduced.
- L3/L4: structural decision requires explicit approval.

Risk may be raised by any relevant engineering role.

Security may block release for critical findings.

---

# 5. Context architecture

## Principle
Context is routed, not dumped.

Project repository should contain durable context such as:

```text
AGENTS.md
.erei/
├── PROJECT_PROFILE.md
├── ARCHITECTURE.md
├── SECURITY_MODEL.md
├── DATA_MODEL.md
├── PERFORMANCE_BUDGET.md
└── PROJECT_RULES.md

adr/
standards/
runbooks/
```

The framework should eventually support:

1. Project inspection.
2. Standard discovery.
3. Standard classification.
4. Context index.
5. Task-aware retrieval.
6. Path-aware local instructions.
7. Progressive disclosure.

Chat/project custom instructions should remain a lightweight bootstrap pointer.

---

# 6. Evidence model

Claims should identify their evidence basis where material.

Initial taxonomy:

- `CODE_CONFIRMED`
- `DOC_CONFIRMED`
- `TEST_CONFIRMED`
- `TOOL_CONFIRMED`
- `USER_CONFIRMED`
- `RUNTIME_CONFIRMED`
- `INFERRED`
- `UNKNOWN`

Critical decisions should not silently treat `INFERRED` as `CONFIRMED`.

---

# 7. Review architecture

For L2+ work, default review sequence:

1. **Requirement/spec compliance**
2. **Engineering/code quality**
3. **Security review** when applicable
4. **Data integrity review** when applicable
5. **Performance review** when applicable
6. **Regression verification**
7. **Convergence**

Critical review should prefer fresh/independent context.

---

# 8. Definition of Done

Applicable items must be satisfied:

- Requirement satisfied.
- Architecture respected.
- Tenant boundaries preserved.
- Authorization validated server-side.
- Input validation applied.
- Data invariants preserved.
- Errors handled.
- Relevant tests passed.
- Regression risk checked.
- Performance budget checked where applicable.
- Logging/observability sufficient.
- Evidence captured.
- Candidate verified.
- Rollback available for production-impacting change.
- Convergence found no unresolved blocking drift.

"Code written" is never sufficient Definition of Done.

---

# 9. Performance contract

Approved baseline:

| Operation | Budget |
|---|---:|
| UI feedback | < 100 ms |
| Simple search | < 1 s |
| Normal search | < 2 s |
| Heavy operation | < 5 s |

Prefer percentile behavior (especially P95) over best-case measurements.

A successful operation that routinely violates its budget remains a performance defect.

---

# 10. Security architecture principles

Non-negotiable baseline:

- Frontend is never trusted for authorization.
- Hidden/disabled UI is not a security control.
- Client-supplied identity/tenant scope must not be blindly trusted.
- Authorization is server-side.
- Cross-tenant leakage is release-blocking.
- High-risk skills contain explicit unsafe rationalizations to reject.
- Dependencies are minimized and security-reviewed.
- Secrets are not committed to source.
- Security rigor scales with risk.
- Threat boundaries should be explicit for L3/L4 changes.

---

# 11. Release model

```text
DEV
  ↓
Candidate
  ↓
QA / Security / Data / Performance evidence
  ↓
Stable
```

Stable must have:
- Version/change identifier.
- Verification evidence.
- Known-risk record.
- Rollback point or documented rollback strategy.

Direct Stable edits are prohibited by default.

---

# 12. Project overlays

Framework Core must remain technology-neutral.

Technology knowledge is delivered through overlays.

Initial planned overlay:

```text
overlays/google-apps-script/
├── concurrency/
├── quotas/
├── caching/
├── properties/
├── spreadsheet-access/
├── google-script-run/
├── deployment/
├── identity/
├── observability/
└── performance/
```

Project-specific business rules remain in the project repository, not the generic overlay.

---

# 13. Runtime adapters

Core should not be tied to one agent product.

Planned adapters:

- ChatGPT / Codex
- Claude Code
- Cursor
- OpenCode
- GitHub Copilot
- future runtimes

Adapters translate framework assets into runtime-specific installation/invocation mechanisms.

Core logic and standards should not be duplicated per adapter.

---

# 14. Evaluation architecture

EREI must test not only software produced by the framework, but the framework assets themselves.

## Skill evals

### Trigger evals
- Should trigger.
- Should not trigger.
- Ambiguous trigger.

### Behavior evals
- Required steps followed.
- Mandatory evidence collected.
- Stop conditions respected.
- Unsafe shortcuts rejected.

### Regression evals
A previously fixed skill failure becomes a permanent eval.

## Workflow evals
Simulated scenarios should test:
- Correct risk classification.
- Correct role/skill routing.
- Approval gates.
- Review independence.
- Evidence completeness.
- Convergence.

---

# 15. Knowledge promotion

Project learning does not automatically become framework law.

Promotion lifecycle:

```text
Project observation
      ↓
Repeated usefulness?
      ↓
Remove project assumptions
      ↓
Security/license/provenance review
      ↓
Create pattern/spec
      ↓
Add evals
      ↓
Framework candidate
      ↓
Approval
      ↓
Framework Core
```

This is a key EREI-native differentiator.

---

# 16. Proposed repository structure

```text
EREI-Engineering-Framework/
├── README.md
├── constitution/
│   └── ENGINEERING_CONSTITUTION.md
├── agents/
├── skills/
├── workflows/
├── standards/
├── presets/
├── bundles/
├── overlays/
├── adapters/
├── evals/
├── schemas/
├── templates/
├── architecture/
│   └── EREI_ARCHITECTURE_V1.md
└── research/
    ├── LANDSCAPE.md
    ├── BENCHMARK_MATRIX.md
    ├── PATTERN_CATALOG.md
    ├── ANTI_PATTERNS.md
    └── RESEARCH_LEDGER.md
```

---

# 17. Next implementation sequence

Do **not** begin by creating every agent and skill.

Recommended order:

1. Freeze Architecture V1 baseline.
2. Draft Engineering Constitution.
3. Define framework schemas/contracts:
   - Agent contract
   - Skill contract
   - Workflow contract
   - Evidence contract
   - Risk contract
4. Build Chief Engineer role + workflow router.
5. Build `impact-analysis` skill.
6. Build `project-discovery` and `brownfield-onboarding`.
7. Build review/evidence baseline.
8. Build first specialist roles.
9. Build Security core.
10. Build Google Apps Script overlay.
11. Apply framework to EREI APP Google as first real-world validation.
12. Feed failures back into evals and promotion pipeline.

---

# 18. Open design questions for the next phase

These are not blockers for the current baseline:

- Exact manifest/lock format.
- Whether an existing installer (e.g. dotagents-style tooling) should be reused.
- Exact adapter mechanics for each coding-agent runtime.
- Exact eval harness implementation.
- Whether schemas should be YAML, JSON Schema, or Markdown + frontmatter.
- How project-standard discovery should be automated.
- How framework versions are pinned per project.

These should be resolved by evidence and prototypes, not preference alone.
