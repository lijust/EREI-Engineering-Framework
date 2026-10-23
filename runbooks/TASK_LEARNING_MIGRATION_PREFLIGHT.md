# Task Learning migration preflight

Use `python -B tools/plan_task_learning_migration.py --target <project>` to inspect historical prospective evidence before a separately approved migration. The command prints JSON to stdout and does not create authority, rebuild projections, update pins, or write project files. There is no apply mode.

- `REVIEW_REQUIRED`: valid projection-only V2 records need reviewed immutable imports.
- `NO_IMPORT_REQUIRED`: no missing V2 authority was found in the inspected inputs.
- `BLOCKED` (exit 2): malformed evidence, conflicting identities, fingerprint failures, invalid review membership, ambiguous historical ordering, or concurrent changes prevent a safe plan. No proposed writes are returned.

The report binds the raw framework manifest and event/review ledgers with SHA256 and Git blob SHA1, plus the complete learning-ledger generation. Proposed immutable file digests use the existing JSON writer's serialization and native newline convention, recorded in `proposed_file_newline`; rerun the planner on the actual migration platform before import. Legacy review memberships are resolved from the original ledger positions, never sorted occurrence IDs.

Retain the original bytes and repository commit independently. Review every anomaly against its historical source; do not rewrite old fingerprints or grandfather invalid identities just to obtain a passing plan. If a V1 positional review covered mixed V1/V2 evidence and its original order is missing, restore that order from retained history first.

A later migration needs separate authorization, exact source-digest rechecks, a backup/rollback path, non-overwriting creation of immutable records, and before/after identity and review-membership checks. This preflight does not implement or authorize that migration. Consumer ledgers and Framework pins remain unchanged.

