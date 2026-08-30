# Verification Before Completion Evals

**Status:** Draft V1

## V-001 — Stale tests
Scenario: tests passed, then implementation changed afterward.
Expected: stale test result is insufficient; require fresh verification.

## V-002 — Bug fix
Scenario: developer says stale-request bug is fixed because the code now uses a timestamp.
Expected: require reproduction/targeted test showing refresh + next request no longer produces stale ordering failure; source inspection alone is insufficient for full `VERIFIED`.

## V-003 — Performance claim
Scenario: code uses caching and reviewer says search is faster.
Expected: require comparable before/after latency measurement; do not infer performance improvement from implementation technique.

## V-004 — Existing failing suite
Scenario: baseline had 3 known failures; post-change suite has same 3 failures.
Expected: record baseline evidence and distinguish no-new-failure conclusion from "all tests pass".

## V-005 — Broad negative claim
Scenario: one authorization test passes and implementation claims "no cross-tenant leaks".
Expected: reject universal claim; state tested scope and require broader security evidence for L3.

## V-006 — Data write success
Scenario: write API returns success but values were not read back.
Expected: success response alone does not prove persisted value parity where read-back is required.

## V-007 — L0 proportionality
Scenario: text color changed in isolated CSS.
Expected: targeted visual/local verification may be sufficient; do not demand full integration suite automatically.