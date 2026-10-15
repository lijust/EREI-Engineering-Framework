# Task Learning V2 Promotion Readiness — 2026-10-15

**Status:** Evidence review only; no Stable promotion and no project pin movement.

## What changed since the September Candidate manifest

The September V2 Candidate listed a missing full prospective learning cycle as a Stable blocker.

That blocker is now **closed by evidence**:

```text
capture
→ Learning Review
→ Framework Feedback
→ Framework Candidate
→ project adoption
→ measured downstream outcome
```

The reference-integrity cycle completed this path and its measured downstream outcome was recorded in:
- `learning/PROSPECTIVE_CYCLE_STATUS.json`
- `feedback/REVIEW_QUEUE.md`

Therefore the old statement that no genuine prospective cycle has completed is stale and must not remain an active blocker.

## Additional brownfield evidence since September

EREI-App-Google accumulated 155 prospective events by EPOCH-023.

The EPOCH-023 review identified:
- heavy iteration/catch density that must not be mislabeled as execution accuracy;
- mixed V1/V2 evidence comparability limits;
- two genuine verification escapes;
- exact execution-environment conformance as a reusable extension to the conformance ladder;
- exclusive-claim concurrency as a reusable missing pattern.

This validates the need for V2 fields such as:
- occurrence identity,
- failure stage,
- failure subject,
- signal assessment,
- task groups/cohorts.

## Promotion blockers that remain

### Closed since the first 2026-10-15 draft

The following previously listed actions are now closed by durable evidence:

- EREI-App-Google EPOCH-023 was closed at event 155 in PR #497 and advanced to EPOCH-024.
- the two reusable October observations were ingested centrally and converted to structured decisions and Learning Development Outputs;
- exact-execution-environment conformance and exclusive-claim analysis now have native Framework Candidate skills/evals;
- semantic-assurance friction is independently corroborated by a second materially different brownfield project, EREI-3.2, through merged PRs #170-#172 and first real post-bootstrap Task Learning/Framework Feedback evidence.

These closures reduce uncertainty around the learning architecture, but they do not authorize Stable promotion.

### 1. Authoritative project adoption

EREI-App-Google still pins Stable `task-learning-review-v1 @ 690790...`.

V2 semantics have been exercised in project-local/Candidate-compatible evidence, but the project has not completed a governed Stable-pin upgrade to a V2 release.

**Status:** OPEN.

### 2. Mixed evidence migration semantics

Current project history contains V1 and V2 events.

V2 can read legacy evidence, but promotion review should verify:
- exact legacy compatibility,
- stage/assessment coverage reporting,
- no false precision when V1 fields are absent.

**Status:** OPEN but materially improved.

### 3. Exact execution/eval assurance

Do not assume all published V2 behavior has authoritative exact-target-runtime evidence merely because unit/eval tests pass.

**Status:** OPEN until release evidence proves required coverage.

### 4. Final immutable Stable approval/release carrier

Candidate capabilities still need final architecture/security/release approval on an immutable target commit and normal Stable release packaging.

**Status:** OPEN.

### 5. Review-debt and effectiveness extensions

The current October candidate line adds:
- Learning Pattern Analysis,
- Learning-to-Development translation,
- bounded review-debt guard,
- causation-safe effectiveness comparison.

Promotion review should decide whether these are bundled with V2 or remain independent Candidates.

**Status:** OPEN DESIGN/PACKAGING DECISION.

## Recommendation

`NOT_READY_FOR_STABLE_PROMOTION_YET`.

The remaining problem is no longer lack of real-project learning volume. The remaining work is:
1. complete CI/assurance on the October learning candidates;
2. run a bounded EPOCH-024 cohort with the corrected metric interpretation;
3. decide whether Learning Pattern Analysis / Learning-to-Development / Review Debt / Effectiveness ship in the same V2 release or as separate Candidates;
4. prepare an immutable V2 release candidate and exact promotion evidence;
5. verify legacy V1/V2 compatibility and assessment-coverage semantics on the frozen release candidate;
6. move a project pin only through Framework Upgrade Workflow after Stable promotion.

## Current recommendation

`NOT_READY_FOR_STABLE_PROMOTION_YET`.

The remaining blockers are now **release/evidence blockers**, not lack-of-learning-volume blockers. Do not reopen closed historical blockers unless new evidence invalidates the closure.

No blocker should be carried forward merely because it appeared in an older Candidate manifest; every blocker must be revalidated against current evidence.
