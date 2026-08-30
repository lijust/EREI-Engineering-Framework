# ADR-0001 — EREI Eval Harness V1 Architecture

**Status:** PROPOSED  
**Date:** 2026-08-31  
**Decision type:** L3 Framework Architecture  
**Approval:** Required before implementation

## Context

EREI Engineering Framework now contains executable-behavior specifications for agents, skills, workflows, overlays, and many human-readable eval cases.

Markdown cases are useful design artifacts but cannot provide automated regression measurement, repeated-run variance, baseline comparison, or cross-runtime qualification.

Research of current skill/eval systems identified complementary patterns:
- deterministic/plugin tests should remain separate from model-behavior evals,
- programmatically checkable assertions should use deterministic code rather than model judgment,
- important skill changes benefit from candidate-vs-baseline comparison,
- behavior evals should support repeated runs, variance, holdouts, timing/token evidence, and runtime identity,
- full real-agent matrices are expensive and should be tiered rather than mandatory on every change.

See `research/EVAL_HARNESS_RESEARCH.md`.

## Decision

Adopt a lightweight EREI-native Eval Harness V1 with:

1. **Provider-neutral scenario/result contracts** using JSON and JSON Schema.
2. **Python core runner**, targeting the standard library where practical.
3. **Deterministic-first grading** for assertions that code can decide reliably.
4. **Optional runtime adapters** for real-agent execution rather than a mandatory provider SDK in Core.
5. **Separate semantic/model grader adapter** only for genuinely semantic assertions.
6. **Tiered execution**:
   - Tier 0 static validation,
   - Tier 1 deterministic fixture tests,
   - Tier 2 behavioral smoke evals,
   - Tier 3 full behavioral matrix,
   - Tier 4 cross-runtime qualification.
7. **Candidate-vs-baseline comparison** for important skill changes.
8. **Repeat/variance support** for model behavior.
9. **Holdout scenarios** for release qualification.
10. **Evidence provenance** recording framework commit, artifact/scenario versions, runtime/model/grader identity, timing and result scope when available.

## V1 repository boundary

```text
evals/
├── README.md
├── schemas/
│   ├── scenario.schema.json
│   └── result.schema.json
├── scenarios/
│   ├── skills/
│   ├── workflows/
│   ├── agents/
│   └── overlays/
├── runner/
│   ├── __main__.py
│   ├── loader.py
│   ├── validators.py
│   ├── assertions.py
│   ├── results.py
│   └── adapters/
│       ├── base.py
│       └── deterministic.py
└── tests/
```

## V1 non-decisions / deferred scope

V1 does **not** mandate:
- tmux,
- provider Python SDKs,
- hosted eval service,
- database,
- web viewer,
- one required LLM provider,
- full behavioral matrix in every PR CI run.

Runtime adapters are added separately and can use external CLIs/APIs without contaminating Core contracts.

## Why Python

- strong portability across development environments,
- mature subprocess/JSON/testing tooling,
- appropriate for future CLI/runtime adapters,
- no need for a frontend/build toolchain,
- can begin with standard library and add dependencies only when measurable benefit justifies them.

Python is the harness implementation language, not a requirement imposed on projects that consume EREI Framework.

## Why JSON scenarios

- standard-library parsing,
- precise machine-readable contracts,
- straightforward JSON Schema definition,
- avoids a mandatory YAML parser dependency in Core V1,
- portable across runtime adapters/languages.

Human-readable Markdown eval design files may coexist and be gradually converted.

## Alternatives rejected

### Adopt/fork a heavy real-agent harness immediately
Rejected for V1 due runtime/dependency/supply-chain complexity before EREI's own scenario contract stabilizes.

### Markdown/manual evals only
Rejected because regression measurement, automation, variance and portability cannot be established reliably.

### LLM grader for all assertions
Rejected because it violates deterministic-first policy and increases cost/variance for objectively checkable outcomes.

### One provider SDK as the core runtime
Rejected because it creates vendor coupling inconsistent with Framework portability goals.

## Consequences

### Positive
- minimal dependency surface,
- portable core,
- reproducible deterministic checks,
- incremental path to real-agent evals,
- external harnesses can later be integrated as adapters rather than copied wholesale,
- aligns with Constitution principles on evidence, determinism, complexity, portability and dependency restraint.

### Negative
- EREI maintains a small runner codebase,
- advanced actor/verifier functionality arrives later,
- JSON scenarios are more verbose than YAML,
- real-agent qualification requires separately installed/authenticated runtimes.

## Security and privacy

- Eval fixtures must not contain production secrets, credentials, private customer data, or unnecessary sensitive project content.
- Runtime adapters must declare what data is sent to external model/provider services.
- Raw eval transcripts/results require project-appropriate handling when they include code or proprietary context.
- Semantic grading must judge observable output/evidence and must not request hidden chain-of-thought.

## Validation plan

Before marking the harness Stable:
1. schema/loader tests pass,
2. deterministic assertion runner passes self-tests,
3. several existing Skill evals are converted and executed,
4. should-trigger and should-not-trigger scenario representation is proven,
5. candidate-vs-baseline result format is exercised,
6. repeated results aggregate correctly,
7. malformed/unsafe scenario files fail closed,
8. one optional runtime adapter demonstrates the interface without becoming a Core dependency.

## Rollback

Until Stable, the harness is additive. Existing Markdown eval cases remain authoritative design artifacts and no current workflow depends exclusively on the new runner.

If V1 architecture proves unsuitable, remove the executable harness while preserving scenario/evidence research and existing Markdown evals.

## Approval gate

Implementation may begin only after explicit approval of ADR-0001.