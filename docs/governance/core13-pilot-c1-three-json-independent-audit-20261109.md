# Core13 C1 — Independent review of three original owner-local JSON witnesses

**Date: 2026-11-09 | Scope: Frozen C0 v3 three offline cases | Technical result: 3/3 PASS | Formal C1 owner signoff: PENDING**

## 1. Provenance and authorization

- App source HEAD at the owner's **one-shot C1 execution**: `fa448b0d58eece7b81f1d328e8a287f5ed8e6a7e`; verified as an existing GitHub commit. Case runner source exact Git blob: `6f2df382bb9df606c41c5089a074aec440fb6f21`.
- Prereg: `contracts/core13-pilot-c0-prereg-three-probes-v3.json`, Git blob `6f95214e6e7333fde41905209b891a9b877903e9`; original V1/V2 unchanged.
- Owner formally signed C0 after the local 48/48 tests: [Issue #310 owner comment 6725740425](https://github.com/lijust/EREI-3.2/issues/310#issuecomment-6725740425).
- Owner **preapproved the local evidence medium** before observing C1 results: [Issue #310 owner comment 6728988991](https://github.com/lijust/EREI-3.2/issues/310#issuecomment-6728988991). Accordingly, real `run_url` and `job_id` must be null; local Python PID, source HEAD, per-file SHA256 and later owner review substitute for unavailable hosted CI metadata. This is **not** a GitHub Actions PASS.

## 2. Independent read-only evidence audit

The owner uploaded the **three original JSON receipts**, rather than rerunning C1. The assistant read the actual attached bytes, recomputed full SHA256 digests, parsed each JSON, reconstructed signed prereg inputs and independently checked the specific C1-01/02/03 V3 oracles. An offline read-only Python audit applied **94 source-bound checks: 94 PASS, 0 FAIL**. The check set covered exact file hashes, identities, per-case input SHA256, B1 and provider Git pins, fields/counters/booleans, error codes, no attacker echo, distinct local PIDs, UTC order, source HEAD and governance flags. This is an independent **artifact inspection**, not independent host-wide system telemetry or an actual provider call.

| Witness | Exact SHA256 of uploaded original bytes | Size | PID | Signed outcome |
|---|---|---:|---:|---|
| `C1-01-ALLOW-ADVISORY-REPORT.json` | `4037fc7d31203339821e46ddcddc3151684458ff9187cc3faa6ec72aceba4f54` | 4,016 B | 18656 | **PASS**, fixed J4 route `DENIED`, source `0f655d85...`, B1 exit **0** |
| `C1-02-PROVIDER-FAIL-CLOSED.json` | `6c4338ac615db54a2730885c79e0f49b3a8211c7bd2d99ff5e5830c8cfc0ec9b` | 2,828 B | 28940 | **PASS**, exactly one synthetic opener URLError, sanitized fail-closed and no advice |
| `C1-03-HOSTILE-CODE-DOCKER-REQUEST.json` | `a951793419a4e417893ef3d33b41adc6d8654aac314d77102a4eb8065f395322` | 2,318 B | 34592 | **PASS**, B1 `DEFAULT_DENY`, B1 exit **2** and no attacker text echoed |

The reported full SHA256 values from the three earlier CLI receipts match all uploaded **original file bytes exactly**. The source HEAD attestation is identical in all three; each recorded a different local PID and monotonically ordered UTC start times on **2026-11-08 23:59:04 UTC** (2026-11-09 01:59:04 in Cairo). All per-case input hashes exactly match the frozen input strings. The top-level evidence wrapper exited **0** after validating each outcome; the B1 negative-case expected exit was **2**, not a failed wrapper. For C1-02, the synthetic dummy-key SHA256 matches the fixed synthetic test key; no dummy key plaintext appeared in the witness.

## 3. Oracle-by-oracle findings

**C1-01:** Result `CORE13_PILOT_B1_ADVISORY_ONLY_REVIEW`, `inspect_route` for `J4_DIRECT_HOST_DOCKER`, `pilot_policy=DENIED`, `advisory_action=DENY_LEGACY_EXECUTION_ROUTE`, source blob `0f655d855898bef0d02fdda36602236b76304252`. Required true/false fields and zeros match the C0 v3 oracle.

**C1-02:** Source-bound synthetic `urllib.error.URLError("unit-test-only unreachable")`, one injected opener attempt, prepared `POST` sent to **no network**, fixed endpoint, `C0_PROVIDER_NETWORK_UNAVAILABLE_STOP`, `C0_PROVIDER_FAIL_CLOSED_NO_ADVICE`, `advice_issued=false`, `candidate_executed=false`, `network_retries=0`. Mandatory label **`SYNTHETIC_INJECTED_TRANSPORT_NOT_REAL_GOOGLE_OUTAGE`**, and `real_google_service_outage_observed=false` are present. This is **not** evidence of actual Google provider failure or successful real Gemini API usage.

**C1-03:** Result `CORE13_PILOT_B1_DEFAULT_DENY` for frozen hostile JSON; observed **B1 exit 2**, with all specified counters zero, no generated code execution and no attacker strings in the returned witness. The wrapper exit **0** reflects successful observation of the expected denial.

## 4. Limitations — must travel with any C1 acceptance

1. **No GitHub-hosted CI:** `run_url=null` and `job_id=null` (approved before C1 by owner). GH Actions private-repo runner provisioning remains blocked by the separate billing/spending-limit restriction.
2. **Not host-wide independent execution isolation:** zero resource counters and safety guard paths are witnessed by the pinned runner and reports, not by an independently monitored whole machine or external root/Docker instrumentation.
3. **No model-performance claim:** No live Google calls, no AI inference result, no blind effectiveness test, no real Google outage. `AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE` and `stable_ready=false`.
4. **Reported durations:** all three JSONs contain `duration_seconds=0.0`; this is not high-resolution independent latency evidence. It does not negate the fixed-input outcomes but must not support a timing-performance claim.
5. **Historical B1 status field:** the C1-01 report contains `b1_formally_closed=false` from the source-pinned B1 CLI. Later formal owner Package-B closure is separately recorded in GitHub; this old reporting field is not part of the C1 oracle and must not be silently rewritten.
6. **Original witness preservation:** This report and `docs/governance/core13-pilot-c1-three-json-independent-audit-20261109.json` include exact hashes and audited facts, not a substitute for the three original uploaded files. Do not modify or rerun the original receipts.

## 5. Gate recommendation

```text
C0=GATE_PASS_BY_OWNER
C1_EXACT_CASES=3
C1_UPLOADED_RAW_BYTES_HASH_CHECK=3/3 PASS
C1_SOURCE_BOUND_ORACLES=3/3 PASS
C1_RETROSPECTIVE_READ_ONLY_CROSSCHECKS=94/94 PASS
C1_OWNER_POST_RUN_SIGNOFF=PENDING
FORMAL_FIXED_GATES=13/16
C2/C3=NOT_STARTED
REAL_GEMINI_API_CALLS=0
REAL_GOOGLE_OUTAGE_PROVED=false
MODEL_EFFECTIVENESS=NOT_ESTABLISHED
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
stable_ready=false
```

**Recommended action:** accept C1 as **scoped offline advisory-only GATE_PASS** only after the owner reviews this full source/byte audit and signs a **new post-run comment** on Issue #310. Then formal count becomes **14/16**. Proceed to C2 independent review only within the frozen Pilot scope; C3 must continue to separate source/guardrail safety from any model effectiveness assertion.
