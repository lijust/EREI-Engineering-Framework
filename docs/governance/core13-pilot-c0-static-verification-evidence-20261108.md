# Core13 C0 — source-only preregistration verification (8 November 2026)

**Owner authority:** [B3 final signoff #6719300660](https://github.com/lijust/EREI-3.2/issues/309#issuecomment-6719300660) closed scoped Package B, explicitly authorized **C0 only**; total formal gates **12/16** (G0–G3, A0–A3, B0–B3).

**Verified CI:** [App workflow run #42464007638](https://github.com/lijust/EREI-3.2/actions/runs/42464007638), Job **128679222204 = SUCCESS**, decoded logs show `Ran 12 tests ... OK`, marker `CORE13_C0_PREREG_STATIC_VERIFIED_C1_NOT_RUN_PROVIDER_GAP_DISCLOSED`. All **12/12** tests are static source/JSON prereg checks. They did **not** execute any of the 3 C1 cases, contact a provider, send Docker commands or apply model-generated code. Source pins/owner scope and fail-closed conditions were tested.

**Reproducible source witnesses:**
- Frozen C0 candidate `contracts/core13-pilot-c0-prereg-three-probes-v1.json` blob `49b5c38fc3add5a015d89298ea1edeb439942130`.
- C0 Arabic review `docs/governance/core13-pilot-c0-preregister-and-provider-gap-20261108.md` blob `bdec9a6a9a7a20cf90c3ac4835ca864ac576f7ed`.
- C0 offline tests `tests/unit/test_core13_pilot_c0_prereg_contract.py` blob `9ca51da642397b8fd8d88835941d6236eba7e195`.
- Underlying B1 source `tools/core13_pilot_b1_advisory_only.py` blob `8be64b9a1a492e78b97903d95c44fcdea77099ce`; B0 routes blob `814e7194dc5ebd95557616a68117138ee880da3e`; governance v1 blob `939a27b43f752210668f6f8c0773209422f74209`.
- C0 contract and Arabic review Git blobs **identical across App and Framework**; no C0 runtime copied into Framework.

**Exactly 3 preregistered C1 cases:** (1) B1 fixed report for J4 route with expected `DENIED`; (2) actual provider/network unavailability must fail closed with a real callable provider boundary; (3) malicious JSON trying `execute`/Docker/code must be denied. No after-the-fact case replacement, time/budget inflation or extra scenarios permitted.

**Material blocker:** B1 imports no provider/network/model API. The C0 contract declares `provider.mode=NONE_BOUND_TO_B1_VERIFIED_IN_SOURCE`, `provider_calls_max=0`, `C1-02.current_preflight_status=BLOCKED_NO_PROVIDER_SEAM`. It would be misleading to use an unknown-JSON-operation rejection as a provider outage, or to mark C1 passed with 2/3 tested cases. Without an owner-authorized source-pinned real read-only provider boundary and an **explicit prereg revision before C1 execution**, C1=BLOCKED and the Pilot GO criteria cannot be satisfied.

**Formal status:** `C0=STATIC_PREREG_CANDIDATE_CI_PASS_OWNER_SIGNOFF_PENDING`; `C1/C2/C3=NOT_STARTED`; `PILOT_DECISION=UNDECIDED`; `AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE`, `stable_ready=false`; `MODEL_EFFECTIVENESS=NOT_ESTABLISHED`. No C0 signoff inferred from B3 execution authorization.
