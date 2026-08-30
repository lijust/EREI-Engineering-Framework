# Project Discovery Skill Specification

**Status:** Draft V1

## Purpose

Create durable project truth before architecture and implementation decisions become expensive to reverse.

## Scope

Covers:
- product/system boundary,
- users and authority,
- business-critical workflows,
- data ownership/sensitivity,
- non-functional requirements,
- authentication/authorization/tenant assumptions,
- integrations and deployment constraints,
- material unknowns and risk,
- initial project engineering artifacts.

## Non-scope

This skill does not:
- choose final architecture when blocking inputs remain unresolved,
- inspect an existing unfamiliar codebase in depth,
- replace threat modeling,
- replace product discovery beyond what materially affects engineering,
- create every possible artifact regardless of project maturity.

## Design rationale

Project-specific truth must live with the project, not in transient chat state. Discovery should reduce repeated questions while avoiding premature architecture commitments.

## Evidence model

Key decisions should indicate whether they are:
- USER_CONFIRMED,
- DOC_CONFIRMED,
- CODE_CONFIRMED,
- TOOL/RUNTIME_CONFIRMED,
- INFERRED,
- UNKNOWN.

## Failure modes

- Re-asking already answered questions.
- Converting preferences into hard architecture rules.
- Guessing security or tenant boundaries.
- Producing documentation volume without decision value.
- Failing to persist decisions durably.
- Mixing project-specific assumptions into Framework Core.
- Proceeding to architecture despite a blocking unknown.

## Evaluation strategy

Test:
1. Trigger quality for new/underspecified projects.
2. Avoidance of unnecessary discovery for mature, documented projects.
3. Accurate separation of confirmed vs inferred facts.
4. Identification of blocking security/data/architecture unknowns.
5. Proportional artifact creation.
6. Quality of Router handoff.

## Maintenance

When a downstream failure traces to missing discovery context, add a regression eval and update discovery categories if broadly reusable.

## Portability

Technology-neutral. Technology-specific discovery questions should come from overlays and only load when relevant.