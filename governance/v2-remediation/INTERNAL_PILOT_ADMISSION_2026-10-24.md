# T14 — proposed isolated Internal pilot admission (2026-10-24)

## Latest owner exception outcome — 2026-10-25

**Status: SYNTHETIC_INTERNAL_CI_PILOT_PASS_WITH_LIMITS; production/broader Internal Release NOT ADMITTED; Stable BLOCKED.** After user-approved **dual AI review channels + owner risk acceptance** (below), [explicit ADMIT_SYNTHETIC_CI_ONLY](https://github.com/lijust/EREI-Engineering-Framework/issues/81#issuecomment-6392059800) was issued **before** fresh GitHub-hosted CI reruns. [T14 outcome](https://github.com/lijust/EREI-Engineering-Framework/issues/81#issuecomment-6392081972) details post-decision **Python 3.11 attempt 2** and **Python 3.12 attempt 3**, both `4/4 PASS`, on frozen source SHA `31d4e518b9e71a9585df9097e7ca07a7e25af916` / tree `913c6a0daaa7a6efa7d6d2148aa0294812fab360`; same fixture SHA256 `72de745e67512575615ded69a7276f6764ee3bbaecc4e60c3b788edc1b9ac4f8`.

| Execution receipt | Hosted evidence | Accepted synthetic scope |
| --- | --- | --- |
| 3.11 post-admission | [GitHub artifact #12583091131](https://github.com/lijust/EREI-Engineering-Framework/actions/runs/40149707722/artifacts/12583091131) | Exit 0, 4/4, no errors/failures, raw report/hash verified |
| 3.12 post-admission | [GitHub artifact #12582791665](https://github.com/lijust/EREI-Engineering-Framework/actions/runs/40149707722/artifacts/12582791665) | Exit 0, 4/4, no errors/failures, raw report/hash verified |
| Review channels | GitHub Codex + GPT-6 [scoped source review](https://github.com/lijust/EREI-Engineering-Framework/pull/98#issuecomment-6392043597) | AI-only, **not** independent-human or other-provider review |
| Owner risk | [Decision record](https://github.com/lijust/EREI-Engineering-Framework/issues/81#issuecomment-6392059800) | 15-minute per job limit, only ephemeral synthetic data, zero external users, no privileges or production actions |

The raw drill JSON deliberately retains `internal_release_qualified=false`, `live_adoption=false`, `fixture_approved_by_independent_reviewer=false`. **Do not rewrite or override** these source fields: the governance verdict above qualifies only **this user-approved synthetic CI rehearsal**, not a software/adoption release, human security signoff, real App restoration or a release of Stable. Original review threads are kept open. Artifacts have **14-day retention**; archival custody beyond expiry is **not proven**. Original App missing ledger provenance and Core runtime 0/13 and V1/V2 0/48 remain blocked.

**This file is a documentation-only update on stacked PR #99.** It does **not** modify the frozen tested branch/source in PR #98. To stage any subsequent pilot, separately authorize its scope; do not reuse this verdict across different SHA/tree/data or retroactively promote previous CI.

---

### Historical 2026-10-24 hold record (not the latest narrow synthetic CI outcome)

**Current decision: HOLD / NOT ADMITTED.** This is a narrow candidate scope
derived from the existing `MASTER_PLAN.md §5` checklist; it does **not**
install a new governance service or create a Stable release gate. No actual
Internal pilot was executed or approved in preparing this document.

## Update 2026-10-25 — APPROVED exception: two AI review channels plus owner risk acceptance (synthetic Internal ONLY)

**Owner decision:** The owner explicitly approved replacing the *human independent reviewers for a tightly isolated synthetic-only Internal trial* with multiple AI reviews and owner risk acceptance. The authorization has **no effect on Stable**, on real consumer/prod data, or on original P1 review history. The [program master-plan §5](MASTER_PLAN.md#5-internal-release-أقل-نطاق-مفيد-وآمن) has been updated in the same documentation-only PR; the former strict independent human signoff remains the **default**. Where older sections below say independent human review is required for Internal, this approved alternate lane takes priority **only for the exact synthetic scope** below.

| Alternative admission element | Status and precise provenance |
| --- | --- |
| **Owner acceptance of substitute review procedure** | **APPROVED in conversation 2026-10-25**, explicitly limited to Synthetic Internal; not signed independent human approval |
| **AI channel A** | GitHub Codex PR #98 bot review **on SHA 31d4e518b9e71a9585df9097e7ca07a7e25af916**: no major issues reported; model identity/provider independence not assured |
| **AI channel B** | GPT-6 separate source-and-test review [on PR #98](https://github.com/lijust/EREI-Engineering-Framework/pull/98#issuecomment-6392043597) same exact source: `ACCEPT_WITH_EXPLICIT_LIMITS_SYNTHETIC_CI_ONLY`; not an independent human |
| **Original P1 #84/#86/#88** | Source fixes and protective denial verified within specific synthetic scope by Channel B; historical App ledger restoration remains **blocked**. Threads remain open for Stable/real consumers; no automatic resolution |
| **Other source issues #91/#94/#95/#98** | Combined-source failure/denial plus exact-head tests verified by CI; no positive release authority or Independent calibration accepted |
| **Owner residual-risk exception** | **APPROVED FOR SYNTHETIC CI ONLY:** AI-only review limitations, GitHub artifacts expire in 14 days, fixture clock intentionally mocked, no disk-full/power-loss/concurrent writer simulation, inherited Git environment hazard outside trusted hosted runner, no real consumer recovery, no model-efficacy proof. Any emerging P0/P1 affecting this synthetic scope must block |
| **Release scope** | **EXCLUDED:** Stable, paid model trials, production or real consumer deployment, GitHub/settings changes, project pins, secrets, external users, ledger/app data writes, grants of security authority |
| **Frozen target** | Source HEAD `31d4e518b9e71a9585df9097e7ca07a7e25af916`; Git tree `913c6a0daaa7a6efa7d6d2148aa0294812fab360` |
| **Frozen fixture SHA-256** | `72de745e67512575615ded69a7276f6764ee3bbaecc4e60c3b788edc1b9ac4f8` (pre-mutation inputs; 3.11 and 3.12 agree) |
| **Operational operator** | GitHub-hosted Windows read-only PR98 workflow under `lijust` owner control; no persistent personal runner, no project data or secrets. Owner accountable for scope and stopping |
| **Rollback technical custodian** | T14 ephemeral test runner: creates baseline and V2 archive in temp paths; verifies complete restore, preserves V2 history and outstanding `IMMEDIATE_REVIEW` during test; artifacts retained in GitHub Actions 14 days. **No independent third-party archive custodian is claimed** |
| **Timebox / users** | Max **15 minutes** for each admitted workflow job, **zero external users**. Jobs with timeout and fail-closed. No whole-project cutover |
| **Mandatory final gate** | **An explicit new owner `ADMIT_SYNTHETIC_CI_ONLY` decision tied to the exact SHA/tree/fixture before a NEW CI run.** A newly executed exact-head synthetic T14 proof after this decision may establish the limited Internal synthetic pilot's results; earlier CI cannot be backdated/relabelled. |
| **Stable gate** | **UNCHANGED BLOCKED** — requires genuine human independent security/architecture reviews and exact-target Core V2 and V1/V2 comparisons under existing release approvals |

**Immediate current status at documentation update:** `ALTERNATE_REVIEW_PATH_APPROVED / TWO_AI_CHANNELS_DOCUMENTED / OWNER_RISK_ACCEPTED_FOR_SYNTHETIC_ONLY / PRE_ADMISSION_EVIDENCE_GREEN`. **No claimed prior Internal pilot.** When the specific admission and a new run are recorded, the verdict must distinguish `SYNTHETIC_INTERNAL_PILOT_PASS` from `Stable_READY` or operational rollout. This is not a new governance system.

---

## Owner-scoped admission decision — 2026-10-25 (REVIEW RECORD ONLY)

**Status: OWNER_SCOPE_APPROVED / NOT_ADMITTED.** The repository owner explicitly instructed that bounded decisions, approval and authorization proceed. The scope was recorded in the existing [T14 issue #81](https://github.com/lijust/EREI-Engineering-Framework/issues/81#issuecomment-6391909606), not as a qualified independent security or architecture signoff. **This document update is on a separate review-only documentation branch; it does not modify the already-tested source, SHA, tree or fixtures of candidate PR #98.** No protected-main merge or real Internal pilot launch is authorized.

| Admission field | Current verified/proposed value | Approval boundary |
| --- | --- | --- |
| **Frozen source candidate** | `31d4e518b9e71a9585df9097e7ca07a7e25af916` | Owner-selected, pending independent source disposition |
| **Candidate Git tree** | `913c6a0daaa7a6efa7d6d2148aa0294812fab360` | Matched to GitHub PR merge checkout; SHA/tree changes require new evidence |
| **Exact synthetic fixture SHA256** | `72de745e67512575615ded69a7276f6764ee3bbaecc4e60c3b788edc1b9ac4f8` | Owner-selected for review; not yet independently approved |
| **Verified implementation** | PR #98 source-only composite of T10 deny, T14 rollback and T15 calibration | No consumer/pin or production deployment |
| **Operator / owner** | `lijust` is repository owner and **proposed synthetic operator** | Authenticated independent operational acknowledgement not present |
| **Security reviewer** | `UNASSIGNED` | Independent signed `ACCEPT / REJECT / FIX_REQUIRED` **required** |
| **Architecture reviewer** | `UNASSIGNED` | Independent SHA-bound verdict **required** |
| **Rollback custodian** | `UNASSIGNED` | Must confirm archive isolation, authority, retention and restoration |
| **Proposed maximum timebox** | **15 minutes**, counted from a future expressly admitted start | **Owner-approved limit only; no pilot execution permitted yet** |
| **Participants / data** | Zero external users; only ephemeral synthetic fixtures on hosted Windows | No EREI/SAE-DB real data, secrets, SQLite/Sheets or external consumers |
| **Operations expressly denied** | Paid model calls; production writes; project pins; privileged tokens; GitHub settings; publish/merge; consumer workflows | No implied exception |
| **Automatic stop** | Any checkout/hash/fixture mismatch, P1 blocker, denied activation bypass, data change, missing capture/artifact, failed rollback, timebox expiry | Fail closed, preserve independent artifacts, never silently promote |
| **Technical evidence** | [T14 #40149707722](https://github.com/lijust/EREI-Engineering-Framework/actions/runs/40149707722) 4/4 per Python 3.11/3.12 with matching fixture digest; [Assurance #40149707727](https://github.com/lijust/EREI-Engineering-Framework/actions/runs/40149707727), [Evals #40149707726](https://github.com/lijust/EREI-Engineering-Framework/actions/runs/40149707726), [Bootstrap #40149707766](https://github.com/lijust/EREI-Engineering-Framework/actions/runs/40149707766) PASS | **Pre-admission source/fixture diagnostics, not formally admitted Internal** |
| **Required pre-admission decisions** | Original P1 #84/#86/#88; T10 #91, T14 #94, T15 #95, combined #98; explicit independent security/architecture acceptance | **OPEN; no reviewer signature invented** |
| **Exact-target Core / V1-V2 models** | 0/13 and 0/48 respectively | Separate **Stable** work; not itself narrow synthetic Internal gating |
| **Formal admission decision** | **HOLD_NOT_ADMITTED** | Must change only after independent signoffs and explicit SHA-bound owner `ADMIT` |

### Executable evidence already recorded without an admitted pilot

The hosted synthetic T14 replay checked immutable V1 source, rejected pin-only rollback,
preserved the V2 archive and pending `IMMEDIATE_REVIEW`, and separately restored V1
baseline content in isolated temporary directories. Each Windows Python 3.11/3.12
four-case fixture reported the **same** SHA256. Artifacts are retained for 14 days,
not a permanent independent archive. The source-only evidence does **not** prove
production or real consumer rollback, power-loss/data-corruption recovery, external
archive custody, or independent authorization.

### Authorized actions versus release authority

**Allowed now:** examine original reviewer findings, create SHA-bound independent
review requests, inspect and archive public synthetic receipts, maintain this
review-only admission record, and repeat **read-only synthetic pre-admission
diagnostics** when required on the frozen source, without credentials or private
data. **Not allowed now:** mark independent reviews approved on the owner's behalf,
resolve their review threads without qualified reviewer decision, invoke paid AI,
deploy to any consumer, change framework pins or ledger history, merge into protected
main, or relabel previous hosted diagnostics as the formally admitted Internal pilot.

**Owner authorization alone is not the qualified independent acceptance required
by §5.** A future admission must state separate human/authorized security and
architecture decisions, operator/custodian acceptance and approved exact fixture,
then `ADMIT` the **same** SHA/tree. If any version changes, re-evaluate relevant
evidence before launch.

---

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

## Historical unapproved admission record — 2026-10-24 (superseded by conditional owner-scoped record above)

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
