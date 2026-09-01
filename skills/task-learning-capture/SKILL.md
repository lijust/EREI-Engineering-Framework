# Task Learning Capture

**Type:** Reusable engineering procedure  
**Status:** Candidate V1

## Purpose

Capture one structured learning event at the terminal boundary of an engineering execution so the project accumulates measurable evidence about how the Framework performs in real work.

This skill is broader than `framework-feedback-capture`: every routed engineering execution should create a Task Learning Event, while Framework Feedback is created only when evidence suggests a Framework limitation or reusable lesson.

## When to use

Use after convergence/terminal classification for any engineering request that entered the Workflow Router and performed execution, including:

- verified completion,
- completion with explicit deferred items,
- blocked work,
- failed execution,
- canceled execution after material work.

Do not create a task event for explanation-only conversation that never entered engineering execution.

## Required inputs

- project repository identity,
- exact pinned Framework ref,
- selected workflow,
- risk level,
- terminal state and outcome class,
- whether the task was material,
- observable rework/verification signals,
- Framework Feedback IDs/fingerprints if feedback was captured,
- observable workaround/context/scope/security-data signals.

## Procedure

1. Finish applicable verification and convergence first.
2. Classify the terminal outcome truthfully.
3. Count rework cycles and verification failures from observable execution evidence; do not invent counts.
4. Mark `verification_escape=true` only when a prior verification/completion claim was later contradicted by an escaped defect or equivalent evidence.
5. Link Framework Feedback when an event was actually captured.
6. Record only structured engineering signals; never store private chain-of-thought, credentials or unrelated conversation content.
7. Append the Task Learning Event under `.erei/learning/TASK_EVENTS.jsonl` using `tools/task_learning.py capture` or equivalent compliant behavior.
8. Read the returned deterministic review trigger.
9. Surface `REVIEW_RECOMMENDED`, `REVIEW_DUE` or `IMMEDIATE_REVIEW` in the task's terminal report. `LEARNING_WATCH` may be recorded without interrupting normal work.
10. Do not modify Framework Core or the project Framework pin because a trigger fired.

## Review-trigger handling

- `LEARNING_HEALTHY`: no review action required.
- `LEARNING_WATCH`: evidence is accumulating; continue capture.
- `REVIEW_RECOMMENDED`: a Learning Review is useful soon.
- `REVIEW_DUE`: queue a Learning Review before substantial additional Framework-dependent work where practical.
- `IMMEDIATE_REVIEW`: review the learning evidence promptly; underlying security/data/verification evidence may independently block release.

## Output

At minimum:

```text
Task learning event: <task-id>
Learning epoch: <epoch-id>
Learning trigger: <level>
Trigger reasons: <reasons or none>
```

## Invariants

- one terminal event per routed engineering execution,
- event data remains project-local,
- event capture never changes completion evidence,
- event capture never self-promotes Framework changes,
- successful executions are captured as well as failures,
- task-learning metrics are evidence inputs, not proof that causation is known.
