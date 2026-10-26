# Gemini 3.8 Flash — isolated Core 13 adapter (LOCAL / one request only)

**Status:** adapter source and offline mocked tests only. **No real model execution has been authorized, made or counted.** The original disabled Copilot workflow stays disabled. The approved PR #98 synthetic T14 scope remains separate.

## Confirmed project limit shown by the owner (2026-10-25)

Google AI Studio project **EREI Gemini**, Free tier; model **Gemini 3.8 Flash** selected in usage charts. Displayed approximate limits: **5 RPM**, **250,000 input TPM**, **20 RPD**. Recent usage chart blank/zero. This is a user-provided *point-in-time screenshot*, not authenticated API quota from an API key. **The Antigravity row is a different agent quota, not Gemini 3.8 Flash.** Free tier standard input/output prices are zero according to Google's pricing page, but live quota and the billing tier of the key must still be checked in AI Studio.

The model endpoint ID is exactly `gemini-3.8-flash`. Only synthetic public Framework scenarios may be sent; Google states free-tier data may be used to improve its products. **Never send private project files or EREI/SAE-DB records.**

## Technical boundary

- One *explicit* `--live` invocation = **one REST POST maximum** to Google `v1beta/models/gemini-3.8-flash:generateContent`. No external SDK or package installation.
- API key read **only** from process environment `GEMINI_API_KEY`. No key stored in code, command arguments, logs, artifacts or repository. The model/service is accessed only if the operator supplies a key **belonging to the intended Free-tier project**; the adapter cannot independently prove a project's billing status, so do not use a paid-tier key.
- Adapter requires a **separate checkout** of reviewed target **PR #98 commit `31d4e518b9e71a9585df9097e7ca07a7e25af916`**, Git tree `913c6a0daaa7a6efa7d6d2148aa0294812fab360`. The adapter code itself is on its **own isolated PR** based on main; its revision must be recorded separately and is not a new target release commit. **The target worktree must be clean** (no modified or untracked files) before the call. In addition, each resolved public Framework artifact's UTF-8 bytes are compared to **the exact frozen Git HEAD blob**, blocking Git `assume-unchanged` hidden worktree edits; HEAD/tree plus `git status` alone are insufficient.
- Only the two public Core13 artifacts are readable. The precise V2 blind request, existing candidate resolver and direct prompt format are reused from `copilot_cli_exact_target.py`. No scorer expectations, hidden fixtures, or external tool execution. Requires structured `erei-action-simulation-v1` model output.
- No automatic retries on HTTP 429, response limit 512 KB, prompt limit 200 KB, model max output tokens 4096, **Gemini 3.8 Flash `thinkingLevel=low`** (no deprecated `temperature` field), timeout 5–120 seconds, one candidate with `STOP` only. A partial/bad response **fails**; no fabricated PASS.
- By itself the adapter does **not** enforce daily cross-process 20 RPD or 5 RPM limits, track owner quota, authenticate external provider, or qualify `exact_target_runtime` release evidence. **The separate one-case-only smoke launcher below** is now available for user-operated local execution, with bounded raw/usage capture. The existing `exact_target_run.py` still runs every case in an input suite, so do not use it to launch a bulk free-tier trial.
- Before any actual one-case call, require the owner's exact model/key/project/Free-tier confirmation and frozen clean target. The new **local smoke launcher** retains the raw provider envelope, usage metadata and one-case scorer verdict without including credentials; this is still only **unverified model evidence**, not a signed independent release acceptance or full 13-case admission.
- CI only runs mocked unit tests; no `GEMINI_API_KEY` is configured or used in GitHub Actions. Production, Stable, data/project pins and billing are never changed by this PR.

## Commands for offline tests (no key, no usage)

From the checkout of this adapter branch:

```powershell
python -m unittest evals.tests.test_gemini_core13_exact_target evals.tests.test_gemini_core_smoke -v
```

## Diagnosing `MODEL_REQUEST_FAILED_NOT_SCORED` without a second model call

The original smoke script at `ee4f0c4` suppresses its HTTP status and writes only `reason_category=GeminiAdapterError` to `smoke-001/attempt-failed.json`. Therefore the error alone **does NOT identify** an invalid key, missing permission, HTTP 400 payload issue, 403 model restriction, 429 project quota or a network timeout. Do not delete `smoke-001` or automatically retry the paid/limited POST.

The updated branch includes `evals/probe_gemini_access.py`. After checking out the **CI-green new PR #101 SHA**, run:

