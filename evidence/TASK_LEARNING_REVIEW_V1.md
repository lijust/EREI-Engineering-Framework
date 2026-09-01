# Task Learning & Learning Review V1 — Release Evidence

**Release date:** 2026-09-02  
**Architecture decision:** `adr/ADR-0005-TASK-LEARNING-AND-REVIEW-TRIGGERS.md`  
**Candidate PR:** #26 — Task Learning & Deterministic Review Triggers V1  
**Candidate head:** `2a689da353675cae3f4ae354f9d0e72d66adae92`  
**Candidate merge commit:** `557074d34f8076b212c35b325df425584861fb32`

## Scope verified

The candidate implements:

- Task Learning Event V1 schema,
- derived Learning State schema,
- Learning Review record schema,
- project-local append-only task/review ledgers,
- deterministic learning-state/review-trigger engine,
- Task Learning Capture skill/spec/evals,
- Learning Review workflow/evals,
- universal Router terminal capture,
- Chief Engineer review-trigger handling,
- project bootstrap learning scaffolding,
- Knowledge Promotion linkage for task/epoch evidence,
- Python-standard-library-only tooling,
- dedicated CI.

## Deterministic review states

V1 exposes:

- `LEARNING_HEALTHY`
- `LEARNING_WATCH`
- `REVIEW_RECOMMENDED`
- `REVIEW_DUE`
- `IMMEDIATE_REVIEW`

Initial thresholds are transparent and documented in ADR-0005/Task Learning specification. They are explicitly subject to calibration from real project evidence.

## Local pre-upload verification

Final hardened task-learning implementation passed **8/8** deterministic local unit scenarios including:

- 20 material tasks → review recommended,
- 40 material tasks → review due,
- verification escape → immediate review,
- same Framework-feedback fingerprint three times → review due,
- review closure starts a new epoch,
- empty epoch cannot be closed,
- malformed feedback fingerprint rejected,
- semantic event tampering detected.

## GitHub CI on exact candidate head

All required PR-triggered workflows completed successfully on `2a689da353675cae3f4ae354f9d0e72d66adae92`:

- **Task Learning Tests** — SUCCESS
- **Framework Evals** — SUCCESS
- **Framework Feedback Tests** — SUCCESS
- **Project Bootstrap Tests** — SUCCESS

No failed/canceled required run was accepted for promotion.

## Safety / governance evidence

The candidate explicitly preserves:

- no Framework self-modification from task learning or review triggers,
- no automatic project Framework-pin movement,
- project-local ownership of raw learning data,
- no private chain-of-thought, credentials or tenant/customer payload capture,
- metrics as signals rather than automatic root-cause claims,
- separate Framework Feedback / Knowledge Promotion for reusable Framework changes,
- separate security/data/verification blocking authority from the learning trigger itself.

## Project impact

This release does **not** modify any product repository or existing project Framework pin.

Projects adopt Task Learning V1 only after upgrading to this Stable Framework revision through Framework Upgrade Workflow at an appropriate project checkpoint.

## Next validation

The next evidence target is not additional architecture. It is real-project calibration:

1. generate Task Learning Events from real feature/bug/review work,
2. observe the first real review trigger,
3. close a real Learning Epoch,
4. validate whether threshold values are useful,
5. complete at least one Learning Review → Framework Feedback → Knowledge Promotion → project Framework Upgrade loop,
6. use before/after epochs to evaluate whether the promoted Framework change actually improved outcomes.
