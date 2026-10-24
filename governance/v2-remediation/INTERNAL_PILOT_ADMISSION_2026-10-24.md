# T14 — proposed isolated Internal pilot admission (2026-10-24)

**Current decision: HOLD / NOT ADMITTED.** This is a narrow candidate scope
derived from the existing `MASTER_PLAN.md §5` checklist; it does **not**
install a new governance service or create a Stable release gate. No actual
Internal pilot was executed or approved in preparing this document.

## Smallest viable pilot

- **Purpose:** demonstrate Task Learning V2 behavior and rollback on a
  fixed, synthetic, isolated read-only fixture. **No real EREI/SAE-DB data**.
- **Reference:** protected `main` at `c4a3f0caaf81430c8ff1f3b09fefd50d821f8300`
  is a historical comparison anchor, **not automatically the pilot target**.
- **Candidate:** T14 isolated rollback PR #94 at
  `8b067b57edfa671f70caa90d9fc03862ded70885` is **unmerged and
  awaiting independent review**. Assemble/freeze one new aggregate
  target SHA/tree after scope-specific reviews; do not claim the two source
  refs above form a tested aggregate.
- **Allowed operations:** read-only source evaluation; deterministic synthetic
  scenario replay; temp-directory code/data rollback drill retaining pre-
  and post-restore evidence. No producer pin changes.
- **Disallowed:** production writes, live Sheets/SQLite ledgers, app secrets,
  privileged GH tokens, new workflow dispatch/publish, untrusted PR execution
  with write credentials, paid AI/model runs or release/activation.
- **Duration and user count:** one time-boxed operator-controlled trial,
  **zero external users**. Exact time window to be admitted by owner.

## Scope-specific admission checks (ALL required before running pilot)

| Checklist item from existing plan | Status now | Required evidence |
|---|---|---|
| §5 aggregate source SHA/tree frozen | **MISSING** | Exact target+tree, combined source hashes, exact per-workflow digest |
| V1 golden fixtures/review epochs | **PARTIAL** | Passing unchanged real fixtures at same target, no historical ledger rewrites |
| Planner and App quarantine | **PARTIAL** | Valid synthetic planner output; App contradicted live data still `BLOCKED` |
| Candidate activation fail-closed | **REQUIRES REVIEW** | Explicit deny-before-mutation on declared synthetic target |
| Behavioral scorer contradictory examples | **SOURCE GREEN ONLY** | Target-bound scorer output; do not confuse reference-oracle synthetic and actual models |
| Windows 3.11/3.12 and finite metrics | **SOURCE GREEN ONLY** | Fresh target-bound CI, clear Linux/POSIX evidence limits |
| T14 rollback code **and isolated data** | **SYNTHETIC DRILL ONLY** | Authorized operator runs/certifies rollback against same aggregate target; preserve V2 archive |
| Reviewer P1 disposition affecting scope | **PENDING** | Independent SHA-bound decision for originally open #84/#86/#88 threads and any target-specific findings |
| Named operator, owner, rollback custodian | **MISSING** | Actual identities, granted permissions, command logs with private details segregated |
| Scope/time/data approval | **MISSING** | Explicit authorization record limiting synthetic data, duration and participant access |

**T11 / Stable:** protected `main` and required unfiltered `assurance` are
already active, but genuine release workflow source trust and independent
consumer acceptance are not proven. Do **not** redo ruleset setup. The
complete Stable T11 approval chain is **not** a prerequisite for this
synthetic/no-production Internal proposal; independent scope-specific
safety approval **is** required. A full 12-task benchmark does **not**
gate this isolated read-only pilot.

## Admission record — deliberately unapproved

| Required signoff | Value |
|---|---|
| Aggregate target SHA/tree | **UNSET** |
| Operator | **UNASSIGNED** |
| Independent security reviewer | **UNASSIGNED** |
| Independent architecture reviewer | **UNASSIGNED** |
| Rollback custodian | **UNASSIGNED** |
| Approved synthetic input digest | **UNSET** |
| Timebox | **UNSET** |
| Decision | **HOLD_NOT_ADMITTED** |
| Source actions/production writes | **NONE AUTHORIZED** |

Before starting, the owner/reviewers must provide an explicit admission
for that precise target. A future `PASS` must report its **synthetic scope,
observed fail-closed decisions, time, rollback recovery, pre/post source
hashes and residual risks**. It cannot be relabeled "Stable" or count as
the 13 exact-target Task Learning V2 Core runtime evaluations or the 48
V1/V2 model benchmark slots.

See also [MASTER_PLAN §5](MASTER_PLAN.md), [T14 issue #81](https://github.com/lijust/EREI-Engineering-Framework/issues/81),
[T11 issue #78](https://github.com/lijust/EREI-Engineering-Framework/issues/78)
and [independent review decision requests](evidence/independent-review-disposition-requests-20261024.md).