```powershell
cd "$env:userprofile\desktop\erei-core13-adapter"
python -m evals.probe_gemini_access --metadata-only
```

This prompts for the key invisibly again and issues **one GET** for `models/gemini-3.8-flash` metadata. **No `generateContent` call and no output token generation.** It emits only a safe HTTP status, model name match, and `generateContent` method presence. A 200 response verifies only key/model metadata access, **not** free-tier identity or entitlement to execute costly model calls; a 400/401/403/404 status suggests key/project/model access problems, 429 a quota issue; transport error suggests networking/proxy/TLS. The endpoint intentionally never prints Google's free-form error body, the secret, or any response content.

A *later* explicitly approved and controlled one-case smoke now writes `reason_category` as safe `GEMINI_HTTP_ERROR` / `GEMINI_TRANSPORT_ERROR` and `provider_http_status` for denial, rather than losing the HTTP code. **Use a new evidence directory `smoke-002` because the original `smoke-001` is preserved and must not be overwritten.** Never repeat the model POST merely to discover a quota issue before the metadata GET.

**Critical reviewer safety fixes:** Codex caught that the frozen suite/scorer could be modified under Git `assume-unchanged`, that cached `evals/__pycache__/runner*.pyc` could run despite checking source bytes (**P1**), and that clean Windows CRLF checkouts could be incorrectly rejected (**P2**). The current implementation now **reads the suite JSON directly from the immutable PR #98 Git blob** and **compiles/executes the scorer from Git blob bytes**, without reading the worktree scorer source or importing a cached `.pyc`. Public Framework Markdown artifacts are still independently compared against their committed Git blobs. Both safety regressions and clean-CRLF behavior are covered by offline tests. This is necessary before another smoke and does not confer independent model admission.

---

## Owner diagnostic update — 2026-10-25: HTTP 503 is service capacity, not an invalid key

The owner achieved metadata GET `HTTP 200` (the model and `generateContent` are listed) and attempted the frozen TLR-001 smoke a second time, using the corrected adapter `b09e229`. The generation POST returned **`GEMINI_HTTP_ERROR HTTP_503`**. Google's API error documentation describes 503 as **temporary service overload or unavailability**, distinct from 429 quota or 401/403 authorization errors. **Do not assume this proves an invalid key or an exhausted 20 RPD quota.** No successful raw model envelope, usage receipt or scored Core case was created. The provider might still meter an attempted request.

The immediately repeated launch with **the same evidence path** `smoke-002` produced `CORE_SMOKE_BLOCKED: GeminiAdapterError` **before any POST**, because the first attempt created that immutable output directory. This fail-closed no-overwrite behavior is intentional. Preserve both `smoke-001` and `smoke-002`; don't rename or delete them to conceal failed attempts.

Google's troubleshooting guide recommends waiting and applying bounded exponential backoff with jitter to transient 503s. This project deliberately disables automatic retries and keeps one request per invocation. If the free-tier project/model capacity is still available and the source revision passed exact-head CI/review, a subsequent *single* manually authorized attempt must use **a new** `smoke-003` folder, not `smoke-002`. If 503 persists, pause calls and inspect service status or switch to an **explicitly separate diagnostic model** rather than silently changing Core's pinned evaluation target.

**P1 source boundary discovered in Codex review:** Git replacement refs can substitute arbitrary scorer/Framework blobs even when HEAD and tree look correct. Current source Git subprocess reads now use `git --no-replace-objects` (including head/tree, artifact checks, frozen scorer/suites and adapter checkout identity), with mocked invariant tests plus a real temporary Git repo replacement regression. This must pass CI before another live attempt; independent reviewer decision remains separate.

---

## 2026-10-25 — repeated 3.8 Flash 503: stop identical Core POSTs

The owner received another `GEMINI_HTTP_ERROR HTTP_503` for `smoke-003`, following the same 503 for `smoke-002`. The metadata probe succeeded with GET 200, but this **does not** imply inference was available. Google Developers' public forum has independent October 2026 reports of precisely the same Free-tier `gemini-3.8-flash` GenerateContent 503 on minimal text requests, and Google staff attributes it to temporary capacity: https://discuss.ai.google.dev/t/repeated-503-unavailable-on-gemini-3-8-flash-free-tier-including-minimal-text-only-requests/189051 . **Do not keep repeating 3.8 Flash requests today**. Preserve `smoke-001`, `smoke-002`, `smoke-003` failed attempt directories.

