# Security Review Skill Specification

**Status:** Draft V1

## Purpose

Verify that implemented controls enforce the security model and threat mitigations across real code/config/runtime boundaries.

## Scope
- authorization/tenant enforcement,
- identity trust,
- object ownership/scope,
- sensitive data paths,
- cache/log/export/background-job isolation,
- privileged/destructive operations,
- failure behavior,
- material integration/dependency security,
- targeted negative verification.

## Non-scope
- generic checklist-only auditing,
- redefining product permissions,
- replacing threat modeling,
- claiming exhaustive absence of vulnerabilities,
- unrelated code quality review.

## Design rationale

Security design and security implementation are separate questions. A control described in documentation, a UI restriction, or a successful allowed-path test is insufficient to prove enforcement.

## Failure modes
- checking authentication but not authorization,
- ignoring indirect data paths such as cache/export/logging,
- failing to test denied paths,
- trusting client-controlled scope,
- treating scanner output as final judgment,
- severity inflation without exploit/failure path,
- accepting material residual risk without authority.

## Evaluation strategy
Test direct endpoint bypass, wrong-tenant/object negative paths, client manipulation, cache leakage, fail-open behavior, and threat-to-control traceability.

## Independence
For L3/L4 changes, independent security review context is expected where practical.

## Portability
Technology-neutral; overlays provide platform-specific secure implementation references/checks.