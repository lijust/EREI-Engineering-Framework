# Security/source disposition requests — 2026-10-24

**Status: REQUESTED / NOT APPROVED.** This is a bounded reviewer worklist,
not an independent review signature, release authority or finding closure.
An independent reviewer must record a concrete `ACCEPT`, `REJECT`, or
`FIX_REQUIRED` against the *actual current* source HEAD plus referenced
applicable aggregate target/tree; old GitHub CI or automated advisory results
are not substitutes. Existing original review threads stay open.

| Scope | Exact GitHub source HEAD inspected | Outstanding reviewer decision |
|---|---|---|
| P1 original #84 (already merged; thread open) | `6abd58c121b85015c85649d12251b2fb27ba8e2f` | Verify mixed V1/V2 positional review fails closed even for backdated events; explicitly accept strict-deny migration compatibility behavior. Original thread `PRRT_kwDOUJKdL86twqqM`. |
| P1 original #86 (already merged; thread open) | `f47ac7c213334eb84b89ed7bdcf46766503c2d72` | Verify actual clean Git checkout does not become dirty from CPython bytecode, but new untracked Python source still fails guard; original thread `PRRT_kwDOUJKdL86t670K`. |
| P1 original #88 (already merged; thread open) | `17607351767a44ff9b3a47ff7388e63f4997b214` | Verify canonical review-ID ordering before deriving prospective state and explicit no-apply scope; original thread `PRRT_kwDOUJKdL86t8zea`. |
| CI security #67 (open; P1/P2) | `4f2464738017dcecd24dbbd264c8478e99593289` | Verify PR changes cannot cancel protected main/release push jobs via repository-wide concurrency group; unfiltered assurance still runs and doc/test match. Original unresolved threads `PRRT_kwDOUJKdL86v0S8I`, `PRRT_kwDOUJKdL86v0VLe`. |
| T10 release deny #91 (open) | `ca39da92ee21620a294457744dcdcacf97054ed2` | Verify review-only/forged workflow/check evidence cannot become release authority. Does not constitute positive T11 source/consumer approval. |
| T14 synthetic rollback #94 (open; P2) | `8b067b57edfa671f70caa90d9fc03862ded70885` | Verify persistent 3.11/3.12 source-bound drill receipts including error paths, preserve synthetic-only limit. Unresolved thread `PRRT_kwDOUJKdL86v0EsZ`. |
| T15 calibration #95 (open; P2) | **update to latest HEAD before signoff** | Verify source-recipe/content-hash changes, pinned private-source confidentiality, originally failing PY-04 mutant rejection, replacement one-assertion result, APP-04 12-case preview boundary oracle, independent hidden acceptance missing. |

## Required per-finding reviewer record

For each row above, the independent reviewer must supply all of:
- Reviewer identity and independently authorized role; reviewer must not silently
  assume the implementation author's role.
- Exact PR commit SHA **and** applicable combined/merge target SHA/tree.
- Finding ID/thread, evidence run IDs and clear decision
  `ACCEPT` / `REJECT` / `FIX_REQUIRED`, with rationale and scope.
- Explicit distinction between a *source-only fix*, *synthetic isolated drill*,
  *Internal read-only pilot*, and *Stable release/consumer acceptance*.
- Any residual risk, required remediation and reviewer date.

An outstanding finding remains `PENDING` even if its PR was merged.
Do not mark GitHub review threads resolved on this draft. Consumer/
workflow-source authentication and positive independent release authority
remain T11 blockers; existing main ruleset protection/required `assurance`
should **not** be recreated.

**No user-data writes, workflow/pin changes, merges, production actions,
paid model calls, or release authority are authorized by this file.**