To verify model-serving connectivity on a **separate** and explicitly non-Core route, the same branch now includes `evals/probe_gemini_fallback_generate.py`. After exact-head GitHub CI succeeds and the operator checks the selected alternate model's *actual project* Free-tier eligibility in AI Studio, this bounded script can send at most **ONE** minimal public text request to either `gemini-3.6-flash` or `gemini-3.5-flash-lite` (models with standard Free-tier prices). It never sends Framework source/cases or hidden expectations, does not log the key/provider error body, and **always counts 0 Core and 0 V1/V2 comparisons**. No retries, no paid-tier assumption. It prints only fixed success/error codes, model metadata and bounded usage fields.

```powershell
cd "$env:userprofile\desktop\erei-core13-adapter"
git fetch origin pull/101/head
git checkout --detach <LATEST_PR101_EXACT_CI_GREEN_SHA>
remove-item env:gemini_api_key -erroraction silentlycontinue
python -m evals.probe_gemini_fallback_generate --model gemini-3.6-flash --live --confirm-free-tier
```

The placeholder SHA is replaced by the last verified PR101 head, **not** a command literal. If 3.6 is denied or busy, do not automatically invoke another model—review the returned safe status and quota first. A successful probe establishes *only* that this alternative model could return one minimal text response, not that 3.8 is fixed or the alternate is validated for the Core13 behavior contract. Switching actual Core runtime requires explicit fixed model/version and acceptance evidence labels. This diagnostic does not alter protected main or enable billing.

---

## 2026-10-25 — Gemini 3.6 Flash inference diagnostic succeeded, Core model now explicitly selectable

Owner successfully ran the **standalone non-Core** `gemini-3.6-flash` diagnostic, obtaining `HTTP 200`, `finish_reason=STOP`, `returned_ready=true`, `provider_model_version=gemini-3.6-flash`. Provider reported **6 prompt tokens, 1 candidate token and 64 total tokens** (including other categories such as thinking). **Diagnostic remains `counted_core_cases=0`**, and cannot prove correctness of the Core13 behavior.

Google's official model page lists `gemini-3.6-flash` as a stable model with structured output and thinking support; the standard pricing table lists **Free-tier input/output tokens**. This is **not** an API receipt for a Core case, nor proof of remaining per-project model quota. Source: https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash and https://ai.google.dev/gemini-api/docs/pricing.

The Core adapter's current branch now supports **explicit `--model gemini-3.6-flash`** (stable exact ID only), while preserving the original **fixed Framework target PR #98 SHA/tree** and the original `gemini-3.8-flash` legacy default. The single-case launcher supplies the model to the single bounded `generateContent` call, records both **requested** and **provider-returned** model identity and refuses to score if they differ. The full original frozen case input + public Framework contracts are used, with separate immutable Git-backed scorer and case suites. **No Core case has yet been run on 3.6 as of this note.**

After exact-head CI and security review, and after the owner checks the Free-tier remaining quota for **the 3.6 model**, the optional **one owner-operated behavioral smoke** is:

```powershell
cd "$env:userprofile\desktop\erei-core13-adapter"
git fetch origin pull/101/head
git checkout --detach <EXACT_NEW_CI_GREEN_PR101_SHA>
git status --short
remove-item env:gemini_api_key -erroraction silentlycontinue
python -m evals.run_gemini_core_smoke --model gemini-3.6-flash --target-root "$env:userprofile\desktop\erei-core13-target" --case-id TLR-001-SUCCESS-STILL-LEARNING-DATA --output-dir "$env:userprofile\desktop\erei-core13-evidence\smoke-004" --timeout 90 --live --confirm-free-tier
```

Use a **new** `smoke-004` directory; do **not** delete `smoke-001/002/003` or rerun the old 3.8 Flash case. This command generates at most one real request and saves the provider raw JSON, usage metadata and local frozen-case scorer verdict. Any passing response is still labeled `observed_unverified` and requires independent examination before counted Core acceptance or a Stable promotion; **Core accepted 0/13, V1/V2 model comparisons 0/48**. If the selected provider model is unavailable at this time, stop and review the safe HTTP status rather than cycling more calls.

---

## 25 October 2026 — offline differential after genuine Core HTTP 503 (no additional API)

