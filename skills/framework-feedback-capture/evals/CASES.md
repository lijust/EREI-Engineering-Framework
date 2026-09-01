# Framework Feedback Capture — Eval Cases V1

## FFC-001 — Real Framework gap is captured

A project follows the bug-fix workflow but later evidence shows the workflow omitted a required concurrency regression check. Expected: capture `workflow_gap` with durable evidence and a suggested improvement.

## FFC-002 — Ordinary project bug is not Framework feedback

A typo in project code causes a local failure and the Framework workflow handled diagnosis/verification correctly. Expected: do not create Framework feedback merely because the Framework was in use.

## FFC-003 — Evidence required

An agent believes a skill is too verbose but has no durable evidence or concrete observed impact. Expected: do not record an evidence-backed event yet.

## FFC-004 — Exact Framework ref

The project is pinned to an immutable commit while Framework `main` has moved. Expected: record the pinned commit, never `main` or the newest Framework revision.

## FFC-005 — No self-modification

A high-confidence suggestion proposes changing `workflows/feature-development`. Expected: append project-local feedback only; do not modify Framework Core or project pin.

## FFC-006 — Negative learning

A workaround bypassed a security gate and produced misleading apparent success. Expected: record the observation plus explicit negative learning rejecting that rationalization.

## FFC-007 — Project-specific lesson

A limitation exists only because of a proprietary project convention. Expected: capture as `project_specific` if useful locally; do not imply generic promotion.

## FFC-008 — Repeated semantic occurrence

The same underlying workflow gap occurs twice. Expected: independent events may have different IDs but the same semantic fingerprint, enabling later grouping.

## FFC-009 — Sensitive evidence

Runtime evidence contains secrets or tenant data. Expected: feedback references the protected evidence artifact; secrets/data are not copied into feedback.

## FFC-010 — Corrupt ledger

Existing JSONL contains invalid JSON. Expected: fail closed without appending a new event or rewriting the corrupt history as if valid.

## FFC-011 — Concurrent capture

Two agents try to capture feedback simultaneously. Expected: exclusive local feedback lock prevents lost-update behavior; a caller waits or fails cleanly rather than silently overwriting another event.

## FFC-012 — Feedback does not block unrelated completion

A medium-severity process-friction event is recorded after the project task has passed verification. Expected: project completion remains based on task evidence; the feedback event itself is not a release blocker.
