# Core13 C0 v2 — Gemini read-only advisory transport, source review and CI checkpoint

**8 نوفمبر 2026 | Current state: IMPLEMENTED_SOURCE / CI_FAILED_UNDIAGNOSED / NO_C1_RUN**

## What actually changed

1. The earlier `contracts/core13-pilot-c0-prereg-three-probes-v1.json` remains byte-identical (Git blob `49b5c38fc3add5a015d89298ea1edeb439942130`), still recording the old missing-provider blocker.
2. New isolated App-only source `tools/core13_pilot_c0_gemini_readonly_boundary.py`, blob **`01ecbd606980220f459772644efc45068b963968`**. It reuses only the bounded HTTPS transport/fail-closed behavior from historical `core13_gemini_pair_live.py` blob `df6b8ca9e64882f43abb7ac43b68085bb8315fb0` (not the full two-arm runner, filesystem writes or private prompts). Exact HTTPS Gemini `gemini-3.5-flash-lite` endpoint, fixed generic public prompt, one request per invocation, 10-second timeout, max 128 output tokens, no tools/function calling/code execution and no automatic live CLI. API key only memory-supplied by a future owner-local authorized caller. It performs **no network access when imported**.
3. New `contracts/core13-pilot-c0-prereg-three-probes-v2.json`, Git blob **`a0399b97583fb6a2f5b379ba32ac70711a5b0b16`**, mirrored identically into Framework. It retains **exactly 3 C1 cases** and revises only the C1-02 provider-outage oracle to recognize genuine network unavailability or HTTP 502/503/504, not mock errors, HTTP 401/auth denial, 429/quota, or successful requests.
4. The original B1 entrypoint source `tools/core13_pilot_b1_advisory_only.py` stays unchanged, blob `8be64b9a1a492e78b97903d95c44fcdea77099ce`; **it does not import the C0 boundary**. An actual C1 harness/owner-local invocation is **not yet implemented or authorized**.
5. Added 16 offline injected-transport unit tests and 10 static v2 amendment tests, alongside the original 12 v1 static tests. Their source Git blobs are `1d436e4563ba1cf9ae097ae973da5f1049c0ee19` and `3f53314faf4ee81429dc345e3dbb3e95b27d0b19`. **Do not claim 38/38 PASS until an actual successful CI run.**

## Actual verifications / failures

- **Verified through live GitHub file reads:** All 11 C0 source pins in the amended Actions workflow match the corresponding Git blob SHA. V1 is preserved; V2 source binding and three case IDs match. The App/Framework V2 contract and Arabic technical decision were created from identical text. These source facts are **not** runtime proofs.
- Last original *v1* static CI [#42464124217](https://github.com/lijust/EREI-3.2/actions/runs/42464124217) succeeded **12/12** *before the C0 v2 amendment*; do not reattribute that pass to the new code.
- The v2 CI runs [#42467134130](https://github.com/lijust/EREI-3.2/actions/runs/42467134130), [#42467391106](https://github.com/lijust/EREI-3.2/actions/runs/42467391106), [#42467442759](https://github.com/lijust/EREI-3.2/actions/runs/42467442759) and [#42467547902](https://github.com/lijust/EREI-3.2/actions/runs/42467547902) are **FAILURE**. In the latest run, three independent nonroot jobs (original aggregate, provider unit isolation, v2 amendment isolation) all ended FAILURE. The connected API returned **no step metadata** and attempts to fetch all failing job logs returned **404 BlobNotFound**. Therefore their cause **cannot be proven yet** from the available evidence. Do not label tests as PASS or infer that the new source is broken; both assertions would be unjustified.
- **No model calls, provider contacts, API keys, Root, Docker, model-generated code execution or C1 scenario run was performed by us.**

## Safety/acceptance

- Provider source includes a real callable Gemini API transport **but no live, independently witnessed provider outage**. Mocked URLError/HTTP 503 in a unit test is **not C1-02 evidence**. HTTP POST to Google may incur billing; request cap is one per invocation, but no globally enforced dollar limit has been established.
- The owner must explicitly review the *v2 amendment* and provider cost/tier/secret custody **before any C1 live invocation**. Their previous authorization was to implement the C0 recommendation, not to run live API calls automatically.
- Pending diagnosis of failed CI, `C0=AMENDMENT_SOURCE_REVIEW_PENDING`; `C1/C2/C3=NOT_STARTED`; **12/16 formal gates** remain. No owner C0 signoff, no Pilot GO.
- **Stop condition:** do not create more security phases or run C1 without a successful reproducible C0 CI and explicit owner gate. Current blocker is retrieving the GitHub workflow failure reason (or source tests running successfully elsewhere with exact pinned bytes).

```text
PACKAGE_A=CLOSED_PASS_SCOPED_READ_ONLY
PACKAGE_B=CLOSED_PASS_SCOPED_ADVISORY_ONLY
GATES_FORMALLY_CLOSED=12/16
C0_V2=SOURCE_IMPLEMENTED_CI_FAILED_REASON_NOT_ESTABLISHED
C1_LIVE_PROVIDER_CALLS=0
C1_02_REAL_PROVIDER_OUTAGE_EVIDENCE=NONE
MODEL_EFFECTIVENESS=NOT_ESTABLISHED
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
stable_ready=false
```
