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

Measure retained evidence at a specific assurance level:

```bash
python evals/runner.py coverage evals/cases \
  --evidence evals/EXECUTION_EVIDENCE.json \
  --minimum-level exact_target_runtime
```

At runtime assurance levels, suites declared `harness_only` are intentionally excluded from the required behavioral case set. See `EXACT_TARGET_EVIDENCE.md`.

## Exit codes

- `0`: pass
- `1`: one or more valid eval cases failed
- `2`: harness/suite/adapter configuration or execution error

## Canonical suite

Each `*.eval.json` contains:

- `schema_version`
- `suite_id`
- `artifact`
- `assurance_scope`
- `cases[]`

`assurance_scope` is one of:

- `behavioral_runtime`: observable Framework behavior that must be evaluated by independent runtime evidence for managed/exact-target assurance;
- `harness_only`: an eval-harness self-test that remains mandatory in reference-contract CI but must not be treated as external behavioral evidence.

Each case contains:

- stable case ID,
- input payload,
- optional context/tags,
- deterministic expectations.

See `schema/eval-case.schema.json`.

## Adapter protocol

See `adapters/PROTOCOL.md`.

Adapters isolate runtime-specific behavior from EREI's canonical eval contract. The adapter request contains the artifact identity and case input/context/tags; scorer expectations remain in the harness and are not part of the adapter request.

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

The aggregate `Framework Assurance Gate` validates every published suite and executes all 44 current cases at reference-contract level. Independent exact-target evidence is a separate release gate over the 43 current `behavioral_runtime` cases; `harness-smoke/SMOKE-001` remains a harness-only self-test and is never counted as external behavioral evidence.
