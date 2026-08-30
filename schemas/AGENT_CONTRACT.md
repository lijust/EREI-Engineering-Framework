# Agent Contract

**Status:** Draft V1

## Purpose

An Agent is an engineering role: a perspective, accountability boundary, and decision responsibility. It is not a reusable procedure and must not become a giant catch-all prompt.

## Required fields

Every agent definition must specify:

1. **Mission** — what engineering responsibility the role owns.
2. **Authority** — decisions it may make autonomously.
3. **Escalation boundaries** — decisions requiring approval or another role.
4. **Inputs** — minimum context required.
5. **Responsibilities** — what the role must inspect or protect.
6. **Non-responsibilities** — what it must not own alone.
7. **Applicable skills** — reusable procedures the role may invoke.
8. **Required collaborators** — roles required for specific change classes.
9. **Evidence obligations** — what must support material conclusions.
10. **Output contract** — required shape of findings/decisions.
11. **Stop conditions** — when work must pause/escalate/block release.
12. **Anti-patterns** — common role failures to avoid.

## Behavioral rules

- An agent must obey the Engineering Constitution.
- Role expertise does not override project truth.
- A role should not duplicate procedural detail already owned by a Skill.
- A role must identify uncertainty rather than invent missing project facts.
- A role must not silently lower risk classification to simplify execution.
- Critical reviews should prefer independent/fresh context where practical.

## Minimum output for material decisions

- Decision or recommendation.
- Affected layers.
- Risk level.
- Evidence basis.
- Assumptions/unknowns.
- Blocking issues.
- Required follow-up or approvals.

## Versioning

Agent definitions are framework artifacts and should be versioned. Behavior-changing updates require regression evaluation appropriate to impact.