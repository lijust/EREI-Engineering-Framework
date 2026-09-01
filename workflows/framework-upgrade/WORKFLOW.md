# Framework Upgrade Workflow

**Status:** Candidate V1

## Objective

Upgrade an integrated project's pinned EREI Engineering Framework revision without silently changing engineering governance, project truth, security posture, release behavior, or runtime assumptions.

A Framework upgrade is a controlled dependency/governance change, not a blind edit to `.erei/framework.json`.

## Entry conditions

Use this workflow when a project already contains a valid `.erei/framework.json` and intends to move from one Framework baseline/ref to another.

Do not use this workflow to bootstrap a project that has no Framework integration; use `project-integration-bootstrap` instead.

## Risk applicability

Default: **L2**.

Raise to **L3** when the target revision changes or may change any of the following:

- Engineering Constitution,
- risk/evidence/agent/skill/workflow contracts,
- project integration manifest schema,
- security authority or veto behavior,
- release/promotion rules,
- data-governance boundaries,
- required runtime trust boundaries,
- a project's enabled technology overlay in a way that changes security/data/release behavior.

Raise to **L4** only when the project-specific upgrade path includes destructive/irreversible production actions.

## Required roles

- Chief Engineer
- System Architect
- QA Engineer
- Release Engineer

## Conditional roles

- Security Engineer — when security/governance/trust-boundary content changed or security-sensitive overlays are affected.
- Data Engineer — when data contracts, migrations, persistence semantics, or data-oriented overlays are affected.
- Performance Engineer — when performance contracts/overlays relevant to the project changed.
- Frontend/Backend engineers — when project verification requires implementation changes caused by Framework compatibility drift.

## Required skills

- impact-analysis
- regression-analysis
- verification-before-completion

## Conditional skills

- security-review
- threat-model
- requirement-compliance-review
- engineering-quality-review

## Inputs

Required:

1. project `.erei/framework.json`,
2. current pinned Framework immutable ref,
3. target Framework immutable ref,
4. current and target Framework baseline metadata or equivalent exact revision diff,
5. project `.erei/` context,
6. project release/test rules.

Target Candidate/Stable project state must not depend only on a mutable branch name.

## Compatibility classes

### `NO_GOVERNANCE_CHANGE`

The target does not alter Constitution, contracts, integration schema, approval/security/release authority, or project-relevant overlay semantics.

Normal L2 verification may be sufficient.

### `PROJECT_REVIEW_REQUIRED`

The target changes skills/workflows/overlays or other behavior that may affect how this project is engineered, but does not alter a protected governance boundary.

Project-specific impact and regression review are required.

### `ARCHITECTURE_APPROVAL_REQUIRED`

The target changes a protected governance boundary listed in the L3 section above.

Explicit architecture approval is required before the project pin is promoted.

### `BLOCKED`

Use when any required evidence is missing, the target ref is mutable for a Candidate/Stable state, the target Framework state is not acceptable for the requested project state, or compatibility cannot be established safely.

## Stages

### 1. Read current project integration

Read:

- `.erei/framework.json`,
- applicable `.erei/*` context,
- `AGENTS.md`,
- project ADR/release/test rules.

Record the current pin exactly. This is the rollback pin.

### 2. Resolve exact target Framework state

Confirm:

- repository identity,
- target baseline name,
- target immutable commit/tag,
- target status,
- required overlays/adapters exist at that exact ref.

Do not infer Stable from a branch name.

### 3. Compare Framework revisions

Compare current → target and classify changes at minimum across:

- Constitution,
- schemas/contracts,
- roles,
- workflows,
- skills,
- project-integration schema/tooling,
- enabled project overlays,
- eval/evidence rules,
- runtime adapter contracts,
- release/governance metadata.

Unrelated new Framework assets do not automatically imply project impact; route context by relevance.

### 4. Classify compatibility and risk

Assign one compatibility class and Framework-upgrade risk.

If evidence is incomplete, classify `BLOCKED` rather than guessing compatibility.

### 5. Project impact analysis

Map changed Framework capabilities to the project's:

- architecture,
- security boundaries,
- data model,
- performance budget,
- current workstream,
- release/rollback process,
- enabled overlays/adapters.

Record what is unaffected as well as what is affected.

### 6. Approval gate

Explicit approval is mandatory for `ARCHITECTURE_APPROVAL_REQUIRED` and any L3/L4 project impact.

No approval is implied by the existence of a newer Framework baseline.

### 7. Update candidate pin

Change only the intended project integration state first:

- target baseline,
- immutable target ref,
- overlays/adapters only when separately justified.

Do not bundle unrelated project implementation changes into the pin update unless compatibility requires them and the change plan makes that explicit.

### 8. Integration validation

Verify:

- manifest schema,
- referenced project context files exist,
- target Framework ref exists,
- enabled overlays/adapters exist at target ref,
- no project truth was overwritten,
- no secret/runtime identifier was introduced.

### 9. Project regression/verification

Run the project's applicable source/static/eval/runtime tests according to project risk.

A Framework upgrade cannot claim success solely because the manifest parses.

### 10. Convergence

Compare intended vs actual state:

- exact target pin,
- compatibility assumptions,
- required project rules,
- required specialist gates,
- verification evidence,
- unchanged protected invariants.

Any material drift blocks promotion.

### 11. Promote or rollback

Promote only after required evidence/gates pass.

Rollback is primarily restoration of the prior known-good Framework pin plus reversal of any compatibility implementation changes introduced solely for the upgrade.

Project runtime/deployment rollback remains governed by the project's own release model.

## Gates

- Immutable-target gate
- Framework-status gate
- Compatibility classification gate
- L3/L4 approval gate
- Security/data specialist gates when triggered
- Project verification gate
- Convergence gate
- Release/promotion gate

## Durable artifacts

For material upgrades preserve:

- old pin,
- target pin,
- Framework diff/compatibility classification,
- project impact report,
- approval record when required,
- verification evidence,
- rollback instructions.

An ADR is required when the upgrade adopts a new governance/security/data/architecture boundary for the project.

## Stop/block conditions

Stop when:

- current or target ref cannot be resolved exactly,
- Candidate/Stable target uses only a mutable branch,
- target Framework status is incompatible with requested project state,
- required Framework/project evidence is missing,
- protected governance changes lack approval,
- security/data veto is active,
- project regression evidence fails,
- convergence finds unexplained drift.

## Rollback / exit behavior

The pre-upgrade `.erei/framework.json` pin is mandatory rollback evidence.

Do not delete or rewrite history to hide a failed upgrade attempt.

## Definition of Done

A Framework upgrade is complete only when:

- target Framework revision is exact and reproducible,
- compatibility/risk classification is recorded,
- required approvals are recorded,
- project manifest/context remains valid,
- project-relevant regressions are verified,
- protected project invariants remain intact,
- convergence passes,
- old pin and rollback path remain recoverable.
