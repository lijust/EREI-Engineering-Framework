# Gemini 3.8 Flash — isolated Core 13 adapter (LOCAL / one request only)

**Status:** adapter source and offline mocked tests only. **No real model execution has been authorized, made or counted.** The original disabled Copilot workflow stays disabled. The approved PR #98 synthetic T14 scope remains separate.

## Confirmed project limit shown by the owner (2026-10-25)

Google AI Studio project **EREI Gemini**, Free tier; model **Gemini 3.8 Flash** selected in usage charts. Displayed approximate limits: **5 RPM**, **250,000 input TPM**, **20 RPD**. Recent usage chart blank/zero. This is a user-provided *point-in-time screenshot*, not authenticated API quota from an API key. **The Antigravity row is a different agent quota, not Gemini 3.8 Flash.** Free tier standard input/output prices are zero according to Google's pricing page, but live quota and the billing tier of the key must still be checked in AI Studio.

The model endpoint ID is exactly `gemini-3.8-flash`. Only synthetic public Framework scenarios may be sent; Google states free-tier data may be used to improve its products. **Never send private project files or EREI/SAE-DB records.**

## Technical boundary

- One *explicit* `--live` invocation = **one REST POST maximum** to Google `v1beta/models/gemini-3.8-flash:generateContent`. No external SDK or package installation.
- API key read **only** from process environment `GEMINI_API_KEY`. No key stored in code, command arguments, logs, artifacts or repository. The model/service is accessed only if the operator supplies a key **belonging to the intended Free-tier project**; the adapter cannot independently prove a project's billing status, so do not use a paid-tier key.
- Adapter requires a **separate checkout** of reviewed target **PR #98 commit `31d4e518b9e71a9585df9097e7ca07a7e25af916`**, Git tree `913c6a0daaa7a6efa7d6d2148aa0294812fab360`. The adapter code itself is on its **own isolated PR** based on main; its revision must be recorded separately and is not a new target release commit.
- Only the two public Core13 artifacts are readable. The precise V2 blind request, existing candidate resolver and direct prompt format are reused from `copilot_cli_exact_target.py`. No scorer expectations, hidden fixtures, or external tool execution. Requires structured `erei-action-simulation-v1` model output.
- No automatic retries on HTTP 429, response limit 512 KB, prompt limit 200 KB, model max output tokens 4096, timeout 5–120 seconds, one candidate with `STOP` only. A partial/bad response **fails**; no fabricated PASS.
- By itself the adapter does **not** enforce daily cross-process 20 RPD or 5 RPM limits, track owner quota, authenticate external provider, store original API transport/usage tokens, or qualify `exact_target_runtime` release evidence. The operator must constrain use; **do not launch 13 cases automatically**. The existing `exact_target_run.py` runs every case in an input suite and has no one-case selector. Do not use it as a one-case smoke-test driver before a reviewed bounded selector exists.
- Before any actual one-case call, fix the invocation to a source-scoped case and validate that a raw response and its metadata can be retained without including private credentials. Current harness can retain adapter-normalized responses; it does **not** preserve the full raw provider envelope/usage meter, so this path is **not yet sufficient for complete accepted Core13 evidence**.
- CI only runs mocked unit tests; no `GEMINI_API_KEY` is configured or used in GitHub Actions. Production, Stable, data/project pins and billing are never changed by this PR.

## Commands for offline tests (no key, no usage)

```powershell
python -b -m unittest evals.tests.test_gemini_core13_exact_target -v
```

**Current gate:** `ADAPTER_OFFLINE_VALIDATION_ONLY`; `CORE_ACTUAL_MODEL_EVIDENCE=0/13`. Further live use requires securely configuring a Free-tier-project key locally, approving the exact bounded single-case invocation and persistence contract, and confirming that quota capacity remains. **Do not paste keys into GitHub issues or this conversation.**
