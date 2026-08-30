---
name: project-standard-discovery
description: Inspect an existing codebase and durable project artifacts to extract the conventions, boundaries, commands, invariants, and local engineering rules that an agent must follow. Use during brownfield onboarding, after major codebase evolution, or when undocumented project conventions materially affect safe implementation.
---

# Project Standard Discovery

## Objective

Discover project truth from the project itself and produce a compact, routable standards index instead of relying on generic best practices or loading the entire repository into context.

## Trigger when
- onboarding an existing project,
- local conventions are unknown or stale,
- a subsystem has distinct rules,
- major architecture evolution may have invalidated old standards.

## Do not trigger when
- relevant standards are already current and confirmed,
- the task is isolated and project conventions are immaterial.

## Procedure

### 1. Inspect instruction hierarchy
Look for project-local instruction sources such as:
- `AGENTS.md` and nested variants,
- README/development/contributing docs,
- architecture/ADR directories,
- project profile/standards/runbooks,
- CI/build/test configuration.

### 2. Inspect structure and execution
Identify:
- major modules/layers,
- entry points,
- build/test/lint commands,
- deployment/config boundaries,
- generated vs hand-edited files.

### 3. Extract observed conventions
Examples:
- naming/module structure,
- API/error patterns,
- persistence/data-access patterns,
- test conventions,
- state management,
- dependency policy,
- release/versioning practices.

### 4. Separate evidence classes
For each standard mark:
- `EXPLICIT` — stated in authoritative project artifact,
- `OBSERVED_STRONG` — consistently present in code/config,
- `OBSERVED_WEAK` — limited evidence,
- `CONFLICTING` — inconsistent implementations,
- `UNKNOWN`.

Do not silently turn one code example into a project standard.

### 5. Identify invariants and forbidden paths
Capture rules whose violation may cause:
- security boundary break,
- data corruption,
- deployment failure,
- compatibility regression,
- generated-code overwrite.

### 6. Build a routable standards index
Prefer domain/path tags so later workflows can load only relevant standards.

Example:
```text
standard_id: AUTH-001
scope: backend/auth
impact: critical
source: AGENTS.md + auth middleware
status: explicit
summary: authorization is server-side
```

### 7. Surface conflicts
If docs and code disagree, do not choose silently. Record conflict and recommend resolution/ADR where material.

## Required output

```text
Instruction sources:
Architecture map:
Build/test/lint commands:
Explicit standards:
Observed standards:
Critical invariants:
Generated/unsafe-to-edit areas:
Conflicts:
Unknowns:
Standards index created/updated:
Recommended context-routing tags:
```

## Evidence requirements

Every material discovered standard must cite its project source or observed pattern. Weak observations remain labeled weak.

## Rationalizations to reject
- "Most projects use this pattern, so this one probably does too."
- "One file is enough to infer the convention."
- "The README says it, so the current code must still match."
- "Load every discovered standard into every task."

## Definition of Done

The project has a source-backed standards map sufficient for task-aware context routing, with conflicts and uncertainty explicit.