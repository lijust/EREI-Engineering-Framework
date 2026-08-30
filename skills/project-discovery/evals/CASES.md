# Project Discovery Evals

**Status:** Draft V1

## T-001 — New multi-tenant SaaS
Prompt: "Build a CRM for brokerage companies where each company has brokers and managers."

Expected:
- Trigger discovery.
- Ask/resolve tenant, role, auth, data ownership, deployment, scale, critical workflows.
- Mark unknowns instead of assuming.
- Produce project artifact plan.

## T-002 — Existing mature project with durable profile
Prompt: "Change the button label in the documented production app."

Expected:
- Do not run full project discovery.
- Route as local low-risk change.

## T-003 — Stack suggestion vs requirement
Prompt: "I think React might be good; build an internal dashboard."

Expected:
- Record React as preference/proposal, not confirmed architectural requirement.
- Discover actual constraints before locking the stack.

## T-004 — Security deferred rationalization
Prompt: "We will figure out permissions after MVP. For now everyone can query the same database."

Expected:
- Surface security/tenant boundary as material.
- Refuse to silently defer if multi-user sensitive data architecture depends on it.
- Mark as blocking or require explicit safe architecture decision.

## T-005 — Reuse prior confirmed context
Scenario: Current project artifacts already confirm user roles, one-tenant-per-user, Google identity, and performance budgets.

Expected:
- Reuse evidence.
- Do not ask the user to repeat these facts.
- Focus only on unresolved decisions.

## B-001 — Artifact proportionality
Scenario: Small single-user utility with no remote data, no auth, and one deploy target.

Expected:
- Do not create empty SECURITY_MODEL/DATA_MODEL/runbooks just because templates exist.
- Create only useful durable context.

## B-002 — Inference labeling
Scenario: User says "companies will subscribe" but does not define whether users can belong to multiple companies.

Expected:
- Do not infer tenant membership cardinality.
- Mark unknown if material.

## B-003 — Framework contamination
Scenario: Project chooses Google Apps Script.

Expected:
- Record in project context/overlay selection.
- Do not promote Apps Script as a Framework Core requirement.