# Regression Analysis Skill Specification

**Status:** Draft V1

## Purpose

Turn change impact into targeted, risk-proportional regression protection instead of relying on either narrow changed-line tests or indiscriminate full-suite execution.

## Scope
- changed surface,
- dependency/consumer surface,
- invariants intended to remain stable,
- historical escaped failures,
- regression risk prioritization,
- selection of verification types,
- coverage gaps/residual risk.

## Non-scope
- root-cause diagnosis,
- defining new feature requirements,
- generic test-suite maintenance,
- specialist security/performance review when those are independently required.

## Design rationale

Regression risk follows dependencies, contracts and invariants—not line count. Full-suite execution may be useful evidence but does not explain whether the risky path is actually covered.

## Failure modes
- changed-file-only scope,
- full-suite-only thinking,
- no negative-path regression for security fixes,
- forgetting data/export/integration consumers,
- not preserving real escaped failures,
- claiming isolation without evidence,
- excessive test breadth for isolated low-risk work.

## Evaluation strategy

Test shared API changes, security fixes, data migrations, isolated UI changes, refactors, stale/concurrency bugs, and known historical failures.

## Maintenance

Every escaped regression should be evaluated as a new durable case or reusable pattern.

## Portability

Technology-neutral; project and technology overlays supply dependency/test/runtime-specific checks.