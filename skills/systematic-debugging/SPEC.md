# Systematic Debugging Skill Specification

**Status:** Draft V1

## Purpose

Replace trial-and-error bug fixing with an evidence-driven procedure that confirms root cause and creates durable regression protection.

## Scope
- symptom definition,
- reproduction/equivalent evidence,
- boundary tracing,
- hypothesis generation/testing,
- root-cause confirmation,
- minimal safe fix strategy,
- regression guard,
- post-fix verification.

## Non-scope
- broad architecture redesign,
- generic performance optimization when bottleneck is already measured,
- incident coordination/containment,
- security risk acceptance,
- large refactoring unless required by confirmed root cause and separately justified.

## Design rationale

AI coding agents can rapidly generate plausible patches, which increases the risk of changing symptoms without understanding causes. Debugging should preserve causality: observed failure → violated invariant → evidence → root cause → targeted fix → regression proof.

## Failure modes
- changing code before reproduction,
- conflating correlation with cause,
- multiple simultaneous speculative edits,
- retry/catch used to hide root cause,
- declaring success after one non-reproducing run,
- ignoring pre-existing failures,
- root cause statement broader than evidence,
- large rewrite proposed because local code appears messy.

## Evidence model

Prefer:
- TEST_CONFIRMED reproduction,
- RUNTIME/TOOL_CONFIRMED traces/logs/state,
- CODE_CONFIRMED causal path,
with INFERRED hypotheses clearly labeled until tested.

## Evaluation strategy

Test:
- deterministic bug,
- intermittent/race bug,
- misleading recent change,
- swallowed error temptation,
- unreproduced but strong production evidence,
- wrong-layer symptom patch,
- real regression case from Apps Script stale sequence behavior.

## Maintenance

Every meaningful bug where this skill fails to identify a reusable diagnostic class should become a regression eval/pattern.

## Portability

Technology-neutral. Platform overlays supply runtime-specific debugging probes, concurrency semantics, logs, and limits.