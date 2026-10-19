# Learning-to-Development Workflow V1

**Status:** Candidate V1  
**Activation:** Dormant unless explicitly active under Candidate Capability Activation Governance; project trials use `.erei/CANDIDATE_CAPABILITIES.json`.  
**Release boundary:** Outside Task Learning V2 Core Stable scope.  
**Purpose:** Turn Task Learning evidence into bounded engineering-development outputs without letting metrics self-modify the Framework.

## Entry gate

Before entering this workflow, including invocation from Learning Review or the router, run `tools/capability_activation.py --target <project> --capability learning_to_development`. Proceed only on `ACTIVE_STABLE` or `ACTIVE_CANDIDATE`. On `DORMANT_CANDIDATE`, return to Core review findings/actions/closure without creating or persisting an LDO. On `BLOCK_*` or resolution failure, stop translation and repair the activation evidence.

Resolve each subordinate capability separately immediately before use. This workflow's adoption does not authorize `learning_pattern_analysis`, `framework_effectiveness_measurement`, or `learning_review_debt_guard`. No workflow authority, project pin upgrade, or source artifact validation substitutes for exact capability/ref/version adoption.

## Ownership

The **Chief Engineer owns translation and interpretation** of learning evidence, with QA and the relevant specialist roles supplying evidence and challenge.

Deterministic tools may:
- compute metrics,
- detect review debt,
- cluster observable signals,
- identify comparable cohorts,
- validate schemas/evidence.

They do **not** decide root cause or authorize Framework mutation.

## Core translation path

```text
Task Learning events
→ deterministic Pattern Analysis
→ Learning Review
→ evidence-backed interpretation
→ Learning Development Output
→ project action / measurement adjustment / Framework Feedback
→ candidate implementation when justified
→ eval + real trial
→ Stable promotion when justified
→ project adoption
→ before/after effectiveness measurement
```

## Metric semantics

Never label these raw metrics as execution accuracy:

- `rework_rate`: share of assessed material tasks with >=1 material iteration after the first candidate;
- `verification_failure_rate`: share of assessed material tasks with >=1 failed deterministic verification attempt;
- `verification_escape_task_rate`: share of material tasks whose prior verification/completion assumption was contradicted later;
- `final_failed_task_rate`: share of material tasks ending in terminal `failed`.

Interpret together with:
- rework-free task rate,
- rework cycles per material task,
- verification-clean task rate,
- lifecycle failure stage,
- escape rate,
- terminal outcomes,
- task risk/workflow mix.

A high pre-merge catch rate can indicate strong assurance. A verification escape is a stronger negative signal.

## Procedure

### 1. Freeze evidence

Bind the exact project, epoch/review, Framework ref and evidence set.

### 2. Compute deterministic patterns

Resolve `learning_pattern_analysis` separately, then run `tools/learning_pattern_analysis.py --target <project>` (or guarded `analyze_target`) only when active. If dormant, use the Core review's retained evidence and explicitly record that optional analysis was skipped; if the requested outcome requires it, stop that outcome. Activation failure prohibits analyzer dispatch.

### 3. Interpret each material signal

For every notable pattern, answer:

1. What exactly happened?
2. At which lifecycle stage?
3. What invariant/assumption was violated?
4. Was the issue caught before acceptance or did it escape prior assurance?
5. Is the mechanism project-local or reusable?
6. Does an existing Framework pattern already cover it?
7. What additional evidence could falsify the proposed interpretation?

### 4. Classify

Use one review classification:

- `HEALTHY_PATTERN`
- `PROJECT_LOCAL_ACTION`
- `FRAMEWORK_FEEDBACK`
- `MEASUREMENT_ADJUSTMENT`
- `NEEDS_MORE_EVIDENCE`
- `CRITICAL_FOLLOWUP`

Map reusable mechanisms to `learning/PATTERN_TAXONOMY.json`.

### 5. Produce a Learning Development Output

Use `schemas/learning-development-output.schema.json`.

Every output records:
- source epoch/review,
- pattern ID/class,
- human interpretation,
- classification,
- development route,
- durable evidence,
- expected effect,
- success metrics,
- promotion boundary.

