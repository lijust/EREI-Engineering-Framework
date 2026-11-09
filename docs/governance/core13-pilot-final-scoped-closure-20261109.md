# EREI Core13 — Final Owner-Signed Scoped Pilot Closure

**Date:** 2026-11-09  
**Disposition:** `PILOT_ADVISORY_ONLY_GO` — **only for the completed owner-local, deterministic, source-bound, offline, advisory-only evidence demonstration**  
**Formal fixed gates:** **16/16 GATE_PASS**  
**Authoritative owner decision:** [GitHub `lijust`, Issue #310 comment #6738737883](https://github.com/lijust/EREI-3.2/issues/310#issuecomment-6738737883)

## 1. Authority and decision

The human GitHub repository owner explicitly reviewed the C3 evidence packet, the immutable decision rules and prior signed gates, negative safety evidence, rollback and cleanup limitations, and residual risks, then accepted **C3 as `GATE_PASS`** and selected **`PILOT_ADVISORY_ONLY_GO`**.

This is a **retrospective, restricted-scope governance closure**. It records successful completion of a **fixed offline evidence demonstration**; it does **not** authorize deployment, real model calls, arbitrary repository or host operations, Docker CREATE/START, Root operations, automatically applied patches, or execution of model-generated code.

The scope and rules derive from immutable `contracts/core13-pilot-closure-v1.json` (Git blob `939a27b43f752210668f6f8c0773209422f74209`) and frozen C0 V3 `contracts/core13-pilot-c0-prereg-three-probes-v3.json` (Git blob `6f95214e6e7333fde41905209b891a9b877903e9`). **Neither frozen contract was modified to close this pilot**.

## 2. Evidence and signatures supporting 16/16

| Group | Signed evidence | Fixed gates accepted | Scope |
|---|---|---:|---|
| Governance | [Owner G decision, Issue #307](https://github.com/lijust/EREI-3.2/issues/307) | G0–G3 (4/4) | Fixed owner-gated, capped governance |
| Package A | [A2 bounded real secondary Docker GET-only run](https://github.com/lijust/EREI-3.2/actions/runs/42418179869); [A owner closeout](https://github.com/lijust/EREI-3.2/issues/308#issuecomment-6713657840) | A0–A3 (4/4) | Scoped, GET-only secondary Docker evidence—not universal isolation |
| Package B | [Source/negative test run](https://github.com/lijust/EREI-3.2/actions/runs/42463022672); [B owner closeout](https://github.com/lijust/EREI-3.2/issues/309#issuecomment-6719300660) | B0–B3 (4/4) | One pinned deterministic non-executing advisory CLI—not a repository-wide runtime guarantee |
| C0 | [Owner final C0 freeze approval](https://github.com/lijust/EREI-3.2/issues/310#issuecomment-6725740425) | C0 (1/1) | Fixed exactly-three-case prereg; owner-local 48/48 offline tests |
| C1 | [Owner post-run C1 approval](https://github.com/lijust/EREI-3.2/issues/310#issuecomment-6737778354); `docs/governance/core13-pilot-c1-three-json-independent-audit-20261109.md` | C1 (1/1) | Exactly three owner-local offline JSON receipts, 3/3 SHA256 and 94/94 retrospective content assertions |
| C2 | [Owner independent-evidence review decision](https://github.com/lijust/EREI-3.2/issues/310#issuecomment-6738106706); `docs/governance/core13-pilot-c2-independent-evidence-review-20261109.md` | C2 (1/1) | Review of A/B/C1 positive, negative, fault, cleanup, rollback and residual limits |
| C3 | [Explicit owner final GO/NO-GO decision](https://github.com/lijust/EREI-3.2/issues/310#issuecomment-6738737883); `docs/governance/core13-pilot-c3-final-scoped-go-no-go-review-20261109.md` | **C3 (1/1)** | Final scoped **offline pilot closure**; separates safety evidence from model usefulness |

**Total:** 4 + 4 + 4 + 1 + 1 + 1 + 1 = **16/16 formally owner-accepted gates**. The existence of historical successful Actions jobs must not be misrepresented as GitHub-hosted C1 CI success.

## 3. Mandatory negative evidence, fault classification and rollback

- **C1-02** injected **one synthetic `urllib.error.URLError`** into a pinned local provider seam. The HTTP request was prepared but **never sent**. This does **not** demonstrate a real Google outage or actual provider reliability. Sanitized fail-closed/no-advice behavior was accepted **only** for that fixed synthetic case.
- **C1 provenance:** original three local JSON receipts, exact SHA256 integrity checks and 94/94 independently run, read-only *content* checks; the GitHub-hosted `run_url` and `job_id` are **null under advance owner consent** because billing prevented the C1 runner starting. The receipts do not establish independent whole-host observation.
- **A/B safety negatives:** A2 mutation attempts rejected within bounded read-only verifier, while the B1 source-based deterministic CLI rejected disallowed and hostile routes. These are **not** proof that old J4/J4S entrypoints elsewhere are globally disabled.
- **Cleanup:** A2 workflow asserted that the scoped scratch resource was removed and secondary Docker inventory baseline unchanged. This is **not** an independent Root/terminal settlement witness. Offline B1/C1 created no persistent service; retain the three original receipts unmodified.
- **Rollback:** existing draft, unmerged pilot branches may be left dormant by **not invoking** their bounded CLI. No destructive rollback, removal of evidence or production deployment is reported. [App C Draft PR #316](https://github.com/lijust/EREI-3.2/pull/316) and [Framework C Draft PR #176](https://github.com/lijust/EREI-Engineering-Framework/pull/176) must remain **Draft/unmerged** under the owner's final instruction.

## 4. Explicit non-claims and deferred obligations

**NOT ESTABLISHED:** independent Root/terminal settlement or root-independent receipt custody; durable external late-create-quiescence proof; host-wide Docker isolation; globally complete application execution-path migration or legacy J4/J4S disablement; independent L3; real Google downtime/provider reliability; hosted C1 CI; live Gemini behavior or **blinded independent model effectiveness**; Stable or production readiness.

The original deferred Issue [#311](https://github.com/lijust/EREI-3.2/issues/311) remains **DEFERRED** and cannot auto-activate from this closeout. Any later live provider test, model-effectiveness study, deployment, merged pilot code, Docker/Root operation or model-generated-code execution needs separately justified scope and explicit fresh authorization, not this decision.

```text
FORMAL_GATES_PASSED=16/16
PILOT_DECISION=PILOT_ADVISORY_ONLY_GO
DECISION_SCOPE=OWNER_LOCAL_OFFLINE_SOURCE_BOUND_ADVISORY_EVIDENCE_ONLY
C3=GATE_PASS
MODEL_EFFECTIVENESS=NOT_ESTABLISHED
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
stable_ready=false
LIVE_MODEL_CALLS_AUTHORIZED=false
DOCKER_CREATE_START_AUTHORIZED=false
MODEL_GENERATED_CODE_EXECUTION_AUTHORIZED=false
PRODUCTION_DEPLOYMENT_AUTHORIZED=false
DEFERRED_CAPABILITIES_ACTIVATED=false
```

## 5. Closure actions and evidence preservation

This final record and `contracts/core13-pilot-closure-progress-v1.json` are mirrored between App and Engineering Framework. Original C0 V3 inputs/oracles, original C1 receipts and retrospective C1/C2/C3 evidence reports are **preserved**, not overwritten. No tests, model/network requests, Docker/Root operations or generated-code execution were performed to author this post-decision record.

**Closure criterion met:** a distinct human owner C3 decision + 16 signed fixed gates + frozen boundary + documented non-claims. **The bounded pilot is closed; Stable and model acceptance remain explicitly blocked.**
