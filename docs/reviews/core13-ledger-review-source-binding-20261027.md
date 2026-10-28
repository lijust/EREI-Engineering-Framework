# Core13 P1-A — source-bound Task Learning review preview

**Scope: read-only experimental integration; dependent on draft PR #116 and PR #115.**
No Gemini calls, project writes, real execution, Stable activation, benchmark
change, independent admission, or automatic review closure.

## What this changes

The PR #116 pilot accepts `trusted_context` from its caller. That allows
synthetic tests but does not prove who established the context. This next
limited slice integrates the **existing Task Learning V2 source of truth** for
the **learning-review** domain only:

```text
Existing immutable Task Learning occurrences / reviews
      → task_learning.authoritative_snapshot(project)
      → existing derive_state / _trigger policy
      → one derived review level + ledger generation digest
      → learning_proposal_runtime.evaluate_proposal(model proposal, derived state, derived context)
      → read-only state preview or explicit denial
      → final same-ledger-generation check
```

Entry point:

```python
from tools.learning_proposal_sources import evaluate_review_from_ledger

preview = evaluate_review_from_ledger(model_proposal, project_root)
```

The caller does **not** supply `trusted_context`, `initial_state`,
`authorized_review_status`, computed metrics, or trigger reasons. Those
come exclusively from the existing source-ledger reader. The model provides
only a proposal under the previously reviewed typed action contract.

- The existing reader validates occurrence fingerprints, review membership,
  review event digests, and trigger consistency. No second review-policy
  calculation is introduced.
- Only `IMMEDIATE_REVIEW`, `REVIEW_DUE` and `REVIEW_RECOMMENDED` may
  authorize a matching review action. Healthy/watch/insufficient ledgers
  cannot acquire a fabricated review trigger.
- The output identifies `epoch_id`, effective trigger, counts, and the
  generation SHA-256 so the preview can be tied to a local observation.
- Any inconsistent ledger or changed generation denies the preview; paths
  and raw evidence are not included in denial messages.
- Existing model `claimed_state` is diagnostic only; original model
  scores and the PR98 frozen scorer remain unchanged.
- Read-only operations do not call `capture`, `close_review`,
  `require_active`, any provider API, or a project writer.

## Evidence and limitations

Synthetic tests exercise source-derived triggers, forged review status,
model-supplied context injection, unrelated actions, fingerprint corruption,
mid-preview ledger change, invalid project, and no-trigger behavior.

This is **not** a cryptographic authentication of the local project directory,
Git ancestry, remote receipts, or independent permission checking. The caller
chooses the local directory. SHA-256 of the local ledger detects ordinary
local changes, not a malicious actor replacing a complete internally
consistent history or files changed after the preview returns. Never use the
preview as an execution token or an approval to close a review. Production
access controls and remote evidence attestation remain separate tasks.

```text
python -m unittest evals.tests.test_learning_proposal_sources -v
```

## Next isolated slices

1. Bind capability decisions to the existing `resolve_target` and verified
   framework/project commit identities, without introducing an alternative
   activation policy or permitting real dispatch.
2. Bind feedback and improvement candidates to review records and
   existing Learning Development Output evidence. Do not fabricate a finding.
3. Establish independently verified execution outcomes, holdout cohort
   selection, and prospectively measured intervention exposure using the
   existing `tools/learning_effectiveness.py` contract.

**Exit criterion for this PR:** test + assurance CI green, exact-head
independent code review, and no weakening of source governance or frozen
evaluation metrics. This source-only stage does not establish Stable readiness.
