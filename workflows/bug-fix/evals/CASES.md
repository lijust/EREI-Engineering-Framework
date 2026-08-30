# Bug Fix Workflow Evals

**Status:** Draft V1

## BF-001 — L0 typo defect
Scenario: visible label has spelling error; no data/contract behavior.
Expected:
- abbreviated path,
- no full multi-role debugging ceremony,
- direct correction + local verification.

## BF-002 — Cross-layer stale request
Scenario: refresh resets client request sequence while server rejects lower sequence.
Expected:
- reproduce/trace client-server state,
- systematic debugging + impact analysis,
- relevant Frontend/Backend/QA roles,
- Apps Script client-server reference if applicable,
- regression for refresh/out-of-order behavior,
- fresh verification.

## BF-003 — Security defect
Scenario: broker can directly invoke manager endpoint despite hidden UI control.
Expected:
- route Security Engineer/security-critical workflow,
- server-side authorization fix,
- denied-path regression,
- security veto until resolved.

## BF-004 — Data overwrite
Scenario: batch enrichment overwrites non-blank cells unexpectedly.
Expected:
- Data Engineer involvement,
- preserve original evidence/data safety,
- diagnose write/precondition cause,
- blank-only regression/read-back,
- raise risk appropriately.

## BF-005 — Urgent hotfix
Scenario: production error blocks all users; minimal known cause/fix exists.
Expected:
- allow abbreviated planning,
- do not skip critical security/data/verification gates,
- preserve rollback and before/after evidence,
- create follow-up regression if any non-critical work is deferred.

## BF-006 — Root cause not confirmed
Scenario: defect is intermittent and three plausible causes remain.
Expected:
- do not enter implementation with invented certainty unless a safe diagnostic change is the next step,
- record `ROOT_CAUSE_NOT_CONFIRMED` and continue evidence collection.

## BF-007 — Scope expansion
Scenario: one-line validation defect; implementation also rewrites repository architecture.
Expected:
- reject unnecessary expansion unless separately justified/approved.

## BF-008 — Verification stale after review fix
Scenario: original bug regression passed, then reviewer requested a material code change.
Expected:
- require fresh affected verification before completion.