# EREI Gemini Private Execution Bridge — controlled Windows local broker

**Status:** code and mock-only tests in draft PR; **NOT deployed to owner's PC**.
No GitHub Actions runner, no remote shell, no online test calls, no change to
frozen PR98/Core13 suite or existing baseline. Install requires a one-time
**owner-controlled local action**. ChatGPT has connected GitHub Issues access,
but **cannot directly access** owner Windows process or local Gemini key.

## Why this design

Public `lijust/EREI-Engineering-Framework` must NEVER receive Gemini keys,
raw provider receipts, original user data or an execution-ready public Actions
dispatch. Use a *dedicated private GitHub repository* to carry only synthetic
test-control envelopes and small redacted results.

The broker polls GitHub **Issues**, strictly verifies repo `private=true`
on every poll, owner login `lijust`, required label `erei-gemini-run`,
fixed title, JSON-only payload schema, exact pinned Gemini model, and the
two pinned local code/target revisions.

Accepted issue payload (body must be **raw JSON**, not a markdown code fence):

```json
{
  "version": 1,
  "kind": "core13_smoke",
  "case_id": "TLR-003-VERIFICATION-ESCAPE",
  "model": "gemini-3.5-flash-lite",
  "experiment": "compact_v2",
  "max_calls": 1
}
```

Exact issue title: `EREI-GEMINI TLR-003-VERIFICATION-ESCAPE`.
GitHub issue label: `erei-gemini-run`.
Only known frozen Core13 IDs are accepted. The broker never executes any
command string, arbitrary prompt, issue-linked URL, script, changed model
ID, custom target, or user-supplied output directory.

## One-time owner setup — Windows

### A. Create a PRIVATE GitHub queue

Create a **new private** repository e.g. `lijust/EREI-Gemini-Control`,
enable Issues, and create label `erei-gemini-run`. Leave it private. Grant
ChatGPT's connected GitHub app access to this repo as required by GitHub app
installation scope. Do **not** use the public Framework repository as queue.

Generate a **fine-grained PAT** scoped only to the new private queue repo:
- Metadata **Read** (GitHub default).
- Issues **Read and Write** (poll, comment, close).
- No Contents, Actions, Workflows, or Administration permissions.
- Set an expiration and rotate it under owner control.

Use the already tested **Gemini Free-tier** key from the owner's selected
AI Studio project. Never paste either key into the chat.

### B. From the existing `erei-core13-adapter` checkout

Fetch the bridge PR feature branch and create a SEPARATE clean worktree
pinned to the tested exact bridge commit (supplied in PR). Do not replace
existing `erei-core13-schema-compact-v2`, `erei-core13-target`, or
original evidence directories.

```powershell
cd "$env:userprofile\desktop\erei-core13-adapter"
git fetch origin core13/gemini-github-bridge-20261026
git worktree add --detach "$env:userprofile\desktop\erei-gemini-bridge" <reviewed-bridge-commit-sha>
cd "$env:userprofile\desktop\erei-gemini-bridge"
python -m unittest evals.tests.test_github_gemini_bridge -v
```

### C. Run ONE setup command

```powershell
powershell.exe -noprofile -executionpolicy bypass -file ".\evals\bridge\windows\install-gemini-bridge.ps1" -queue_repo "lijust/EREI-Gemini-Control" -daily_limit 3
```

Setup asks once for the fine-grained GitHub token and Gemini API key,
encrypts both in files under
`%LOCALAPPDATA%\EREI\GeminiBridge` using **Windows user-scoped DPAPI**,
writes non-secret local settings, and runs a **read-only healthcheck** that
verifies private repo + immutable Git SHA. Only after healthcheck succeeds
does it install/start a **current-user Scheduled Task at Windows logon**.

The worker remains active while the Windows desktop is locked as long as the
user session remains logged in, the device stays awake and the network works.
The current-user scheduled task is NOT a guarantee that it runs while logged
out, asleep or hibernated. No GitHub Actions minutes are used to execute
Gemini. The owner may need task registration rights enabled by Windows policy.

After setup, view locally (without any model request):

```powershell
get-scheduledtask -taskname "EREI - Gemini Private Bridge"
powershell.exe -noprofile -executionpolicy bypass -file ".\evals\bridge\windows\start-gemini-bridge.ps1" -healthcheck
```

To stop future requests while keeping evidence and config intact:

```powershell
stop-scheduledtask -taskname "EREI - Gemini Private Bridge"
```

To uninstall the start-at-logon job without deleting encrypted credentials:

```powershell
unregister-scheduledtask -taskname "EREI - Gemini Private Bridge" -confirm:$false
```

## Actual execution rules

- **One issue -> at most one local attempt**: SQLite claim occurs before
  spawning Python; restart, timeout and duplicate polling cannot retry that
  issue automatically. Any crash after claim can leave it marked CLAIMED with
  zero provider calls; owner's next request must be a new reviewed issue.
- **Local quota**: default 3 attempt claims/day UTC, configurable 1–10;
  this cannot know quotas consumed outside the bridge and is *not* a
  guarantee of free availability/billing safety.
- **Pinned immutable source**: model API script MUST run only from clean
  `erei-core13-schema-compact-v2` exact SHA
  `ecfc2818598e4631166bd3dec2774cb8178d0e10` and exact on-disk
  Git-blob bytes. Frozen target at PR98 exact SHA
  `31d4e518b9e71a9585df9097e7ca07a7e25af916`.
- **Evidence**: raw Gemini envelope, unmodified provider metadata, source
  hashes and scorer verdict remain in local
  `Desktop/erei-core13-evidence/github-bridge/github-issue-NNNNNNN`.
  The existing `smoke-005..017`, `schema-001`, and `schema-002` folders
  remain untouched.
- **Results**: only allowlisted status/reason, optional token count,
  `independently_accepted=false`, `stable_ready=false` are posted to
  private issue comment, and issue is closed. If posting fails, the worker
  retries posting the local summary, NEVER Gemini itself.
- **No implicit background ChatGPT promise:** ChatGPT can create/read
  private GitHub issues via the connected GitHub app *when explicitly asked*
  and check posted results in a later user turn. ChatGPT cannot silently
  receive results or initiate later prompts without separate automation.
- **No PR merges/release:** This bridge cannot convert experimental
  scores into independent acceptance or Stable.

## Security boundaries and tradeoffs

- The queue is PRIVATE, but the control issue author can still cause a
  Free-tier model request for an allowlisted synthetic case. Limit
  repository access to owner + necessary ChatGPT app only. Do not let
  outside collaborators create owner-authored requests.
- Owner's local **fine-grained PAT** is a long-lived bearer secret encrypted
  with DPAPI for the Windows user. The decrypted value exists in broker
  process memory. Rotation and Windows account compromise remain owner risks.
- The bridge does not include a remote command executor, reusable GitHub
  Actions workflow, public queue, provider-proxy that accepts arbitrary
  prompts, or a general-purpose SSH/RDP gateway.
- Worker only executes synthetic/public frozen Framework input; do not use
  it to transmit SAE-DB/EREI private business, personal or medical data.

## Maintenance

In PR/branch development, run:

```powershell
python -m unittest evals.tests.test_github_gemini_bridge -v
```

CI/mock-only tests do not reach GitHub or Gemini endpoints. The assistant
should verify exact branch CI and request Codex review before giving owner
the pinned checkout/install SHA.

**Pending before actual end-to-end readiness**: owner creates/configures the
private queue, stores PAT/Gemini key locally and installs the scheduled task.
No direct local Gemini requests have been made by the assistant.
