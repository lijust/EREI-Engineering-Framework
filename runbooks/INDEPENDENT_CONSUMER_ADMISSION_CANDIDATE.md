# Independent Consumer Admission — Source-Only Candidate

**State:** Candidate only; no trusted external controller, signed consumer permit or consumer activation authority is provisioned.

## Why this exists

The private Framework `main` branch remains unprotected. Exact-source GitHub Actions SUCCESS after PR #64 and PR #65 does not prevent a malicious direct push. The eventual consumer must deny a release until independently controlled admission permits it. This module is a read-only building block toward that, **not** a live consumer enforcement point.

## Offline layout (proposed, all external to worktree)

```text
<verifier-host>/pinned-code/    # reviewed, hash-pinned: this module + all imported dependencies
<verifier-host>/submission/     # permit.json, consumer-architecture.sig, consumer-security.sig
<verifier-host>/consumer-trust/  # independent Architecture/Security allowed_signers files
<verifier-host>/carrier-packet/  # PR64 admission.json and release-owner/independent-security .sig
<verifier-host>/carrier-trust/   # PR64 release-owner and independent-security allowed_signers
<verifier-host>/actions-policy.json  # PR65 policy, its SHA pinned outside release inputs
<verifier-host>/replay-store/    # NOT IMPLEMENTED: independent durable one-time nonce state
```

Never put private keys, a read-only GitHub token or trusted policy anchors in the Framework repository, PRs, GitHub Actions secrets, untrusted runner or EREI App Google browser. Independently pin the entire verifier dependency chain, including `independent_release_admission.py`, `release_target.py`, `validation_contract.py`, `independent_actions_source.py` and their imports. Use a sandbox with strict time/CPU/memory limits for untrusted Git objects.

## Canonical permit contract

Exact keys (no extras): `schema_version=1`, `purpose=erei-framework-v2-consumer-admission-precheck`, `repository=lijust/EREI-Engineering-Framework`, `consumer_id=erei-app-google`, `target_ref`, `carrier_ref`, `scope_sha256`, `admission_envelope_sha256`, `actions_policy_sha256`, `actions_run_id`, `actions_run_attempt`, `nonce` (64 lowercase hex), `issued_at`, `expires_at`.

Canonical JSON is `json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\\n"` encoded UTF-8; actual file must contain a literal one-byte LF. Lifetime: positive, <=30 minutes, with maximum five minutes of early clock skew and no late grace. The `nonce` is **bound in the permit but not consumed or replay-protected by this precheck**.

Independent principals: `consumer-architecture@erei.invalid` and `consumer-security@erei.invalid`. Sign the **exact canonical file bytes** using `ssh-keygen -Y sign -n erei-consumer-admission@erei.invalid` under two different independently provisioned Ed25519 private keys. The verifier accepts only `ssh-keygen -Y verify` detached signatures under the same namespace. Neither signer may use either PR64 admission key. Public trust files contain exactly one `<principal> ssh-ed25519 <base64>` line each, and are independently managed outside the checkout.

## Candidate invocation

```text
EREI_INDEPENDENT_GITHUB_READ_TOKEN=<secret held only by verifier authority>
python tools/independent_consumer_gate.py \
  --repo-root <independently authenticated exact checkout> \
  --permit-dir <external signed consumer permit> \
  --consumer-trust-dir <external Architecture+Security signer trust> \
  --admission-packet-dir <external PR64 admission packet> \
  --admission-trust-dir <external PR64 signer trust> \
  --actions-policy-file <external pinned PR65 policy> \
  --expected-consumer erei-app-google \
  --expected-target <independently pinned exact target commit> \
  --expected-carrier <independently pinned exact carrier commit> \
  --expected-actions-policy-sha256 <independently pinned policy sha256>
```

**Exit code 2 means DENIED. Exit code 0 means *read-only precheck* only**: output expressly includes `consumer_activation_authorized=false`, `stable_enforcement_satisfied=false`, `independent_runtime_enforcement_attested=false`, and `replay_protection_attested=false`. Never invert or bypass these flags. Absent a separately governed consumer-side enforcement point, **all release activation remains denied**.

## Review hardening: trust-file rotation and path races

The candidate first validates the external Actions policy and then copies the **exact original permit, both detached consumer signatures, signed carrier envelope, both detached release signatures, four allowed-signers files, and pinned Actions policy** into one owner-only temporary directory outside the checkout. Distinct public keys and both OpenSSH `-Y verify` calls operate on these **same private snapshots**; the upstream PR64/PR65 verifiers also receive those snapshots, not the mutable submission paths. Malformed `source_assurance` structures are denied explicitly instead of bubbling out as `AttributeError`.

Every external file used to build the snapshot (two consumer detached signatures, both release detached signatures, both admission/consumer envelopes, four public signer-allowlist files, and the independent Actions policy) is read from one file descriptor with a regular-file check, `st_nlink == 1`, an inode identity check and before/after size/time metadata check. A hard link from the mutable checkout into external trust is **rejected**, even if it points to identical bytes. This is a source-only TOCTOU hardening measure, not proof that a privileged trusted-host administrator cannot alter memory or files during execution. Retained negative tests include actual hard links into the checkout for consumer trust, release trust and Actions policy.

POSIX private-temp permission checks are applied on POSIX systems. Windows `st_mode` cannot attest NTFS ACL independence: that requires trusted-host setup and an **independent Windows ACL/security review** before any real use. A privileged same-user attacker, compromised verifier process or mutable working tree can still bypass source-only checks, so external host/process immutability remains mandatory.

## Required staged testing before installation

- Re-run PR64 exact-Git and PR65 Actions-source tests; run `python -m unittest tools.tests.test_independent_consumer_gate -v` with OpenSSH to test real signatures and negative cases.
- Prove an unprotected direct `main` push and a malicious workflow change cannot trigger a consumer deployment. Merely changing a source-only test fixture is **not** proof of an actual consumer bypass test.
- Prove a consumer rollout cannot occur through an alternate service account/SDK/manual path without an independently authenticated, single-use permit and target/tree approval.
- Test nonce replay under concurrency, token/Actions outages, wrong SHA, signers/key revocation, clock drift, expired approvals, rollback and emergency stop.
- Capture external Architecture and Security approval receipts from independent principals **after** trusted-host admission and actual no-bypass integration is audited.

No permanent GitHub-hosted runner migration, App Google production changes, Stable pin changes, RC freeze or Copilot enablement are made by this change. Issue #31 remains OPEN.
