# New Project Workflow

**Type:** Project bootstrap workflow  
**Status:** Draft V1

## Objective

Bootstrap a new software project under EREI Engineering Framework with enough durable context, architecture discipline, security/data awareness, and project-local source of truth to begin implementation safely without overdesigning the project.

## Entry conditions
- new project or product is being established,
- no reliable project engineering baseline exists,
- Router selects `new-project`.

## Default roles
- Chief Engineer
- System Architect once discovery is sufficient for architecture decisions

## Conditional roles
Activate according to discovery/impact:
- Security Engineer
- Data Engineer
- Frontend Engineer
- Backend Engineer
- Performance Engineer
- QA Engineer
- Release Engineer

## Required skill
- `project-discovery`

## Conditional skills
- `impact-analysis`
- `threat-model`
- architecture design (when available)
- dependency review (when available)
- test design (when available)

## Stage 1 — Discovery

Run `project-discovery` to establish:
- purpose/boundary,
- users/roles/tenant model,
- critical workflows,
- data and sensitivity,
- security assumptions,
- technology/deployment constraints,
- non-functional requirements,
- material unknowns.

Do not force architecture decisions before blocking discovery is resolved.

## Stage 2 — Project-local source of truth

Create/update only useful durable artifacts, typically:

```text
AGENTS.md
.erei/PROJECT_PROFILE.md
.erei/ARCHITECTURE.md
.erei/SECURITY_MODEL.md
.erei/DATA_MODEL.md
.erei/PERFORMANCE_BUDGET.md
.erei/PROJECT_RULES.md
adr/
standards/
runbooks/
```

Artifact depth must match project maturity.

## Stage 3 — Architecture baseline

Once sufficient inputs exist:
- select the simplest architecture that meets known requirements,
- separate required technology from preference,
- define major boundaries/contracts,
- define persistence/data approach,
- define identity/authz model when applicable,
- define deployment/runtime baseline,
- identify likely migration/evolution boundaries.

Material architecture/security/data decisions are approval-gated under the Risk Contract.

## Stage 4 — Security/data baseline

If the project has users, sensitive data, tenants, privileged actions, or external integrations:
- establish trust boundaries,
- establish server-side authorization authority,
- establish tenant/data ownership rules,
- run threat modeling when L3 security boundary decisions are introduced.

## Stage 5 — Engineering standards baseline

Define only standards that have immediate value:
- supported runtime/toolchain,
- testing baseline,
- dependency policy,
- formatting/lint/build commands,
- release flow,
- project-specific constraints.

Do not invent a large style guide before code exists unless required.

## Stage 6 — Initial acceptance baseline

Define:
- initial success criteria,
- verification approach,
- performance budgets where material,
- DEV/Candidate/QA/Stable expectations appropriate to project stage.

## Stage 7 — Convergence

Check that durable artifacts agree with approved decisions and that unresolved items are explicit.

## Required output

```text
Discovery status:
Project artifacts:
Architecture decisions:
Security/data decisions:
Approved decisions:
Unresolved/blocking decisions:
Initial standards:
Verification baseline:
Risk register:
Recommended first implementation workflow:
```

## Stop / block conditions
- blocking discovery prevents safe architecture choice,
- security/tenant/data boundary remains materially undefined,
- requested architecture conflicts with Constitution and is not resolved,
- irreversible foundational choice is being made without required approval.

## Rationalizations to reject
- "We should create every framework artifact now."
- "Use the most scalable architecture just in case."
- "Security/data modeling can wait until after features."
- "The user's technology preference means alternatives need no consideration."
- "A new project should start with a major framework/dependency stack by default."

## Definition of Done

The project has a proportional durable engineering baseline, foundational decisions are approved where required, blocking unknowns are resolved or explicit, and the Router can enter the first implementation workflow without relying on transient conversation state.