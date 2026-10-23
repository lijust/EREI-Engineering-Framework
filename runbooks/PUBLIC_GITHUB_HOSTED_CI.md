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
2. Merge only by PR under Ruleset `EREI-Main-Protection`, id `25712179`; currently deletion and force-push denied, PR required, 0 review approvals and 0 required status checks.
3. After a successful hosted push, choose required check context names from live completed hosted jobs before enabling status checks. Preserve standard job names. Demonstrate failed PR remains blocked without requiring unavailable external approvers.
4. Do not reconnect long-lived personal Windows machines to untrusted public pull_request workflows. Scope any private self-hosted machines to private repositories.
5. [T14 PR #94](https://github.com/lijust/EREI-Engineering-Framework/pull/94) has a separate opt-in rollback workflow originally pointed to self-hosted Windows. Retarget that workflow on its own branch after this main migration, and rerun its exact-head synthetic drill.

## Boundaries

CI green never proves trusted immutable workflow identity, independent security approval, consumer-side release enforcement, 13 genuine exact-target model evaluations, Internal qualification or Stable promotion. No project data/consumer pins, public GitHub ruleset settings, billing, secrets or paid AI are modified by this PR. Open-source disclosure audit is deferred by owner, with public visibility risk acknowledged.
