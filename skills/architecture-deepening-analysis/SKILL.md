---
name: architecture-deepening-analysis
description: Identify evidence-backed opportunities to deepen shallow or high-friction modules by improving interface depth, seam placement, locality, leverage, and testability without performing speculative refactors. Use when repeated change/rework, hard-to-test behavior, architecture friction, or an explicit architecture review justifies focused structural analysis.
---

# Architecture Deepening Analysis

**Status:** Stable V1

## Objective

Find structural changes that would concentrate complexity behind smaller, more stable interfaces **only where evidence shows architectural friction worth paying to fix**.

This skill is an analysis/recommendation skill. It does not authorize or perform a structural refactor by itself.

## Core vocabulary

Use these terms consistently:

- **Module** — implementation hidden behind an interface. A module may be a function, class, package, subsystem, or vertical slice.
- **Interface** — everything a caller must know to use the module correctly, including invariants, ordering, errors, configuration, and relevant performance behavior.
- **Seam** — the location where behavior can vary without callers being edited.
- **Adapter** — a concrete implementation satisfying a seam.
- **Depth** — useful behavior hidden behind a comparatively small interface.
- **Leverage** — useful capability callers gain per unit of interface they must understand.
- **Locality** — change, knowledge, failure handling, and verification concentrated in one place rather than scattered across callers.

Do not measure depth by implementation-line/interface-line ratios.

## Trigger when

Use when one or more of the following is true:

- the user explicitly asks for architecture/codebase improvement analysis,
- Task Learning shows repeated rework or verification failures around the same area,
- Framework Feedback shows recurring architecture/process friction,
- recent history shows the same paths changing repeatedly for related behavior,
- a feature/bug repeatedly requires edits across many callers for one concept,
- meaningful behavior is hard to test through a stable public surface,
- a cluster of wrappers/adapters/helpers appears to add navigation without hiding complexity,
- engineering review identifies a material architecture/testability concern needing deeper analysis.

## Do not trigger when

- the change is cosmetic/local L0 work,
- there is no evidence of material structural friction,
- a proposed refactor is based only on aesthetic preference,
- current behavior/architecture has not been inspected,
- an existing ADR explicitly settles the design and no new evidence justifies reopening it.

## Required inputs

Use available:

- project architecture and ADRs,
- accepted requirement/task scope,
- affected code/module paths,
- recent relevant change history,
- tests and testability evidence,
- `.erei/learning/` signals when available,
- Framework Feedback related to the area,
- project standards/overlays,
- risk classification.

## Procedure

### 1. Select evidence-backed scope

Prefer the narrowest hotspot supported by evidence.

Possible evidence:

- repeated edits to the same concept,
- repeated rework cycles,
- repeated verification failures,
- recurring manual workarounds/context gaps,
- recurring Framework Feedback fingerprint,
- duplicated behavior across callers,
- hard-to-test orchestration,
- frequent contract drift.

Do not scan/refactor the whole repository by default.

### 2. Reconstruct current caller knowledge

For the candidate module/cluster, identify what callers must currently know:

- functions/methods and parameters,
- sequencing/order requirements,
- state assumptions,
- error modes,
- configuration,
- data-shape knowledge,
- retry/idempotency rules,
- authorization/tenant requirements,
- performance caveats.

This is the effective interface even when not declared formally.

### 3. Identify shallow or leaky structure

Look for evidence such as:

- pass-through wrappers that merely rename calls,
- callers duplicating orchestration/invariants,
- repeated switches/branching over the same domain condition,
- one logical change requiring edits in many places,
- helper extraction that improves unit-test access but worsens locality,
- tests reaching around the public interface into private implementation,
- adapters that exist without real variation,
- interfaces nearly as complex as the behavior they hide.

### 4. Apply the deletion test

Ask:

> If this module were deleted, would its complexity disappear, or would the same complexity spread back into its callers?

- If complexity mostly disappears, the module may be shallow/pass-through.
- If complexity spreads across callers, the module is likely earning locality/leverage.

Treat this as a heuristic, not an automatic verdict.

### 5. Evaluate seam reality

A seam is justified when there is meaningful variation or isolation need.

Evidence may include:

- two or more real adapters,
- local vs hosted runtime implementations,
- production implementation vs intentionally supported in-memory/test implementation,
- provider variation required by accepted architecture,
- a trust/runtime boundary that must remain replaceable.

One implementation alone is not enough reason to manufacture an interface unless another EREI architecture/security/testing requirement justifies it.

### 6. Design a deeper candidate shape

For each worthwhile candidate describe:

- current interface knowledge burden,
- proposed smaller/stabler interface,
- behavior/invariants moved behind it,
- seam location,
- real adapters if any,
- locality gain,
- leverage gain,
- test surface improvement,
- migration cost/risk,
- compatibility/security/data implications.

Do not write implementation unless separately authorized through the normal workflow.

### 7. Check against accepted architecture

Existing project architecture, Constitution, security/data rules, and ADRs outrank generic design heuristics.

If the candidate conflicts with an ADR:

- identify the conflict,
- show the new evidence that could justify reopening it,
- do not silently override the ADR.

### 8. Rank candidates

Use:

- `STRONG` — repeated evidence + clear locality/leverage/testability gain + bounded migration,
- `WORTH_EXPLORING` — plausible gain but some assumptions/unknowns remain,
- `SPECULATIVE` — insufficient evidence; do not implement yet,
- `REJECT` — duplicates existing architecture, violates accepted constraints, or increases abstraction without real leverage.

### 9. Route structural change correctly

If a recommendation would create/change a material architecture seam, persistence boundary, security boundary, tenant authority, or deployment/runtime contract, return to Router/architecture approval according to risk level before implementation.

## Required output

```text
Analysis scope:
Hotspot evidence:
Current module/cluster:
Current effective interface:
Observed friction:
Deletion-test result:
Existing seam/adapters:
Candidate deeper interface:
Behavior moved behind interface:
Locality gain:
Leverage gain:
Test-surface effect:
ADR/architecture compatibility:
Migration/compatibility risk:
Recommendation strength:
Required approval/routing:
Unknowns:
```

## Evidence requirements

A `STRONG` recommendation requires concrete evidence from code/history/tests/Task Learning/feedback, not taste.

Claims such as "this is hard to maintain" must identify the navigation, duplication, rework, verification, or caller-knowledge burden causing that judgment.

## Rationalizations to reject

- "More interfaces are always cleaner."
- "Every dependency should have an adapter."
- "A small wrapper improves architecture automatically."
- "The agent can navigate many files, so locality does not matter."
- "This module has many lines, so it is deep."
- "Tests need private access, so expose more internals."
- "We should refactor the whole subsystem while we are here."
- "An ADR is old, so it can be ignored."

## Definition of Done

The analysis is scoped to evidence-backed friction, reconstructs the real caller interface, evaluates depth/seam/locality/leverage/testability, respects accepted architecture, ranks recommendations proportionately, and routes any structural change through normal EREI approval and verification rather than treating analysis as authority to refactor.
