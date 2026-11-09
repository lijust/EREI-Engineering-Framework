# EREI Core13 — C2 Independent Evidence Review Packet (pre-owner decision)

**9 November 2026 | Mode: EXISTING_EVIDENCE_READ_ONLY | Decision status: C2 OWNER/HUMAN REVIEW PENDING**

## 1. Mandate, owner signoff, and review independence

**C1 owner signoff verified live**, user `lijust`, [issue #310 comment #6737778354](https://github.com/lijust/EREI-3.2/issues/310#issuecomment-6737778354): accepts **exactly 3 of 3** separately witnessed owner-local **offline advisory-only** C1 cases, acknowledges 94/94 source-bound posthoc receipt audit, synthetic (not real Google) fault, unavailable hosted CI, and authorizes **C2 independent evidence review only**. The signer explicitly retained `AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE`, `stable_ready=false`.

**Formal count:** G0–G3 + A0–A3 + B0–B3 + C0 + C1 = **14 of 16 PASS**. C2 and C3 are **NOT_PASS**, and C3 execution or final GO/NO-GO is not authorized. The frozen `contracts/core13-pilot-closure-v1.json` and prereg v1/v2/v3 remain immutable.

The source contract's C2 reviewer must be a **human GitHub owner or authorized independent reviewer**, not AI self-attestation. This assistant can cross-check publicly/API-supported source evidence and draft the decision record, but **cannot issue that human signoff**. Reviewer name, scope judgment, substantive comments/unknowns and final disposition must be entered **after a human independently inspects this packet**.

## 2. Source-verification table — positive and negative evidence

| Previous gate | Positive witness (reviewed evidence) | Negative / containment evidence | Trust boundary / known unknown | Evidence origin |
|---|---|---|---|---|
| G0–G3 | Fixed ABC governance and owner-gated narrow stages; signed ledger `GATE_PASS` | Fourth package and automatic AI/Stable escalation denied in frozen policy | Governance policy and CI are not operational effectiveness | `contracts/core13-pilot-closure-progress-v1.json`, [G initial CI](https://github.com/lijust/EREI-3.2/actions/runs/42303466210) |
| A0–A1 | GET-only model; 30/30 A0 and 29/29 nonroot socket/peer identity checks reported; owner-approved scoped progression | POST/START/DELETE, unexpected FD and mismatched peer denied in source/unit witnesses | Unit tests not global host isolation | G/A owner ledger, A source review |
| A2–A3 | [Owner-successful A2 run](https://github.com/lijust/EREI-3.2/actions/runs/42418179869), **two actual success jobs**: nonroot source/offline deny `128540689948`, secondary Docker GET-only `128540730256`; owner [#6713657840](https://github.com/lijust/EREI-3.2/issues/308#issuecomment-6713657840) formally closed A | Denied POST before backend, host baseline equality and temporary scratch-root absent after return asserted by source + successful jobs; cleanup/regression history | Root-held HMAC is **not independent of Root**; **no** external terminal-settlement audit or global Docker exclusivity | `docs/governance/core13-pilot-a2-success-a3-closure-review-20261107.md` |
| B0 | 14 specifically pinned route source files, seven source routes DENIED, successful [source-only job](https://github.com/lijust/EREI-3.2/actions/runs/42420217755); owner [#6713825884](https://github.com/lijust/EREI-3.2/issues/309#issuecomment-6713825884) | Unknown/unsafe routes and completeness claims fail-closed | 14 selected files **not a complete repository graph**; compare capped at 300 files | `contracts/core13-pilot-b0-source-route-inventory-v1.json`; B0 review |
| B1–B3 | Fixed **B1 deterministic advisory-only CLI** `8be64b9a1a492e78b97903d95c44fcdea77099ce`; [41/41 final CI](https://github.com/lijust/EREI-3.2/actions/runs/42463022672) successful, owner [B final #6719300660](https://github.com/lijust/EREI-3.2/issues/309#issuecomment-6719300660) formally closed B | Executable and hostile operations rejected, exact allowed B1 source graph/AST, no model/code/Docker/root calls in bounded tests | **Old J4/J4S/F5 entrypoints still exist**, are not globally disabled; no whole-repo runtime proof | B1/B2/B3 governance docs and B0 source manifest |
| C0 | 48/48 owner-local offline tests PASS, V3 exact 3-case prereg; owner [#6725740425](https://github.com/lijust/EREI-3.2/issues/310#issuecomment-6725740425) formally accepted | V1/V2 source immutable; C1-02 injection explicitly **synthetic**, no accidental model authorization; LF/CRLF fixed | No GitHub-hosted CI due account billing block; 48 passes are owner-local | `contracts/core13-pilot-c0-prereg-three-probes-v3.json`, C0 reports |
| C1 | Owner preapproved local evidence substitution [#6728988991](https://github.com/lijust/EREI-3.2/issues/310#issuecomment-6728988991); **three original uploaded JSONs**, SHA256 **3/3 match**, offline read-only audit **94/94 PASS**; owner postrun signoff [#6737778354](https://github.com/lijust/EREI-3.2/issues/310#issuecomment-6737778354) | C1-01 J4 `DENIED`; C1-02 one synthetic `URLError` fail-closed/no advice; C1-03 hostile Docker/code input `DEFAULT_DENY` exit 2 | `run_url/job_id=null` by consent; no independent host-side instrumentation or real provider test; all three witness durations rounded to 0.0 | `docs/governance/core13-pilot-c1-three-json-independent-audit-20261109.md` and JSON audit manifest |

**Cross-check done for this C2 preparation:** GitHub API returned `conclusion=success` for both A2 jobs (`128540689948`, `128540730256`) and for B0/B1/B2/B3 scoped source-only jobs. Separately confirmed the owner approval posts were made by GitHub account `lijust`. The 3 uploaded C1 original JSONs were read **without running C1**; the checked-in independent audit script (`/mnt/data/core13_c1_receipt_audit.py`, SHA256 `49585dec0ba023c054c51bb15ada8cd7a38e3e7e669703f3b13e4591726d8dcd`) was rerun **read-only** on the three originals: `checks 94 passed 94 failed 0; total_bytes 9162`. This is a byte/source audit, **not** independently observed runtime hardware state.

## 3. Required review of safety negatives, rollback, and cleanup

**Negative witnesses:** A2 rejected mutations to the secondary Docker daemon and exercised the nonroot peer/FD negative paths; B1 rejected commands, unknown routes and hostile extra fields; C1-03 returned `CORE13_PILOT_B1_DEFAULT_DENY` with reported `docker_api_calls=0`, `shell_calls=0` and `patches_written=0`. C1-02 stopped after the **controlled synthetic** provider-transport fault with `C0_PROVIDER_FAIL_CLOSED_NO_ADVICE`, one injected opener attempt and zero retry. **No claim that Google was actually down.**

**Cleanup evidence:** A2 workflow's post-run source assertion verified the private scratch directory absent and secondary Docker container inventory unchanged. This is **bounded source/CI evidence**, not an external root-independent settlement witness. For B/C there is no persistent pilot service/container to clean up: B1/C1 were standalone local non-executing CLI operations; the only expected C1 writes were three exclusive JSON receipts outside the repo. The original owner-local receipts should be preserved, never overwritten or rerun.

**Rollback:** B1/C1 remains **Draft/unmerged** as at C2 review ([App B #315](https://github.com/lijust/EREI-3.2/pull/315), [Framework B #175](https://github.com/lijust/EREI-Engineering-Framework/pull/175), [App C #316](https://github.com/lijust/EREI-3.2/pull/316), [Framework C #176](https://github.com/lijust/EREI-Engineering-Framework/pull/176)). Narrow rollback is simply **stop invoking the B1/C1 entrypoints**. Any later merge would require an explicit, separately reviewed `git revert` of approved commits (no `git reset --hard` or evidence deletion). No destructive rollback was performed or required by the standalone offline pilot.

## 4. Mandatory unknowns and restrictions — DO NOT waive

| Item | Current status | Why C2 cannot claim more |
|---|---|---|
| Independent human reviewer approval | **PENDING** | AI-produced evidence packet cannot satisfy human GitHub owner/authorized independent reviewer requirement |
| Independent AI effectiveness and model predictions | **NOT_ESTABLISHED / zero live model calls** | The three C1 scenarios test deterministic safety and a simulated transport, not Gemini performance |
| Actual Google service outage or live provider reliability | **NOT_TESTED** | One `urllib.error.URLError` was injected into an offline opener; zero Google requests |
| Independent external host/root receipt | **NOT_ESTABLISHED** | A2 root-held HMAC not independent of Root; no external terminal settlement/late-create-quiescence |
| Complete repo-wide path isolation | **NOT_ESTABLISHED** | B1 source graph limited; legacy J4/J4S entrypoints still independently callable |
| Hosted GitHub Actions for C0/C1 | **BLOCKED BEFORE RUNNER, billing/payment** | Owner approved truthful local process/PID+SHA substitutes, NOT hosted CI success |
| Source-based zero effect claims | **SCOPED** | Counters and patch guards cover fixed code under the pinned test process, not any arbitrary OS process |
| Measured C1 latency | **NOT_VERIFIED HIGH RESOLUTION** | Three artifact `duration_seconds=0.0` values cannot establish performance |
| C3 final pilot GO/NO-GO | **NOT_STARTED/NOT_AUTHORIZED** | Requires separately reviewed C2 closure; cannot auto-pass or promote model/stable |
| Root/Docker create/start or AI code execution | **NOT AUTHORIZED** | Remain blocked even if C2 passes |

## 5. Reviewer decision requirements (human only)

The independent human reviewer should inspect the prior source/run/job links and the immutable C0 V3/C1 uploaded evidence audit, then leave a GitHub Issue #310 comment that answers each of the following **substantively**, not with a blanket automatic PASS:

1. **Evidence provenance:** Were the A2/B3 GitHub jobs, owner gates, and the three separately witnessed C1 owner-local receipts sufficiently corroborated for *this bounded offline pilot*? Note that 94 C1 audit assertions evaluate supplied report content, not host-wide observation.
2. **Safety negative/fault classification:** Confirm that A2 mutation denial, B1/hostile request denial and C1-02 **synthetic, not real-Google-outage** classification align with the documented boundaries.
3. **Rollback/cleanup:** Review A2 scoped cleanup and unchanged baseline, plus the no-service stop-invoking rollback and open Draft PRs; affirm that no unperformed destructive revert is being claimed.
4. **Residual risks/unknowns:** Explicitly accept or reject each material limitation in Section 4; do not imply model utility, universal isolation or Stable.
5. **C2 disposition:** `C2_SCOPED_EVIDENCE_REVIEW_ACCEPTED`, `C2_BLOCKED_MORE_EVIDENCE_NEEDED`, or `C2_NO_GO`, with an owner/reviewer link and boundaries. Only an explicit post-review human signoff can set `C2=GATE_PASS`. This cannot authorize C3 automatically without the exact separately approved C3 scope.

### Recommended evidence-based reviewer disposition (not a gate decision)

**C2 appears eligible for `GATE_PASS` only as a source-bound, non-executing, offline advisory pilot evidence review**, if the human reviewer accepts the limitations above. The available evidence **does not support** labeling this a validated live Gemini pilot, real model utility, Docker/root host-wide isolation or `stable_ready=true`.

```text
FORMAL_GATES_PASSED=14/16
C2_EVIDENCE_PACKET=PREPARED_SOURCE_CROSSCHECKED
C2_HUMAN_INDEPENDENT_REVIEW=REQUIRED_NOT_YET_RECEIVED
C2_GATE_PASS=false
C3=NOT_STARTED
C1_SIGNOFF=https://github.com/lijust/EREI-3.2/issues/310#issuecomment-6737778354
GO_FOR_LIVE_AI=false
MODEL_EFFECTIVENESS=NOT_ESTABLISHED
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
stable_ready=false
```
