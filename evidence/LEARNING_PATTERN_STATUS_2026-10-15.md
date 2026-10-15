# Learning Pattern Status — 2026-10-15

**Status:** Candidate evidence snapshot; no Stable promotion and no project pin movement.

## Current observed state

Framework repository:
- main: `45b0c21cf8b57777337aee507e9ad1ca4f9c361c`
- last main update: 2026-09-12
- Stable project baseline remains `task-learning-review-v1 @ 69079018606750312344cb3c648952b9ab72d35b`
- prospective Task Learning V2 remains Candidate.

Primary brownfield project:
- repository: `lijust/EREI-App-Google`
- observed main: `0a9b48b2cba932ae4375ac9780f2ee330900426b`
- project pin remains Stable Task Learning V1.
- current Learning State: `EPOCH-023`
- total prospective events: 155
- last reviewed cutoff: 126
- unreviewed material tasks: 29
- trigger: `IMMEDIATE_REVIEW`
- rework rate: 75.9%
- verification-failure rate: 58.6%
- verification escapes: 2
- Framework-feedback tasks in current epoch: 0.

The two current-epoch verification escapes are:
1. Windows PowerShell 5.1 native-stderr behavior in the O2 B1 source remediation path.
2. A random-ref race detected during O2 project-creation source readiness review.

## Interpretation

The capture layer is working: tasks, rework, failures and escapes are being recorded.

The weak point is conversion from evidence to governed learning action:

1. Immediate-review debt accumulated while 29 additional material tasks remained unreviewed.
2. Current V1 aggregate rates still conflate healthy pre-merge catches with more serious escapes.
3. The epoch mixes V1 and V2 event semantics, reducing stage/assessment comparability.
4. Repeated escapes did not create Framework Feedback; this may be correct, but the no-feedback decision has not yet been made in a current Learning Review.
5. The Framework central learning state has not absorbed roughly one month of subsequent App evidence.
6. Cross-project corroboration is still absent, so project evidence must not be generalized automatically.

## Candidate response in this branch

This branch adds `tools/learning_pattern_analysis.py` as a deterministic review aid.

It detects:
- review debt,
- verification-escape clusters,
- mixed learning schema epochs,
- verification-stage coverage gaps,
- feedback-conversion gaps,
- high rework density,
- high verification-catch density,
- repeated task-group cohorts.

It intentionally does not:
- create Framework Feedback,
- move a Framework pin,
- promote a capability,
- infer Framework causation,
- mutate project or Framework state.

## Required next evidence

1. Run the analyzer against the current EREI-App-Google learning corpus.
2. Close EPOCH-023 using exact current evidence.
3. Compare the two verification escapes for reusable mechanism versus independent project-local defects.
4. Create Framework Feedback only for any genuinely reusable limitation.
5. Reassess promotion readiness for prospective Task Learning V2 after current brownfield evidence is incorporated.
6. Add cross-project aggregation only after a second materially different project produces real Task Learning volume.