### 5.1 Persist provenance

The canonical project-local location is:

```text
.erei/learning/development-outputs/<LDO-ID>.json
```

The source project owns this provenance record. Re-resolve `learning_to_development` immediately before project output generation/persistence if the invocation resumes later or its approval may have expired. Validate project outputs with `tools/learning_development_output.py --target <project> --input <output>`. The validator's standalone `--input` form only checks retained artifact structure; it does not generate outputs or activate this workflow.

When a Framework-relevant output is accepted into central intake, the Framework may retain a generalized copy under:

```text
learning/development-outputs/<LDO-ID>.json
```

The Framework copy must retain source project/review/evidence references and must not silently replace or rewrite the project-local source.

### 6. Convert to development

Allowed routes:

- no change,
- project-local change,
- Framework Feedback,
- Framework Candidate,
- measurement change,
- workflow change,
- tooling change,
- specialist review,
- evidence collection.

A `FRAMEWORK_FEEDBACK` classification does not itself authorize a Framework Candidate.

### 7. Define effectiveness before implementation

Before changing Framework behavior, define the expected measurable effect.

Prefer:
- verification escape rate,
- final failed-task rate,
- review-debt frequency,
- context-gap/manual-workaround rate,
- exact-conformance escape count,
- repeated root-cause recurrence,
- rework-free rate only when task mix is reasonably comparable.

Do not optimize for fewer failing tests by weakening verification.

### 8. Trial and measure

After Candidate adoption, use a bounded real cohort.

Resolve `framework_effectiveness_measurement` separately. Only when active, compare before/after using `tools/learning_effectiveness.py --target <project> --before <report> --after <report>` or guarded `compare_target`. A dormant measurement capability is skipped and recorded as unmeasured, never reported as evidence of effectiveness. Activation failure prohibits the comparison dispatch; translation adoption alone is insufficient.

No causal claim is allowed solely from a raw metric delta. Task/risk/workflow comparability and confounders must be reviewed.

### 9. Promote or reject

Only normal Knowledge Promotion and Stable release governance may promote a Framework change.

## Review-debt rule

Before applying review-debt policy, derive the current Learning State from the authoritative Task Learning event/review ledgers using `tools/task_learning.py status --target <project>` or equivalent locked derivation. Never trust a stale or absent `LEARNING_STATE.json` projection as evidence that review debt is clear.

Use `tools/learning_review_debt_gate.py --target <project> --state <derived-state>` (optional `--defer <record>`). Core state validation and security/data stops remain unconditional. The following ordinary debt/defer policy applies only when the gate resolves `learning_review_debt_guard` as active. When dormant, retain Core trigger handling and underlying security/data/verification stops without requiring or applying a bounded defer. Activation failure prohibits Candidate policy use.

If authoritative derivation reaches `IMMEDIATE_REVIEW` — or the debt gate derives an effective immediate-review requirement from escape/critical metrics — the default is to close the Learning Review before accumulating a large new material cohort.

Continuation is allowed only through a bounded defer record with:
- exact epoch,
- reason,
- evidence,
- explicit reviewer role,
- expiry,
- maximum additional material tasks.

The defer never overrides security/data/release blocking evidence.

## Intake cadence

Framework intake is **event-driven**, not calendar-driven:

- high/critical reusable feedback → central intake promptly;
- any closed Learning Review that creates Framework Feedback → central intake before the feedback is treated as resolved;
- repeated same fingerprint/pattern → deduplicate/cluster immediately;
- no-feedback reviews remain project-local.

## Cross-project boundary

A single project can justify a Candidate when evidence is strong and bounded.  
Claims of broad generic effectiveness require a second materially different project or an explicit reason why cross-project evidence is not necessary.

## Definition of Done

Learning is converted to development only when:
- raw metrics are interpreted correctly,
- root cause is not inferred from correlation alone,
- reusable vs project-local scope is explicit,
- a durable Learning Development Output exists,
- development route is explicit,
- effectiveness metrics are defined before promotion,
- no automatic self-modification or pin movement occurred.
