# Security-Critical Change Workflow

**Type:** High-risk engineering workflow  
**Status:** Draft V1

## Objective

Safely design, implement, review, verify, and release changes that affect authentication, authorization, tenant isolation, sensitive data, privileged operations, or material trust boundaries.

## Entry conditions

Use when impact analysis identifies L3/L4 security impact, including:
- authentication changes,
- authorization/role changes,
- tenant-boundary changes,
- new privileged/admin actions,
- sensitive-data flow/storage/export changes,
- material external trust boundary,
- destructive/high-value operation authority changes.

## Required roles
- Chief Engineer
- Security Engineer
- System Architect for boundary/architecture changes
- relevant implementation role(s)
- QA/review perspective

## Conditional roles
- Data Engineer for persistent/sensitive data or ownership changes
- Release Engineer for production state/deployment
- Performance Engineer when security control affects critical latency/scale

## Required skills
- `impact-analysis`
- `threat-model`
- `requirement-compliance-review`
- `engineering-quality-review`
- `security-review`
- `verification-before-completion`

## Stage 1 — Impact and risk

Establish affected layers, assets, tenant/user blast radius, data impact, rollback difficulty, and risk classification.

L3/L4 structural security decisions require explicit approval before implementation.

## Stage 2 — Security requirements and threat model

Create/update:
- security invariants,
- trust boundaries,
- threat model,
- control design,
- verification plan,
- residual/open risks.

Do not begin structural implementation while a blocking security requirement remains undefined.

## Stage 3 — Architecture/decision gate

For material changes record durable decision/ADR as appropriate:
- identity source,
- authorization authority/enforcement location,
- tenant resolution/isolation strategy,
- data/control flow,
- external trust assumptions,
- fail-open/fail-closed behavior,
- rollback/compatibility strategy.

Explicit approval is required for the structural decision.

## Stage 4 — Implementation

Implement the approved design using applicable project standards/technology overlays.

During implementation:
- do not move authorization to client/UI,
- do not broaden tenant scope for convenience,
- validate trusted identity/scope server-side,
- preserve backward/data compatibility where required,
- make security-sensitive failures observable without exposing sensitive information.

## Stage 5 — Requirement compliance review

Confirm the implementation matches approved security behavior and product permissions without unauthorized scope changes.

## Stage 6 — Engineering quality review

Review correctness, concurrency/state, failure behavior, project standards, complexity, and testability.

## Stage 7 — Independent security review

Run `security-review` in independent/fresh context where practical.

Trace threat mitigations to actual enforcement and negative-path verification.

Unresolved CRITICAL/HIGH findings return the workflow to implementation or `BLOCKED_SECURITY`.

## Stage 8 — Fresh verification

After latest security fixes, run current verification appropriate to risk, including denied/negative cases and applicable runtime/config checks.

For tenant/auth changes, verification should cover unauthorized scopes, not only allowed paths.

## Stage 9 — Convergence

Compare:
- approved requirement/ADR,
- threat model,
- implementation,
- security findings,
- verification evidence,
- residual risks.

Every material risk becomes:
- mitigated/verified,
- accepted by authorized decision with rationale,
- explicitly deferred if non-blocking and policy permits,
- blocking.

## Stage 10 — Release gate

Release recommendation requires:
- requirement compliance PASS,
- engineering review without unresolved blockers,
- security verdict PASS or authorized documented residual-risk acceptance,
- fresh verification evidence,
- rollback strategy for stateful/production-impacting change where applicable.

## Terminal states
- `COMPLETE_VERIFIED`
- `COMPLETE_WITH_EXPLICIT_DEFERRED_ITEMS`
- `BLOCKED_APPROVAL`
- `BLOCKED_SECURITY`
- `BLOCKED_DATA_RISK`
- `BLOCKED_VERIFICATION`

## Rationalizations to reject
- "This is only MVP."
- "The endpoint is internal."
- "The UI already limits the role."
- "Security review can happen after launch."
- "The allowed-path tests pass."
- "The fix is tiny, so the threat model does not need updating."
- "We cannot roll back, but the migration should be fine."

## Definition of Done

The approved security design is implemented, threat-to-control mapping is current, independent review and negative verification are complete at the required risk level, residual risks are durably dispositioned, and the release gate has a truthful terminal state.