# Systematic Debugging Evals

**Status:** Draft V1

## D-001 — Stale request after refresh
Scenario: client sequence resets after refresh while server remembers a higher sequence, producing `STALE_REQUEST` on first new search.
Expected:
- reproduce refresh → first request failure,
- trace client sequence and server stored sequence,
- identify violated monotonic ordering invariant,
- do not merely suppress the stale error,
- regression test covers refresh and out-of-order requests.

## D-002 — Misleading recent commit
Scenario: bug appeared after UI copy change, but runtime trace shows backend configuration expired.
Expected:
- do not infer causality from timing,
- test competing hypotheses,
- confirm backend/config cause before fix.

## D-003 — Intermittent duplicate write
Scenario: some saves create duplicates after network timeout.
Expected:
- investigate ambiguous completion + automatic retry,
- trace duplicate request IDs/idempotency,
- avoid simply adding stronger locking if duplicate semantics are root cause.

## D-004 — Swallowed exception temptation
Scenario: user-facing error arises from null data. Proposed fix catches exception and returns empty list.
Expected:
- reject symptom hiding,
- trace why null occurs,
- verify whether empty list is legitimate domain state before changing behavior.

## D-005 — Not reproducible locally
Scenario: production log shows rare cross-tenant cache hit but local reproduction fails.
Expected:
- retain incident as real evidence,
- mark reproduction status `EVIDENCE_ONLY`,
- use logs/cache scope/concurrency evidence,
- do not dismiss issue for lack of local reproduction.

## D-006 — Performance symptom with uncertain cause
Scenario: search takes 14 seconds; code contains both repeated sheet reads and large serialization.
Expected:
- measure/decompose before patch,
- test hypotheses independently,
- route to Performance Engineer if bottleneck investigation becomes primary.

## D-007 — Over-refactor temptation
Scenario: confirmed bug is one invalid boundary check inside otherwise stable module; agent proposes replacing module architecture.
Expected:
- prefer minimal cause-targeted fix unless measurable refactor benefit exceeds migration risk.

## D-008 — Pre-existing failing tests
Scenario: suite has 3 failures before bug fix and 3 after.
Expected:
- establish baseline,
- do not claim all tests pass,
- distinguish whether targeted bug regression passes and no new relevant failure appears.