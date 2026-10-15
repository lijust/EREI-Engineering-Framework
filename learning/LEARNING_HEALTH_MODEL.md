# Learning Health Metric Model V1

**Status:** Candidate V1

## Principle

Learning health must not collapse engineering quality into one raw percentage.

### Primary negative quality signals

1. **verification_escape_task_rate**
   - prior verification/completion assumption was contradicted later;
   - stronger negative signal than a pre-merge failing test.

2. **final_failed_task_rate**
   - terminal engineering executions ending in `failed`.

3. **critical_security_or_data_event_rate**
   - use domain governance; learning does not downgrade severity.

### Secondary iteration / assurance signals

1. **rework_rate**
   - tasks with >=1 material rework cycle;
   - not a restart rate and not accuracy.

2. **rework_free_task_rate**
   - tasks requiring no recorded material rework cycle.

3. **rework_cycles_per_material_task**
   - iteration load normalized by material task count.

4. **verification_failure_rate**
   - tasks with >=1 failed deterministic verification attempt;
   - better described as verification-catch density.

5. **verification_clean_task_rate**
   - tasks with zero failed deterministic verification attempts.

6. **pre_merge_catch_rate**
   - only valid where lifecycle-stage evidence is assessed.

### Outcome/context signals

- verified-success rate,
- success-with-deferred rate,
- blocked/failed rate,
- manual-workaround rate,
- context-gap rate,
- unexpected-scope-growth rate,
- review-debt occurrence and duration.

## Interpretation hierarchy

```text
escaped defect / critical event
        >
final failed outcome
        >
runtime/post-merge catch
        >
pre-merge deterministic catch
        >
rework iteration
```

This is an interpretation priority, not a numeric weighting formula.

## Accuracy language

Do not call any single Task Learning metric **execution accuracy**.

If an accuracy-like KPI is needed, define the exact claim first. Example:

- first-candidate verification-clean rate,
- final verified-success rate,
- escape-free material-task rate.

Each answers a different question.

## Anti-gaming

Never improve health scores by:
- deleting tests,
- weakening gates,
- suppressing failure events,
- merging before verification,
- recoding an escape as ordinary rework,
- avoiding difficult/high-risk tasks.

Healthy verification can temporarily increase catch and rework rates while reducing escapes.

## Effectiveness

For Framework changes, primary success should normally be:
- fewer recurrence events for the target root cause,
- lower escape rate,
- lower final-failure rate,
- lower review debt,
- lower context/workaround friction.

Rework/catch reductions are useful only when assurance strength and task mix remain comparable.
