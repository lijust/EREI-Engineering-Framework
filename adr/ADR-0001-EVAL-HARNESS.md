# ADR-0001 — Provider-Neutral Eval Harness Core

**Status:** Accepted  
**Date:** 2026-08-31  
**Accepted:** 2026-08-31  
**Risk:** L3 — Framework architecture/runtime contract

## Context

EREI Engineering Framework now has human-readable eval cases across skills, workflows, and technology overlays. The next requirement is automated execution.

The framework is explicitly portable across coding-agent runtimes. Making Promptfoo, DeepEval, Inspect AI, Braintrust, OpenAI Evals, or any other external system the canonical eval runtime would couple Framework Core to one ecosystem and risk schema/runtime drift.

At the same time, writing a large proprietary evaluation platform would violate the Constitution's simplicity and dependency rules.

## Decision

Adopt a **small provider-neutral EREI Eval Harness Core**.

### Canonical suite format

Machine-readable suites use versioned JSON files:

`*.eval.json`

Human-readable `CASES.md` files may remain as rationale/documentation, but automated acceptance must eventually have a machine-readable representation.

### Core runtime

- Python 3 standard library only.
- No required third-party package.
- No API key required for validation/self-tests.
- CLI-first and CI-friendly.
- Core runner remains small enough to audit directly.

Python is selected for the harness runtime because it is portable, widely available in engineering environments, strong for subprocess/JSON tooling, and does not impose a JavaScript/Node runtime on projects that do not otherwise use Node.

This choice applies to **Framework tooling**, not to project application stacks.

### Runtime adapter contract

Agent/model execution is externalized behind a language-neutral CLI protocol:

1. Harness sends one JSON request on stdin.
2. Adapter invokes the target runtime/agent.
3. Adapter returns one normalized JSON object on stdout.

Minimum normalized response:

```json
{
  "output": "...",
  "metadata": {},
  "trace": []
}
```

This allows adapters for:

- ChatGPT / Codex,
- Claude Code,
- Cursor,
- OpenCode,
- GitHub Copilot,
- Promptfoo,
- Inspect AI,
- DeepEval,
- Braintrust,
- provider-native APIs,
- local/mock deterministic runtimes.

### Scoring policy

Core uses deterministic scorers first.

V1 scorers:

- output contains all required concepts,
- output contains none of forbidden concepts,
- output regex,
- metadata equality,
- required tool called,
- forbidden tool not called,
- maximum trace steps.

Future deterministic scorers may be added when distinct evidence requires them.

Model-as-judge scoring is **optional** and lives behind adapters/plugins. It must not become the sole release blocker for deterministic security/data invariants.

### Exit semantics

- `0` — all requested validations/evals passed.
- `1` — valid harness execution with one or more failed cases.
- `2` — harness/configuration/adapter execution error.

### Source of truth

The repository remains the durable source of truth for:

- eval suites,
- expected behavior,
- scorer configuration,
- regression cases,
- adapter contracts.

Hosted eval platforms may receive/export results but do not replace repository truth.

## Consequences

### Benefits

- no vendor lock-in,
- zero third-party Core dependency,
- deterministic-first behavior,
- usable in local and CI environments,
- external eval tools remain available where they add value,
- same case can be run against multiple runtimes,
- supports routing/trace/evidence evaluation, not only answer quality.

### Costs

- EREI owns a small protocol and runner,
- adapters must be maintained,
- sophisticated semantic/agent scoring still requires optional external tooling or model graders,
- existing Markdown eval cases need gradual machine-readable migration.

## Rejected alternatives

### Make Promptfoo the canonical harness
Rejected as Core architecture because it would make its runtime/config model authoritative for EREI. Keep as an adapter candidate.

### Make DeepEval the canonical harness
Rejected as Core architecture because its strongest value is LLM/trace quality evaluation, while many EREI governance assertions are deterministic and cross-runtime. Keep as an adapter candidate.

### Make Inspect AI the canonical harness
Rejected as Core architecture because it is more capable and heavier than needed for the portable contract layer. Keep as an advanced adapter candidate.

### Use a hosted eval platform as source of truth
Rejected because durable project/framework state must survive vendor/account/runtime changes.

### Build a full proprietary eval platform
Rejected as overengineering. V1 deliberately implements only the minimum stable abstraction.

## Decision record

ADR-0001 was explicitly approved under the L3 architecture gate on 2026-08-31. Eval Harness V1 may be promoted to the stable Framework baseline, subject to normal release verification and metadata promotion.