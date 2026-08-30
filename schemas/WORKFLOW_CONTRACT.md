# Workflow Contract

**Status:** Draft V1

## Purpose

A Workflow orchestrates roles, skills, tools, gates, and durable artifacts to achieve an engineering outcome.

A Workflow is not a single role and must not duplicate every skill procedure inline.

## Required fields

1. **Objective** — the outcome the workflow exists to achieve.
2. **Entry conditions** — when the workflow applies.
3. **Risk applicability** — supported/default risk levels.
4. **Required roles** — mandatory engineering perspectives.
5. **Optional roles** — conditionally activated roles.
6. **Required skills** — procedures that must run.
7. **Conditional skills** — activated by impact/risk/context.
8. **Inputs** — project/request/evidence required to start.
9. **Stages** — ordered execution phases.
10. **Gates** — approval, security, data, QA, release checkpoints.
11. **Durable artifacts** — specs, plans, ADRs, reports, evidence, etc.
12. **Convergence rule** — how actual state is compared with intended state.
13. **Stop/block conditions** — conditions that halt progress.
14. **Rollback/exit behavior** — required when workflow changes durable state.
15. **Definition of Done**.

## Workflow design principles

- Rigor scales with risk.
- Low-risk work may use explicitly defined abbreviated paths.
- Required gates may not be silently skipped.
- The same workflow may activate different roles/skills depending on impact analysis.
- Workflows should produce durable evidence, not only conversational summaries.
- Security/data vetoes outrank normal completion.
- Convergence is required for material implementation workflows.

## Default material-change lifecycle

```text
Request
  ↓
Risk + Impact Analysis
  ↓
Requirement / Spec
  ↓
Plan
  ↓
Implementation
  ↓
Requirement Compliance Review
  ↓
Engineering Quality Review
  ↓
Conditional Security/Data/Performance Review
  ↓
Verification
  ↓
Convergence
  ↓
Release Decision
```

## Change control

Workflow changes that alter approval gates, security behavior, release rules, or risk handling are architectural changes and require explicit review.