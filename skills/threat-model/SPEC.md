# Threat Model Skill Specification

**Status:** Draft V1

## Purpose

Create architecture-specific security reasoning before controls are accepted as sufficient.

## Scope
- assets,
- actors/abuse sources,
- trust boundaries,
- important data/control flows,
- credible threats,
- existing/proposed controls,
- residual risk,
- verification requirements,
- evidence confidence.

## Non-scope
- generic vulnerability scanning,
- code-level secure coding review of every file,
- penetration testing,
- product permission definition,
- precise numeric risk scoring without evidence.

## Design rationale

Security checklists often miss where a system actually trusts data/identity/control. The model must be tied to real architecture and explicitly distinguish confirmed facts from inferred assumptions.

## Failure modes
- generic threat list unrelated to actual flow,
- missing cross-tenant actor,
- treating authenticated user as trusted,
- ignoring stale/replay/duplicate system behavior,
- assuming third-party guarantees without evidence,
- failing to map mitigation to verification,
- presenting inferred architecture as confirmed.

## Evaluation strategy
Test tenant isolation, client-controlled identity/scope, third-party boundaries, replay/idempotency, sensitive logging/export, and evidence-labeling behavior.

## Maintenance
Update when trust boundaries, data flows, identity model, integrations, or high-impact operations materially change.

## Portability
Technology-neutral. Overlay references may add platform-specific threats and controls.