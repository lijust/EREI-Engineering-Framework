# Eval Harness Benchmark

**Status:** Research V1  
**Date:** 2026-08-31

## Goal

Select an evaluation architecture for EREI Engineering Framework that can test framework assets across multiple agent runtimes without locking Framework Core to one model vendor, one SaaS platform, or one eval library.

The target is broader than LLM answer quality. EREI needs to evaluate:

- skill triggering and non-triggering,
- workflow/risk routing,
- required/forbidden behavior,
- tool usage and tool non-usage,
- trace shape and efficiency,
- evidence obligations,
- stop/escalation behavior,
- regression cases from real project failures,
- optional model-graded quality where deterministic checks are insufficient.

## Benchmarked approaches

### Inspect AI
Repository: `UKGovernmentBEIS/inspect_ai`

Strengths:
- mature Python evaluation framework,
- tool use and multi-turn agent evaluation,
- model-graded scoring,
- extensible tasks/solvers/scorers,
- strong reproducibility and evaluation ecosystem.

Tradeoff for EREI:
- powerful but substantially larger than the minimum runtime needed for framework routing/contract evals,
- would make a third-party Python framework a hard dependency of Framework Core if adopted directly.

Decision: **ADAPTER CANDIDATE, NOT CORE DEPENDENCY**.

### DeepEval
Repository: `confident-ai/deepeval`

Strengths:
- pytest-like developer ergonomics,
- agent trace evaluation,
- task completion, tool correctness, reasoning/action/execution metrics,
- broad LLM/agent framework integrations.

Tradeoff for EREI:
- optimized for LLM application quality and trace metrics,
- introduces an external package and optional platform ecosystem,
- many EREI governance/routing assertions are more deterministic than LLM-as-judge metrics.

Decision: **OPTIONAL TRACE/JUDGE ADAPTER, NOT CORE DEPENDENCY**.

### Promptfoo
Repository: `promptfoo/promptfoo`

Strengths:
- declarative test configuration,
- strong CLI/CI ergonomics,
- provider comparison,
- red teaming/security testing,
- broad provider support.

Tradeoff for EREI:
- Node-oriented primary runtime,
- its configuration model should not become the canonical EREI artifact format,
- EREI must also test non-prompt artifacts such as role/workflow routing contracts.

Decision: **OPTIONAL CI/RED-TEAM ADAPTER, NOT CORE DEPENDENCY**.

### Braintrust
Repository: `braintrustdata/braintrust-sdk-python`

Strengths:
- eval datasets/scorers,
- tracing and observability,
- wide framework/provider integrations,
- strong iteration analysis and hosted workflows.

Tradeoff for EREI:
- platform/API-key coupling for the full value proposition,
- EREI's durable source of truth must remain repository-local and runnable without a hosted service.

Decision: **OPTIONAL OBSERVABILITY/EVAL EXPORT ADAPTER**.

### OpenAI Evals / provider-specific eval systems

Strengths:
- strong model/system evaluation capabilities,
- useful provider-native graders and datasets.

Tradeoff for EREI:
- provider-specific dependency conflicts with the portability requirement.

Decision: **RUNTIME ADAPTER ONLY**.

## Common patterns worth adopting

Across the evaluated systems, the strongest reusable patterns are:

1. Machine-readable eval cases.
2. Separate dataset/case definition from execution runtime.
3. Multiple scorer types rather than one universal correctness metric.
4. Trace-aware evaluation for agents.
5. CLI/CI execution with non-zero exit on failure.
6. Reproducible, versioned eval assets.
7. Regression cases promoted from real failures.
8. Optional model-graded evaluation for inherently semantic criteria.

## EREI-specific requirements not fully solved by choosing one tool

EREI additionally needs:

- zero required SaaS dependency,
- cross-runtime adapters for ChatGPT/Codex, Claude, Cursor, OpenCode, Copilot and future agents,
- deterministic-first scoring consistent with the Engineering Constitution,
- ability to evaluate role/skill/workflow routing metadata, not only final text,
- explicit tool-call trace assertions,
- stable machine-readable protocol that external tools can consume,
- capability to use third-party eval frameworks without making their schemas the EREI source of truth.

## Recommendation

Build a small **EREI Eval Harness Core** with:

- Python standard library only,
- canonical `*.eval.json` suites,
- a language/runtime-neutral CLI adapter protocol over JSON stdin/stdout,
- deterministic scorers in Core,
- external/model graders as optional adapters,
- CI-friendly exit codes,
- no required model provider or hosted service.

Then integrate external systems where they add distinct value:

- Inspect AI for sophisticated agent/model evaluation,
- DeepEval for trace-centric agent quality metrics,
- Promptfoo for declarative provider comparison/red-team workflows,
- Braintrust for tracing/experiment analytics,
- provider-native eval APIs when a project explicitly wants them.

## Why not adopt an existing framework wholesale?

The concern is not that existing frameworks are weak. They are stronger than a bespoke tool in their own target domains. The issue is **architectural ownership**: EREI needs one canonical evaluation contract that can be executed by many runtimes and exported to many evaluation systems.

The smallest stable abstraction is therefore:

`EREI eval suite → EREI adapter protocol → runtime → normalized result → deterministic/optional scorers`

External frameworks plug into that architecture rather than defining it.