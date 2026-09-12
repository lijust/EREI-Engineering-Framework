# Matt Pocock Pattern Candidates — Promotion Readiness V1

**Status:** Evidence review only — no Candidate→Stable promotion authorized or applied.  
**Framework baseline:** `46e2481edf6102bc629c8c9a9d561534894846ba`  
**Stable release remains:** `task-learning-review-v1 @ 69079018606750312344cb3c648952b9ab72d35b`  
**Upstream inspiration snapshot:** `mattpocock/skills@3cca18b368ae95cdbdebbff572ccafa662551015`

## Purpose

Assess whether the three EREI-native Candidate V1 capabilities introduced by Framework PR #45 have accumulated enough real-project evidence for a governed Stable promotion review.

This document does **not**:

- change `CAPABILITIES.json`,
- create a Stable release,
- move any project Framework pin,
- alter any project runtime,
- grant architecture/refactor authority,
- treat all three candidates as a single promotion unit.

Promotion decisions remain independent and require explicit approval plus the normal Framework release/promotion process.

## Framework-level baseline evidence

Framework PR #45 introduced:

1. `architecture-deepening-analysis`
2. `behavior-first-testing`
3. `domain-language-modeling`

The candidate package passed:

```text
Framework Assurance Gate = PASS
Framework Evals          = PASS
Framework tool tests     = PASS
Eval harness self-tests  = PASS
Published eval cases     = 53/53 PASS
Capability registry      = PASS
Stable release/pin       = UNCHANGED
```

The original candidate evals therefore establish contract-level readiness. The sections below assess real brownfield evidence after adoption in `lijust/EREI-App-Google`.

---

# 1. architecture-deepening-analysis

## Current recommendation

**`READY_FOR_PROMOTION_REVIEW`**

This is a recommendation to start governed Stable promotion review, not an automatic promotion.

## Real-project trigger

The candidate method identified repeated lifecycle knowledge across independent App host-candidate builders:

- inventory search,
- match scoring,
- broker CRM,
- plus partial repetition in additional candidate tooling.

Repeated caller knowledge included artifact hashing, manifest verification, portable-dependency guards, source copying, source immutability, candidate digesting, and success-evidence writing.

The analysis used the deletion test and locality/caller-knowledge reasoning rather than adding an abstraction for symmetry.

## Resulting deeper seam

The bounded extraction created:

`tools/lib/portable-host-candidate-builder.js`

The shared module owns only the repeated safe-build lifecycle. Domain-specific lock rules, source transformations, host responsibility assertions, and evidence semantics remain local to each consumer.

## Independent migration evidence

### Slice 1 — inventory search

App PR: `lijust/EREI-App-Google#129`  
Merged App commit: `9c6f905d3810a185b9c51f2a322259b3a4c18fab`  
Full-source self-hosted run: `34669516572` — **SUCCESS**

Observed evidence:

```text
TARGETED_GREEN_CODE_CONTINUITY=PASS
PORTABLE_LIFECYCLE_EXACT_APP=PASS
INVENTORY_CANDIDATE_FULL_SOURCE=PASS
APP_SRC_DIFF=NONE
RUNTIME_MUTATION=NONE
DEPLOYMENT_MUTATION=NONE
```

### Slice 2 — match scoring

App PR: `lijust/EREI-App-Google#130`  
Merged App commit: `0ece49b3f07a5b92498fa3d79b0c3f9b80a54816`  
Full-source self-hosted run: `34669750904` — **SUCCESS**

Observed evidence:

```text
portable-host-candidate-builder.test.js=PASS
match-scoring-host-candidate.test.js=PASS
PORTABLE_LIFECYCLE_EXACT_APP=PASS
MATCH_SCORING_FULL_SOURCE=PASS
APP_SRC_DIFF=NONE
RUNTIME_MUTATION=NONE
DEPLOYMENT_MUTATION=NONE
```

No modification to the shared lifecycle module was required for this second domain.

### Slice 3 — broker CRM

App PR: `lijust/EREI-App-Google#131`  
Merged App commit: `60a219276c207ebcef1e4f21c84820df728e569d`  
Full-source self-hosted run: `34669855690` — **SUCCESS**

