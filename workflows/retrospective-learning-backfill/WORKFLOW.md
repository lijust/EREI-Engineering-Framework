# Retrospective Learning Backfill Workflow V1

## Purpose
Recover useful engineering experience from work completed before Task Learning V1 was enabled, without pretending retrospective reconstruction has the same evidentiary quality as prospective capture.

## Core rule
Historical evidence is supporting learning evidence. It is stored separately from prospective `TASK_EVENTS.jsonl` and does not automatically advance prospective review-trigger task counts.

## Inputs
- source project repository;
- exact Framework ref active when the historical work occurred, when known;
- durable sources such as merged PRs, commits, CI runs, release evidence, ADRs, incident records and verified runtime artifacts;
- no private chain-of-thought, credentials, customer/tenant payloads or unnecessary raw transcripts.

## Evidence quality
- `confirmed`: the exact signal is directly stated/proven by durable evidence;
- `reconstructed`: the event/task is reliably reconstructed from durable metadata, but not captured prospectively at execution time;
- `inferred`: a plausible signal derived after the fact; it must never be silently promoted to confirmed.

Each reconstructed signal carries its own quality and source refs.

## Procedure
1. Select a bounded historical cohort and record start/end criteria.
2. Resolve the project Framework pin that governed the cohort.
3. Treat one durable task/PR/release unit as one candidate historical event; do not split or merge arbitrarily to inflate counts.
4. Record only observable facts and evidence-backed signals.
5. Leave unavailable signals absent rather than guessing.
6. Generate/import events with `tools/backfill_task_learning.py` into `.erei/learning/RETROSPECTIVE_TASK_EVENTS.jsonl`.
7. Validate fingerprints and deduplicate semantic duplicates.
8. Produce a cohort summary separating confirmed/reconstructed/inferred evidence.
9. Use retrospective evidence to prioritize review hypotheses and Feedback candidates, but do not allow it to move the project Framework pin or self-modify Framework Core.
10. Prospective Task Learning remains the primary source for calibration of review thresholds.

## Suitable sources
Strong:
- merged PR metadata and exact head/base refs;
- successful/failed CI run IDs;
- durable release/rollback evidence;
- explicit ADR/gate outcomes;
- runtime evidence with exact version/commit binding.

Weak:
- memory-only summaries;
- reconstructed intent without source refs;
- agent self-assessment without deterministic evidence.

## Output
Project-local:

```text
.erei/learning/RETROSPECTIVE_TASK_EVENTS.jsonl
```

Optional aggregate report may summarize historical cohort counts and notable evidence-quality distributions.

## Invariants
- retrospective and prospective ledgers remain distinguishable;
- historical evidence never rewrites the original project artifacts;
- unknown signals remain unknown;
- a failed CI run is not automatically a Framework failure;
- historical event volume does not by itself trigger Framework promotion;
- security/data evidence quality is never upgraded by inference.
