# Framework Feedback Capture — Specification V1

## Intent

Turn project execution lessons into durable, reviewable Framework feedback without self-modification.

## Inputs

- current project repository identity,
- exact pinned Framework ref,
- current task/workflow context,
- observation,
- durable evidence references,
- proposed improvement,
- classification metadata.

## Preconditions

- project is EREI-integrated (`.erei/framework.json` exists),
- feedback relates plausibly to Framework behavior/guidance or a reusable engineering lesson,
- at least one durable evidence reference is available.

## Invariants

1. Raw feedback is project-local.
2. Raw feedback is append-only at capture time.
3. Framework ref is exact, not inferred as `latest`.
4. Evidence is required.
5. Suggestion does not equal approval.
6. Capture never changes Framework Core or the project's Framework pin.
7. Sensitive material is referenced, not copied, when possible.
8. Project-specific observations may remain project-specific.
9. Semantic fingerprint enables later grouping without collapsing independent occurrences.
10. Promotion requires a separate Knowledge Promotion workflow.

## Classification vocabulary

### Type

- architecture_gap
- workflow_gap
- skill_gap
- role_gap
- security_gap
- data_gap
- verification_gap
- runtime_gap
- performance_gap
- context_gap
- integration_gap
- false_positive
- false_negative
- process_friction
- missing_pattern
- documentation_gap

### Severity

- low
- medium
- high
- critical

### Generalizability

- project_specific
- possible_generic
- likely_generic
- confirmed_multi_project

### Confidence

- low
- medium
- high

### Lifecycle status

Capture creates `new`. Later intake may move an event through:

`new → triaged → candidate → promoted | rejected | archived`

## Storage contract

`FRAMEWORK_FEEDBACK.jsonl` contains one valid Feedback Event V1 JSON object per non-empty line.

`FRAMEWORK_FEEDBACK.md` is derived and must not be treated as the machine source of truth.

## Failure behavior

Fail closed when:

- target project is missing,
- `.erei/framework.json` is missing,
- evidence is absent,
- required textual fields are empty,
- existing JSONL is corrupt,
- feedback lock cannot be acquired.

No partial ledger append should be reported as success.
