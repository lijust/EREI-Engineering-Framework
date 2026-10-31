# Core13 — reusable historical evidence handoff, not Learning acceptance

**31 October 2026 · Framework main-based source-only Candidate**

## Why this is integration, not a duplicate architecture

Framework main already contains the merged **PR #124** (29 selected P1 Candidate source/docs/test/workflow files). It implements:
- `tools.learning_proposal_runtime.evaluate_proposal`: typed proposal → trusted caller facts/policy → deterministic in-memory state preview;
- `tools.learning_project_runtime_bridge`: project-local, activation-gated, opt-in knowledge-read seam;
- `tools.learning_exposure_traces`, `tools.learning_intervention_sources`: existing project learning exposure/source joins;
- source-only, synthetic-only, fail-closed project preflight.

**These components should be reused, not implemented again inside a project application.**

This small tool consumes a generic **read-only historical receipt** from a project-specific functional witness. It reuses `evaluate_proposal` to verify that the correct action is **`omit_task`**, because running a historical test is **not** a real prospective engineering task. Thus no new task event, learning promotion or Stable assertion occurs.

## Project-neutral contract

`tools/core13_external_historical_receipt_boundary.py` accepts `erei-cross-project-historical-receipt-v1`. The source project owns the actual historical test, functional oracles and bounded execution. The generic Framework checks only:
- bounded schema, unique JSON keys and SHA-256-shaped source identifiers;
- explicit trusted historical rather than model-generated runtime;
- no host mounts, no model calls, no claim of untrusted-runtime certification;
- bounded, positive project-owned check statuses;
- explicit operator-observed, **not independently attested** provenance;
- existing P1 typed policy/reducer is called to **omit** the historical replay from prospective learning.

A self-reported hash or `passed=true` does **not** independently authenticate Git content or actual task execution. The receipt is a description of operator-reported evidence, not a cryptographic attestation. The generic Framework does **not** duplicate project-specific pagination record counts or other domain oracles.

The real source project adapter is implemented separately in application a separately maintained project repository (trusted V5O/V5V Git/Docker path). No source is imported from that application into this cross-project Framework.

## Unit/CI verification

```powershell
python -m unittest evals.tests.test_core13_external_historical_receipt_boundary -v
```

Thirteen synthetic-only tests cover mandatory schema, true-to-scope flags, source digests, alternate valid project names, duplicate check IDs, no prospective task captures, and fail-closed behavior if the *existing* Framework P1 policy rejects an omission. Github Actions workflow runs the same tests without secrets or provider calls.

**Expected/newly authored tests are not operator-verified until runner evidence is available.** Existing Framework main remains untouched and no Stable manifest is edited.

## End-to-end handoff path (separate repos)

In an explicitly authorized project-owned checkout with already-pinned Docker image and trusted Git source:
1. Project calls its **actual** historical source witness and V5V known-code canary.
2. Project exporter emits a versioned JSON receipt (no credentials/tenant records).
3. Owner passes a *local copy* to the Framework CLI via `--receipt`.
4. Framework checks receipt schema and reuses existing P1 `evaluate_proposal` policy to return `omit_task`, `prospective_task_events_added=0`.

This is a **retrospective read-only cross-repository contract**. It cannot establish that a model consumed knowledge, repaired code or improved in a prospective task.

## Explicit remaining prerequisites for real Learning Pattern proof

- Separate project-local opt-in: use already existing activation contract and `core13_real_project_trial_preflight` (which presently blocks real project trial admission by design).
- Select a real engineering task and independent observable behavioral scorer; record every attempt and failure, not only success.
- Model-generated code must not be executed in V5V's limited Docker canary; a deliberately reviewed stronger isolation design is needed before arbitrary patches.
- Prospective control/treatment study must avoid V5S's control ceiling and historical-fix leakage, with no new provider calls before a new explicit trial authorization.
- Do not merge the 311-commit a project application experiment branch into main wholesale. Review the independent Main-based consolidation PR first.

## Safety & evidence conclusion

`FRAMEWORK_HISTORICAL_RECEIPT_READONLY_BOUNDARY_PASS` means **contract and in-memory policy routing** only. It does not mean external evidence authenticity was independently established. `learning_effectiveness=NOT_ESTABLISHED`; `BLOCK_AI_ACCEPTANCE`; `project_writes=0`; `stable_promotable=false`. PR remains Draft pending CI and independent architecture review.
