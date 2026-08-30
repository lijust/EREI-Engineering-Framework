# Eval Harness Research

**Status:** Architecture research V1  
**Date:** 2026-08-31

## Objective

Define how EREI Engineering Framework should test its own agents, skills, workflows, overlays, and adapters without binding the framework to one model vendor or turning every check into an expensive LLM evaluation.

---

## Sources reviewed

### Anthropic Skill Creator
Repository: `anthropics/skills`  
File: `skills/skill-creator/SKILL.md`

Observed patterns:
- create realistic eval prompts,
- save machine-readable eval definitions,
- run **with-skill and baseline** variants for comparison,
- add objectively verifiable assertions where possible,
- use scripts for programmatically checkable assertions rather than subjective eyeballing,
- use grader model/agent when judgment is genuinely required,
- aggregate pass rate, timing, token use, variance and deltas,
- analyze non-discriminating/flaky evals,
- use holdout cases,
- combine quantitative results with qualitative review,
- optimize skill triggering separately from output behavior.

Key implication for EREI:
A skill should demonstrate **incremental value over baseline**, not merely produce an acceptable answer once.

### Superpowers testing/evals
Repository: `obra/superpowers`  
Files reviewed:
- `docs/testing.md`
- `docs/superpowers/specs/2026-05-06-lift-drill-into-evals-design.md`

Observed patterns:
- clear split between deterministic/plugin tests and LLM behavior evals,
- behavior evals run real coding-agent sessions,
- actor + verifier structure,
- cross-runtime support (e.g. Claude/Codex/Gemini and additional CLI backends),
- scenario fixtures and setup helpers,
- behavioral evals are materially slower/costlier than deterministic tests,
- current guidance points toward tiering: fast subset on PR; full behavioral sweep nightly/on-demand,
- deterministic tests are removed only after behavior-eval coverage is verified assertion-by-assertion.

Key implication for EREI:
Do not replace deterministic verification with LLM evals. They test different properties.

### Sentry Skills
Repository: `getsentry/skills`  
File reviewed: `skills/prompt-optimizer/SPEC.md`

Observed patterns:
- eval-backed maintenance contract lives in SPEC,
- representative working set + holdout validation,
- trigger QA is separate from behavior quality,
- candidate comparisons use the same eval slice,
- residual risk and limitations remain explicit,
- model/provider changes are a reason to re-run evals.

Key implication for EREI:
Eval results are version/model/runtime-sensitive evidence, not permanent truth.

---

# Requirements derived for EREI

## ER-001 — Separate deterministic tests from model behavior evals

EREI needs two fundamentally different test systems:

1. **Framework structural/deterministic tests**
   - file/schema/metadata validation,
   - broken reference detection,
   - duplicate/ambiguous IDs,
   - required sections/contracts,
   - source/provenance checks,
   - adapter/install/config checks,
   - scripts and deterministic assertions.

2. **Agent behavior evals**
   - trigger/routing correctness,
   - procedure compliance,
   - unsafe shortcut rejection,
   - evidence discipline,
   - role boundary adherence,
   - workflow gate behavior,
   - cross-runtime behavior.

They must not be conflated.

## ER-002 — Deterministic first

If an assertion can be evaluated reliably by code, use code.

Examples:
- required output file exists,
- JSON field has expected value,
- forbidden file changed,
- server-side auth check exists at known boundary,
- expected test command passed,
- branch/diff matches constraints.

Use model grading only for genuinely semantic behavior.

## ER-003 — Machine-readable scenarios

Current Markdown eval cases are valuable for design/review but not sufficient for automation.

A machine-readable scenario needs at least:

```text
id
artifact_under_test
kind
prompt/context
fixture
expected_triggers
forbidden_triggers
assertions
risk
runtime_requirements
repeat_count
```

## ER-004 — Baseline comparison

For important Skill changes, support:
- candidate skill vs no skill, or
- candidate skill vs previous stable skill.

This reveals whether added instructions actually improve behavior or merely add tokens/time.

## ER-005 — Trigger and behavior are separate dimensions

A Skill can fail because:
1. it does not trigger when needed,
2. it triggers when it should not,
3. it triggers correctly but executes poorly.

The harness must score these independently.

## ER-006 — Variance matters

A single successful run is weak evidence for model behavior.

Behavioral scenarios should support repeat counts and report:
- pass rate,
- variance/failure distribution,
- latency,
- tokens/cost when runtime exposes them.

## ER-007 — Holdout cases

Do not optimize all Skills against the same visible scenarios indefinitely.

Support a holdout set not used during ordinary prompt/skill tuning.

## ER-008 — Cross-runtime adapters

Core eval scenarios must not embed one vendor's CLI syntax.

Use an adapter interface:

