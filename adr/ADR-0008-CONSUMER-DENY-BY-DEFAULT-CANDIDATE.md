# ADR-0008 — Consumer-Side Fail-Closed Admission Candidate

**Status:** PROPOSED / source-only / independent Architecture + Security approval pending — 2026-10-17.

## Decision context

The Framework repository's private `main` remains unprotected. Both PR #64 (signed carrier admission) and PR #65 (official Actions-source metadata) have merged, but neither creates a trusted external authority. A direct commit to `main`, a spoofed approval comment, a mutated workflow or a successful job in an untrusted runner **must not** authorize EREI App Google to adopt a new Framework Stable release. Nor may this repository's own code assert that it has become an independent policy host.

## Candidate admission design (not yet effective enforcement)

1. An *independently operated* consumer/deployment controller keeps its verifier code plus dependencies pinned outside the unprotected Framework repository. It stores independently pinned signer trust material, Actions policy and read-only GitHub API identity outside the worktree.
2. Prior to any release adoption, the controller invokes the read-only source checks **inside the trusted host**. A newly added `tools/independent_consumer_gate.py` joins:
   - PR #64 offline, double-signed exact Git target/carrier evidence;
   - PR #65 authenticated official `push` Actions source/run/attempt/job metadata, checked against external policy SHA;
   - a separate **canonical, consumer-bound, time-limited permit**, signed by independent consumer Architecture and Security keys in a dedicated OpenSSH namespace.
3. The consumer permit binds exact target/carrier SHA, frozen scope SHA256, original signed admission envelope SHA256, external Actions policy SHA256, run ID/attempt and consumer identity `erei-app-google`. Its validity window is at most **30 minutes**. Four cryptographic signer keys (release-owner, independent-security, consumer-architecture, consumer-security) must be distinct. Neither permit nor trust input may be accepted from the mutable release checkout.
4. Missing, malformed, expired, cross-namespace, altered or improperly signed permits, wrong refs/scope/run/policy, duplicate keys, missing token, or an upstream verification failure **deny**. The precheck performs **no consumer activation** and does not write a trust-state marker.
5. The only eventual **effective** consumer control is an exclusive deployment/activation path outside GitHub, with a durable replay/nonce ledger, independent approval review, trusted code execution and auditable *negative* bypass tests. The consumer must not use CLI success alone to deploy. A separate independently authorized mechanism is required to operate that path.

## Security assertions that are NOT made

- `consumer_admission_precheck_only` is a **candidate building block**, never evidence that a real consumer cannot bypass a gate.
- This source-only repository cannot authenticate its own execution, enforce App Google release adoption or prove administrative independence of key custodians.
- A signed permit proves the holder of approved *keys* signed some bytes, not that human Architecture/Security reviewers accepted the risk or that a runner was clean.
- No Copilot token, runtime credentials, external key provisioning, IAM mutation, frozen target, consumer deployment, permanent CI migration, pin change, or Stable V2 promotion is authorized by this ADR.
- The current Stable pin stays unchanged and `security/ASSURANCE_ENFORCEMENT.json` must retain `candidate_control` / `equivalent_enforcement_verified=false`.

## Mandatory external exit criteria

1. Architecture + Security approve independently owned custody/key rotation, exact verifier+dependency hashes, decision policy, and operator identity; maintain immutable audit receipts.
2. Install an **exclusive** enforcement point at the EREI App Google consumer; prevent direct admin/API/config/integration bypass, with deny-default under outages and rollback.
3. Provision tamper-resistant nonce replay state and attest independent runtime execution; test revoked keys, incorrect policy/workflow, direct unprotected-`main` push, unapproved release, stale permit, retry/replay, and bypass of every alternate activation path.
4. Review real exact-target 13-case evidence and legal/operations authority separately; only then reconsider fallback enforcement and Stable V2.

**Decision:** develop and test a bounded source-only precheck now; **do not label effective enforcement until external controls are installed and independently demonstrated**. See ADR-0007 and issue #31.
