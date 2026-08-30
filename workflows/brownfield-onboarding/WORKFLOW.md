# Brownfield Onboarding Workflow

**Type:** Engineering workflow  
**Status:** Draft V1

## Objective

Establish a trustworthy engineering baseline for an existing, unfamiliar, or partially documented codebase before material modification.

The workflow answers:
- What actually exists?
- How is it built, tested, deployed, and operated?
- What conventions and boundaries matter?
- What is currently healthy/broken?
- Which documentation is trustworthy or stale?
- What must not be changed blindly?

## Entry conditions

Use when:
- adopting an existing project under EREI Engineering Framework,
- resuming a project whose current state is not sufficiently known,
- project documentation and code may have diverged,
- major changes are requested before a reliable baseline exists.

## Default risk

The onboarding workflow itself is normally L1/L2 read-oriented. Discovery of material auth/data/production uncertainty may raise subsequent work to L3/L4.

## Required roles
- Chief Engineer for material onboarding/routing.
- System Architect for architecture map on non-trivial systems.
- QA perspective for executable baseline when tests exist.

## Conditional roles
- Security Engineer when auth/trust/secrets/tenant boundaries exist.
- Data Engineer when persistent data or migrations exist.
- Performance Engineer when current performance is a material requirement or known issue.
- Release Engineer when deployment/production state is material.

## Required skills
- `project-standard-discovery`
- `impact-analysis` for requested material change after baseline discovery.

## Inputs

Use available:
- repository/files,
- README/AGENTS/ADRs/docs,
- dependency manifests,
- build/test/lint configs,
- CI/CD definitions,
- deployment/config files,
- schema/migration files,
- existing issues/incidents when relevant,
- runtime evidence if accessible.

## Stage 1 — Preserve current state

Before edits:
- identify current branch/version/commit where possible,
- identify uncommitted or generated state where relevant,
- do not mutate project files just to understand them,
- establish a rollback/reference point for any later change.

## Stage 2 — Instruction and documentation discovery

Read the project-local instruction hierarchy and architecture artifacts.

Classify documentation as:
- current/confirmed,
- plausible but unverified,
- stale/conflicting,
- unknown.

## Stage 3 — Architecture map

Identify:
- application entry points,
- frontend/backend/service boundaries,
- domain/business modules,
- persistence/data layer,
- auth/authz boundaries,
- integrations,
- asynchronous/background work,
- caching/state layers,
- deployment/runtime boundary.

Do not require exhaustive documentation; map what matters for safe change.

## Stage 4 — Dependency and platform map

Record:
- languages/runtimes,
- frameworks,
- package/dependency managers,
- external services,
- platform-specific constraints,
- pinned vs floating versions where material.

Unknown or obsolete critical dependencies become explicit risks, not automatic rewrite triggers.

## Stage 5 — Data and security baseline

When applicable, establish:
- source(s) of truth,
- primary keys/identities,
- migrations/schema versioning,
- ownership/tenant boundaries,
- authentication source,
- authorization enforcement location,
- secret/config handling,
- destructive/high-impact operations.

If cross-tenant or data-integrity behavior cannot be established, flag it as a material unknown.

## Stage 6 — Build/test/lint baseline

Determine the supported commands and, where execution is available, establish baseline status before changes.

Record independently:
- build result,
- tests result,
- lint/static checks,
- known pre-existing failures.

Do not attribute pre-existing failures to future changes without evidence.

## Stage 7 — Runtime and performance baseline

If material and accessible:
- verify application start/health,
- capture major latency/performance baseline,
- identify quotas/timeouts/concurrency constraints,
- identify observability/logging entry points.

## Stage 8 — Standard discovery

Run `project-standard-discovery` and produce routable standards rather than a giant global prompt.

## Stage 9 — Risk register

Record:
- architectural unknowns,
- security unknowns,
- data risks,
- test gaps,
- deployment gaps,
- performance risks,
- stale/conflicting documentation,
- fragile/high-coupling areas.

Rank by impact and confidence.

## Stage 10 — Durable onboarding artifacts

Create/update only useful artifacts, commonly:

```text
AGENTS.md
.erei/PROJECT_PROFILE.md
.erei/ARCHITECTURE.md
.erei/SECURITY_MODEL.md
.erei/DATA_MODEL.md
.erei/PERFORMANCE_BUDGET.md
standards/
adr/
runbooks/
```

For an existing project, artifacts should describe observed truth, not idealized architecture.

## Stage 11 — Requested-change impact analysis

If onboarding was triggered by a specific change request, run `impact-analysis` against the newly established baseline.

## Stage 12 — Convergence

Verify that the durable onboarding artifacts match inspected evidence. List unresolved contradictions explicitly.

## Required output

```text
Baseline reference:
Project maturity:
Architecture map:
Instruction/doc sources:
Stack/dependencies:
Build baseline:
Test baseline:
Lint/static baseline:
Runtime baseline:
Data model/source of truth:
Auth/authz/tenant baseline:
Deployment baseline:
Critical invariants:
Project standards discovered:
Known pre-existing failures:
Material unknowns:
Risk register:
Artifacts created/updated:
Recommended next workflow:
```

## Stop / block conditions

Return `NEEDS_DISCOVERY` or block material modification when:
- repository/current state cannot be established sufficiently,
- a requested change depends on unknown auth/data boundaries,
- project truth is contradictory and the conflict materially changes implementation,
- no safe verification path can be defined for the requested high-risk change.

## Rationalizations to reject

- "The README is probably current."
- "Tests fail already, so testing is useless."
- "This looks like a standard framework layout, so we know the architecture."
- "We should refactor the whole codebase before understanding it."
- "Old code is ugly, therefore it is wrong."
- "The requested change is small, so onboarding is unnecessary even though the affected system is unknown."

## Definition of Done

Onboarding is complete when current project behavior, structure, constraints, baseline verification, critical boundaries, local standards, risks, and unknowns are durable enough to support a safe next workflow without pretending the codebase is better understood than the evidence allows.