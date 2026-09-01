# ADR-0005 — Task Learning and Deterministic Review Triggers

**Status:** Accepted  
**Date:** 2026-09-02  
**Risk:** L2 — Framework-wide learning/observability policy

## Context

Framework Feedback Capture V1 records evidence-backed Framework limitations, but a feedback-only dataset is biased toward failures and friction. EREI also needs evidence from successful executions so it can measure workflow effectiveness, rework, verification quality and whether Framework changes actually improve later work.

The learning mechanism must not collect private reasoning, must not self-modify Framework Core, and must not move project Framework pins automatically.

## Decision

Every routed engineering execution should emit one structured project-local **Task Learning Event** at terminal/convergence handling, including blocked or failed work.

The event records engineering signals, not chain-of-thought:

- exact Framework ref,
- selected workflow and risk,
- terminal/outcome class,
- material/non-material classification,
- rework cycles,
- verification failures and verification escapes,
- Framework-feedback linkage when present,
- manual workaround/context-gap/scope-growth signals,
- critical security/data event signal,
- coarse duration class.

Task events are append-only project-local evidence under `.erei/learning/`.

A deterministic state engine derives review readiness from the current **Learning Epoch**. It returns one of:

- `LEARNING_HEALTHY`
- `LEARNING_WATCH`
- `REVIEW_RECOMMENDED`
- `REVIEW_DUE`
- `IMMEDIATE_REVIEW`

V1 review triggers are deliberately transparent and deterministic. A review is recommended after 20 material tasks, due after 40, and may occur earlier for repeated feedback, elevated rework/verification-failure rates, repeated context gaps/manual workarounds, verification escapes, or critical security/data events.

A Learning Review closes the current epoch using evidence and starts the next epoch. Closing a review does not itself change Framework Core. Framework-changing findings must still enter Framework Feedback / Knowledge Promotion and normal Candidate → Stable governance.

## Invariants

1. Every routed engineering execution produces at most one terminal Task Learning Event.
2. Explanation-only conversation that never enters engineering execution is not a task event.
3. No private chain-of-thought or secret credentials are stored.
4. Raw task-learning data remains owned by the source project.
5. Review readiness is deterministic and inspectable.
6. A review trigger is a prompt to review evidence, not permission to modify the Framework.
7. Existing projects remain on their immutable Framework pin until Framework Upgrade Workflow is explicitly executed.
8. Success events are retained so learning is not failure-only.

## Initial thresholds

- `IMMEDIATE_REVIEW`: any verification escape or critical security/data event.
- `REVIEW_DUE`: 40 material tasks, same feedback fingerprint 3 times, or 5 Framework-feedback tasks.
- `REVIEW_RECOMMENDED`: 20 material tasks; or, with at least 8 material tasks, rework rate >=25% or verification-failure rate >=15%; or 3 manual workarounds/context gaps.
- `LEARNING_WATCH`: 10 material tasks or 2 Framework-feedback tasks.

Thresholds are themselves subject to evidence-driven revision after real-project validation.

## Consequences

### Benefits

- every execution becomes structured experience data,
- successful and unsuccessful work are measurable,
- Framework reviews happen when evidence accumulates rather than by memory,
- epochs allow before/after comparison across Framework versions,
- recurring feedback can be detected without automatic promotion.

### Costs

- every engineering task has a small terminal capture obligation,
- metrics can be misleading if agents classify signals dishonestly,
- thresholds need calibration from real project evidence,
- cross-project aggregation requires later privacy/provenance-aware tooling.

## Rejected alternatives

### Record only Framework failures
Rejected because it creates survivorship/failure bias and cannot measure whether workflows usually work.

### Review every fixed number of tasks only
Rejected because a critical verification/security event may justify immediate review before the count threshold.

### Let the agent edit Framework Core when a pattern is detected
Rejected because it violates Knowledge Promotion, approval, evaluation and release governance.

### Store full reasoning transcripts
Rejected as unnecessary, noisy and inappropriate for durable engineering learning. Structured observable signals are sufficient for V1.

## Approval record

The Task Learning / review-trigger mechanism was explicitly requested and approved for implementation on 2026-09-02.
