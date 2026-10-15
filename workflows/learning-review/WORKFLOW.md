# Learning Review Workflow V1

**Type:** Framework/project learning workflow  
**Status:** Candidate V1

## Objective

Review accumulated project-local Task Learning evidence when deterministic thresholds indicate enough evidence, or immediately when critical learning signals appear, without turning metrics into automatic Framework changes.

## Entry conditions

Use when `.erei/learning/LEARNING_STATE.json` reports:

- `REVIEW_RECOMMENDED`,
- `REVIEW_DUE`, or
- `IMMEDIATE_REVIEW`,

or when a human explicitly requests a Learning Review.

`LEARNING_WATCH` normally continues capture unless judgment says an early review has clear value.

## Primary roles

- Chief Engineer — owns review framing, classification and follow-up routing.
- QA Engineer — reviews verification/rework evidence when material.
- Specialist roles only when the learning evidence concerns their domain.

Do not activate every specialist merely because the review spans multiple tasks.

## Inputs

- `.erei/learning/TASK_EVENTS.jsonl`,
- `.erei/learning/LEARNING_STATE.json`,
- Framework Feedback events linked from task events,
- exact project Framework pin(s) represented in the epoch,
- task/review evidence needed to validate surprising signals,
- previous Learning Review where comparison is useful.

## Procedure

### 1. Freeze the review sample

Read the current epoch ID and exact event count. Do not silently include events added after evidence analysis begins without restarting/reconciling the sample.

### 2. Validate ledger integrity

Run `tools/task_learning.py validate` or equivalent deterministic validation.

Stop if:
- JSONL is malformed,
- task fingerprint mismatch is detected,
- review cutoff is invalid,
- project identity/pin evidence is materially inconsistent.

### 3. Read the trigger as evidence, not conclusion

Document the trigger level and reasons.

Examples:
- 20/40 material task threshold,
- repeated feedback fingerprint,
- rework/verification failure rate,
- context gaps/manual workarounds,
- verification escape,
- critical security/data event.

Do not infer Framework causation merely because a threshold fired.

### 4. Segment the epoch

Analyze as applicable by:
- workflow,
- risk level,
- terminal outcome,
- Framework ref,
- task materiality,
- feedback fingerprint/pattern,
- rework/verification/context signals.

Look for both strengths and weaknesses. A workflow with 40 clean executions is learning evidence too.

### 4.1 Run deterministic pattern analysis when available

Run `tools/learning_pattern_analysis.py --target <project>` or equivalent Candidate behavior before assigning root cause.

Use the report to surface:

- review debt after a deterministic review trigger fired,
- repeated verification escapes that deserve explicit comparison,
- mixed V1/V2 evidence that weakens metric comparability,
- verification failures whose lifecycle stage is unknown,
- high-rework/high-verification-catch cohorts,
- repeated task groups/workflows that merit focused evidence review.

The analyzer is triage evidence only. It must not create Framework Feedback, change the project pin, or treat correlation as Framework causation.

### 5. Validate notable patterns

For each candidate pattern, distinguish:

- project defect,
- misuse/non-compliance with Framework,
- stale Framework pin behavior,
- project-specific rule gap,
- Framework workflow/skill/context limitation,
- measurement/classification noise,
- insufficient evidence.

Inspect cited evidence before escalating a Framework claim.

### 6. Compare prior epoch/version where possible

If a prior Learning Review or Framework upgrade exists, compare normalized signals carefully.

Do not claim improvement solely because raw counts changed when task mix/risk/workflow mix materially differs.

### 7. Produce findings

Classify each finding as one of:

- `HEALTHY_PATTERN`
- `PROJECT_LOCAL_ACTION`
- `FRAMEWORK_FEEDBACK`
- `MEASUREMENT_ADJUSTMENT`
- `NEEDS_MORE_EVIDENCE`
- `CRITICAL_FOLLOWUP`

### 8. Route Framework findings

For genuine Framework limitations:
- create/cluster project-local Framework Feedback with evidence,
- preserve source task IDs/epoch,
- use Knowledge Promotion separately.

Do not modify Framework Core from this workflow.

### 9. Close the Learning Epoch

Record:
- findings,
- decision,
- evidence,
- follow-up actions,
- exact event cutoff,
- metrics/trigger at closure.

Use `tools/task_learning.py review-close` or equivalent.

A closed review starts the next project-local epoch without deleting historical evidence.

## Immediate-review handling

`IMMEDIATE_REVIEW` means the learning review should happen promptly. Avoid accumulating a large new material cohort while immediate-review debt remains open unless continuation is explicitly justified by an independent release/security/data need. Release/blocking behavior still comes from the underlying evidence:

- a critical security finding follows Security governance,
- material data risk follows Data governance,
- a verification escape may invalidate prior completion/release evidence.

The learning trigger itself is not an authorization or release state.

## Output

```text
Learning review ID:
Epoch reviewed:
Event cutoff:
Framework refs represented:
Trigger and reasons:
Task/workflow mix:
Healthy patterns:
Project-local findings:
Framework feedback created/clustered:
Measurement issues:
Critical follow-up:
Decision/actions:
Next epoch:
```

## Definition of Done

- ledger integrity verified,
- trigger reasons examined,
- notable patterns grounded in project evidence,
- causation not overstated,
- Framework findings routed through feedback/Knowledge Promotion,
- review closure recorded with evidence,
- next epoch initialized deterministically.
