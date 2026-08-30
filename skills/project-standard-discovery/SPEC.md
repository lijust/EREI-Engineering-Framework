# Project Standard Discovery Skill Specification

**Status:** Draft V1

## Purpose

Provide evidence-backed project conventions for brownfield work and task-specific context routing.

## Scope
- local instructions,
- architecture/module conventions,
- build/test/deploy commands,
- coding/data/error/testing patterns,
- critical invariants,
- generated/unsafe edit zones,
- conflicts and uncertainty,
- routable standard metadata.

## Non-scope
- declaring generic best practices to be project rules,
- resolving architecture conflicts without review,
- full security audit,
- full codebase documentation.

## Design rationale

Existing systems contain implicit knowledge. Agents either ignore it or overload context by reading everything. This skill creates a middle layer: source-backed standards that can later be selectively injected.

## Failure modes
- overgeneralizing from one file,
- trusting stale docs over contradictory runtime/code evidence,
- losing provenance,
- hiding conflicting conventions,
- producing a giant non-routable standards document.

## Evaluation strategy
Test source attribution, conflict detection, evidence-strength labeling, path/domain routing, and avoidance of invented conventions.

## Maintenance
Re-run when major architecture changes land or when repeated violations reveal stale standards.

## Portability
Technology-neutral. Overlays may define additional discovery probes for their platforms.