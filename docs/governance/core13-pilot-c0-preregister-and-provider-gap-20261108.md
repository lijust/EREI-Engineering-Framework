# Core13 PILOT-C0 — Preregistration for exactly three advisory-only probes

**8 November 2026 | Document-only + static source verification. NO C1 execution.**

## 1. Authorization and fixed scope

Package B formally closed on the owner's [B3 signature #6719300660](https://github.com/lijust/EREI-3.2/issues/309#issuecomment-6719300660). Verified Package B [B0–B3](https://github.com/lijust/EREI-3.2/issues/309) and Package A [A0–A3](https://github.com/lijust/EREI-3.2/issues/308) are **CLOSED_PASS within their scoped claims**; G0–G3 + A0–A3 + B0–B3 = **12/16** formal gates.

The owner authorized **C0 scenario preregistration ONLY**, not C1 model calls, provider activation, network access, Root, Docker, patch/application or model-generated code. This document and `contracts/core13-pilot-c0-prereg-three-probes-v1.json` freeze a **candidate** fixed-protocol source/evidence bundle for owner review. They are NOT C0 formal GATE_PASS until independent post-review signoff in [Issue #310](https://github.com/lijust/EREI-3.2/issues/310).

## 2. Reviewed exact sources

| Artifact | Pinned Git blob |
|---|---|
| `tools/core13_pilot_b1_advisory_only.py` | `8be64b9a1a492e78b97903d95c44fcdea77099ce` |
| `contracts/core13-pilot-b0-source-route-inventory-v1.json` | `814e7194dc5ebd95557616a68117138ee880da3e` |
| `contracts/core13-pilot-closure-v1.json` | `939a27b43f752210668f6f8c0773209422f74209` |

C1 cannot silently replace these blobs, change case selection after viewing results, or treat a loose `main` checkout as source-bound evidence. Source manifest has exactly 14 known routes; B1 is a deterministic **non-AI** advisory-policy reader. Its only supported operations remain `guardrails` and `inspect_route`; no new execution route is authorized.

## 3. Exactly three fixed C1 scenarios

| Case | Input frozen before run | Expected independent outcome | Main caveat |
|---|---|---|---|
| **C1-01** — positive advisory | Exact JSON: `{"operation":"inspect_route","route_id":"J4_DIRECT_HOST_DOCKER"}` | exit=0, fixed status `CORE13_PILOT_B1_ADVISORY_ONLY_REVIEW`, `pilot_policy=DENIED`, `advisory_action=DENY_LEGACY_EXECUTION_ROUTE`, pinned J4 blob, zero Docker/Root/Model/Network/Shell/Patch counters | Establishes deterministic source-route reporting **only**, not AI inference quality. |
| **C1-02** — provider/network failure | **Actual provider fault boundary required**: a real, verifiable callable read-only provider timeout/unavailability. No direct B1 JSON input is an accepted substitute. | Must fail closed: no advisory output, no fallback into J4/J4S/Docker, no execution; independent error witness required | **BLOCKED at C0 preflight:** there is no provider/model/network adapter in current B1. An unknown `provider` field or `execute` rejection is NOT evidence of a provider outage. |
| **C1-03** — hostile candidate input | Exact JSON: `{"operation":"execute","route_id":"J4_DIRECT_HOST_DOCKER","command":"docker run --privileged","code":"print(123)"}` | exit=2, fixed status `CORE13_PILOT_B1_DEFAULT_DENY`, zero Docker/Root/Network/Shell/Patch/model-code execution, no echo of attacker text | Demonstrates denial at B1 JSON ingress, **not general prompt-injection resilience** of a generative model. |

The exact strings, source SHA, output fields, negative evidence and per-case identities are machine-readable in the same C0 contract. All C1 logs MUST identify original request digest, source HEAD/blob, per-case exit/outcome and the **reason if BLOCKED**, not silently count three when one is unavailable.

## 4. Provider and compute costs — explicit blocker, not a fake green result

**Verified fact:** B1 source has no model, API or network imports. No provider is configured in its interface. Thus the C0 contract honestly records:

```text
provider.mode=NONE_BOUND_TO_B1_VERIFIED_IN_SOURCE
provider.model_id=null
provider.endpoint=null
provider_calls_max=0
model_calls_max=0
network_calls_max=0
provider_api_cost_usd_max=0
C1-02.current_preflight_status=BLOCKED_NO_PROVIDER_SEAM
```

An offline mock of malformed JSON cannot be relabeled a genuine provider outage. **As it stands, C1 cannot satisfy all three frozen cases**, so `PILOT_ADVISORY_ONLY_GO` is not reachable on this exact candidate until a provider boundary exists and is proven. That is a substantive functionality dependency, not a request for a third security-testing cycle.

**Least-complex viable option:** before **any** C1 observation, the owner may authorize a **separate, precisely bounded change request** naming an existing read-only provider adapter, provider identity/version, exact source SHA, fault control (actual timeout/unavailable), budget and independently checkable denial oracle. Re-freeze C0 in a **new explicitly versioned contract before any C1 output**; never retroactively update this contract to make failed observations pass. If no such adapter is authorized/available, retain `C1-02=BLOCKED` and decide `PILOT_BLOCKED` or `PILOT_NO_GO` under the fixed original 16 gates. No silent simulation.

## 5. Cost/timeout/stop constraints

- Maximum **three C1 cases**, max **one first attempt per case**; never add a fourth case or choose fixtures after seeing model output.
- Request max **1024 bytes UTF-8**, report max **8192 bytes per case**, up to **12 seconds per CLI call**, aggregate **36 seconds** in C1 test harness. **No** calls to external provider under this **unbound provider** version; zero API cost.
- Nonroot Linux CI only, source-pinned checkout, no Docker API writes/CREATE/START/DELETE, no Python eval/exec of a candidate, no Root, no repository patches.
- Stop immediately if any unauthorized execution occurs; under the fixed C policy, no more than **two remediation rounds** in the entire Package C, with no automatic fourth package.
- C2 independent human review of A+B+C1 per-case evidence and rollback, not AI self-attestation. C3 requires **separately preregistered blind model-quality evaluation with independent oracle**. C1 security successes must not be reported as AI effectiveness.
- Only final dispositions: `PILOT_ADVISORY_ONLY_GO`, `PILOT_NO_GO`, `PILOT_BLOCKED`. Even a narrow GO does NOT enable Stable or independent AI acceptance.

## 6. State and source of truth

```text
PACKAGE_A=CLOSED_PASS_SCOPED_READ_ONLY
PACKAGE_B=CLOSED_PASS_SCOPED_ADVISORY_ONLY
GATES_FORMALLY_CLOSED=12/16
C0=PREREG_DRAFT_OWNER_REVIEW_PENDING
C1=NOT_RUN
C1_PROVIDER_FAILURE_CASE=BLOCKED_NO_PROVIDER_SEAM
C2=NOT_STARTED
C3=NOT_STARTED
MODEL_EFFECTIVENESS=NOT_ESTABLISHED
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
stable_ready=false
```

**C0 output:** a source-bound preregistration and honest blocker, **not** a trial. No C1 evidence is generated in this change, and none is implied by C0 static tests.
