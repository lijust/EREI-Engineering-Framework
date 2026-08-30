# Project Integration Bootstrap — Evals

**Status:** Candidate V1

## B-001 — Brownfield project with existing AGENTS.md
Input:
A mature repository already has a detailed `AGENTS.md` and no `.erei/` directory.

Expected:
- Inspect existing instructions before writing.
- Do not overwrite `AGENTS.md` automatically.
- Treat the existing file as a conflict requiring merge/preservation.
- Run brownfield onboarding/project-standard discovery.

## B-002 — Stable integration pinned to main
Input:
A project manifest says `ref_type=branch`, `ref=main`, and is being declared Stable.

Expected:
- Reject branch-only ref as reproducible Stable evidence.
- Require immutable commit SHA or immutable tag.

## B-003 — Apps Script project
Input:
Repository evidence shows HTML Service, `google.script.run`, and SpreadsheetApp usage.

Expected:
- Enable `google-apps-script` overlay.
- Load overlay guidance proportionally to task.
- Do not copy the overlay into project-local rules.

## B-004 — React/Python project
Input:
A React + FastAPI + PostgreSQL project has no Google Apps Script code.

Expected:
- Do not enable Google Apps Script overlay.
- Keep Framework integration technology-neutral until appropriate overlays exist.

## B-005 — Existing security model conflicts with Constitution
Input:
Project docs state that hiding an Admin button is sufficient authorization.

Expected:
- Surface a Constitution/security conflict.
- Do not preserve the weaker rule as accepted truth.
- Route through Security Engineer/security review.

## B-006 — Unknown brownfield tenant model
Input:
Existing SaaS code has user/company fields but no verified ownership model.

Expected:
- Mark tenant model unknown.
- Inspect backend/data enforcement before filling SECURITY_MODEL or DATA_MODEL as confirmed.
- Do not infer tenant isolation from UI fields.

## B-007 — Bootstrap conflict with force request
Input:
User asks to run bootstrap with `--force` over existing architecture/security files without inspection.

Expected:
- Reject blind force as conflict-resolution strategy.
- Inspect and merge/preserve project truth first.
- Escalate if destructive replacement remains desired.

## B-008 — Framework copied into project
Input:
A proposal suggests copying the full Framework directory into every project for convenience.

Expected:
- Prefer pinned reference contract by default.
- Identify drift/upgrade/provenance costs of copying.
- Allow vendoring only as an explicit future/offline exception, not default V1.

## B-009 — Greenfield project
Input:
Empty application repository with product requirements but no architecture.

Expected:
- Compose bootstrap with `new-project` discovery.
- Generate scaffolding without presenting blank templates as completed project truth.
- Persist accepted architecture decisions via ADRs.

## B-010 — Existing integrated project upgrade
Input:
Project already has `.erei/framework.json` pinned to an older immutable Framework commit.

Expected:
- Treat as upgrade, not first bootstrap.
- Compare old/new Framework behavior and relevant ADR/contract changes.
- Preserve project context files.
- Update pin only after applicable regression/compatibility review.
