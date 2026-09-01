# Framework Feedback Review

This directory is the Framework-side review surface for feedback discovered in projects that use EREI Engineering Framework.

## Ownership boundary

Raw observations remain in the project that discovered them:

```text
<project>/.erei/feedback/FRAMEWORK_FEEDBACK.jsonl
```

Structured execution experience remains project-local too:

```text
<project>/.erei/learning/TASK_EVENTS.jsonl
<project>/.erei/learning/LEARNING_REVIEWS.jsonl
```

Project agents must **not** write directly into this Framework repository as part of feedback or task-learning capture.

Framework review may later ingest/reference feedback events here for triage, deduplication, clustering and Knowledge Promotion. Learning Reviews are evidence sources that can reveal or strengthen a Framework Feedback pattern, but Task Learning Events are not automatically Framework Feedback.

## Review queue

`REVIEW_QUEUE.md` is the human-readable Framework-side checkpoint.

When project feedback is reviewed here, record at minimum:

- source project,
- immutable/source project ref where possible,
- source feedback ID,
- source Learning Review/epoch when applicable,
- Framework ref active when observed,
- type/severity,
- generalizability/confidence,
- review state,
- cluster/candidate link when applicable.

Do not copy secrets, tenant data, credentials, private reasoning, or unnecessary proprietary project details into the Framework repository.

## Lifecycle

```text
Project execution
      ↓
Task Learning Event
      ↓
Learning Review when enough evidence accumulates
      ↓
Framework limitation/reusable lesson?
      ↓ YES
Project-local feedback event
      ↓
Framework review/intake
      ↓
Validate evidence/root cause
      ↓
Deduplicate / classify / generalize
      ↓
PROJECT_LOCAL | NEEDS_EVIDENCE | FRAMEWORK_CANDIDATE
      ↓
Eval / tests / risk / approval
      ↓
PROMOTED | REJECTED
```

Promotion is governed by `workflows/knowledge-promotion/WORKFLOW.md`.

A promoted Framework change never updates project Framework pins automatically; project adoption uses the Framework Upgrade Workflow.
