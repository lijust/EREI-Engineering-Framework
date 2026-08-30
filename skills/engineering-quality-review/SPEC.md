# Engineering Quality Review Skill Specification

**Status:** Draft V1

## Purpose

Provide a technical review stage that is deliberately separate from requirement compliance.

## Scope
- correctness/invariants,
- architecture fit,
- maintainability/complexity,
- project-standard adherence,
- obvious security/data/concurrency risks,
- error/failure handling,
- performance implications,
- testability/verification gaps.

## Non-scope
- redefining approved product requirements,
- replacing dedicated threat modeling/security audit,
- replacing measured performance investigation,
- demanding preferred stylistic architecture without project evidence.

## Design rationale

A strong review needs concrete failure modes and proportional severity. Separating this stage from compliance lets reviewers focus on engineering quality without hiding missing product requirements or using style preferences as blockers.

## Failure modes
- vague review comments,
- severity inflation,
- aesthetic refactoring pressure,
- assuming tests imply coverage,
- duplicating specialist security/performance work without routing,
- ignoring project-local standards.

## Evaluation strategy
Test real defects, false positives, over-refactor recommendations, concurrency cases, and severity proportionality.

## Independence
For L2+ work, fresh or independent review context is preferred when practical.

## Portability
Technology-neutral; overlays may add platform-specific checks.