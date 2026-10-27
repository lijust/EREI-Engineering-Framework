# Owner-local Learning V5 enablement (Framework Stage 2, synthetic-only)

V5 is a **different** case-blind prompt strategy based on four *real scored*
V4 regressions. It retains the frozen PR98 target/scorer, compact typed-action
V4 response schema, Gemini 3.5 Flash Lite and private evidence custody.
**It does not prove learning or guarantee uplift.**

## Exact source pins

| Source | Reviewed immutable SHA |
| --- | --- |
| Core13 V2 adapter | `ecfc2818598e4631166bd3dec2774cb8178d0e10` |
| Learning V3 adapter | `bfe43153a137db15e93d8f6e81d145e4bf9ab024` |
| Typed-action V4 | `7bbb44f14ce695ce660270b79a3bf25b4ce193ef` |
| Case-blind policy/state V5 | `2bb9ba94c342f2d86967a2ac214bea62c8734638` |
| Frozen PR98 target/scorer | `31d4e518b9e71a9585df9097e7ca07a7e25af916` |
| Owner bridge | PR114 exact CI + Codex-reviewed final SHA |

## Local setup after reviews of both PR113 and PR114

The same `EREI - Gemini Private Bridge` scheduled task, SQLite claim
journal, DPAPI-protected PAT/API key, `daily_limit=450` and 429 stop
mechanism remain intact. Installing V5 is **not** a model call.

```powershell
cd "$env:USERPROFILE\Desktop\erei-core13-adapter"
git fetch origin core13/learning-state-policy-v5-20261027 core13/gemini-bridge-v5-router-20261027
git worktree add --detach "$env:USERPROFILE\Desktop\erei-core13-learning-v5" 2bb9ba94c342f2d86967a2ac214bea62c8734638
git worktree add --detach "$env:USERPROFILE\Desktop\erei-gemini-bridge-v5" FINAL_REVIEWED_PR114_SHA
cd "$env:USERPROFILE\Desktop\erei-gemini-bridge-v5"
python -m unittest evals.tests.test_github_gemini_bridge -q
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\evals\bridge\windows\enable-learning-v5.ps1"
```

Replace FINAL_REVIEWED_PR114_SHA with the exact final source revision.
The owner-only upgrade script verifies the clean **detached** V5 source,
confirms existing V3/V4 roots, stops and restarts only the private task,
read-only checks all exact pins, and attempts a config/task rollback upon
failure. Never paste any PAT or Gemini API key into chat or GitHub.

Success requires `PRIVATE_V5_BRIDGE_UPGRADE_SUCCESS`,
`V5_SOURCE_AND_QUEUE_HEALTHCHECK_PASS`, `DAILY_LIMIT_UNCHANGED_450`
and `NO_GEMINI_MODEL_CALLS_DURING_UPGRADE`.

## One-request private Issue contract

A private owner-authored GitHub Issue may contain the following exact
allowlisted JSON payload, with title
`EREI-GEMINI TLR-007-REVIEW-NOT-SELF-MODIFICATION`, after installation:

```json
{
  "version": 1,
  "kind": "core13_smoke",
  "case_id": "TLR-007-REVIEW-NOT-SELF-MODIFICATION",
  "model": "gemini-3.5-flash-lite",
  "experiment": "policy_v5",
  "max_calls": 1
}
```

Adding label `erei-gemini-run` triggers a single provider attempt. Do not
enable any request while source is not installed locally; do not auto-bulk
rerun all benchmarks. Start with the four historical V4 failures and check
for unexpected transport/parsing errors before a full 13-case regression.

V4 previously **9/13 PASS, 4/13 FAIL** (scored but not independently
accepted). Stable/independent acceptance remain false. No offline CI run
may invoke Gemini or consume Free Tier.
