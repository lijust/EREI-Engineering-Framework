---
name: threat-model
description: Build an evidence-labeled threat model for a system or material change by identifying assets, actors, trust boundaries, data/control flows, abuse paths, controls, residual risk, and verification needs. Use for L3/L4 security-sensitive architecture, authentication/authorization/tenant changes, sensitive integrations, or when the security boundary is not obvious.
---

# Threat Model

## Objective

Understand how the system can be abused or fail across trust boundaries before relying on security controls.

## Trigger when
- authentication or authorization changes,
- tenant isolation changes,
- new privileged/admin operation is introduced,
- sensitive data flow/storage/export changes,
- new external service receives sensitive/control data,
- destructive/high-value operation changes,
- architecture creates a new trust boundary,
- Security Engineer or Router classifies security impact L3/L4.

## Do not trigger full model when
- isolated L0/L1 change has no material security boundary impact,
- an existing current threat model fully covers the unchanged boundary; update only affected paths.

## Required inputs
- architecture/data-flow evidence,
- actors/roles/tenants,
- assets and data sensitivity,
- identity/authz model,
- affected components/services,
- existing security controls,
- deployment/integration boundaries,
- existing threat model/ADRs if any.

## Procedure

### 1. Define scope and evidence confidence
For material claims label basis as:
- `CODE_CONFIRMED`,
- `DOC_CONFIRMED`,
- `TEST_CONFIRMED`,
- `TOOL/RUNTIME_CONFIRMED`,
- `USER_CONFIRMED`,
- `INFERRED`,
- `UNKNOWN`.

### 2. Identify assets
Examples:
- identities/sessions,
- tenant data,
- customer records,
- payments/financial state,
- secrets/tokens,
- administrative authority,
- audit evidence,
- deployment/configuration authority.

### 3. Identify actors and abuse sources
Include:
- normal user,
- user from another tenant,
- privileged/admin user,
- compromised account/client,
- unauthenticated external actor,
- third-party integration,
- accidental/stale/duplicate client behavior,
- insider/service misconfiguration when relevant.

### 4. Map trust boundaries and flows
For each important flow record:
- source,
- destination,
- data/control crossing,
- identity context,
- authorization decision point,
- validation point,
- storage/logging side effects.

### 5. Enumerate threats by boundary
Ask concrete questions:
- Can identity be spoofed or stale?
- Can privilege/tenant scope be selected by untrusted input?
- Can a request be replayed/duplicated/reordered?
- Can data be read/modified outside intended scope?
- Can sensitive data leak through logs/errors/exports/cache?
- Can availability/resource quotas be abused?
- Can dependencies/integrations expand privilege or data exposure?
- Can privileged/destructive operations occur without sufficient checks?

Use structured threat taxonomies only as prompts; do not generate generic lists disconnected from the architecture.

### 6. Map controls
For each credible threat identify existing/proposed controls and where enforcement occurs.

Distinguish:
- preventive,
- detective,
- recovery/containment controls.

### 7. Evaluate residual risk
Classify likelihood/feasibility and impact proportionally. Avoid fake precision.

### 8. Define verification
Every material mitigation should have a verification method where practical:
- authorization tests,
- cross-tenant negative tests,
- replay/idempotency tests,
- schema/validation checks,
- runtime/config inspection,
- dependency/config checks,
- audit/log review.

### 9. Produce decisions and open risks
Threats must end in one of:
- mitigated/verified,
- mitigation planned,
- accepted with authorized rationale,
- transferred by external guarantee with evidence,
- unresolved/blocking.

## Required output

```text
Scope:
Evidence confidence/unknowns:
Assets:
Actors/abuse sources:
Trust boundaries:
Important flows:
Threats:
Existing controls:
Proposed mitigations:
Verification plan:
Residual risks:
Blocking risks:
Required ADR/security decisions:
```

## Rationalizations to reject
- "Authenticated users are trusted users."
- "The frontend already validates this."
- "Nobody would guess this endpoint."
- "Tenant IDs are random, so isolation is fine."
- "The provider handles security."
- "We have HTTPS, so the data flow is secure."
- "There is a permission check somewhere in the app."
- "A generic OWASP checklist is the threat model."

## Definition of Done

Material assets, actors, boundaries, flows, credible threats, controls, residual risk, evidence uncertainty, and verification requirements are explicit enough for architecture/security review and release gating.