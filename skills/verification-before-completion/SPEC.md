# Verification Before Completion Skill Specification

**Status:** Draft V1

## Purpose

Prevent unsupported completion claims and create a consistent evidence gate before convergence or release.

## Scope
- claim enumeration,
- verification-method selection,
- fresh evidence execution,
- scope/limitation recording,
- baseline vs new-failure separation,
- risk-proportional verification verdict.

## Non-scope
- implementing fixes,
- deciding product scope,
- replacing specialist security/data/performance procedures when those are required,
- claiming universal absence of defects.

## Design rationale

AI-assisted development fails when plausible implementation is treated as verified behavior. Verification must be fresh, scoped, reproducible where practical, and stronger as risk grows.

## Failure modes
- stale evidence,
- claiming more than a test proves,
- treating exit code success as proof of unrelated invariants,
- mislabeling new failures as pre-existing,
- skipping runtime checks because source looks correct,
- using narrow evidence for universal negative claims.

## Evaluation strategy
Test stale-check rejection, pre-existing failure separation, performance before/after claims, targeted bug reproduction, and risk-proportional evidence depth.

## Portability
Technology-neutral; overlays may provide verification commands/checklists.