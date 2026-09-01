# ADR-0004 — Concrete Runtime Implementations Are Outside Framework Core

**Status:** Accepted  
**Date:** 2026-09-02  
**Risk:** L3 — Framework scope / runtime boundary

## Context

EREI Engineering Framework defines engineering governance, roles, skills, workflows, risk, evidence, project integration, evaluation, release rules and optional integration contracts.

During Runtime Adapter Contract validation, an experimental Tutti-specific client was implemented inside the Framework repository. The prototype proved that the provider-neutral Runtime Adapter Contract is implementable, but it also demonstrated that concrete runtime clients have a different change cadence, dependency surface and operational responsibility from Framework Core.

Keeping Tutti-, Codex-, Claude-, OpenCode- or other runtime-specific implementations in the Framework repository would couple Framework releases to external runtime API changes and expand Framework scope without a demonstrated project need.

## Decision

Concrete runtime implementations are outside the scope of `EREI-Engineering-Framework`.

The Framework may contain:

- provider-neutral Runtime Adapter contracts and schemas,
- standardized capability vocabulary,
- generic adapter validation/conformance rules,
- runtime-neutral eval adapter protocol,
- research and architecture assessments of external runtimes when useful.

The Framework must not normally contain:

- runtime/provider-specific HTTP/CLI/SDK clients,
- provider-specific credentials or discovery logic,
- provider-specific adapter manifests intended for enablement,
- provider-specific CI or implementation unit tests,
- provider/session/process lifecycle implementations,
- a mandatory multi-agent host.

A concrete runtime integration should be created only when a real project requirement justifies it and should live outside Framework Core. Repository/package placement may be decided at that time based on actual scope rather than pre-creating an adapter ecosystem.

## Runtime Adapter Contract remains Stable

ADR-0003 and Runtime Adapter Contract V1 remain valid.

They are optional extension points: they define how an external execution environment can interoperate with EREI governance without making runtime integration a required part of normal Framework use.

Projects do not need a Runtime Adapter to use EREI Engineering Framework.

## Tutti

Tutti remains research evidence showing that a provider-neutral runtime/shared-workspace system can sit behind the Runtime Adapter boundary.

Tutti is not part of the Framework roadmap unless a concrete project later demonstrates a need for that integration.

Existing Tutti research may remain under `research/` for provenance and architectural learning. Tutti-specific implementation, manifest, tests and CI are removed from Framework scope.

## Parallel project rule

Projects consume an immutable Stable Framework pin and may continue working while Framework development proceeds independently.

Candidate Framework work does not become project truth until it is promoted Stable and the project explicitly upgrades its pin through the Framework Upgrade Workflow.

## Consequences

### Benefits

- keeps Framework Core focused and technology/runtime neutral,
- avoids coupling Framework releases to external runtime churn,
- reduces trusted computing base and maintenance burden,
- preserves optional future integration through the generic contract,
- avoids building infrastructure before a real project requires it.

### Costs

- a future runtime integration will require a separate implementation decision,
- provider-specific conformance cannot be performed inside Framework Core alone.

## Rejected alternatives

### Keep all concrete adapters in Framework

Rejected because external runtime changes would drive Framework churn and blur responsibility boundaries.

### Create `EREI-Runtime-Adapters` immediately

Rejected for now. No current project requirement justifies a separate adapter product/repository. Create one only if real usage evidence requires it.

### Remove Runtime Adapter Contract entirely

Rejected. The generic optional boundary is small, provider-neutral and already validated as useful architecture.

## Approval record

The user explicitly approved this scope correction on 2026-09-02 after clarifying that the overlap between Tutti and EREI Engineering Framework is intentionally small.
