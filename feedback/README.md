# Framework Feedback Review

This directory is the Framework-side review surface for feedback discovered in projects that use EREI Engineering Framework.

## Ownership boundary

Raw observations remain in the project that discovered them:

```text
<project>/.erei/feedback/FRAMEWORK_FEEDBACK.jsonl
```

Project agents must **not** write directly into this Framework repository as part of feedback capture.

Framework review may later ingest/reference those events here for triage, deduplication, clustering and Knowledge Promotion.

## Review queue

`REVIEW_QUEUE.md` is the human-readable Framework-side checkpoint.

When project feedback is reviewed here, record at minimum:

- source project,
- immutable/source project ref where possible,
- source feedback ID,
- Framework ref active when observed,
- type/severity,
- generalizability/confidence,
- review state,
- cluster/candidate link when applicable.

Do not copy secrets, tenant data, credentials, or unnecessary proprietary project details into the Framework repository.

## Lifecycle

```text
Project observation
      ↓
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
