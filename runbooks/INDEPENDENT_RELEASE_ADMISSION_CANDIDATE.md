# VNext Candidate Independent Release Admission — Offline Signature Design

**Design/test candidate only. No trusted keys, offline signing, live token grant or independent authority currently provisioned.**

## Scope

This is an optional out-of-band admission verification primitive, not the final Stable V2 gate. It reduces reliance on mutable GitHub branches through signed immutable SHA assertions, but does **not** by itself protect the unprotected GitHub repository or activate the Copilot workflow.

Do not create `release/vnext-rc4` until **all release-control code is merged to `main`**, `main` push assurance on that exact SHA reports SUCCESS, and trusted source admission design is independently approved. RC1–RC3 are historical and must not be rewritten.

## Proposed independent authority (not yet deployed)

1. Independently provision two **different** OpenSSH Ed25519 signing keys for principals `release-owner@erei.invalid` and `independent-security@erei.invalid`, on separately administered devices. Private keys are never put in GitHub secrets/repo, never shared between roles.
2. Store **only** the independently reviewed public keys as `release-owner.allowed_signers` and `independent-security.allowed_signers` in a separately controlled, read-only directory **outside the repository**. Each file format is exactly `<principal> ssh-ed25519 <base64-public-key>`. Pin the fingerprints out-of-band; do not trust files handed to the verifier by the release submitter.
3. Pin the verifier source/binary hash and the accepted policy on the **independent execution host**. CI passing on a mutable checkout is no substitute.
4. Freeze the exact target and one-commit carrier; independently verify the original GitHub workflow and exact successful push assurance run/attempt, plus source tree and scope against a trusted policy.
5. Prepare a canonical `admission.json` envelope matching the public module schema with a maximum lifetime of 72 hours. Sign the exact bytes independently using the OpenSSH domain `erei-framework-admission@erei.invalid`. The signatures are `release-owner.sig` and `independent-security.sig`.
6. Reject cross-role key reuse, key changes without independent rotation, stale envelopes, mismatched commits/trees, extra carrier files, missing approvals or manipulated assurance metadata.
7. Run the independently pinned verifier **outside** the mutable checkout:
   ```text
   python independent_release_admission.py --repo-root <verified-exact-git-repo> --packet-dir <external-packet> --trust-dir <external-trust> --expected-target <exact-40-hex-sha> --expected-carrier <exact-40-hex-sha>
   ```
   Output `verified_offline_signatures_only` means only cryptographic/Git shape validation; `stable_enforcement_satisfied=false` is intentional.
8. Extend the external admission service to authenticate release workflow source/run directly using a separate read-only GitHub API credential and a trusted workflow digest, and to **deny consumption of unsigned/untrusted releases** regardless of mutable GitHub state. Execute adversarial attacks from separate accounts. This step is **not implemented** yet.
9. Independently evaluate risk with Architecture and Security reviewers. Only an accepted, demonstrably effective policy may inform the existing `security/ASSURANCE_ENFORCEMENT.json` fallback review; approval is not automatic.

## OpenSSH verification

This Candidate uses `ssh-keygen -Y verify -f <role.allowed_signers> -I <role-principal> -n erei-framework-admission@erei.invalid -s <role.sig>`, feeding canonical `admission.json` on stdin. It does not invoke `ssh-keygen -Y sign` itself and never reads private keys.

## Immediate controls

- `main` is unprotected; there is **no verified equivalent enforcement**.
- Copilot manual workflow remains disabled with `if: ${{ false }}`.
- Neither this code nor reference/synthetic tests are independent model proof.
- Never copy signing keys or public trust anchors into the release checkout.
- Stop/fail closed if the source authority or signer independence cannot be verified.
