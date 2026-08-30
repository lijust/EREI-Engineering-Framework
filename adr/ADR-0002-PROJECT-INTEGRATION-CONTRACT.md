# ADR-0002 — Project Integration and Framework Pin Contract

**Status:** Accepted  
**Date:** 2026-08-31  
**Risk:** L3 — Cross-project integration contract

## Context

EREI Engineering Framework is now a stable reusable engineering system, but a project needs a durable, provider-neutral way to declare:

- which Framework repository it consumes,
- which immutable Framework revision it is pinned to,
- which project profile/security/data/performance documents define local truth,
- which technology overlays are enabled,
- which runtime adapters may be used.

Relying on chat memory, custom instructions, a branch name such as `main`, or duplicated Framework files inside every project would create drift and weak provenance.

The integration mechanism must remain readable by humans, coding agents, CI, and future adapters without adding a package-manager dependency.

## Decision

Adopt a small project-local integration contract centered on:

`/.erei/framework.json`

### 1. Canonical machine-readable manifest

Each integrated project contains a versioned JSON manifest with:

- manifest schema version,
- Framework repository identity,
- Framework baseline name,
- immutable Framework ref for reproducibility,
- project context document paths,
- enabled overlays,
- optional runtime adapter preferences.

JSON is chosen because it is universally parseable and requires no third-party parser in the Framework bootstrap tooling.

### 2. Immutable pin for stable project state

A project may temporarily track a branch during experimentation, but Candidate/Stable project baselines should pin the Framework by immutable commit SHA or immutable tag.

A mutable branch name alone is not sufficient release evidence.

### 3. Project truth remains in the project repository

The bootstrap creates/standardizes:

```text
AGENTS.md
.erei/
├── framework.json
├── PROJECT_PROFILE.md
├── ARCHITECTURE.md
├── SECURITY_MODEL.md
├── DATA_MODEL.md
├── PERFORMANCE_BUDGET.md
└── PROJECT_RULES.md

adr/
```

These files contain project-specific facts and decisions. They are not copied into Framework Core.

### 4. AGENTS.md is a bootloader, not the knowledge base

The root `AGENTS.md` should be concise and instruct an agent/runtime to:

1. Read `.erei/framework.json`.
2. Load the pinned Framework Constitution and applicable contracts.
3. Read the project profile and scoped local documents.
4. Run project-standard discovery when onboarding brownfield code.
5. Route work through the Chief Engineer/workflow model.
6. Persist durable architectural decisions in the project repository.

### 5. Bootstrap tooling is additive and fail-closed

`tools/bootstrap_project.py` may create the integration skeleton, but:

- it does not overwrite existing project files by default,
- it supports dry-run/inspection,
- it reports conflicts explicitly,
- it writes only inside the target repository,
- it requires an explicit overwrite flag for replacement,
- it does not clone, execute, or install third-party code.

### 6. Framework is referenced, not vendored by default

The default integration model does **not** copy the entire Framework into each project and does not require a Git submodule.

Runtimes/adapters may obtain the pinned Framework content through their available Git/GitHub/local-checkout mechanism.

Vendoring or submodules may be supported later for environments that require offline/local operation, but they are not the canonical V1 model.

## Manifest example

```json
{
  "schema_version": 1,
  "framework": {
    "repository": "lijust/EREI-Engineering-Framework",
    "baseline": "project-integration-bootstrap-v1",
    "ref_type": "commit",
    "ref": "<immutable-commit-sha>"
  },
  "project": {
    "profile": ".erei/PROJECT_PROFILE.md",
    "architecture": ".erei/ARCHITECTURE.md",
    "security_model": ".erei/SECURITY_MODEL.md",
    "data_model": ".erei/DATA_MODEL.md",
    "performance_budget": ".erei/PERFORMANCE_BUDGET.md",
    "rules": ".erei/PROJECT_RULES.md",
    "adr_directory": "adr"
  },
  "overlays": [],
  "runtime_adapters": []
}
```

## Consequences

### Benefits

- reproducible Framework behavior per project,
- explicit provenance,
- provider-neutral integration,
- project facts remain local,
- no package-manager dependency,
- easy CI validation,
- easy upgrade diff from one Framework pin to another.

### Costs

- projects must update their pin deliberately,
- runtime adapters need a way to retrieve the pinned Framework ref,
- bootstrap tooling and manifest schema become maintained Framework artifacts.

## Rejected alternatives

### Custom instructions only
Rejected because they are not durable project source of truth and are difficult to version/review.

### Copy Framework files into every project
Rejected as the default because copies drift and make upgrades/provenance difficult.

### Git submodule as mandatory integration
Rejected as the V1 canonical model because it adds Git operational complexity and is unnecessary for runtimes that can read the Framework repository directly.

### Pin to `main` only
Rejected for Candidate/Stable project baselines because a mutable branch does not reproduce an exact engineering policy state.

### Build a package manager first
Rejected as overengineering. A manifest + adapters are sufficient for V1.

## Approval record

ADR-0002 was explicitly approved on 2026-08-31. Project Integration Bootstrap V1 may be promoted to Framework Stable through the normal release flow.