# EREI Framework Windows Runner — Event Deduplication Candidate

**Status: SOURCE-ONLY CANDIDATE; NOT YET APPROVED AS A SECURITY/RELEASE WORKFLOW CHANGE.**

## Problem and measured source

The Windows self-hosted Framework runner appeared to repeat `assurance` and `bootstrap-self-test` dozens of times during PR #66. The earlier `.github/workflows/assurance-gate.yml` dispatched an `assurance` job on **both** push to `hardening/**` and an open `pull_request`. The Bootstrap workflow ran a matrix of Python 3.11 and 3.12 for each PR touching `tools/tests/**`. Multiple source-only commits during security review therefore created approximately **four** jobs per commit: two Assurance plus two Bootstrap. A backlog of previously queued commits continued to run after later commits had superseded them; the runner did not spontaneously retry a job.

## Candidate change

- Keep unfiltered `pull_request` **Assurance** for all PRs, including `hardening/**`, and preserve `push` **Assurance** on `main` and `release/**`. Remove only the duplicative `hardening/**` push event. This must **not** weaken GitHub's separately authenticated successful **main** push requirement for candidate release admission.
- Keep Bootstrap `pull_request` changed-path filters, `push: main`, and Python 3.11 + 3.12. Both interpreters still execute for relevant PR changes.
- Add scoped GitHub Actions `concurrency` to both workflows. Group PRs by workflow name plus PR number and `cancel-in-progress` **only** on `pull_request`. This cancels superseded PR evaluations.
- Give **each push run** its own `run_id`-scoped group, regardless of `github.ref`. GitHub always replaces an older **pending** run if it shares a concurrency group, even when `cancel-in-progress=false`; **unique push groups are essential** so no authoritative `main`/`release/**` push evidence is silently lost.
- No work moves to third-party runners; no extra services, new secrets, IAM changes, provider writes, branch protection or production mutation.

For a **single changed PR commit touching `tools/tests/**`**, expected scheduling decreases from four to **three** jobs (one Assurance, two Bootstrap), with old PR attempts canceled after a successor arrives. The actual percentage saved depends on PR update frequency; it is not a measured performance improvement until GitHub scheduling evidence is collected. On direct `main`/`release/**` push, preserve all Assurance runs rather than cancel them.

## Source checks and acceptance criteria

`tools/tests/test_ci_event_dedup_contract.py` validates:
1. unfiltered Assurance PR trigger plus preserved `main` and `release/**` push triggers;
2. absence of duplicate `hardening/**` push;
3. PR-only cancel expression and exact unique per-push-run concurrency key;
4. preservation of critical Assurance test/release checks; and
5. Bootstrap both-Python matrix with its original paths and exact main push.

Before merging this source-only candidate:
- Verify exact PR-head official Windows Assurance and Bootstrap 3.11/3.12 PASS and a fresh Codex review with no unresolved findings.
- Review this workflow change as **security-sensitive**: independently approve any new assurance source hash before externally authenticating release candidates. `tools/independent_actions_source.py` requires an **externally pinned exact workflow SHA-256**, so a new workflow file invalidates a prior external policy pin. **Never silently update trust pins inside mutable GitHub.**
- Confirm behavior with a short nonrelease branch sequence: two rapid PR commits; see whether the older PR run canceled and the latest completed, and confirm a `main` push is never canceled or treated as equivalent to a PR run.
- Check external required-status/check policies if ever enabled; canceling obsolete PR checks must not remove the latest exact-HEAD status. Review Bootstrap path filters before making Bootstrap a required check for *all* PRs.
- Never use canceled PR results, reference-eval success or green CI as Stable V2 authority.

## Security boundary

Private `main` remains unprotected; externally audited consumer deny-by-default admission, signer custody, immutable independent execution, and authenticated Architecture/Security approvals remain unimplemented. Workflow efficiency is **not** effective security enforcement. No V2 release freeze, Copilot activation, or Stable promotion follows from this change.

Track Stable V2 authority separately in issue #31. This PR only reduces avoidable Windows runner work while retaining explicit release-evidence behavior.
