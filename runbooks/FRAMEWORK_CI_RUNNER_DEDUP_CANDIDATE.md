# EREI Framework Windows Runner — Event Deduplication Candidate

**Status: SOURCE CANDIDATE. Protected public hosted CI must pass at the final PR head, and independent workflow review is still required before acceptance.**

## Problem and measured source

The historical Windows self-hosted Framework runner appeared to repeat `assurance` and `bootstrap-self-test` dozens of times during PR #66. The earlier `.github/workflows/assurance-gate.yml` dispatched an `assurance` job on **both** push to `hardening/**` and an open `pull_request`. The Bootstrap workflow ran a matrix of Python 3.11 and 3.12 for each PR touching `tools/tests/**`. Multiple source-only commits during security review therefore created approximately **four** jobs per commit: two Assurance plus two Bootstrap. A backlog of previously queued commits continued to run after later commits had superseded them; the runner did not spontaneously retry a job.

## Candidate change

- Keep unfiltered `pull_request` **Assurance** for all PRs, including `hardening/**`, and preserve `push` **Assurance** on `main` and `release/**`. Remove only the duplicative `hardening/**` push event. This must **not** weaken GitHub's separately authenticated successful **main** push requirement for candidate release admission.
- Keep Bootstrap `pull_request` changed-path filters, `push: main`, and Python 3.11 + 3.12. Both interpreters still execute for relevant PR changes.
- **Do not set any GitHub Actions `concurrency` group on these mixed PR/push workflows.** The public PR can edit its own workflow source and deliberately choose a group equal to an active authoritative push run; an incoming PR run can cancel that push even if the push side uses `cancel-in-progress: false`. Unique push `run_id` values are not a defense against a deliberately chosen collision.
- Defer obsolete-PR cancellation until a separately reviewed PR-only workflow is isolated from all authoritative push runs. This candidate only removes the redundant `hardening/**` push trigger; it never silently trades away main/release evidence availability.
- The current public Framework workflows already run on GitHub-hosted standard Windows; this proposal does not alter their runner labels, installation, credentials, settings or project data.

For a **single changed PR commit touching `tools/tests/**`**, expected scheduling decreases from four to **three** jobs (one Assurance, two Bootstrap), with older PR attempts retained rather than canceled. This predicts one avoided duplicate hardening push-trigger job for the scoped case; the total execution-time and runner-minute saving is **not measured**. No cancellation-driven saving is claimed. On direct `main`/`release/**` push, preserve all Assurance runs rather than cancel them.

## Source checks and acceptance criteria

`tools/tests/test_ci_event_dedup_contract.py` validates:
1. unfiltered Assurance PR trigger plus preserved `main` and `release/**` push triggers;
2. absence of duplicate `hardening/**` push;
3. no PR-controlled concurrency group in either mixed PR/push workflow, preventing group-collision cancellation of authoritative push attempts;
4. preservation of critical Assurance test/release checks; and
5. Bootstrap both-Python matrix with its original paths and exact main push.

Before merging this source-only candidate:
- Verify exact PR-head official Windows Assurance and Bootstrap 3.11/3.12 PASS and a fresh Codex review with no unresolved findings.
- Review this workflow change as **security-sensitive**: independently approve any new assurance source hash before externally authenticating release candidates. `tools/independent_actions_source.py` requires an **externally pinned exact workflow SHA-256**, so a new workflow file invalidates a prior external policy pin. **Never silently update trust pins inside mutable GitHub.**
- Observe a pair of normal nonrelease PR updates only if needed to verify that **both** runs are retained (no automated cancel), while the `hardening/**` duplicate push trigger is gone. Independently inspect a `main` push run without creating an intentional cancellation attempt.
- Confirm existing required GitHub Actions `assurance` check remains globally triggered under the protected public main Ruleset. Do not require path-filtered Bootstrap on all PRs; future cancellation requires a reviewed isolated PR-only design.
- Never use canceled PR results, reference-eval success or green CI as Stable V2 authority.

## Security boundary

Public `main` is protected by active Ruleset #25712179 (required up-to-date `assurance` check). Independently trusted immutable workflow identity, audited consumer deny-by-default admission, signer custody, and authenticated separate Architecture/Security approvals remain unimplemented. Workflow efficiency is **not** effective security enforcement. No V2 release freeze, Copilot activation, or Stable promotion follows from this change.

Track Stable V2 authority separately in issue #31. This PR only reduces avoidable Windows runner work while retaining explicit release-evidence behavior.

## T09 focused Python 3.12 follow-up (separate PR #92, source-only)

The protected public main Ruleset **requires the unfiltered `assurance` check** by GitHub Actions; its `windows-latest` Python 3.12 job always runs **all Framework tool tests** on every PR and main push. For eligible Bootstrap events, this follow-up keeps the complete Python 3.11 tools suite and narrows Python 3.12 Bootstrap to explicit bootstrap/capability-activation smoke tests. The independent Assurance step continues to own full Python 3.12 discovery and must be green at the same SHA before merging.

No self-hosted runner, interpreter path, matrix job ID, PR/push trigger, permission, release pin or consumer behavior is changed. Its parent #67 intentionally removes PR/push concurrency groups for safety. This is a reduction in duplicate full-suite execution, **not permission to skip Assurance**. The `tools/tests/test_ci_test_partition.py` regression executes the actual PowerShell selector with a fake `python` function on Windows, verifying argv and negative exit propagation for both versions and an invalid matrix value.

**Do not infer effectiveness from forecast:** compare hosted job durations and coverage under the final source; no PR cancellation is implemented in these mixed PR/push workflows, so no cancellation savings are claimed. If an external verified release workflow source digest exists, an authorized separate reviewer must re-bind/accept it before release enforcement. The independent review and exact-head hosted CI acceptance are pending; no Stable or Internal promotion.
