# Skill Contract

**Status:** Draft V1

## Purpose

A Skill is a reusable engineering procedure that can be invoked by one or more roles and composed inside workflows.

A Skill is not a persona, project memory store, or generic knowledge dump.

## Standard structure

Substantial skills should use:

```text
skill-name/
├── SKILL.md
├── SPEC.md
├── SOURCES.md          optional
├── references/         optional
├── scripts/            optional
├── evals/              recommended
└── fixtures/           optional
```

## SKILL.md required sections

1. Name and concise description.
2. Trigger conditions.
3. Should-not-trigger conditions.
4. Required inputs/context.
5. Preconditions.
6. Procedure.
7. Evidence requirements.
8. Required outputs.
9. Stop/escalation conditions.
10. Rationalizations to reject where risk warrants it.
11. References/scripts that may be loaded.
12. Definition of Done for the procedure.

## SPEC.md required sections

1. Purpose and design intent.
2. Scope and non-scope.
3. Why the skill exists.
4. Risks and failure modes.
5. Evidence model.
6. Evaluation strategy.
7. Maintenance/currentness expectations.
8. Compatibility/portability constraints.
9. External provenance or licensing concerns when applicable.

## Design rules

- Follow progressive disclosure: do not inline large references unnecessarily.
- Prefer deterministic scripts/tools for reproducible checks.
- Keep technology-specific rules in overlays unless universally applicable.
- Keep project-specific rules in project repositories.
- High-risk skills must be more prescriptive than low-risk exploratory skills.
- Avoid duplicate skills with overlapping triggers; clarify routing instead.
- A skill must not claim completion without its required evidence.

## Evaluation requirements

At minimum, important skills should have:

### Trigger evals
- should trigger
- should not trigger
- ambiguous cases

### Behavior evals
- required steps followed
- evidence collected
- unsafe shortcuts rejected
- stop conditions respected

### Regression evals
Every material previously observed skill failure should become an eval where practical.

## Promotion rule

A project-local procedure becomes Framework Core only after project assumptions are removed, provenance/security reviewed, and reusable value is evidenced.