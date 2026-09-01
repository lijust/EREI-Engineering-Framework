# Framework Task Learning

Task Learning turns real project execution into structured, reviewable experience data without training or self-modifying an AI model directly.

## Two distinct loops

```text
Every routed engineering execution
        ↓
Task Learning Event
        ↓
Deterministic Learning State / Review Trigger
        ↓
Learning Review when enough evidence exists

Only when a Framework limitation/reusable lesson exists
        ↓
Framework Feedback
        ↓
Knowledge Promotion
        ↓
Framework Candidate → Stable
```

Task Learning is therefore broader than Framework Feedback.

## Project ownership

Raw task events and Learning Reviews remain in the source project under `.erei/learning/`. This Framework repository stores the schema, procedures, thresholds, evals and generic review workflow—not a hidden global copy of project data.

## V1 review trigger states

- `LEARNING_HEALTHY`
- `LEARNING_WATCH`
- `REVIEW_RECOMMENDED`
- `REVIEW_DUE`
- `IMMEDIATE_REVIEW`

The state is derived deterministically by `tools/task_learning.py`.

## Default threshold policy

- Immediate: verification escape or critical security/data event.
- Due: 40 material tasks, same Framework-feedback fingerprint 3 times, or 5 Framework-feedback tasks.
- Recommended: 20 material tasks; elevated rework/verification-failure rates after a minimum sample; 3 manual workarounds or context gaps.
- Watch: 10 material tasks or 2 Framework-feedback tasks.

These thresholds are an initial calibration, not eternal truth. Real-project evidence should determine later adjustments.

## Data minimization

Task events store observable engineering signals and references. They must not store private chain-of-thought, credentials, customer/tenant payloads, or large execution transcripts merely for future learning.

## Review boundary

A Learning Review can conclude that:

- a pattern is healthy,
- project-local action is required,
- measurement needs adjustment,
- more evidence is needed,
- Framework Feedback should be created/clustered,
- critical specialist follow-up is required.

It cannot directly promote a Framework change. Framework changes remain governed by Feedback → Knowledge Promotion → risk/approval → evals/tests → Candidate → Stable.
