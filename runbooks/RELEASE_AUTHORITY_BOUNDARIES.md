# Review authentication and release authority

A schema-valid record asserts a decision. An authenticated GitHub review proves
that a review of the bound artifact occurred. Neither proves independently granted
release authority, two independent principals, deployed enforcement, or exclusive
consumer admission.

The current fallback authenticates review provenance for diagnostics and returns
`authenticated_review_only`, with `authority_verified=false`. It cannot satisfy
`verify_effective_enforcement`, even if an earlier review wrapper claimed
`status=verified`. The existing live-server verifier remains a separate path;
this change does not implement its missing positive-path controls.

Structured Architecture/Security records are still shape-checked and their reviews
authenticated. Promotion then denies if both reviews identify the same principal,
regardless of distinct role labels. Distinct names also deny because no independent
approval-authority verifier is connected. This deliberately has no positive authority
path until the separately reviewed deployment/trust design is implemented.

No authority is installed or activated by this change. Existing Candidate validation
and V1 compatibility remain; V2 Stable stays blocked. Never edit the truth record to
claim enforcement merely to satisfy a test. The corresponding tests mock authority
only to isolate unrelated manifest/evidence validation, and label that mock synthetic.

To enable a future positive path, first decide and independently verify the actual
trust anchor, authorized identities, independence, revocation, exact-target binding,
consumer enforcement and runner/source policy. Do not infer them from repository
strings or a bot review. Track that work in issues #77/#78 and Stable issue #31.

Rollback must preserve denial of unverified authority. This source change writes no
keys, approvals, deployment state, project data or release artifacts.
