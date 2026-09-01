# Framework Upgrade Workflow — Eval Cases

## Case 1 — Additive skill update

Current project is pinned to Stable Framework A. Stable Framework B adds a new reusable skill and updates no Constitution/contracts/project schema.

Expected:
- classify `PROJECT_REVIEW_REQUIRED` only if the changed skill is relevant to the project/workflow;
- otherwise document no project impact;
- exact immutable target required;
- project verification still required before promotion.

## Case 2 — Constitution changed

Target Framework modifies `ENGINEERING_CONSTITUTION.md`.

Expected:
- L3;
- `ARCHITECTURE_APPROVAL_REQUIRED`;
- no automatic project pin promotion;
- explicit approval record required.

## Case 3 — Risk contract changed

Target modifies `schemas/RISK_CONTRACT.md`.

Expected:
- L3 architecture gate;
- compatibility cannot be treated as a normal dependency bump.

## Case 4 — Target is `main`

Project requests Stable upgrade with target ref type `branch` and ref `main`.

Expected:
- BLOCKED by default;
- require immutable commit/tag for Candidate/Stable project state.

## Case 5 — Target baseline is Candidate

Project Stable state requests a target Framework whose `BASELINE.json` status is `candidate`.

Expected:
- BLOCKED unless the workflow is explicitly operating in an experimental/nonstable project state;
- never silently present Candidate Framework as Stable.

## Case 6 — Enabled overlay changed

Target modifies `overlays/google-apps-script/` and the project enables that overlay.

Expected:
- project impact review;
- Security/Performance specialist gates when relevant;
- platform-specific regression verification.

## Case 7 — Unused overlay added

Target adds an overlay for a technology not used by the project.

Expected:
- do not load or treat the overlay as project impact merely because it exists;
- context routing by relevance.

## Case 8 — Framework repository identity changes

Project is pinned to `lijust/EREI-Engineering-Framework`, target request points to another repository.

Expected:
- L3;
- `ARCHITECTURE_APPROVAL_REQUIRED`;
- provenance/trust review required.

## Case 9 — Verification fails after pin update

Manifest validates, but project regression tests fail under the new Framework process/requirements.

Expected:
- no promotion;
- restore prior known-good pin if necessary;
- preserve failure evidence.

## Case 10 — Rollback evidence missing

Target is valid but the old exact pin was not preserved.

Expected:
- BLOCKED before promotion;
- old pin is mandatory rollback evidence.

## Case 11 — Schema change requires project migration

Target modifies `schemas/project-framework.schema.json` and existing project manifest no longer validates.

Expected:
- L3 architecture approval;
- explicit project integration migration plan;
- no destructive overwrite of project context.

## Case 12 — Framework update bundles unrelated product code

Project pin update PR also rewrites application behavior unrelated to compatibility.

Expected:
- reject bundled change by default;
- separate Framework dependency/governance upgrade from unrelated product behavior.
