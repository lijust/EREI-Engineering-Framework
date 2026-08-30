# EREI Eval Harness

**Status:** Candidate V1 — governed by `ADR-0001-EVAL-HARNESS.md`

## Purpose

Automate evaluation of EREI framework assets without coupling the framework to one agent runtime or external eval vendor.

The harness evaluates:

- skill trigger behavior,
- role/workflow routing,
- expected and forbidden output concepts,
- normalized metadata such as risk/route decisions,
- tool-call traces,
- bounded step behavior,
- regression scenarios promoted from real failures.

## Core design

```text
*.eval.json
    ↓
EREI runner
    ↓ JSON stdin
CLI adapter
    ↓ target runtime / agent
normalized JSON result
    ↓
deterministic scorers
    ↓
PASS / FAIL / HARNESS ERROR
```

Core has **zero third-party Python dependencies**.

## Commands

Validate suite files:

```bash
python evals/runner.py validate evals/cases
```

Run through an adapter:

```bash
python evals/runner.py run evals/cases \
  --adapter "python evals/fixtures/mock_adapter.py"
```

Run a specific suite:

```bash
python evals/runner.py run evals/cases/impact-analysis.eval.json \
  --adapter "<adapter command>"
```

## Exit codes

- `0`: pass
- `1`: one or more valid eval cases failed
- `2`: harness/suite/adapter configuration or execution error

## Canonical suite

Each `*.eval.json` contains:

- `schema_version`
- `suite_id`
- `artifact`
- `cases[]`

Each case contains:

- stable case ID,
- input payload,
- optional context/tags,
- deterministic expectations.

See `schema/eval-case.schema.json`.

## Adapter protocol

See `adapters/PROTOCOL.md`.

Adapters isolate runtime-specific behavior from EREI's canonical eval contract.

## Scoring philosophy

Deterministic checks come first.

V1 supports:

- `output_contains_all`
- `output_contains_none`
- `output_regex`
- `metadata_equals`
- `trace_tool_called`
- `trace_tool_not_called`
- `max_trace_steps`

Semantic/model-graded scorers may be provided later through optional adapters/extensions. They must not silently replace deterministic security/data invariants.

## Markdown evals

Existing `CASES.md` files remain valuable as human-readable rationale and regression documentation.

Migration policy:

1. Keep the narrative case when useful.
2. Add a machine-readable `*.eval.json` case for behavior that can be automated.
3. Give real escaped defects permanent regression IDs.
4. Do not mechanically convert prose that has no stable observable assertion.

## CI

The runner is intentionally CLI-first and returns stable exit codes so GitHub Actions or any other CI system can call it later without changing the canonical eval format.

Adding a CI workflow is a separate release/integration decision.