Owner's first FULL Core request on Gemini 3.6 Flash, `TLR-001`, separate local `smoke-004`, returned **HTTP 503** despite successful *non-Core* `READY` on the same model with a tiny public prompt. The backend did not return a scored Core response. **This does not establish that Framework behavior failed or that any particular parameter caused the 503.** These requests differ in at least FOUR simultaneous factors: prompt text and length, 64 vs 4,096 maximum output tokens, plain text vs `responseMimeType=application/json`, and default vs low thinking level.

**No-model-call inspection on the reviewed local adapter checkout:** the owner can now inspect the **EXACT outgoing Core body** without reading or providing any API key, generating tokens, writing evidence or contacting Google. This is the same canonical request-body constructor used by the live call:

```powershell
cd "$env:userprofile\desktop\erei-core13-adapter"
git fetch origin pull/101/head
git checkout --detach <CURRENT_EXACT_PR101_CI_GREEN_SHA>
git status --short
python -m evals.run_gemini_core_smoke --model gemini-3.6-flash --target-root "$env:userprofile\desktop\erei-core13-target" --case-id TLR-001-SUCCESS-STILL-LEARNING-DATA --inspect-request
```

The command returns `prompt_utf8_bytes`, `request_body_utf8_bytes`, SHA256s, exact requested config, frozen Framework source SHA/tree and adapter SHA, plus the four confounded differences. It **never outputs the full prompt, hidden case expectations or API key**; `model_calls=0`, `accepted_core_cases=0`, `cause_of_http_503=NOT_ESTABLISHED_BY_OFFLINE_COMPARISON`. A passing offline inspection is not a solution to a provider 503, not a model readiness claim, and not justification for automatically repeating a 3.6/3.8 API POST.

**Critical source safety:** the PR also checks that the ordered resolved Framework artifact paths match the exact frozen #98 declaration (`SKILL.md`, `SPEC.md`, `WORKFLOW.md` for TLR; only `WORKFLOW.md` for CCA). Even a symlink from an `assume-unchanged` tracked file to another *genuine* committed Markdown blob is rejected before constructing the prompt. This resolves the last previously identified Codex P2 path-substitution finding without creating another governance tool.

**Operational next gate:** keep existing `smoke-001`…`smoke-004` unchanged, stop repeated identical API calls, review this no-network delta and supplier service availability before selecting a *single* controlled diagnostic. The current 3.6 successful minimal probe is **non-Core**, and genuine accepted Core results remain **0/13**; no Stable promotion.

---

## 26 October 2026 — offline request shape confirmed; one DIFFERENTIAL (not retry) option

The owner ran the **exact** `--inspect-request` for frozen `TLR-001` on `gemini-3.6-flash` with adapter commit `4e342af8ad0bc504c702b187cf4596c8daf4b882`, target head `31d4e518b9e71a9585df9097e7ca07a7e25af916`, tree `913c6a0daaa7a6efa7d6d2148aa0294812fab360`. **No API request occurred.** Actual Core prompt is **18,832 UTF-8 bytes**; canonical REST body **19,532 bytes** (including JSON encoding and request settings), prompt digest `b2da2935cc4509e0384bd3b74d9bd9d151397c18e485f254ea6aca75e6356c8f`, body digest `2e4b4c5d2d758104658cf60a3be3eb007b26a5ae2e6daca0ce857af707b68ae5`. Core settings: **JSON MIME**, 4,096 max output tokens, **thinking low**. Past successful six-input-token `READY` connectivity control instead used **plain text**, 64 max output tokens, default thinking. The offline digest proves **which bytes were about to be sent**, not the cause of 503 and not any actual Core completion.

**One controlled alternative to repeated full Core HTTP 503 calls:** The existing one-shot `evals/probe_gemini_fallback_generate.py` now optionally accepts `--core-config-diagnostic`, which sends **a single tiny constant public JSON prompt** while using the exact Core generation settings. It contrasts **short prompt / full Core settings** to the previous **short prompt / basic settings** and the failed **long prompt / full Core settings**. This can narrow the contributing factor (subject to transient provider capacity), but cannot prove causation or count as a Core test. No Framework artifacts, hidden expectations, project data or API key are included in the prompt. It does not retry, does not activate paid billing, and prints only a safe status and usage data. Use only after confirming a remaining eligible free-tier call and latest exact-head CI on this branch:

```powershell
cd "$env:userprofile\desktop\erei-core13-adapter"
git fetch origin pull/101/head
git checkout --detach <LATEST_EXACT_GREEN_PR101_SHA>
git status --short
remove-item env:gemini_api_key -erroraction silentlycontinue
python -m evals.probe_gemini_fallback_generate --model gemini-3.6-flash --core-config-diagnostic --live --confirm-free-tier
```

