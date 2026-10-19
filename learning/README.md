# Framework Task Learning

Task Learning turns real project execution into structured, reviewable experience data without training or self-modifying an AI model directly.

## Four evidence paths

```text
Prospective path
Every routed engineering execution
        ↓
Task Learning Event
        ↓
Deterministic Learning State / Review Trigger
        ↓
Learning Review when enough evidence exists

Retrospective path
Historical durable project evidence
        ↓
Retrospective Learning Backfill
        ↓
RETROSPECTIVE_TASK_EVENTS.jsonl
        ↓
Supporting review evidence only

Framework-improvement path
Only when a Framework limitation/reusable lesson exists
        ↓
Framework Feedback
        ↓
Knowledge Promotion
        ↓
Framework Candidate → Stable

Learning-to-development path
Pattern Analysis + Learning Review
        ↓
Chief Engineer interpretation
        ↓
Learning Development Output
        ↓
Project action / measurement change / Framework Feedback
        ↓
Candidate trial when justified
        ↓
Before/after effectiveness measurement
```

Prospective Task Learning is the primary calibration dataset. Retrospective backfill exists to recover useful evidence from work completed before Task Learning V1 was enabled, without pretending historical reconstruction has the same evidentiary quality.

## Project ownership

Raw task events, retrospective events and Learning Reviews remain in the source project under `.erei/learning/`. This Framework repository stores schemas, procedures, thresholds, evals and generic workflows—not a hidden global copy of project data.

Project-local ledgers:

```text
.erei/learning/TASK_EVENTS.jsonl                 # prospective
.erei/learning/RETROSPECTIVE_TASK_EVENTS.jsonl  # historical backfill
.erei/learning/LEARNING_REVIEWS.jsonl
.erei/learning/LEARNING_STATE.json
.erei/learning/LEARNING_SUMMARY.md
```

Retrospective events carry `evidence_quality = confirmed | reconstructed | inferred`, and each reconstructed signal carries its own quality and source references. Unknown historical signals stay absent rather than being guessed.

## V1 review trigger states

- `LEARNING_HEALTHY`
- `LEARNING_WATCH`
- `REVIEW_RECOMMENDED`
- `REVIEW_DUE`
- `IMMEDIATE_REVIEW`

The prospective state is derived deterministically by `tools/task_learning.py`.

## Default prospective threshold policy

- Immediate: verification escape or critical security/data event.
- Due: 40 material tasks, same Framework-feedback fingerprint 3 times, or 5 Framework-feedback tasks.
- Recommended: 20 material tasks; elevated rework/verification-failure rates after a minimum sample; 3 manual workarounds or context gaps.
- Watch: 10 material tasks or 2 Framework-feedback tasks.

Retrospective event counts do **not** automatically advance these prospective thresholds. Historical evidence may justify targeted review hypotheses or an immediate Feedback candidate when independently strong, but it cannot inflate calibration volume.

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


## Metric interpretation update

Raw `rework_rate` and `verification_failure_rate` are not execution-accuracy metrics.

Use `learning/LEARNING_HEALTH_MODEL.md` and the Learning-to-Development workflow to distinguish:

- material iteration from task restart/final failure,
- healthy pre-merge verification catches from escaped defects,
- final failed outcomes from success-with-deferred,
- raw metric movement from actual Framework effectiveness.

The Chief Engineer owns interpretation; deterministic tooling supplies evidence and pattern signals only.

## Immediate-review debt

Candidate governance defines a bounded defer contract for unresolved `IMMEDIATE_REVIEW` debt, applied only when `learning_review_debt_guard` resolves active for the exact project pin/version. A dormant Candidate does not require or apply a defer. Core authoritative-state validation, prompt review of signals, and security/data/verification stops remain in effect. An active defer is time-limited, task-count-limited and evidence-backed; it never authorizes security/data/release risk.
