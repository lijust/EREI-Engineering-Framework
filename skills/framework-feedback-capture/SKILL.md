# Framework Feedback Capture

## Purpose

Capture evidence-backed limitations, friction, missed conditions, unsafe assumptions or reusable lessons discovered while a project uses EREI Engineering Framework.

This Skill records feedback. It does **not** modify Framework Core, change the project's Framework pin, or promote a suggestion automatically.

## Trigger

Run a Framework Feedback Check near the end of every material engineering task and after material failures/rework.

Capture feedback when project evidence shows at least one of the following:

- the selected Framework workflow/skill/role missed a material condition,
- a bug escaped despite the applicable Framework verification path,
- risk was materially over- or under-classified,
- a repeated workaround was required outside the documented Framework procedure,
- Framework/project context routing caused avoidable confusion or missing information,
- security, data-integrity or performance evidence exposed a Framework gap,
- Framework instructions conflict or create recurring process friction,
- a reusable pattern is absent from Framework guidance,
- the same project lesson should explicitly become negative learning / an anti-pattern.

Do not capture an ordinary project-specific bug merely because the Framework was in use. There must be a plausible Framework limitation, reusable lesson or process issue.

## Required evidence

Every event requires at least one durable evidence reference. Evidence may point to project test output, an ADR, issue, regression record, log, PR, runbook, evidence artifact or another durable repository/runtime record.

Do not use unsupported agent opinion as evidence.

## Event fields

Use `schemas/framework-feedback.schema.json`.

Required semantics:

- exact Framework ref used when the observation occurred,
- project repository identity,
- feedback type and severity,
- precise observation,
- durable evidence references,
- suggested Framework improvement,
- generalizability assessment,
- confidence,
- `new` status,
- deterministic semantic fingerprint.

Optional fields include source Framework artifact, negative learning and tags.

## Storage

Project-local source of truth:

```text
.erei/feedback/
├── FRAMEWORK_FEEDBACK.jsonl
└── FRAMEWORK_FEEDBACK.md
```

`FRAMEWORK_FEEDBACK.jsonl` is authoritative. The Markdown file is a generated human-readable projection.

The project owns this raw feedback until a later Knowledge Promotion/Intake process evaluates it.

## Procedure

1. Identify the concrete Framework limitation or reusable lesson.
2. Separate project defect from Framework feedback.
3. Identify the exact pinned Framework ref active when observed.
4. Collect durable evidence references.
5. Classify type, severity, confidence and likely generalizability.
6. Write a concise observation describing what happened, not what should have happened.
7. Write a separate suggested improvement.
8. Record negative learning when a tempting but unsafe/ineffective approach should be rejected later.
9. Capture the event with `tools/capture_framework_feedback.py` or an equivalent schema-conformant project-local mechanism.
10. Continue project delivery normally unless the underlying evidence itself represents an unresolved project blocker.

## Safety rules

- Feedback capture must never silently modify the pinned Framework repository.
- Feedback capture must never silently change `.erei/framework.json`.
- A suggestion is not an accepted Framework decision.
- A project may specialize its own rules without pretending the specialization is generic Framework truth.
- Sensitive data, secrets, credentials, personal data and tenant data must not be copied into feedback events.
- Evidence references should point to protected source artifacts rather than duplicating sensitive contents.

## Output

One append-only project-local feedback event plus refreshed human-readable projection.

## Completion

Feedback capture is complete when:

- the event is schema-conformant,
- the exact Framework ref is recorded,
- at least one evidence reference exists,
- observation and suggestion are distinct,
- no automatic Framework mutation/promotion occurred,
- the feedback ledger remains readable after append.
