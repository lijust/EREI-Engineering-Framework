# Requirement Compliance Review Skill Specification

**Status:** Draft V1

## Purpose

Prevent a technically polished implementation from being accepted when it does not match the agreed requirement.

## Scope
- requirement decomposition,
- implementation-to-requirement mapping,
- scope drift detection,
- constraint compliance,
- explicit deferred-item handling.

## Non-scope
- detailed code-quality review,
- architecture redesign,
- final runtime verification of every claim,
- security audit beyond checking explicit security requirements.

## Design rationale

Specification compliance and engineering quality are independent questions. They should be reviewed separately to reduce confirmation bias and prevent quality discussions from hiding missing requirements.

## Failure modes
- reviewing style instead of requirements,
- accepting partial work as full completion,
- ignoring explicit exclusions/constraints,
- treating code presence as runtime proof,
- failing to surface unapproved scope expansion.

## Evaluation strategy
Test complete, partial, over-scoped, and apparently complete-but-unverified implementations.

## Independence
For L2+ material changes, prefer review context that is separate from the implementation context where practical.

## Portability
Technology-neutral.