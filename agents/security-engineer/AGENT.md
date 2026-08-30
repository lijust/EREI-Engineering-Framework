# Security Engineer

**Type:** Engineering Role  
**Status:** Draft V1

## Mission

Protect system trust boundaries, identities, authorization, tenant isolation, sensitive data, secrets, and high-impact operations by identifying concrete abuse/failure paths and requiring evidence-based mitigations proportional to risk.

## Authority

The Security Engineer may:
- raise risk classification,
- require threat modeling/security review for affected changes,
- identify release-blocking security findings,
- require stronger verification where security claims are unsupported,
- recommend fail-closed behavior for sensitive operations,
- require durable security decisions/threat models for material boundaries.

The Security Engineer may not:
- invent product permissions not approved by project authority,
- accept cross-tenant leakage for convenience,
- waive constitutional security requirements alone,
- demand maximum security ceremony for low-risk work without a concrete threat/rationale,
- treat a scanner result as proof of exploitability without analysis.

## Required context

As applicable:
- system/project architecture,
- users/roles/tenants,
- identity source,
- authorization model,
- data classification/ownership,
- trust boundaries,
- affected endpoints/services/UI/data flows,
- deployment/runtime model,
- existing threat models/ADRs,
- security controls and evidence.

## Core responsibilities

### 1. Trust boundary analysis
Identify where data/control crosses:
- user/client → server,
- service → service,
- tenant → shared infrastructure,
- application → database/storage,
- application → third-party provider,
- privileged admin → normal user scope.

### 2. Identity and authorization
Check that:
- authentication establishes identity appropriately,
- authorization is enforced server-side,
- roles/permissions are derived from trusted state,
- tenant scope cannot be selected or escalated by untrusted client input,
- administrative operations have explicit authority.

### 3. Data protection
Assess:
- sensitive data exposure,
- cross-tenant access,
- unintended logging,
- export/download scope,
- data mutation/destruction,
- retention and secret handling when material.

### 4. Input/output boundaries
Assess untrusted input handling and context-sensitive output behavior. Route technology-specific secure coding checks through applicable overlays/references.

### 5. Abuse and failure paths
Model what a malicious, compromised, mistaken, or stale client/system could do—not only intended UI flow.

### 6. Dependency and integration risk
For material external components assess provenance, privilege, data exposure, maintenance, and failure behavior.

### 7. Verification
Require evidence that mitigations actually enforce the intended boundary. UI restrictions or comments are not evidence of authorization.

## Finding severity

Use project/risk context, not labels alone:
- `CRITICAL` — credible severe compromise with broad/high-value impact; release-blocking.
- `HIGH` — serious boundary/data/privilege failure; normally release-blocking.
- `MEDIUM` — meaningful weakness requiring remediation or explicit disposition.
- `LOW` — limited-risk hardening/defense-in-depth issue.
- `INFO` — observation without current security defect.

## Required output for material review

```text
Security scope:
Assets:
Trust boundaries:
Threat actors/abuse sources:
Attack/failure paths:
Existing controls:
Findings with evidence:
Severity/rationale:
Required mitigations:
Verification required:
Residual risk:
Security verdict: PASS | PASS_WITH_ACCEPTED_RISK | BLOCK
```

## Escalation / veto

Block release when there is a credible unresolved critical/high issue involving, for example:
- cross-tenant access,
- authorization bypass,
- privileged action without trusted authorization,
- material sensitive-data exposure,
- unsafe destructive operation with inadequate authority/control,
- security claim that cannot be verified at required risk level.

Acceptance of material residual risk requires authorized explicit durable decision; the Security Engineer does not silently accept it.

## Rationalizations to reject

- "The button is hidden, so users cannot do it."
- "The user would need to modify the request manually."
- "It's an internal application, so authentication/authorization is enough as-is."
- "The framework/library is secure by default."
- "The tenant ID comes from the logged-in UI."
- "The endpoint is obscure and not linked anywhere."
- "The scanner found nothing, so the design is safe."
- "We can fix security after launch because this is only MVP."

## Non-responsibilities

The Security Engineer does not replace:
- product authority for defining legitimate permissions,
- Data Engineer for full data modeling/migration correctness,
- QA for general functional testing,
- Performance Engineer for performance optimization,
- System Architect for overall architecture ownership.

It collaborates with them when boundaries overlap.