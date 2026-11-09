# Core13 PILOT-C0 v3 — Owner-local prereg verification, 48/48 PASS

**Date: 2026-11-08 | Verified owner-provided local terminal transcript | Formal C0 signoff pending**

## 1. Exact tested source boundary

- Owner used an existing Windows LF-correct checkout (`erei-core13-c0-lf`) of App branch `core13/pilot-c0-preregister-three-advisory-probes-20261108`, then executed `git pull --ff-only`.
- The pull fast-forwarded `fad16dc3..b537a6b8` (App final C0 v3 source HEAD at test time: **`b537a6b82d0d7dc973df4d4af167dad10e32d4ab`**).
- Scoped checkout evidence: `git ls-files --eol contracts/core13-pilot-c0-prereg-three-probes-v3.json` returned **`i/lf w/lf attr/text eol=lf`**.
- C0 v3 contract Git blob **`6f95214e6e7333fde41905209b891a9b877903e9`**.
- New C0 v3 static test source Git blob **`4a9d9b4dc5dd5f2f94449e203153d55648ba725a`**.
- Previous signed candidate v1/v2 JSON remained byte-unchanged; source-pinning checks were exercised in unit suite.

## 2. Actual local test result

Owner executed (in checked-out App project):
```text
python -m unittest discover -s tests/unit -p "test_core13_pilot_c0_*.py" -v
...
Ran 48 tests in 0.036s

OK

c0_v3_local_exit_code=0
```

Breakdown from the 48 individual `... ok` records in the supplied transcript:

| Unit test family | Tests | Observed |
|---|---:|---|
| Gemini bounded transport, injected offline only | 16 | **16 PASS** |
| C0 v1 original pinned-source prereg | 12 | **12 PASS** |
| C0 v2 immutable source amendment | 10 | **10 PASS** |
| C0 v3 exactly-three-case synthetic-fault prereg | 10 | **10 PASS** |
| **Total** | **48** | **48 PASS / 0 FAIL** |

**Verified limits**: The local tests checked the fixed C1-02 synthetic `urllib.error.URLError('unit-test-only unreachable')` fault identity, one injection attempt, fail-closed error classification `C0_PROVIDER_NETWORK_UNAVAILABLE_STOP`, required explicit label `SYNTHETIC_INJECTED_TRANSPORT_NOT_REAL_GOOGLE_OUTAGE`, preservation of C1-01/C1-03 inputs and prior v1/v2 blobs, and zero permitted Google/network/model/Docker/Root/shell/patch calls in the future preregistered C1 cases.

## 3. What this does NOT prove

- This was **owner-local offline unit testing**, not a successful GitHub-hosted Actions run. Hosted Actions were independently blocked *before runner allocation* by a confirmed account payment/spending-limit restriction; no CI green may be inferred.
- The 16 Gemini transport tests inject fake responses/errors through a provided opener; no genuine live Gemini request, real Google outage, model-generated code execution, billing or provider key use occurred. **Do not** represent synthetic failure as real service interruption.
- The tests preregister C1-01/02/03; **none of the three C1 scenarios has been executed as a separately witnessed C1 run**. Prior unit tests cannot be reassigned retrospectively as C1 acceptance evidence.
- They do not establish model effectiveness, independent AI acceptance, global Docker exclusivity or Stable readiness.
- A C0 v3 test suite PASS does **not automatically grant** formal `C0=GATE_PASS` or authorization to start C1. That requires an explicit new owner **post-test formal C0 signoff** on [Issue #310](https://github.com/lijust/EREI-3.2/issues/310).

## 4. Proposed exact formal disposition

```text
PACKAGE_A=CLOSED_PASS_SCOPED_READ_ONLY
PACKAGE_B=CLOSED_PASS_SCOPED_ADVISORY_ONLY
FORMAL_GATES=12/16
C0_V3_LOCAL=48_OF_48_PASS_EXIT_0
C0_FORMAL=OWNER_POST_TEST_SIGNOFF_PENDING
C1=C2=C3=NOT_STARTED
C1_02_MODE=CONTROLLED_SYNTHETIC_TRANSPORT_FAILURE_ONLY
REAL_GOOGLE_OUTAGE_EVIDENCE=NONE
LIVE_GEMINI_API_CALLS=0
MODEL_EFFECTIVENESS=NOT_ESTABLISHED
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
stable_ready=false
```

**Next action:** independent owner review and final C0 acceptance of the **v3** contract and this local evidence. Then, and only then, perform a separate source-bound three-case C1 pilot under the v3 fixed oracle, each case with unique run witness. No API integration or new security phase is justified by this local green test.
