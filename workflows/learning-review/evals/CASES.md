# Learning Review Workflow — Eval Cases V1

## LR-001 — Count-based review

State reports `REVIEW_RECOMMENDED` after 20 material tasks.

Expected: review accumulated evidence; do not assume a Framework defect exists.

## LR-002 — Immediate verification escape

State reports `IMMEDIATE_REVIEW` because a previously verified task escaped.

Expected: inspect the escaped evidence promptly and separately re-open/block affected completion/release claims when applicable.

## LR-003 — Three identical feedback fingerprints

Three task events link the same Framework-feedback fingerprint.

Expected: inspect/cluster recurrence, preserve all occurrences, and route through Knowledge Promotion only if evidence supports a generic Framework change.

## LR-004 — Healthy epoch

Forty tasks are mostly clean verified executions with no repeated gap.

Expected: record the healthy pattern and close the review; do not invent changes merely because review was due.

## LR-005 — Mixed Framework refs

The epoch spans a project Framework upgrade.

Expected: segment evidence by exact Framework ref before claiming before/after improvement.

## LR-006 — Project-local root cause

High rework rate is traced to a project-specific undocumented API contract.

Expected: project-local action or feedback about context only if Framework handling plausibly contributed; do not automatically change generic workflows.

## LR-007 — Metrics are noisy

Task classification is inconsistent enough that rework rates cannot be trusted.

Expected: `MEASUREMENT_ADJUSTMENT` / more evidence, not a false Framework optimization.

## LR-008 — Review closure

Evidence review is complete.

Expected: append review record with exact event cutoff; next epoch starts without deleting old events.
