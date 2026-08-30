# Apps Script Quotas and Runtime

**Source baseline:** official Google Apps Script quotas documentation, verified 2026-08-31.

## Current baseline facts

At the baseline date, official limits include:
- script runtime: 6 minutes per execution,
- simultaneous executions: 30 per user,
- simultaneous executions: 1000 per script,
- properties value size: 9 KB,
- properties total storage: 500 KB per property store,
- versions: 200 per script.

Daily service quotas vary by account type and service. Google states quotas/limits can change without notice.

## Engineering rules

### Q-001 — Never design to the exact runtime ceiling
A normal operation should have meaningful headroom below the current execution limit. A workflow that often approaches the hard ceiling is an architecture/performance defect even if it sometimes succeeds.

### Q-002 — Capacity claims require current quota verification
Do not make user-count, throughput, email, URLFetch, trigger-runtime, or similar capacity promises from memorized numbers. Verify the official quota page for the actual account context.

### Q-003 — Concurrency is multi-dimensional
Browser call concurrency, per-user Apps Script execution limits, per-script limits, external API quotas, and resource-level locks are separate constraints. Passing one does not imply system capacity.

### Q-004 — Quota errors need explicit classification
Recognize quota/rate-limit failures separately from application defects. Retry only when bounded and appropriate; never loop indefinitely against a hard quota.

### Q-005 — Monitor real execution health
For production Apps Script systems, use execution history/dashboard and applicable Cloud/API quota telemetry to validate capacity assumptions.

### Q-006 — Long work should be decomposed
When operations can exceed runtime safely:
- batch/chunk work,
- persist durable progress/checkpoints,
- make steps idempotent where possible,
- resume in later execution/trigger,
- ensure partial completion is visible and recoverable.

Do not use conversational/client state as the only checkpoint.

## Capacity review checklist

For a scale-sensitive feature identify:
- expected calls per user/action,
- service calls per request,
- execution duration P50/P95,
- concurrent user behavior,
- trigger/background runtime,
- URLFetch/external quotas,
- properties/cache use,
- retry amplification,
- worst plausible burst.

## Escalation

If a project regularly requires work close to Apps Script hard limits, assess migration/hybrid architecture rather than continuing to accumulate workarounds.