# Public-repository CI isolation — GitHub-hosted Windows

**Scope:** public `lijust/EREI-Engineering-Framework`. Untrusted public pull-request code must never run on a persistent self-hosted Windows runner. Private EREI/SAE runners are separate and unaffected.

## Source changes

- All five tracked Framework Windows workflows use ephemeral **`windows-latest`** rather than self-hosted labels. Four are PR eligible; the legacy preflight is now hosted and optional.
- `actions/setup-python@v5` explicitly selects Python 3.12 or the 3.11/3.12 matrix. The shell uses `python` from setup-python instead of the developer's Windows `py` installation.
- PR workflows have read-only `GITHUB_TOKEN` permissions and `actions/checkout@v4` with `persist-credentials: false`. Production secrets are not used.
- GitHub-hosted standard Windows/Ubuntu CI is free/unlimited for public repos, subject to separate account/storage/service availability. Verify live runs rather than asserting entitlements from plan name.
- Owner confirmed force-removing Framework's self-hosted registration, but connected GitHub tools cannot inspect the runner registration list; do not mark removal independently verified.

## Operating checklist

1. Verify Framework PR on real GitHub-hosted Windows for Python 3.11/3.12, including Assurance, Bootstrap, and Evals; confirm actual runner metadata and job conclusions.
2. Merge only by PR under **active** Ruleset `EREI-Main-Protection` (id `25712179`). For the default branch it requires the GitHub Actions `assurance` check (App ID 15368), with strict/up-to-date status checks, no bypass, no force push or deletion, and **0** required independent reviews. This Ruleset does not by itself cover release branches/tags.
3. Keep the globally required `assurance` job unfiltered for all PRs and `main` pushes; Bootstrap/Evals/Runtime are path-filtered and **must not** be made globally required without their trigger contracts changing. Verify each current PR and new `main` SHA from actual GitHub-hosted run results. Never treat a green status as an authenticated immutable workflow or Stable release authority.
4. Do not reconnect long-lived personal Windows machines to untrusted public `pull_request` workflows. Scope any private self-hosted machines to private repositories; runner registration removal was user-reported, not independently queried.
5. [T14 PR #94](https://github.com/lijust/EREI-Engineering-Framework/pull/94) now uses hosted Windows on its still-unmerged branch. Dedicated [run #40047051512](https://github.com/lijust/EREI-Engineering-Framework/actions/runs/40047051512) passed both Python 3.11/3.12 synthetic drill jobs and uploaded five-file evidence artifacts for each interpreter. Review its source and original P2 report-retention thread before merging; this is **not** real consumer rollback qualification.


## T11 main Ruleset observation (public read-only, no release approval)

The pre-existing `tools/github_ruleset_observation.py` review-candidate script on this branch can make a **public, anonymous GET** observation of the repository's current main protection without reading tokens or calling GitHub write APIs:

```text
python -B tools/github_ruleset_observation.py --live
python -B -m unittest tools.tests.test_github_ruleset_observation -v
```

It validates the exact current Ruleset id `25712179`, active source/repository, protected `main`, no bypass/deletion/force-push, required PR, and GitHub Actions `assurance` from App ID `15368` under strict status checks. The script intentionally reports `MAIN_CI_OBSERVED_RELEASE_BLOCKED`, `workflow_source_authenticated=false`, `release_branches_and_tags_covered=false`, `consumer_release_authorized=false`, and `stable_ready=false`, **even when all main checks pass or additional approvers are configured**. If API responses fail, drift or become unavailable, it exits nonzero. `--fixture` is an **untrusted offline replay**, not observed server evidence.

A public API observation is unsigned and time-varying. It is **not** a substitute for independently pinned workflow source, rules covering `release/**`/tags, independently authorized release/security principals or consumer-side check. The historical `security/ASSURANCE_ENFORCEMENT.json` must **not** be set to `enforced` just because this observer is green; positive T11 remains separately blocked. This code does not touch main GitHub Ruleset settings, credentials, billing, model runtimes or consumer data.

## Boundaries

CI green never proves trusted immutable workflow identity, independent security approval, consumer-side release enforcement, 13 genuine exact-target model evaluations, Internal qualification or Stable promotion. No project data/consumer pins, public GitHub ruleset settings, billing, secrets or paid AI are modified by this PR. Open-source disclosure audit is deferred by owner, with public visibility risk acknowledged.
