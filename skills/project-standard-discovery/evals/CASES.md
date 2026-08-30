# Project Standard Discovery Evals

**Status:** Draft V1

## T-001 — Nested instructions
Scenario: root `AGENTS.md` says tests required; `frontend/AGENTS.md` adds RTL/accessibility rules.

Expected:
- Discover hierarchy.
- Scope frontend rules to frontend paths.
- Do not inject frontend-only rules into backend work.

## T-002 — Documentation/code conflict
Scenario: README says API errors are strings; current backend consistently returns typed error objects.

Expected:
- Mark conflict.
- Do not silently choose one as authoritative.
- Recommend resolution if material.

## T-003 — One-file overgeneralization
Scenario: one service uses repository pattern; ten others access data differently.

Expected:
- Do not call repository pattern a project-wide standard.
- Label observation weak/local.

## T-004 — Generated files
Scenario: build output is checked into a generated directory and source comments warn not to edit it.

Expected:
- Mark as unsafe-to-edit/generated.
- Route implementation to source generator/input.

## B-001 — Context routing
Scenario: discovered standards include auth, CSS, database, and release rules; task is a CSS-only L0 change.

Expected:
- Recommend only relevant UI/CSS/local verification context.
- Do not dump all standards.

## B-002 — Critical invariant
Scenario: middleware and tests demonstrate tenant ID is resolved from server session, never request body.

Expected:
- Record as high-impact invariant with evidence.
- Preserve for auth/data-related tasks.