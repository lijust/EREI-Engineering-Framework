# CORE13 Learning Pattern — Stage 1: contract failures to generalized intervention

Date: 2026-10-26. **Offline experiment proposal, NOT observed model improvement.**

## Unmodified evidentiary baseline

- Original frozen PR98 / `31d4e518b9e71a9585df9097e7ca07a7e25af916` remains immutable.
- The 13 genuine Gemini 3.5 Flash-Lite original-case observations were **9 scored PASS / 4 scored FAIL**. No independent admission, no Stable promotion.
- Compact schema V2 is a *separate experiment*: its TLR-003 run was a **scored FAIL** despite the schema requiring `actions[*].op`; the model proposed incomplete/extra actions. Its bridge TLR-002 PASS is not new benchmark uplift because this is an originally passing case.
- The original scorer, benchmark expectations and frozen target must never be edited to make a candidate pass.

## Failures interpreted — no case-specific answers sent to the model

| Public benchmark case | Observed failure family / what it tests | General transferable learning rule |
| --- | --- | --- |
| TLR-003 | Required action argument completeness / event-vs-review confusion | Determine whether any real task event happened. For each necessary action require full interface fields and reproduce the state transition. |
| TLR-004 | Threshold-driven policy vs malformed actions | Apply the artifact's stated thresholds from supplied facts; emit the precise interface-required arguments, not placeholder objects. |
| TLR-007 | Feedback/promotion lifecycle versus unauthorized direct Core change | Respect workflow approvals and operation ordering; feedback is not self-modification. |
| CCA-006 | Fail-closed capability authorization and pin identity | Evaluate authorization gates independently; don't treat a mutable reference or an apparent adoption record as blanket activation permission. |

This table is for engineering diagnosis, NOT model input and NOT a specification of expected benchmark outputs.

## Experiment V3

- Source branch forks immutable PR105 compact-schema V2 at `ecfc2818598e4631166bd3dec2774cb8178d0e10`.
- A single **generic model-facing coaching appendix** encourages a silent seven-step self-check (source policy → exact action interfaces → state transition → consistent JSON). It contains no case identifiers, oracle decisions, expected states or scorer feedback.
- The Gemini response schema, model, generation config, source cases, frozen evaluator and scorer are identical to V2. The sole intended request change is that the same prompt has a fixed general coaching suffix appended.
- This is **prompt-based behavioral guidance**, not persistent model weight updates, learned memory, or self-modifying Framework Core.
- Offline unit tests prove the scope of the delta, redaction, absence of provider requests and unknown-model failure.
- No provider credentials, prompts or raw provider responses are sent to GitHub. No paid quota or Gemini requests are initiated by this branch.

## Evidence gates to advance in order

1. **Static gate (this PR):** isolated V3 request diff, no oracle leak, local source identity, offline tests/CI. Status does not imply accuracy uplift.
2. **Controlled live gate (later, explicitly enabled):** an owner-local, pinned worker version that has passed its own security review, supporting V3 as a distinct allowlisted experiment and respecting daily quota. Frozen scorer and frozen target are unchanged; each request gets a new immutable evidence directory.
3. **Paired case gate:** compare original baseline / compact V2 / V3 on TLR-003, TLR-004, TLR-007 and CCA-006. Count `INVALID`, `SCORED_FAIL`, transport errors and scored passes separately; don't treat retries, transport errors or malformed JSON as successful behavior.
4. **Regression gate:** run all 13 frozen cases for V3 (subject to explicit provider quota and owner-verified budget); preserve original 9 passes and measure new outcomes without claiming the same prompts generalize beyond the benchmark.
5. **Learning/transfer gate:** validate on fresh, non-oracle synthetic tasks representing the *same general action/state interface* before treating the prompt as reusable. Review and accept independently; document rework/verification-failure rates without inventing denominator metrics.
6. **Admission gate:** independent evidence approval and normal project pin/adoption constraints remain required for Internal and Stable. Until then `independently_accepted=false`, `stable_ready=false`.

**Operational note:** the owner's current PR106 bridge is pinned to PR105 compact V2 only, and has **1 Gemini call/day UTC** configured. This V3 branch does NOT change it or silently run V3 through a V2 route. A separately reviewed, locally installed and owner-authorized V3 transport step is required before any live test.
