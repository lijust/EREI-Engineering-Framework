# GitHub Copilot CLI Exact-Target Adapter

**Status:** Candidate infrastructure. It does not authorize Stable promotion by itself.

## Purpose

Execute the Framework's `behavioral_runtime` eval cases against an independent GitHub Copilot CLI runtime while keeping scorer expectations outside the model boundary.

## Blind transport

The exact-target harness keeps the canonical suite ID, case ID, tags, and expectations for deterministic scoring and evidence. The adapter receives only:

- protocol version;
- opaque blinded suite/case identifiers;
- the declared Framework artifact;
- case input;
- case context.

Real suite IDs, real case IDs, tags, and scorer expectations must never cross the adapter boundary.

## Artifact boundary

For direct semantic evaluation, the adapter resolves only canonical Framework contract files (`SKILL.md`, `SPEC.md`, `WORKFLOW.md`, or `CONTRACT.md`) from the frozen target checkout. It does not recursively load directories and rejects paths through `evals`, `tests`, `fixtures`, or `.github`.

For routing-sensitive `skills/impact-analysis` evaluation, the adapter stages only the exact frozen `SKILL.md` into an isolated temporary workspace under `.github/skills/impact-analysis/SKILL.md`. The skill name and skill text are not injected into the prompt. Copilot must discover and invoke the staged skill from the request and workspace behavior itself.

## Trace truthfulness

The adapter must never synthesize tool or skill traces from the eval artifact declaration. Routing evidence is accepted only from Copilot JSONL runtime events such as `skill.invoked`. The normalized eval trace is derived from those observed runtime events.

If a positive trace expectation exists and the runtime emits no matching invocation event, the case fails.

## Runtime isolation

Each case runs in a fresh temporary workspace and fresh Copilot home/cache. Direct semantic mode exposes no effective model tools. Routing mode exposes only the skill tool. Built-in MCPs, custom instructions, remote access/export, experimental behavior, auto-update, and interactive approval are disabled.

The Copilot child process receives an allowlisted environment containing only basic process/network/certificate variables plus its Copilot PAT. Unrelated runner secrets are not inherited.

Because this repository is personal-account owned, the controlled workflow requires the dedicated `EREI_COPILOT_EXACT_TARGET_TOKEN` secret rather than silently falling back to the normal Actions `GITHUB_TOKEN`. The workflow-level `GITHUB_TOKEN` is restricted to `contents: read`; it receives no Copilot, issue, pull-request, status, check, or repository-write permission.

The runtime supply chain is pinned at two layers:

- every third-party GitHub Action used by the workflow is referenced by an exact 40-character commit, not a mutable major tag;
- the Copilot CLI requires both an exact `@github/copilot` npm version and its exact full npm `dist.integrity` SHA-512 SRI. The workflow verifies the registry's integrity for that exact version before installation and before any model call.

The observed CLI version and approved package SRI are retained in runtime provenance. `latest`, version ranges, mutable npm tags, truncated SRI values, or an unbound version are not acceptable for release evidence.

## Evidence production

`.github/workflows/vnext-exact-target-copilot.yml` is manual-only and requires an exact frozen release carrier and validated `VNEXT_TARGET.json`. It checks out the exact target revision/tree, verifies the runtime supply-chain pins, runs behavioral exact-target evidence, validates complete coverage, confirms only the two evidence outputs changed in the target checkout, and uploads an Actions artifact.

The V2 run manifest retains each normalized adapter response in addition to its response digest and status. Stable/readiness validation must be able to reload the published case, validate the retained response, rerun the authoritative scorers, and reproduce the recorded PASS/FAIL result. Digest-only exact-target manifests are not sufficient for V2 Stable.

The Actions artifact package contains three files:

1. `exact-target-run.json` — reconstructible runtime responses;
2. `execution-evidence.json` — case-level assurance rows;
3. `runtime-identity.json` — strict structured provenance that binds the exact repository, target, carrier, GitHub run/attempt, adapter, model, CLI version, full CLI package SRI, governed destination paths, run id, and SHA-256 digests of the first two files.

The governed importer retains all three package files in the frozen release closure. The identity is not disposable import metadata: its retained destination is derived from the run-manifest path as `<run>.identity.json`, and Stable/readiness validation must reopen it, re-hash the retained run manifest and execution-evidence file, confirm the exact execution row is digest-bound to that evidence file, verify runtime provenance, and only then rerun the published scorers.

Manual copying is not valid release evidence. The workflow itself does not commit, push, open a pull request, change approvals, or promote Stable.

## Release boundary

- Reference-contract CI remains responsible for all 44 published cases.
- Independent runtime evidence is required only for the 43 `behavioral_runtime` cases.
- `harness_only` cases are never sent to the external model runtime.
- RC1 remains immutable. This adapter is intended for a later RC selected after its implementation and the assurance-scope correction have passed executable CI.
