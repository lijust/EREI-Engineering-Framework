# EREI Gemini Bridge — Learning V3 Opt-in Upgrade (26 Oct 2026)

**Scope:** source-only opt-in upgrade, owner-run Windows Task Scheduler activation. No
remote shell, arbitrary GitHub command, provider prompts, secrets in GitHub,
or Gemini calls from CI. Original V2 worker and task remain untouched until
the owner runs the upgrade script locally.

## Immutable identity and controls

| Component | Exact required revision |
| --- | --- |
| Old V2 adapter / compact schema | `ecfc2818598e4631166bd3dec2774cb8178d0e10` |
| New Learning V3 adapter | `bfe43153a137db15e93d8f6e81d145e4bf9ab024` |
| Frozen PR98 target + scorer | `31d4e518b9e71a9585df9097e7ca07a7e25af916` |
| New bridge source | Exact reviewed/CI-green PR108 HEAD, detached clean checkout |
| Private queue | `lijust/EREI-Gemini-Control`, label `erei-gemini-run` |

The owner currently configured **1 model attempt per UTC day**. The upgrade
preserves the **same SQLite journal, quota, state and evidence roots**; V2/V3
attempts consume the **same limit**. The initial V2 Issue #3 has already used
one attempt on 26 Oct UTC; do not queue a live V3 case until the owner checks
local UTC-day capacity and explicitly opts in.

## Upgrade (only after PR108 Code Review and Assurance succeed)

On the Windows owner machine, from the preexisting
`Desktop/erei-core13-adapter` repository, fetch the two exact revisions
in a real Git worktree. Avoid modifying the existing source roots:

```powershell
cd "$env:userprofile\desktop\erei-core13-adapter"
git fetch origin core13/learning-contract-v3-20261026 core13/gemini-bridge-v3-router-20261026
git worktree add --detach "$env:userprofile\desktop\erei-core13-learning-v3" bfe43153a137db15e93d8f6e81d145e4bf9ab024
git worktree add --detach "$env:userprofile\desktop\erei-gemini-bridge-v3" REVIEWED_PR108_SHA
cd "$env:userprofile\desktop\erei-gemini-bridge-v3"
python -m unittest evals.tests.test_github_gemini_bridge -v
powershell.exe -noprofile -executionpolicy bypass -file ".\evals\bridge\windows\enable-learning-v3.ps1"
```

Replace `REVIEWED_PR108_SHA` with the exact final green PR108 SHA. The script
preserves the preexisting encrypted PAT and Gemini key, stops **only**
`EREI - Gemini Private Bridge`, adds the local SHA-pinned V3 root to the
owner's JSON config, verifies the queue/PR105/PR107/PR98 pins without a model
call, changes **only this task's executable path**, then starts it.
Failure triggers a config/task-action rollback and restores the old task when
possible. Do not copy or paste credential values.

The read-only healthcheck should include `v3_enabled: true`, and the script
should finish with `PRIVATE_V3_BRIDGE_UPGRADE_SUCCESS`,
`DAILY_LIMIT_UNCHANGED_1`, `NO_GEMINI_MODEL_CALLS_DURING_UPGRADE`.

## Strict GitHub issue format

A Core13 V3 request uses the same owner-authored private repository and
`erei-gemini-run` label, and the exact following allowlisted JSON shape
(no paths, commands, model overrides or arbitrary prompts):

```json
{
  "version": 1,
  "kind": "core13_smoke",
  "case_id": "TLR-003-VERIFICATION-ESCAPE",
  "model": "gemini-3.5-flash-lite",
  "experiment": "learning_v3",
  "max_calls": 1
}
```

Issue title is `EREI-GEMINI TLR-003-VERIFICATION-ESCAPE`.
The private owner-local worker will compare the actual V3 checkout against
the exact Git SHA and pinned source blobs, compare the frozen target SHA,
reserve the shared UTC-day SQLite budget **before** any model HTTP request,
then make a single provider call and write its raw receipt **locally**.
Only the fixed allowlisted result/usage summary is posted back to GitHub.

The earlier V2 Issue #3 is independently observed a **scored PASS**, but that
case was already a historical baseline pass; no V3 improvement is established.

## Strict release limits

Do not merge PR108, change the frozen scorer/cases, raise daily budget, claim
Stable, or run private production data. This upgrade is synthetic/internal
experimental only. No actual V3 model call has been made by this PR.
If task state is Running but V3 healthcheck fails, stop this dedicated task
and diagnose locally; do not keep a mixed-version worker claiming jobs.

The Learning V3 behavioral sequence remains:
(1) four historically failing cases → (2) whole Core13 13-case regression
→ (3) unseen transfer/adversarial cases → (4) independent acceptance.
A single success never proves a learning improvement across the suite.