Observed evidence:

```text
portable-host-candidate-builder.test.js=PASS
broker-crm-host-candidate.test.js=PASS
PORTABLE_LIFECYCLE_EXACT_APP=PASS
BROKER_CRM_FULL_SOURCE=PASS
APP_SRC_DIFF=NONE
RUNTIME_MUTATION=NONE
DEPLOYMENT_MUTATION=NONE
```

No modification to the shared lifecycle module was required for this third domain.

## Why the evidence is promotion-grade

Three materially different consumers now share the same deeper lifecycle seam while preserving different domain callbacks and security/host boundaries.

The second and third consumers required **zero shared-module changes**, which is strong evidence that the interface was not overfit to the first inventory-search extraction.

The work also stayed vertical and bounded:

- one consumer migrated at a time,
- each slice independently verified before merge,
- no broad all-builders refactor,
- no `src/**` mutation,
- no runtime/deployment authority change.

## Remaining promotion review questions

Before Stable promotion, reviewers should confirm:

1. the Candidate skill wording still reflects the proven bounded behavior;
2. no trial-specific language should become mandatory process for low-risk/local changes;
3. the capability remains analysis/advice and does not itself authorize refactoring;
4. Stable release packaging and migration notes preserve existing project behavior.

No additional brownfield proof is currently required by this readiness review.

---

# 2. behavior-first-testing

## Current recommendation

**`CONDITIONAL — NEEDS_AUTHORITATIVE_RED_GREEN`**

Do **not** promote to Stable yet solely from the current evidence.

## Evidence obtained

The App trial created and used a public lifecycle behavior seam:

`tests/portable-host-candidate-builder.test.js`

The test covers externally meaningful lifecycle behavior including:

- source immutability,
- verified bundle installation,
- artifact tamper fail-closed,
- host/platform dependency fail-closed,
- illegal source mutation fail-closed,
- success evidence only after safety checks.

Subsequent authoritative executions were GREEN on the App self-hosted runner, including full-source validation during PRs #129, #130, and #131.

The method also materially improved evidence honesty: multiple GitHub-hosted jobs with `runner_id=0` and `steps=[]` were classified as infrastructure non-execution rather than falsely counted as behavioral RED or GREEN evidence.

## Missing evidence

The first behavior test was intentionally committed before implementation, but the intended RED run never executed because GitHub-hosted Actions failed before allocating a runner.

Therefore:

```text
intended RED commit existed          = YES
authoritative RED behavior executed  = NO
authoritative GREEN behavior executed= YES
```

A later test-fixture failure was caused by CRLF normalization in a bounded validation fixture and does not count as a product/behavior RED for the candidate method.

## Promotion condition

Before Stable review, obtain **one real, non-manufactured engineering change** where:

1. an approved public behavior seam already exists or is independently justified;
2. a new/changed behavior is expressed first;
3. the authoritative runner executes and observes RED for the intended behavioral reason;
4. the smallest implementation turns that same behavior GREEN;
5. regression/final verification passes without weakening the test;
6. the RED and GREEN commits/runs are durably referenced.

Do not invent a product behavior or deliberately break working code merely to satisfy this condition. Wait for a real suitable change if necessary.

## Why this is not a rejection

Framework contract evals pass and real GREEN/public-seam evidence is strong. The only missing item is direct empirical proof of the distinguishing red→green execution discipline under authoritative runner evidence.

---

# 3. domain-language-modeling

## Current recommendation

**`READY_FOR_PROMOTION_REVIEW`**

This is a recommendation to begin governed Stable review, not automatic promotion.

## Real-project trigger

Read-only brownfield analysis of `lijust/EREI-App-Google` found load-bearing terminology that affected authentication, tenant ownership, CRM identity and idempotency:

- canonical runtime authentication uses **Subscriber + Workspace**;
- **Client** is a broker-managed CRM entity inside a Workspace, not the authenticated principal;
- legacy activity `user_id` currently carries `subscriber_id`;
- `09_User_Config` is legacy storage vocabulary rather than proof of a separate canonical User identity;
- `request_id` is API/mutation/idempotency identity;
- `requirement_id` is a Client-owned real-estate criteria entity;
- `Project` and `Developer` are overloaded between real-estate and software contexts.

