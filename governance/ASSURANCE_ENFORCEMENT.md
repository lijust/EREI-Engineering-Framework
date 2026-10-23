# Assurance Enforcement Boundary

## Verified in-repository state (2026-10-23)

The public `lijust/EREI-Engineering-Framework` `main` branch is protected by the active GitHub Ruleset **EREI-Main-Protection** (ID `25712179`). It blocks deletion and non-fast-forward updates, requires a pull request, and enforces the **GitHub Actions app-authenticated `assurance` check** with `strict_required_status_checks_policy=true`. There are no bypass actors. The Ruleset currently requires **zero independent approving reviews**. This is real repository/PR CI enforcement, **not proof of a protected immutable workflow identity, protected release authority, independent security approval or consumer-side release admission**.

## In-repository enforcement and scheduling

The Framework runs `Framework Assurance Gate` on **all pull requests** (not path-filtered), and each push to **`main`** and **`release/**`**. A direct push to `hardening/**` **without** an open/synchronized pull request does not trigger this workflow; with a PR, the `pull_request` event runs the required aggregate check. The previous extra `hardening/**` push event is removed to prevent duplicate checks. A distinct **main/release push run** retains its own unique `run_id` concurrency group, while an updated PR cancels only its superseded PR check. No cross-event cancellation of immutable push-side evidence is authorized.

All Framework public PR Windows checks execute on GitHub-hosted `windows-latest` rather than personal self-hosted runners. Python setup and read-only checkout remain scoped as in [the hosted CI runbook](../runbooks/PUBLIC_GITHUB_HOSTED_CI.md). `Project Bootstrap Tests` retains its two Python 3.11/3.12 matrix jobs and path-filtered triggers; Bootstrap is **not** a global required status check because it does not run on every PR.

The aggregate `assurance` check performs compilation, machine contract verification, full tool unit tests, eval harness tests, release evidence/readiness checks, and publishes **75 synthetic cases** at `reference_contract` level. Those 75 are *not* model-executed target evaluations. For VNext Task Learning V2, the frozen scope requires **13 exact-target behavioral cases**, signed independent evidence, verified effective release enforcement and final Architecture/Security approvals. Historical evidence is not silently upgraded.

## Independent release authority and limitation

GitHub's branch Ruleset validates the mutable named `assurance` check but is **not by itself** an immutable workflow-source trust anchor. An attacker with appropriate repository permissions could attempt to change the workflow while preserving the same check name. The external verifier must independently bind trusted workflow contents, run/attempt/job/source identity, actual candidate SHA, separated approvers and consumer-side rejection; `tools/independent_actions_source.py` intentionally does not claim consumer enforcement or runner hardware attestation. The live `server_enforcement_satisfied` remains false until authenticated, governed T11 evidence exists.

Do not infer Stable qualification or Internal adoption from green checks. The current genuine model evidence is 0/13, effective Stable enforcement remains unsatisfied, and independent final approvals are deferred. A real measured prospective cycle is also required before any claim of improved effectiveness or causality.

## Safe operation and rollback

Always merge through a PR with a fresh green exact-head `assurance` check. Do not grant unqualified bypasses, delete source pins, or promote private project/consumer data through this repository. The CI dedup source change only affects event scheduling; a rollback restores the `hardening/**` push trigger and removes the two concurrency blocks, leaving Ruleset protections and both Python coverage unchanged.
