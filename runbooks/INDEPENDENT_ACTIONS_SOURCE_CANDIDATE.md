# Independent GitHub Actions Source Verification — Candidate

**Source-only, fail-closed, not GitHub enforcement equivalence.**

## Purpose

The private Framework repository's main branch currently reports `protected=false`. Source code, workflows, jobs and PR comments in that repo cannot serve as independent authority. This module offers one necessary, not sufficient, external building block: when invoked on an independently controlled machine, authenticate the *reported* official GitHub Actions push-side run and the exact source workflow bytes, against an out-of-band pinned policy. It does not prove a Windows self-hosted runner or its filesystem was uncompromised, nor stop direct pushes.

## Controlled inputs

- `--repo-root`: independently obtained checkout, with verified exact commit SHA; do not trust a mutating checkout or caller-controlled environment.
- `--target-ref`: exact reviewed immutable Framework Git revision; not a branch name.
- `--policy-file`: **outside** the repository and held by the independent verifier authority.
- `--expected-policy-sha256`: independently pinned SHA-256 of the entire external policy file; must come from a separate approved policy control, never from the release submitter's input.
- `--run-id`, `--run-attempt`: authenticated GitHub Actions run identity expected for the target.
- `EREI_INDEPENDENT_GITHUB_READ_TOKEN`: narrowly scoped read-only API token available exclusively on the separate verification host, not supplied via PR, repository file, or Copilot execution workflow.

The external policy has exact keys: `schema_version` (1), `repository` (`lijust/EREI-Engineering-Framework`), `workflow_path` (`.github/workflows/assurance-gate.yml`), `workflow_sha256` (digest of the exact workflow source bytes from target Git object), `workflow_id` (numeric official GitHub workflow identity approved out-of-band), `required_job` (`assurance`), `head_branch` (`main`).

## Authenticated-source verification

The verifier rejects unpinned policy bytes or embedded trust settings, wrong target workflow digest, incorrect Git objects, Git replacements or grafts, and commit-graph manipulation. It makes read-only HTTPS API requests to the exact official repository and rejects redirects. It requires an official completed-successful `push` run on `main` with the exact target SHA, pinned workflow ID and path, exact attempt number, and repository/head repository. It retrieves that same attempt's complete job list and requires exactly one completed-successful `assurance` job bound to the same run, attempt and target SHA.

The result `authenticated_actions_source_metadata_only` explicitly returns `stable_enforcement_satisfied=false`, `trusted_externally_enforced_consumption=false`, and `self_hosted_runner_execution_attested=false`. A forged green CI can still exist if the workflow's dependencies or runner were compromised. An independently reviewed exact target/tree and consumer-side denial remain mandatory.

## Invocation (only on independently controlled verifier)

```text
python tools/independent_actions_source.py --repo-root <immutable independently verified checkout> --policy-file <external authority file> --expected-policy-sha256 <externally pinned 64-hex> --target-ref <exact SHA> --run-id <official run ID> --run-attempt <attempt>
```

This does not mint or store secrets, write to GitHub, run Copilot, create a new release candidate, sign release packets, authorize promotion or change `ASSURANCE_ENFORCEMENT.json`.

## Requirements before declaring independent equivalent enforcement

1. Establish external verifier host with controlled identity, pinned code hash, trusted policy fingerprint and operational audit retention.
2. Confirm two Ed25519 private keys are on independently controlled devices; establish signing policy, revocation, rotation, and independent reviewer identity.
3. Design and independently test an enforced **consumer-side deny-by-default** admission gate: direct push to unprotected `main`, changed workflows, and unsigned release packets must all fail downstream activation.
4. Independently assess runner and build input integrity, with architecture/security reviewer authorization for the exact frozen target/tree.
5. Only then design a narrow token-execution broker for genuine Copilot model tests, without enabling the existing disabled credential-bearing workflow on arbitrary dispatch inputs.

See ADR-0007 and issue #31 for the larger V2 fallback-security boundary. This Candidate is not a declaration of equivalent GitHub protection.
