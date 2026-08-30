# Impact Analysis Skill Specification

**Status:** Draft V1

## Purpose

Prevent local implementation decisions from missing cross-layer consequences.

The skill exists to answer:

> If we make this change, what else can break, what boundaries matter, what must remain true, and what evidence is required before implementation/release?

## Scope

Covers:
- cross-layer impact,
- blast radius,
- boundaries/invariants,
- security/data/performance implications,
- concurrency/consistency implications,
- rollback implications,
- role/skill recommendations,
- provisional risk classification.

## Non-scope

This skill does not itself:
- design the final architecture,
- perform a threat model in depth,
- implement the change,
- approve L3/L4 decisions,
- replace specialist security/data/performance analysis.

It routes to those procedures when impact indicates they are needed.

## Design rationale

AI-assisted implementation often optimizes the visible code location rather than the full system. A small diff can alter a large boundary. Therefore risk is based on blast radius and invariants, not line count.

## Required evidence

Material conclusions should identify whether they are confirmed from project evidence or inferred.

For brownfield work, conclusions about current architecture should be based on inspected project artifacts/code/runtime where practical.

## Failure modes

- Under-classifying a cross-layer change as local.
- Missing auth/tenant implications because only UI code is edited.
- Ignoring migration/backward-compatibility effects.
- Assuming data invariants without inspection.
- Recommending every specialist role regardless of relevance.
- Producing generic risk lists not connected to actual components.
- Treating an unknown as a confirmed architecture fact.

## Evaluation strategy

Evaluate three dimensions:

### Trigger quality
The skill should activate for genuine cross-layer or uncertain-impact work, but not burden isolated cosmetic work.

### Analysis quality
The output should identify concrete affected layers, invariants, failure modes, evidence plan, and provisional risk.

### Routing quality
Recommended roles and follow-on skills should be proportional to actual impact.

## Success criteria

A strong execution allows the Workflow Router to choose an appropriate workflow and risk level without redoing the entire analysis.

## Maintenance

When a real project failure occurs because impact analysis missed a class of consequence, add:
1. the missing pattern to references/procedure if reusable,
2. a regression eval reproducing that failure.

## Portability

The procedure is technology-neutral. Platform-specific failure modes belong in overlays and should be loaded only when the project uses that technology.