```text
Scenario
   ↓
EREI Eval Runner
   ↓
Runtime Adapter
   ├── Codex
   ├── Claude Code
   ├── OpenCode
   ├── Copilot
   └── future runtimes
```

## ER-009 — Tiered execution

Proposed tiers:

### Tier 0 — Static validation
Fast, deterministic, no LLM/API.
Run on every relevant change.

### Tier 1 — Deterministic fixture tests
Scripts/tests against fixtures and artifact structure.
Fast enough for normal PR CI.

### Tier 2 — Behavioral smoke evals
Small high-value model-driven subset.
Run on important Skill/Agent/Workflow changes or opt-in PR check.

### Tier 3 — Full behavioral matrix
Multiple scenarios × repeats × runtimes/models.
Run nightly/on-demand/release candidate due cost/time.

### Tier 4 — Cross-runtime qualification
Used for adapter/framework releases, not ordinary content edits.

## ER-010 — Evidence provenance

Every behavioral result should record:
- framework commit,
- artifact version/hash,
- runtime adapter,
- model/runtime identifier when available,
- date/time,
- scenario version,
- grader type/version,
- raw/derived evidence references.

---

# Architecture options considered

## Option A — Adopt a heavy external harness directly

Examples: embed/fork a real-agent harness similar to Drill.

### Advantages
- sophisticated behavioral execution immediately,
- established actor/verifier pattern,
- multi-runtime precedent.

### Disadvantages
- large dependency/runtime footprint,
- Python environment + CLI/tmux/provider configuration,
- stronger coupling to upstream architecture,
- supply-chain/maintenance burden,
- excessive complexity before EREI's own scenario schema stabilizes.

### Decision
**Reject for V1. Re-evaluate later.**

---

## Option B — No runner; keep Markdown evals only

### Advantages
- zero dependencies,
- simple.

### Disadvantages
- cannot measure regressions automatically,
- no repeat/variance/baseline comparison,
- difficult cross-runtime qualification,
- evals remain documentation rather than tests.

### Decision
**Reject.**

---

## Option C — Lightweight EREI-native core + adapters

Build a minimal provider-neutral harness with:
- machine-readable JSON scenarios,
- Python standard-library core runner/validator initially,
- deterministic assertion plugins/scripts,
- runtime adapter interface,
- optional model-judge adapter,
- results in JSON/Markdown,
- CI Tier 0/1 first,
- Tier 2/3 behavioral adapters added incrementally.

Avoid mandatory SDKs/provider packages in Core V1. External CLIs/API integrations live behind optional adapters.

### Advantages
- minimal core dependency surface,
- portable,
- deterministic-first,
- lets scenario contract stabilize before heavier tooling,
- can later wrap/reuse external harnesses as adapters,
- consistent with Framework Constitution.

### Disadvantages
- some runner code must be maintained,
- real-agent execution arrives incrementally rather than all at once,
- initial behavioral feature set is less sophisticated than Drill.

### Recommendation
**ADOPT Option C.**

---

# Recommended V1 boundary

Implement only:

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

V1 runner uses Python standard library where practical.

Do **not** initially require:
- tmux,
- provider Python SDKs,
- one mandatory LLM provider,
- hosted evaluation service,
- database,
- custom web viewer.

Later adapters may add:
- Codex CLI,
- Claude Code,
- OpenCode,
- Copilot,
- LLM-as-judge,
- external harness integration.

---

# Recommended grading model

Assertions should declare grader type:

```text
deterministic
semantic
human
```

### Deterministic
Executed by code/script and considered primary when possible.

### Semantic
Evaluated through a runtime/model grader with exact criteria and evidence requirement.

### Human
Used only where subjective/product judgment is genuinely required.

No semantic grader should expose or require hidden chain-of-thought. It grades observable outputs/evidence only.

---

# Recommended adoption sequence

1. Approve scenario/result contracts and V1 boundary.
2. Create JSON Schemas.
3. Convert existing Markdown eval cases gradually; keep Markdown as readable design docs during transition.
4. Build deterministic loader/validator/assertion runner.
5. Add framework self-tests.
6. Add first optional real-agent adapter (recommended: Codex, because EREI is being developed through OpenAI/GitHub workflow and portability interface can be validated immediately).
7. Add candidate-vs-baseline and repeated-run aggregation.
8. Add second runtime adapter to prove portability.
9. Only then consider heavier external harness integration or nightly matrix.

---

# Architectural decision requiring approval

This research recommends:

> **EREI Eval Harness V1 = lightweight provider-neutral Python/JSON core, deterministic-first, with optional runtime adapters and tiered behavioral evals. No mandatory external LLM SDK/harness dependency in Core V1.**

This introduces a new executable framework subsystem and therefore should be treated as an L3 architecture decision requiring explicit approval before implementation.