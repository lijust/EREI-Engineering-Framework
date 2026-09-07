# Controlled Release Assurance

## Purpose

This runbook defines the fallback release control for the EREI Engineering Framework while GitHub server-side branch/ruleset enforcement is unavailable. It reduces release risk but does **not** claim to be equivalent to server enforcement until that equivalence is independently verified and explicitly recorded.

The machine-readable source of truth is `security/ASSURANCE_ENFORCEMENT.json`.

## Current enforcement truth

- `main` is not protected by GitHub branch protection.
- Required status checks are not server-enforced.
- `Framework Assurance Gate` runs in CI, but CI alone cannot stop a direct write to an unprotected branch.
- A harmless direct-write incident on 2026-09-07 wrote `SECURITY-PLACEHOLDER.tmp` to `main` and immediately removed it. The final tree returned to exact parity, but the two commits remain in history. This is retained as evidence that client/process discipline cannot be treated as server enforcement.

## Candidate policy

Candidate hardening may merge to `main` through reviewed pull requests after the aggregate `Framework Assurance Gate` succeeds. Candidate merges do not change the last Stable release identity.

## V2 Stable promotion policy

A V2 Stable release is blocked unless **all** of the following are true:

1. The release manifest is bound to an exact 40-character Framework candidate commit.
2. `approval_ref` and `security_review_ref` are exact immutable commits.
3. Behavioral eval evidence is V2, matches the exact release revision, covers every published case, is PASS, and is at `exact_target_runtime` assurance level.
4. One genuine prospective cycle is complete: capture → review → feedback → validated Framework improvement → project adoption → measured post-adoption outcome.
5. `tools/release_assurance.py` passes for the release manifest.
6. The aggregate `Framework Assurance Gate` passes on the exact release candidate revision.
7. One of these enforcement conditions is satisfied:
   - GitHub branch protection **and** required status checks are server-enforced; or
   - the controlled-release fallback has been independently verified as equivalent and `fallback.equivalent_enforcement_verified` is explicitly set to `true` in `security/ASSURANCE_ENFORCEMENT.json` through a reviewed change.

Until condition 7 is satisfied, VNext remains Candidate even if every other Stable gate passes.

## Controlled release procedure

1. Create a `release/**` branch from the exact Candidate commit; never develop new behavior on that branch.
2. Regenerate/verify the Candidate and proposed Stable release evidence without changing historical evidence.
3. Run the aggregate assurance gate and retain the exact run evidence.
4. Bind architecture and security approvals to immutable commit refs.
5. Run `python tools/assurance_enforcement.py` and `python tools/release_assurance.py <manifest> --repo-root .`.
6. Review the complete diff from the exact candidate SHA; unknown or protected-path changes require L3 review.
7. Merge only the reviewed release PR with an expected-head SHA guard.
8. Verify post-merge tree/release identity and record the immutable Stable release manifest.

## Prohibited shortcuts

- No direct Stable promotion from a mutable branch name or tag-only reference.
- No treating a passing CI run as server branch protection.
- No setting `equivalent_enforcement_verified=true` merely because this runbook exists.
- No rewriting historical learning, feedback, or release evidence to satisfy a gate.
- No using Candidate capabilities as the project Stable pin before explicit Stable promotion.
