# Core13 C0 v2 — Windows owner-local post-EOL verification

**Date:** 2026-11-08. **Observed owner-local result:** 38/38 offline unit tests PASS; exit code 0; Git-pinned checkout EOL confirmed.

## Direct owner console evidence

The owner cloned the updated `core13/pilot-c0-preregister-three-advisory-probes-20261108` branch into a **fresh** Windows worktree `erei-core13-c0-lf`, rather than force-resetting the previous checkout. Fresh clone completed successfully.

```text
git ls-files --eol tools/core13_pilot_b1_advisory_only.py
i/lf    w/lf    attr/text eol=lf

git ls-files --eol contracts/core13-pilot-c0-prereg-three-probes-v1.json
i/lf    w/lf    attr/text eol=lf

python -m unittest discover -s tests/unit -p "test_core13_pilot_c0_*.py" -v
Ran 38 tests in 0.022s
OK

c0_local_exit_code=0
```

All 38 test methods passed:
- 16/16: `test_core13_pilot_c0_gemini_readonly_boundary`, using **injected offline fake HTTP transport only**, no live Gemini API;
- 12/12: `test_core13_pilot_c0_prereg_contract` (unaltered v1 source and SHA rules);
- 10/10: `test_core13_pilot_c0_v2_amendment` (v1 immutable, v2 three fixed cases, source-pinned provider seam and non-promotable model claims).

The prior Windows run had 3 failing test methods with 8 SHA assertion failures; exact Git blob recomputation proved those failures were caused by Windows LF→CRLF checkout conversion. The scoped `.gitattributes` amendment resolved this **in a fresh checkout**. No pinned Python/JSON sources or test oracles were weakened or repinned.

## Scope and limits

**Verified:** Exact two checked files retained `i/lf w/lf`; complete owner-local C0 suite 38/38 PASS and exit 0. The remaining pinned file SHA checks passed within the unit suite.

**Not verified:** GitHub-hosted Actions post-fix run. The private repository's check-run annotation previously proved an account payment/spending-limit hold **before runner assignment**; this is a **separate billing restriction**, not a Python test failure. Therefore `C0_OWNER_LOCAL_PASS` is **not** the same as `GITHUB_CI_PASS`.

**No live Gemini API call, provider outage, C1 scenario, code execution, Docker or Root action occurred in this local test.** Tests exercise offline failure simulations; a fake HTTP 503 is not a genuine observed Google service outage. C1-02 as frozen in C0 v2 still requires independently witnessed actual network/provider unavailability. The v2 contract retains no owner C0 acceptance at this point, and no model effectiveness is established.

## Gate disposition

```text
FORMAL_GATES_PASSED=12/16
C0_V2_SOURCE_AND_OWNER_LOCAL_TESTS=VERIFIED_38_38_PASS
C0_FORMAL_OWNER_SIGNOFF=PENDING
C1/C2/C3=NOT_STARTED
GITHUB_CI=BILLING_BLOCKED_BEFORE_RUNNER
MODEL_EFFECTIVENESS=NOT_ESTABLISHED
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
stable_ready=false
```

**Recommended next action:** formal owner review of the local-source evidence and C0 v2; do not automatically promote C0. Before any C1-02, decide whether the impractical genuine-provider-outage oracle is worth waiting for or whether to authorize a **new, explicitly reviewed prereg** that tests fail-closed using controlled transport fault injection without falsely labeling it an actual provider outage. No post-hoc editing of signed v2 and no C1 execution until this decision is recorded.
