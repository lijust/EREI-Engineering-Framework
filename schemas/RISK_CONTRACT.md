# Risk Contract

**Status:** Draft V1

## Purpose

Risk classification determines the minimum engineering rigor, review depth, approval gates, and evidence required for a change.

## Levels

### L0 — Cosmetic / isolated
Examples: copy, styling, non-functional presentation changes.

Default handling:
- Minimal workflow.
- Local verification.
- No architecture approval unless scope unexpectedly expands.

### L1 — Normal local change
Examples: ordinary feature behavior confined to one layer, low-impact bug fix.

Default handling:
- Targeted impact analysis.
- Relevant tests/verification.
- Normal engineering review where useful.

### L2 — Cross-layer change
Examples: frontend + backend contract change, new shared data flow, performance-sensitive interaction.

Default handling:
- Explicit impact analysis.
- Multi-role review as applicable.
- Requirement compliance + engineering quality review.
- Regression evidence.

### L3 — Architecture / security / data boundary change
Examples: authentication, authorization, tenant isolation, schema migration, new service boundary, major dependency/platform decision.

Default handling:
- Explicit approval for structural decision.
- Architecture review.
- Threat/data integrity analysis as applicable.
- Independent review.
- Strong verification evidence.
- Rollback/compatibility plan when state is changed.

### L4 — Production-critical / destructive / irreversible
Examples: destructive migration, high-blast-radius production operation, irreversible state transformation.

Default handling:
- Explicit approval required.
- Strongest applicable deterministic and runtime verification.
- Backup/rollback or explicit irreversibility acknowledgement.
- Independent critical review.
- Execution checkpoints and post-change verification.

## Classification factors

Risk is raised by any of the following:
- broader blast radius,
- multiple architectural layers,
- user or tenant boundary impact,
- data mutation or migration,
- security-control impact,
- difficult rollback,
- production criticality,
- concurrency or consistency complexity,
- new external dependency/service,
- uncertain current-state understanding,
- insufficient test coverage,
- performance sensitivity at scale.

## Rules

1. Risk may be raised by any applicable engineering role.
2. Risk must not be lowered merely to avoid process cost.
3. The Chief Engineer owns final routing classification, subject to security/data veto.
4. New facts discovered during implementation may reclassify the task upward.
5. A workflow may define stricter handling than this baseline.
6. Project-specific risk rules may add constraints but may not weaken constitutional requirements without explicit approved exception.

## Required risk record for L2+

```text
Risk level:
Affected layers:
Blast radius:
Security impact:
Data impact:
Rollback difficulty:
Performance/scale impact:
Unknowns:
Required roles/skills:
Required gates:
```