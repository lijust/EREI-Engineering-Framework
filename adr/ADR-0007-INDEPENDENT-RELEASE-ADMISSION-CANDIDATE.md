# ADR-0007 — Independent V2 Release Admission (Candidate Design)

**Status:** Proposed / security approval pending — 2026-10-16.

## Context

The private `lijust/EREI-Engineering-Framework` repository has `main.protected=false`. GitHub's Rulesets endpoint currently returns HTTP 403 with an upgrade/public-repository restriction; the classic branch protection endpoint is unavailable to the connected integration. An unprotected repository's green CI, mutable branch names, CODEOWNERS, environment variables, workflow source, and GitHub PR comments are **not** independent release authority.

The project owner chose the lower-cost alternative to changing the repository visibility or relying exclusively on paid GitHub branch protection. This decision starts candidate implementation; **it is not approval to bypass security gates or activate Copilot credentials**.

## Candidate design

A release is identified by two exact Git commits:
- **Target:** reviewed Framework code and release-scope tree.
- **Carrier:** exactly one direct child commit that adds **only** `releases/VNEXT_TARGET.json` and explicitly keeps `promotion_authorized=false`.

An independent release authority runs a **pinned verifier outside the mutable Git checkout**. It receives an external trust store containing independently provisioned SSH Ed25519 public-key allowlists for two **different** roles, plus an out-of-repository three-file submission packet: canonical JSON envelope and two detached OpenSSH signatures.

The envelope binds repository, immutable target/carrier SHAs and tree SHAs, target scope SHA-256, release target ID, claimed push-side assurance run/attempt, issue and expiry timestamps. The verifier cryptographically checks both role signatures under a dedicated domain-separated OpenSSH namespace and checks target-to-carrier Git history. Each key must be distinct and **neither private key may enter GitHub, a runner, a repository secret, or the development machine's repository**.

`tools/independent_release_admission.py` currently returns **`verified_offline_signatures_only`** and explicitly **`stable_enforcement_satisfied=false`**. It does not and must not set `ASSURANCE_ENFORCEMENT.json` to `enforced`.

## Critical trust boundary

A mutable repository cannot validate itself into independence. GitHub-hosted or Windows self-hosted CI and an in-repo verifier, even if all tests PASS, do not protect against direct changes to `main` or changed workflow commands. Operational release consumers must verify the **externally pinned verifier binary/source hash**, external public-key fingerprints, exact Git target/carrier, authenticated GitHub Actions identity and all release constraints from a separately controlled host or independently controlled service. Do not place both independent private keys on one machine or under the same administrator.

A signature here means *two parties signed these bytes*. It is **not** proof that the actual GitHub Actions run passed, that the model was invoked, that an external reviewer accepted equivalence, or that release branch protection existed. A malicious source branch with forged green reports remains excluded until authenticated verification and external authority independently agree.

## Explicit missing proofs before equivalence

1. Independent **trust-host setup**, security ownership, escrow/revocation, rotation/recovery and verifier hash pin external to the repo.
2. Authenticated live GitHub API checks for exact trusted workflow identity, SHA, success, run attempt and immutability of the approved release source, not merely user-asserted run metadata.
3. Trusted external execution broker that does *not* run arbitrary `workflow_dispatch` release refs with Copilot tokens. Current `.github/workflows/vnext-exact-target-copilot.yml` remains `if: ${{ false }}`.
4. Consumer-side denial of unsigned/untrusted releases **even if** someone directly pushes to unprotected `main`, with independently executed negative bypass tests.
5. Authenticated independent Architecture and Security reviews accepting the fallback as effectively equivalent for the exact target/tree and threat model, with immutable audit trail.
6. Real scoped 13-case exact-target model run and time-bounded original artifact provenance; subsequent final Stable carrier verification.

## Decision boundaries

- Hybrid autonomy: source-only candidate work and tests may proceed; signing/provisioning secrets, IAM, provider writes, enforcements, target freeze, live Copilot and Stable promotion require separate, explicit authorization.
- No new Python dependency: use existing system Git + OpenSSH `ssh-keygen -Y verify`, with fail-closed behavior if unavailable.
- Keep the private repository private.
- If independent authority cannot be proved, **Stable V2 stays BLOCKED**. Do not relabel a signed packet as equivalent GitHub server enforcement.