This is exactly the candidate skill's intended trigger class: conflicting/overloaded terms with auth, ownership, data and workflow consequences.

## Bounded resolution

App PR: `lijust/EREI-App-Google#132`  
Merged App commit: `5687578a2a77de9d7284c64e3c720f610b7746cb`

The trial added one canonical lazy artifact:

`.erei/DOMAIN_LANGUAGE.md`

and integrated it into the App `AGENTS.md` read-first order.

It explicitly **did not** rename persisted fields, sheet names, APIs, schema, or runtime identifiers.

Canonical distinctions include:

```text
Subscriber  != Client
Actor       != Client
request_id  != requirement_id
Workspace   != Client
real-estate Project   != software project
real-estate Developer != software developer
```

## Authoritative verification

App self-hosted run: `34670350809` — **SUCCESS**

```text
DOMAIN_LANGUAGE_CANONICAL_TERMS=PASS
DOMAIN_LANGUAGE_CODE_ALIGNMENT=PASS
APP_SRC_DIFF=NONE
PINNED_TASK_LEARNING_BINDING=PASS
PROSPECTIVE_TASK_EVENT_DELTA=1
```

The gate verified the glossary against current `AuthService`, `CRMService`, and Core vocabulary, not only against prose.

The trial was then closed through the project's exact pinned Task Learning tool. The prospective state remained:

`LEARNING_HEALTHY`

## Governance correction discovered during trial

The trial also detected that PRs #129–#131 had been merged before prospective Task Learning closure was recorded.

The correction preserved learning semantics:

- no fake/backdated prospective events were created;
- official Retrospective Task Learning V2 tooling imported three historical occurrences;
- six PR/CI provenance records were frozen;
- the workflow proved prospective learning state/projections remained byte-identical during retrospective import.

Retrospective import run: `34670246613` — **SUCCESS**

This is supporting governance evidence, not a reason to inflate the domain-language capability's scope.

## Why the evidence is promotion-grade

The skill triggered on a real ambiguity with security/data consequences, produced the smallest durable project artifact, avoided schema churn, propagated only to project agent context, and was validated against the current code model.

That is a direct real-world demonstration of the candidate's intended safeguards.

## Remaining promotion review questions

Before Stable promotion, reviewers should confirm:

1. `.erei/DOMAIN_LANGUAGE.md` remains lazy/triggered rather than mandatory boilerplate for every project;
2. the skill continues to distinguish documentation drift, implementation defects, requirement change and unresolved domain decisions;
3. broad renaming remains explicitly non-automatic;
4. ADR escalation remains reserved for genuinely hard-to-reverse/non-obvious tradeoffs.

No additional brownfield proof is currently required by this readiness review.

---

# Overall recommendation

| Capability | Readiness | Evidence decision |
| --- | --- | --- |
| `architecture-deepening-analysis` | `READY_FOR_PROMOTION_REVIEW` | Three independently verified domains; reusable seam confirmed without second/third shared-module changes. |
| `behavior-first-testing` | `CONDITIONAL` | Strong public-seam + GREEN evidence, but no authoritative intended RED execution yet. |
| `domain-language-modeling` | `READY_FOR_PROMOTION_REVIEW` | Real auth/CRM/idempotency ambiguity resolved with a bounded canonical artifact and code-alignment verification. |

## Promotion sequencing recommendation

Do **not** promote these capabilities as a bundle merely because they originated in the same pattern-mining exercise.

Recommended sequence:

1. independently review `architecture-deepening-analysis` for Stable promotion;
2. independently review `domain-language-modeling` for Stable promotion;
3. keep `behavior-first-testing` Candidate until a real authoritative RED→GREEN cycle is captured;
4. if Stable promotion is approved, create the normal Stable release/promotion artifacts and run full Framework assurance/evals before moving any project pin.

## Explicit current state

```text
CAPABILITIES.json candidate statuses = UNCHANGED
Stable release                       = UNCHANGED
Stable framework ref                 = 69079018606750312344cb3c648952b9ab72d35b
Project pins                         = UNCHANGED
Candidate→Stable promotion           = NOT AUTHORIZED / NOT PERFORMED
```
