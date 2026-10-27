# Owner-local Gemini Bridge V4 (schema-only experiment)

## No provider call from CI / GitHub

This optional bridge extends the existing V2/V3 worker. Only locally
SHA-pinned reviewed source can send the private synthetic request.

- V2 source pinned: `ecfc2818598e4631166bd3dec2774cb8178d0e10`.
- V3 source pinned: `bfe43153a137db15e93d8f6e81d145e4bf9ab024`.
- V4 source pinned: `7bbb44f14ce695ce660270b79a3bf25b4ce193ef`
  (PR110 compact typed-action anyOf schema; **only if CI and Codex pass**).
- Frozen evaluator: `31d4e518b9e71a9585df9097e7ca07a7e25af916`.
- Same PRIVATE `lijust/EREI-Gemini-Control` repository, same
  `erei-gemini-run` label, same SQLite journal and **one attempt/day UTC**
  owner-configured quota across V2/V3/V4. No credential changes.

## Owner commands AFTER independent source reviews pass

On Windows PowerShell, source base worktree already present under Desktop:

```powershell
cd "$env:userprofile\desktop\erei-core13-adapter"
git fetch origin core13/learning-action-schema-v4-20261027 core13/gemini-bridge-v4-router-20261027
git worktree add --detach "$env:userprofile\desktop\erei-core13-learning-v4" 7bbb44f14ce695ce660270b79a3bf25b4ce193ef
git worktree add --detach "$env:userprofile\desktop\erei-gemini-bridge-v4" FINAL_REVIEWED_V4_BRIDGE_SHA
cd "$env:userprofile\desktop\erei-gemini-bridge-v4"
python -m unittest evals.tests.test_github_gemini_bridge -v
powershell.exe -noprofile -executionpolicy bypass -file ".\evals\bridge\windows\enable-learning-v4.ps1"
```

Replace `FINAL_REVIEWED_V4_BRIDGE_SHA` with exact final reviewed PR111
head. This does not call Gemini. The upgrade script fails closed when
V3 is not already enabled and checks only exact V4 worktree commit SHA.
It stops/restarts **only** the private bridge scheduled task, keeps the
original local DPAPI secrets, V2/V3 worktrees, SQLite budget and receipts,
and rolls back config/task action on failure.

## Synthetic request format (no arbitrary prompt or source override)

Create an owner-authored PRIVATE Issue with title
`EREI-GEMINI TLR-003-VERIFICATION-ESCAPE`; add label
`erei-gemini-run` only AFTER local healthcheck shows `v4_enabled:true`
and an owner-checked UTC quota is available.

```json
{
  "version": 1,
  "kind": "core13_smoke",
  "case_id": "TLR-003-VERIFICATION-ESCAPE",
  "model": "gemini-3.5-flash-lite",
  "experiment": "action_v4",
  "max_calls": 1
}
```

Provider raw and scorer details remain locally saved. Only sanitized
scored/failed status and token count are posted back. Do not run a
repeated TLR-003 response as evidence of generalizable learning; V4 first
tests only whether Gemini accepts the `anyOf` schema and produces a
complete action object. A Google HTTP 400, schema failure or wrong policy
response remains a failure, never a synthetic PASS.

**Stage status:** `stable_ready=false`, `independently_accepted=false`.
