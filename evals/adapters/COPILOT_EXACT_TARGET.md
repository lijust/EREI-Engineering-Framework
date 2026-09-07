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

Because this repository is personal-account owned, the controlled workflow requires the dedicated `EREI_COPILOT_EXACT_TARGET_TOKEN` secret rather than silently falling back to the normal Actions `GITHUB_TOKEN`. The workflow also requires an exact `@github/copilot` npm version input and records the observed CLI version as runtime identity evidence; `latest` is not accepted for release evidence.

## Evidence production

`.github/workflows/vnext-exact-target-copilot.yml` is manual-only and requires an exact frozen release carrier and validated `VNEXT_TARGET.json`. It checks out the exact target revision/tree, runs behavioral exact-target evidence, validates complete coverage, confirms only the two evidence outputs changed in the target checkout, and uploads an Actions artifact.

The V2 run manifest retains each normalized adapter response in addition to its response digest and status. Stable/readiness validation must be able to reload the published case, validate the retained response, rerun the authoritative scorers, and reproduce the recorded PASS/FAIL result. Digest-only exact-target manifests are not sufficient for V2 Stable.

The workflow does not commit, push, open a pull request, change approvals, or promote Stable. Evidence must later enter the frozen release closure through the governed immutable-evidence process.

## Release boundary

- Reference-contract CI remains responsible for all 44 published cases.
- Independent runtime evidence is required only for the 43 `behavioral_runtime` cases.
- `harness_only` cases are never sent to the external model runtime.
- RC1 remains immutable. This adapter is intended for a later RC selected after its implementation and the assurance-scope correction have passed executable CI.
