---
name: project-discovery
description: Establish the durable engineering context for a new or insufficiently defined software project before architecture or implementation begins. Use when starting a new project, when project goals/constraints/users/data/security/deployment are not yet captured, or when the Router cannot safely choose architecture because project truth is incomplete.
---

# Project Discovery

## Objective

Convert an initial project idea into a durable engineering context that is sufficient for architecture, risk analysis, and future implementation without repeatedly relying on chat history.

## Trigger when

Use when:
- starting a new software project,
- a project exists conceptually but lacks durable engineering definition,
- major user/tenant/security/data/deployment assumptions are unresolved,
- the user asks to bootstrap a project under EREI Engineering Framework,
- the Workflow Router returns `NEEDS_DISCOVERY` because project truth is insufficient.

## Do not trigger when

- the project already has a current, sufficient project profile and the task is a local implementation change,
- the problem is specifically understanding an unfamiliar existing codebase; use brownfield onboarding instead,
- the request is only exploratory discussion with no intent to establish project engineering state.

## Required inputs

Collect or infer from authoritative evidence where possible:
- project purpose,
- primary users/actors,
- success criteria,
- business-critical workflows,
- current or intended stack,
- data classes and ownership,
- identity/authentication model,
- authorization/tenant model,
- integrations,
- deployment/runtime model,
- performance expectations,
- compliance/security expectations,
- operational constraints,
- explicit user preferences and non-negotiables.

Do not ask for information already established in project evidence or current conversation.

## Procedure

### 1. Define the product boundary
Record:
- what the system is,
- what it is not,
- primary outcomes,
- current phase (prototype, MVP, production, migration, etc.).

### 2. Identify actors and authority
For each actor identify:
- identity source,
- tenant/company relationship if applicable,
- role,
- data visibility,
- actions allowed,
- actions requiring elevated authority.

### 3. Identify critical workflows
Capture the user/system flows where failure would materially affect:
- revenue,
- security,
- data integrity,
- customer trust,
- operations.

### 4. Map data
Identify:
- primary entities,
- ownership,
- sensitivity,
- retention needs,
- source of truth,
- cross-entity relationships,
- import/export requirements,
- migration constraints if known.

### 5. Establish non-functional requirements
Capture known expectations for:
- performance,
- scale,
- availability,
- observability,
- backup/recovery,
- accessibility,
- localization,
- browser/device/platform support.

### 6. Establish security model
At minimum capture:
- authentication source,
- authorization authority,
- trust boundaries,
- tenant boundaries,
- administrative authority,
- sensitive data/secrets,
- critical abuse cases.

If these are unresolved and materially affect architecture, mark them explicitly rather than inventing defaults.

### 7. Establish technology and deployment constraints
Separate:
- explicitly required technologies,
- current preferences,
- justified architecture decisions,
- undecided choices.

Do not turn preferences into permanent architecture rules without rationale.

### 8. Identify risks and unknowns
Classify important unknowns as:
- architecture-blocking,
- security-blocking,
- data-blocking,
- implementation-deferable,
- product-deferable.

### 9. Create durable project artifacts
The target project should receive, as applicable:

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

Only create artifacts that are justified at the current maturity level; avoid empty bureaucracy.

### 10. Produce initial architecture questions/decisions
For each material decision:
- confirmed decision,
- current rationale,
- alternatives considered when material,
- status: accepted / proposed / unresolved,
- whether ADR is required.

### 11. Hand off to Router
Return enough context for the Router to choose:
- architecture design,
- feature development,
- security work,
- data modeling,
- brownfield onboarding,
- or further discovery.

## Required output

```text
Project purpose:
Project boundary:
Current maturity:
Primary actors:
Tenant/authorization model:
Critical workflows:
Primary data/entities:
Data sensitivity/ownership:
Authentication:
Integrations:
Runtime/deployment:
Scale/performance expectations:
Security expectations:
Operational constraints:
Technology constraints/preferences:
Confirmed decisions:
Material unknowns:
Blocking unknowns:
Initial risks:
Artifacts created/updated:
Recommended next workflow:
```

## Evidence requirements

- Distinguish user-confirmed decisions from inferred recommendations.
- Existing project files/docs outrank remembered assumptions.
- Material constraints should be persisted in durable artifacts.

## Stop / escalate

Stop architecture commitment when a material unresolved question could change:
- trust boundaries,
- tenant isolation,
- irreversible data model,
- deployment platform viability,
- regulatory/compliance obligations,
- core business invariants.

## Rationalizations to reject

- "We can decide security later."
- "The framework probably knows what the user wants."
- "A README is enough project context for everything."
- "We should choose the most advanced stack by default."
- "Every possible document should be created now."
- "An inferred role model is close enough to a confirmed one."

## Definition of Done

Discovery is complete when the project has enough durable, evidence-labeled context to begin architecture/implementation without re-deriving fundamental users, boundaries, data, security, constraints, and success conditions from conversational memory.