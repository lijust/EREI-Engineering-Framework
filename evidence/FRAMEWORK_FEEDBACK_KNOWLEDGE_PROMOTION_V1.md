# Framework Feedback Capture + Knowledge Promotion V1 — Release Evidence

**Date:** 2026-09-02  
**Status:** Stable release evidence

## Candidate

- Branch: `framework-feedback-v1`
- PR: `#24 — Framework Feedback Capture and Knowledge Promotion V1`
- Approved candidate head: `a8e9f95b7980c5c007c5fd9ea296d7d1dd83b8f2`
- Merge commit: `378e5843fca57c7dfcd8ba8256ca52e2a6a25efe`

## CI evidence on exact candidate head

- Framework Feedback Tests — **SUCCESS** — run `33562814353`
- Framework Evals — **SUCCESS** — run `33562814167`
- Project Bootstrap Tests — **SUCCESS** — run `33562814204`

## Stable capability delivered

### Project-local feedback capture

Projects can durably record evidence-backed Framework observations under:

```text
.erei/feedback/
├── README.md
├── FRAMEWORK_FEEDBACK.md
└── FRAMEWORK_FEEDBACK.jsonl   # created on first event
```

`FRAMEWORK_FEEDBACK.jsonl` is the machine-readable source of truth.

### Feedback event contract

`schemas/framework-feedback.schema.json` defines:

- exact Framework ref,
- source project identity,
- feedback type/severity,
- observation,
- durable evidence references,
- suggested improvement,
- generalizability/confidence,
- lifecycle state,
- semantic fingerprint,
- optional negative learning/tags/source artifact.

### Deterministic tooling

- `tools/capture_framework_feedback.py`
- `tools/validate_framework_feedback.py`

Both use Python standard library only.

Capture is fail-closed when the project is not EREI-integrated, evidence is missing, existing JSONL is corrupt, or the feedback ledger lock cannot be acquired.

The validator checks event shape and recomputes the semantic fingerprint so edited semantics cannot silently retain a stale fingerprint.

### Workflow integration

The Framework Feedback Check is integrated into:

- Chief Engineer routing,
- feature-development workflow,
- bug-fix workflow,
- project bootstrap `AGENTS.md` and project rules templates.

Ordinary project bugs are not automatically Framework feedback.

### Knowledge Promotion

`workflows/knowledge-promotion/WORKFLOW.md` separates raw project observation from Framework decision-making.

Promotion requires:

1. source/evidence validation,
2. project-vs-Framework root-cause separation,
3. classification,
4. deduplication/clustering without deleting independent occurrences,
5. removal of project-specific assumptions,
6. complexity/value gate,
7. Framework candidate + eval/test coverage,
8. normal risk/approval gates,
9. independent verification,
10. Candidate → Stable promotion or documented rejection.

### Framework-side review

- `feedback/README.md`
- `feedback/REVIEW_QUEUE.md`

Raw feedback remains source-project owned. Projects do not write directly into Framework Core during capture.

## Safety invariants verified by design/tests

- no automatic Framework self-modification,
- no automatic project Framework-pin update,
- evidence required for capture,
- exact pinned Framework provenance,
- project-local raw feedback ownership,
- secret/sensitive-content copy discouraged; protected evidence should be referenced,
- feedback suggestion is a hypothesis, not an approved solution,
- L3/L4 changes still require explicit approval,
- promoted changes reach projects only through Framework Upgrade Workflow.

## Project impact

No project repository or project Framework pin was changed by PR #24.

Existing projects remain on their current immutable Stable Framework revision until a separate, conflict-aware Framework Upgrade Workflow is executed in that project.
