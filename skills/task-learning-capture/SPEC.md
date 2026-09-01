# Task Learning Capture — Specification V1

## Intent

Create a low-noise, provider-neutral experience dataset from real project execution so EREI can measure Framework effectiveness and know when enough evidence exists for review.

## Relationship to Framework Feedback

Task Learning answers: **what happened during every engineering execution?**

Framework Feedback answers: **did this execution reveal a plausible Framework limitation or reusable lesson?**

A Task Learning Event may link zero or more Framework Feedback events. The two ledgers must not be conflated.

## Storage model

Project-local canonical data:

```text
.erei/learning/
├── TASK_EVENTS.jsonl
├── LEARNING_REVIEWS.jsonl
├── LEARNING_STATE.json
└── LEARNING_SUMMARY.md
```

`TASK_EVENTS.jsonl` and `LEARNING_REVIEWS.jsonl` are append-only durable evidence. State and summary are derived views and may be regenerated.

## Learning Epoch

An epoch is the set of task events after the previous closed Learning Review and through the next review closure.

Epoch numbering is project-local:

- `EPOCH-001`
- `EPOCH-002`
- ...

A review stores the exact task-event cutoff used so historical calculations remain reproducible.

## Review readiness

The V1 state engine is deterministic. It does not ask an LLM whether the sample is 'enough'. It computes transparent thresholds from observable signals.

Priority order:

1. `IMMEDIATE_REVIEW`
2. `REVIEW_DUE`
3. `REVIEW_RECOMMENDED`
4. `LEARNING_WATCH`
5. `LEARNING_HEALTHY`

Higher-priority evidence dominates lower-priority count thresholds.

## Data minimization

Do not store:

- chain-of-thought/private reasoning,
- prompts or conversations unless separately required as evidence,
- credentials/secrets,
- customer/tenant payloads merely for learning convenience,
- large code or logs that can instead be referenced by evidence path/ID.

V1 uses coarse `duration_class` rather than pretending wall-clock timing is comparable across tools/runtimes.

## Signal definitions

- `rework_cycles`: material implementation/review loops required after an initial candidate, based on observable changes.
- `verification_failures`: deterministic verification attempts that failed during the task.
- `verification_escape`: a prior verification/completion claim was contradicted later by escaped evidence.
- `manual_workaround`: execution required an unmodeled manual bypass/workaround to proceed.
- `context_gap`: missing/misrouted project or Framework context materially affected execution.
- `unexpected_scope_growth`: actual required work expanded materially beyond the classified/planned scope.
- `security_or_data_critical_event`: critical security/data correctness evidence appeared during/after execution.

These are signals, not automatic root-cause assignments.

## V1 thresholds

### Immediate

Any:
- verification escape,
- critical security/data event.

### Due

Any:
- 40 material tasks since last review,
- same Framework Feedback fingerprint occurs at least 3 times,
- 5 tasks generated Framework Feedback.

### Recommended

Any:
- 20 material tasks,
- at least 8 material tasks and rework-task rate >=25%,
- at least 8 material tasks and verification-failure-task rate >=15%,
- 3 manual workarounds,
- 3 context gaps.

### Watch

Any:
- 10 material tasks,
- 2 Framework-feedback tasks.

## Review closure

A Learning Review must record:

- epoch ID,
- task-event cutoff,
- trigger/metrics at review time,
- evidence references,
- findings,
- decision,
- follow-up actions where applicable.

Review closure starts a fresh epoch. It does not erase prior events.

## Promotion boundary

Learning Review findings may create or cluster Framework Feedback. Framework changes still require Knowledge Promotion, risk/approval, evals/tests and Candidate → Stable release.

## Future extensions

Only after real-project evidence:

- cross-project aggregation,
- calibrated thresholds by workflow/risk,
- Framework-version before/after effectiveness comparison,
- privacy-preserving aggregate metrics,
- routing/context effectiveness scoring.

Do not add predictive/ML scoring until deterministic signals have enough real evidence to justify it.
