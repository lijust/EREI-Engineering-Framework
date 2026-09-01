# Knowledge Promotion Workflow V1

## Purpose

Convert project-local Framework feedback into reusable Framework improvements without allowing projects or agents to self-modify Framework Core.

## Entry conditions

At least one evidence-backed project feedback event exists under `.erei/feedback/FRAMEWORK_FEEDBACK.jsonl`, or equivalent evidence has been explicitly submitted for Framework review.

A project Learning Review may strengthen, cluster, or originate such feedback, but Task Learning Events by themselves are not automatically promotion candidates.

## Framework-side review surface

Raw feedback and task-learning evidence stay authoritative in the source project. Framework review is tracked in:

- `feedback/REVIEW_QUEUE.md`
- candidate/eval/ADR artifacts created by this workflow as needed.

A project agent must not push directly into Framework Core as part of capture. Framework-side intake/review is a separate action.

## Main flow

1. **Ingest without trusting the suggestion**
   - read the raw feedback event,
   - verify project identity and exact Framework ref,
   - record source project/ref and feedback ID in `feedback/REVIEW_QUEUE.md`,
   - record source Learning Review/epoch/task IDs when they materially support the feedback,
   - resolve cited evidence where accessible,
   - treat the proposed improvement as a hypothesis, not a decision,
   - avoid copying sensitive or unnecessary proprietary project details into Framework review artifacts.

2. **Validate the observation**
   - determine whether the reported behavior actually occurred,
   - separate Framework limitation from project-specific defect, misuse or stale pin behavior,
   - use Learning Review metrics as supporting evidence, not automatic proof of causation,
   - reject/return for evidence if the observation cannot be substantiated.

3. **Classify**
   - feedback type,
   - severity,
   - affected Framework artifact(s),
   - risk level of any proposed Framework change,
   - project-specific vs potentially reusable.

4. **Deduplicate and cluster**
   - compare semantic fingerprint,
   - compare similar observations across projects/versions,
   - use repeated task/epoch evidence to measure recurrence where available,
   - retain independent occurrence evidence rather than deleting it,
   - create a cluster/pattern only when the similarity is real.

5. **Generalize carefully**
   - remove project-specific names, IDs, proprietary details and assumptions,
   - identify the reusable engineering principle/procedure,
   - preserve negative learning when a tempting approach should be explicitly rejected.

6. **Check whether Framework change is justified**
   - repeated occurrence is strong evidence but not mandatory for critical security/correctness gaps,
   - verify that a Framework change is better than a project-local rule,
   - apply complexity and maintenance-cost gate,
   - avoid adding a skill/workflow/role when a small clarification is enough.

7. **Create Framework candidate**
   - select exact target artifact(s),
   - write spec/pattern/contract change,
   - add or update evals reproducing the original failure/lesson,
   - add deterministic tests where applicable,
   - record provenance and source feedback IDs/Learning Review evidence.

8. **Risk and approval**
   - route candidate through normal Framework risk classification,
   - L3/L4 architecture/security/data/trust changes require explicit approval,
   - no feedback volume or confidence bypasses approval rules.

9. **Verify independently**
   - run applicable Framework tests/evals,
   - confirm original feedback case is addressed,
   - run regression against existing Framework behavior,
   - check for unwanted process complexity.

10. **Promote or reject**
    - promote only through normal Candidate → Stable release flow,
    - update `feedback/REVIEW_QUEUE.md` with final review state/candidate or Stable ref,
    - record promoted Framework version/ref and feedback IDs,
    - if rejected, preserve the reason; do not erase the raw project observation.

11. **Measure after promotion**
    - future project Task Learning epochs provide before/after evidence,
    - compare normalized workflow/risk/task mix before claiming the Framework change improved outcomes,
    - if the promoted change does not improve or creates new friction, capture new feedback rather than defending the old decision.

12. **Project adoption is separate**
    - existing projects stay on their pinned Stable Framework revision,
    - a promoted Framework improvement reaches a project only through Framework Upgrade Workflow.

## Promotion thresholds

### Critical correctness/security gap

One well-proven occurrence may justify immediate candidate work.

### Generic workflow/skill improvement

Prefer repeated evidence, multiple project occurrences, repeated Learning Review evidence, or a strong general engineering invariant.

### Process-friction improvement

Require measurable/repeated burden before expanding Framework Core.

### Project-specific convention

Keep project-local unless abstraction removes the project assumption and independent evidence supports broader value.

## Deduplication semantics

A fingerprint is a grouping aid, not an identity replacement.

- Never discard independent occurrences solely because fingerprints match.
- Similar text with different root causes must not be merged blindly.
- Cross-project recurrence increases generalizability confidence.
- A new Framework version may change whether two observations are meaningfully equivalent.

## Negative learning

When evidence shows a recurring unsafe or ineffective rationalization, promotion may update:

- anti-pattern catalog,
- workflow rejection rules,
- security guidance,
- verification criteria,
- skill evals.

Negative learning must remain specific enough to reject the bad behavior without banning legitimate alternatives.

## Output

One of:

- `PROJECT_LOCAL` — valid observation but not Framework material,
- `NEEDS_EVIDENCE` — insufficient proof,
- `DUPLICATE_CLUSTERED` — grouped with existing feedback while preserving occurrence,
- `FRAMEWORK_CANDIDATE` — candidate change/evals created,
- `PROMOTED` — accepted into a Stable Framework release,
- `REJECTED` — reviewed and intentionally not promoted.

## Invariants

- Raw project feedback/task-learning evidence is never treated as approved Framework truth.
- Framework never rewrites itself merely because an agent emitted a suggestion or a learning trigger fired.
- Every promoted change has evidence and verification.
- Project pins do not move automatically after promotion.
- Sensitive/project-proprietary details and private reasoning are excluded before generic promotion.
