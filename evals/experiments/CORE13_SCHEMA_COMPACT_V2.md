# Core13 schema experiment V2 — compact isolated provider hypothesis

**Baseline:** frozen PR98, pinned `gemini-3.5-flash-lite`, **13 owner-local observed Core13 scores = 9 PASS / 4 FAIL**; none independently accepted. Baseline smoke-005..017 untouched.

**Experiment B1 (PR102 exact SHA `8919c1078aa4afef9ec62c1504b30d98c5d6ce53`):** The owner completed 17/17 local tests and no-network delta preview, then made exactly one real owner-authorized `TLR-003` schema-v1 request into `schema-001`. Provider returned **HTTP400, NOT SCORED**. The provider error message was intentionally redacted, so the exact cause is UNKNOWN. A plausible hypothesis (not proof) is overly complex JSON grammar: v1 uses many optional action fields and `maxItems:16`, and current Gemini API documentation warns that such schemas may be rejected with 400.

**Experiment B2 (this separate child branch):**
- Original v1 schema implementation and immutable failed `schema-001` remain unchanged.
- New `gemini_core13_schema_compact_v2.py` retains only general output/metadata shape with required `output.actions[*].op` string, leaving action details and simulated state unconstrained. No per-case correct actions or statuses, no restricted decision enumerations and no suppression of forbidden operations.
- Drops `actions.maxItems=16` and long optional field/enum combinations. Frozen original scorer STILL enforces action list bound, valid op/field combinations, forbidden effects and semantic correctness.
- Reuses tested single-call, secret-redacted, pre-POST provenance + SHA-bound local evidence launcher, but separately labels every receipt `core13_native_response_json_schema_compact_v2`. **No automatic retry, no alternative model fallback, no CI/live calls.**
- The only change relative to the original API body remains `generationConfig.responseJsonSchema`, now with a smaller schema. Compatible server acceptance is still **UNTESTED**; this is source-only.

## Read-only first (zero Gemini requests)

From a clean checkout of this exact branch:

```powershell
python -m unittest evals.tests.test_gemini_core13_schema_candidate evals.tests.test_gemini_core13_schema_compact_v2 evals.tests.test_run_gemini_schema_smoke -v

python -m evals.experiments.gemini_core13_schema_compact_v2 --target-root "$env:userprofile\desktop\erei-core13-target" --case-id TLR-003-VERIFICATION-ESCAPE --model gemini-3.5-flash-lite
```

Only after both checks succeed, **if the owner explicitly chooses another Free-tier request**, use the standalone live module `evals.experiments.run_gemini_schema_smoke` in this **V2 checkout** with all three owner confirmation flags and a **fresh `schema-002` folder** outside Git checkouts. The original frozen scorer is unchanged. A second 400 must be classified `NOT_SCORED` and **not retried automatically**. Preserve the failed `schema-001` evidence forever. Do not copy any Gemini key/raw provider response, case oracle, or project private data into GitHub.

Original `9/13` baseline, `0/13 independently accepted`, `0/48 V1/V2 comparison`, and `stable_ready=false` are unaffected. A single exploratory V2 PASS will not establish reliable uplift across the suite.