The command is **one generation call**, **NOT** the Core13 smoke runner, so `counted_core_cases=0` and `stable_ready=false` regardless of returned text. **If it yields HTTP200**, the API accepts the Core-style settings for a small input at that time; size/content or transient availability remains a hypothesis for the failed full prompt. **If HTTP503**, capacity or the settings combination remains plausible; pause further attempts. If HTTP400, inspect compatibility of settings before live Core use. Do **not** retry repeatedly or infer that the 3.6 model cannot handle 19 KB based only on two incomparable attempts.

---

## Exactly one genuine Core case: owner-operated LOCAL smoke

**Never run on a GitHub hosted runner and NEVER paste a key in GitHub, ChatGPT or a command line.** The script `evals/run_gemini_core_smoke.py` prompts invisibly with Python `getpass` if `GEMINI_API_KEY` is unset. No key value is persisted. Malformed keys/HTTP header exceptions are **redacted before logging** (a prior Codex P1), including the case of a trailing newline. The owner must first verify in Google AI Studio that **the actual key** is part of **EREI Gemini (Free tier)**; an account screenshot by itself is not proof that every key belongs to that project.

Place the two independent **public repo** checkouts on a local Windows machine (use new folders, not your working project clones):

```powershell
cd "$env:userprofile\desktop"
git clone https://github.com/lijust/EREI-Engineering-Framework.git erei-core13-adapter
cd .\erei-core13-adapter
git fetch origin pull/101/head
git checkout --detach <PR101_CI_VERIFIED_SHA>
cd "$env:userprofile\desktop"
git clone https://github.com/lijust/EREI-Engineering-Framework.git erei-core13-target
cd .\erei-core13-target
git fetch origin pull/98/head
git checkout --detach 31d4e518b9e71a9585df9097e7ca07a7e25af916
cd "$env:userprofile\desktop\erei-core13-adapter"
```

Use the exact HEAD SHA listed in **PR #101 after its latest CI success** in place of `<PR101_CI_VERIFIED_SHA>`. `<...>` is a placeholder, not literal PowerShell syntax. `target-root` is checked for exact HEAD, Git tree and **clean worktree**. `adapter` checkout must also be clean. New evidence directory **must be outside both Git checkouts** and must not exist. The script only accepts one canonical Core13 case ID, never a whole suite.

```powershell
python -m evals.run_gemini_core_smoke --target-root "$env:userprofile\desktop\erei-core13-target" --case-id TLR-001-SUCCESS-STILL-LEARNING-DATA --output-dir "$env:userprofile\desktop\erei-core13-evidence\smoke-001" --timeout 90 --live --confirm-free-tier
```

This exact command performs at most **one** Gemini API `generateContent` request and does not automatically retry on 429 or malformed output. Requires valid Free-tier key, owner's quota, and suitable local network. It never uses paid-model budgets automatically. Before doing the call, it validates the frozen source/adapter identity and a public-only V2 blinded action-simulation contract. It uses the **frozen target runner/scorer** to score the response; it does not send private expectations to Gemini.

If the one call returns, output is retained *locally* under `erei-core13-evidence\smoke-001`:
- `blind-request.json` (one blinded public-only model input; no key);
- `provider-raw.json` (**exact original Gemini envelope including response, `modelVersion`, `responseId`, `usageMetadata`**; do not publish before inspecting);
- `adapter-normalized.json` (typed model response, only on parse success);
- `verdict.json` (frozen-target scorer result plus hashes, actual usage metadata, real source HEAD/tree and adapter commit, with `evidence_kind=observed_unverified` and `independently_accepted=false`);
- `attempt-failed.json` on a blocked remote attempt without a response, with no silent retry.

An actual response **may** fail scoring; this is still an authentic observed attempt, not a pass. A passing local response is an **unverified first model receipt** requiring later independent evidence review, not `Stable` or automatically admitted Core 13. There is no durable signed remote artifact authority in the smoke. **Do not send the API key or private raw response in chat.** Share only the sanitized command summary (case_id, pass, model_version, usage_metadata and status) to plan the next bounded cases.

**Current gate until the owner invokes this command:** `ADAPTER_OFFLINE_VALIDATION_ONLY`; `CORE_ACTUAL_MODEL_EVIDENCE=0/13`. No Copilot workflow reactivation, no new billing account and no EREI/SAE-DB private data needed.
