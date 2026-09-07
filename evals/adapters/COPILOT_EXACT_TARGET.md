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

For routing-sensitive `skills/impact-analysis` evaluation, the adapter stages only the exact frozen `SKILL.md` into an isolated temporary workspace under `.github/skills/impact-analysis/SKILL.md`. The skill name and skill text are not injected into the normal routing-eval prompt. Copilot must discover and invoke the staged skill from the request and workspace behavior itself.

## Trace truthfulness

The adapter never synthesizes tool or skill traces from the eval artifact declaration.

For routing cases, `skill.invoked` is the authoritative name-bearing runtime signal. The adapter validates the observed skill name and path against the one staged routing skill before normalizing it into eval trace. Generic `skill` tool activity is not enough to claim a named invocation.

The parser also inspects observed `assistant.message.toolRequests`, `tool.execution_start`, and `tool.execution_complete` events when present. It fails closed when:

- a `skill` request/start is observed but no authoritative `skill.invoked` event identifies the invoked staged skill;
- request/start call IDs conflict;
- `skill.invoked` names a skill outside the staged routing boundary;
- its path does not resolve to `.github/skills/<name>/SKILL.md`;
- a correlated observed completion explicitly reports `success=false` after invocation;
- a skill invocation appears in direct semantic mode;
- duplicate invocation telemetry would make the trace ambiguous.

Missing optional lifecycle events are not invented. A valid authoritative `skill.invoked` event may stand on its own because the Framework does not assume that every Copilot stdout transport version emits every non-authoritative lifecycle event.

### Runtime telemetry transport probe

Before the governed workflow may execute the 43 behavioral cases, it runs a dedicated telemetry canary through the exact installed CLI/model/adapter path. The probe stages exactly one routing skill, does not name that skill in the prompt, requires the available project skill to be invoked exactly once, and succeeds only when the adapter observes exactly:

```json
[{"type":"tool","name":"impact-analysis"}]
```

If the chosen Copilot CLI transport does not expose an authoritative usable `skill.invoked` event, the workflow stops before behavioral evidence production.

A successful probe is bound into the run manifest's runtime provenance as:

```text
copilot-skill-event-transport:skill.invoked-v1
```

The package-identity builder, governed importer, and Stable/readiness binder all require that marker as part of the exact runtime-evidence set. Therefore an artifact produced by an older path that skipped the probe is not accepted as V2 Stable evidence merely because its other hashes or runtime fields are valid.

## Runtime isolation

Each case runs in a fresh temporary workspace and fresh Copilot home/cache. Direct semantic mode exposes no effective model tools. Routing mode exposes only the skill tool. Built-in MCPs, custom instructions, remote access/export, experimental behavior, auto-update, and interactive approval are disabled.

The Copilot child process receives an allowlisted environment containing only basic process/network/certificate variables plus its Copilot PAT. Unrelated runner secrets are not inherited.

Because this repository is personal-account owned, the controlled workflow requires the dedicated `EREI_COPILOT_EXACT_TARGET_TOKEN` secret. The adapter itself requires `COPILOT_GITHUB_TOKEN` and does not fall back to the normal Actions `GITHUB_TOKEN`. The workflow-level `GITHUB_TOKEN` is restricted to `contents: read`; it receives no Copilot, issue, pull-request, status, check, or repository-write permission.

## Runtime supply chain

The runtime supply chain is pinned at two layers:

- every third-party GitHub Action used by the workflow is referenced by an exact 40-character commit, not a mutable major tag;
- the Copilot CLI requires both an exact `@github/copilot` npm version and its exact full npm `dist.integrity` SHA-512 SRI.

The workflow first requires registry `dist.integrity` equality, then downloads that exact package using `npm pack`, computes SHA-512 over the downloaded tarball bytes, and installs only the byte-verified local tarball. A metadata-only verification followed by a second direct registry install is not allowed.

The observed CLI version and approved package SRI are retained in runtime provenance. `latest`, version ranges, mutable npm tags, truncated SRI values, or an unbound version are not acceptable for release evidence.

## Evidence production

`.github/workflows/vnext-exact-target-copilot.yml` is manual-only and requires an exact frozen release carrier and validated `VNEXT_TARGET.json`. It checks out the exact target revision/tree, verifies runtime supply-chain pins, verifies skill-event telemetry transport, runs behavioral exact-target evidence, validates complete coverage, confirms only the two target-checkout evidence outputs changed, builds the package identity, and uploads an Actions artifact.

The V2 run manifest retains each normalized adapter response in addition to its response digest and status. Stable/readiness validation must be able to reload the published case, validate the retained response, rerun the authoritative scorers, and reproduce the recorded PASS/FAIL result. Digest-only exact-target manifests are not sufficient for V2 Stable.

The Actions artifact package contains three files:

1. `exact-target-run.json` — reconstructible runtime responses;
2. `execution-evidence.json` — case-level assurance rows;
3. `runtime-identity.json` — strict structured provenance that binds the exact repository, target, carrier, GitHub run/attempt, adapter, model, CLI version, full CLI package SRI, governed destination paths, run id, and SHA-256 digests of the first two files.

The package-identity builder validates the run manifest before output and requires its Framework/adapter/runtime identity plus exact runtime provenance set—including `copilot-skill-event-transport:skill.invoked-v1`—to match the package identity. A provenance mismatch stops the workflow before artifact upload.

The governed importer retains all three package files in the frozen release closure. The identity is not disposable import metadata: its retained destination is derived from the run-manifest path as `<run>.identity.json`, and Stable/readiness validation must reopen it, re-hash the retained run manifest and execution-evidence file, confirm the exact execution row is digest-bound to that evidence file, verify runtime provenance, validate evidence Git history, and only then rerun the published scorers.

Manual copying is not valid release evidence. The workflow itself does not commit, push, open a pull request, change approvals, or promote Stable.

## Release boundary

- Reference-contract CI remains responsible for all 44 published cases.
- Independent runtime evidence is required only for the 43 `behavioral_runtime` cases.
- `harness_only` cases are never sent to the external model runtime.
- RC1 remains immutable. This adapter is intended for a later RC selected after its implementation and the assurance-scope correction have passed executable CI.
