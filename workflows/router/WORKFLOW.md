# Engineering Workflow Router

**Type:** Meta-workflow  
**Status:** Draft V1

## Objective

Select the smallest safe engineering workflow for a request based on project context, affected layers, risk, uncertainty, and change type.

## Entry condition

Run for any engineering request that may change project code, data, architecture, deployment, security posture, or durable framework/project artifacts.

L0 conversational explanation-only requests do not require the router unless they lead to implementation.

## Inputs

- User/request intent.
- Project-local instructions and profile.
- Relevant architecture/ADRs.
- Current state evidence where material.
- Engineering Constitution.
- Risk Contract.
- Available roles, skills, workflows, overlays, and tools.

## Stage 1 — Normalize the request

Separate:
- desired outcome,
- explicit constraints,
- suggested implementation,
- acceptance criteria,
- unknowns.

Do not treat the user's proposed implementation as mandatory unless explicitly required.

## Stage 2 — Identify change class

Choose one or more:
- cosmetic/UI,
- feature,
- bug,
- performance,
- security,
- data/schema,
- architecture,
- dependency/platform,
- deployment/release,
- incident,
- documentation/governance,
- brownfield onboarding,
- new project/bootstrap.

## Stage 3 — Impact analysis

Identify affected layers:
- frontend,
- backend,
- contracts/API,
- identity/authentication,
- authorization/tenant isolation,
- data/storage,
- concurrency/consistency,
- performance,
- observability,
- deployment,
- external integrations,
- framework/project governance.

If the actual impact cannot yet be established, route to inspection/discovery before implementation.

## Stage 4 — Risk classification

Apply `schemas/RISK_CONTRACT.md`.

Risk is based on blast radius and boundaries, not perceived task size.

Reclassify upward if new evidence appears later.

## Stage 5 — Choose workflow

Default mapping:

| Condition | Workflow |
|---|---|
| New project | `new-project` |
| Existing unfamiliar project | `brownfield-onboarding` |
| New functional capability | `feature-development` |
| Reproducible defect | `bug-fix` |
| Security/auth boundary | `security-critical-change` |
| Performance target/bottleneck | `performance-investigation` |
| Data/state transformation | `migration` |
| Production promotion | `release` |
| Live operational failure | `incident-response` |

Low-risk variants may abbreviate stages explicitly; required gates remain mandatory.

## Stage 6 — Select roles

Always include Chief Engineer for L2+ routing.

Activate specialist roles only when their responsibility is materially affected.

Examples:

- L0 visual copy/style: Frontend.
- L1 local backend bug: Backend + QA as needed.
- L2 API/search flow: Frontend + Backend + QA; add Performance if budget-sensitive.
- L3 auth/tenant: Architect + Backend + Security + QA; Data when persistence/scope changes.
- L3 schema migration: Architect + Data + Backend + QA + Release; Security if access model changes.
- L4 destructive production operation: Chief Engineer + relevant specialists + Release + independent review.

## Stage 7 — Select skills

Select procedures, not personas. Typical skills:
- impact-analysis,
- architecture-design,
- systematic-debugging,
- root-cause-analysis,
- threat-model,
- security-review,
- performance-analysis,
- test-design,
- regression-analysis,
- refactoring-analysis,
- data-migration,
- dependency-review,
- release-verification.

Avoid activating overlapping skills without a distinct purpose.

## Stage 8 — Approval gate

Before structural execution:

- L0/L1: normally autonomous within approved architecture.
- L2: autonomous if no new architecture/security/data boundary is introduced.
- L3/L4: explicit approval required for structural decision.

Approval does not waive constitutional security/data requirements.

## Stage 9 — Execute and collect evidence

During execution:
- preserve agreed invariants,
- prefer deterministic verification,
- record material evidence,
- escalate discovered risk,
- keep project truth durable.

## Stage 10 — Review

For L2+ default to:
1. requirement/spec compliance review,
2. engineering quality review,
3. conditional security/data/performance review,
4. regression verification.

Prefer independent/fresh review context for material changes.

## Stage 11 — Converge

Compare:
- requested outcome,
- durable spec/plan where present,
- implementation,
- evidence,
- unresolved findings.

Classify every material gap as:
- resolved,
- accepted with rationale,
- deferred explicitly,
- blocking.

Run Framework Feedback Check before terminal learning capture when material evidence suggests a Framework limitation or reusable lesson, so any feedback IDs/fingerprints can be linked into the Task Learning Event.

## Stage 12 — Capture Task Learning Event

Before returning any terminal state for a routed engineering execution, invoke `task-learning-capture` exactly once.

Record observable execution signals only:
- exact project and Framework ref,
- selected workflow/risk,
- terminal state/outcome class,
- materiality,
- rework/verification signals,
- Framework Feedback links when present,
- workaround/context/scope/critical security-data signals.

Do not store chain-of-thought, credentials, or unrelated conversation content.

Read the deterministic learning trigger returned from the project-local `.erei/learning/` state:

- `LEARNING_HEALTHY` — finish normally.
- `LEARNING_WATCH` — continue normal work while evidence accumulates.
- `REVIEW_RECOMMENDED` — surface that a Learning Review is useful soon.
- `REVIEW_DUE` — surface/queue Learning Review before substantial additional Framework-dependent work where practical.
- `IMMEDIATE_REVIEW` — surface promptly and route underlying security/data/verification evidence through its normal blocking governance.

A learning trigger never authorizes Framework self-modification and does not replace the task terminal state.

## Stage 13 — Exit

Return one of:
- `COMPLETE_VERIFIED`
- `COMPLETE_WITH_EXPLICIT_DEFERRED_ITEMS`
- `BLOCKED_APPROVAL`
- `BLOCKED_SECURITY`
- `BLOCKED_DATA_RISK`
- `BLOCKED_VERIFICATION`
- `NEEDS_DISCOVERY`

A generic `DONE` is not an accepted terminal state for material workflows.

## Required router record for L2+

```text
Change class:
Affected layers:
Risk level:
Selected workflow:
Roles:
Skills:
Approval required:
Key invariants:
Evidence plan:
Review plan:
Framework feedback: none | captured <feedback-id(s)>
Task learning event: <task-id>
Learning epoch: <epoch-id>
Learning trigger: <level + reasons>
Exit state:
```

## Rationalizations to reject

- "It is a small code change, so impact analysis is unnecessary."
- "The UI prevents it, so backend authorization is unnecessary."
- "The code looks clean, so verification can be skipped."
- "The deadline is urgent, so the risk level can be lowered."
- "The refactor is cleaner, so migration risk does not matter."
- "The same agent wrote it and understands it best, so independent review adds no value."
- "Only failures are useful learning data, so successful tasks do not need capture."
- "The learning trigger fired, so we can edit the Framework directly."
