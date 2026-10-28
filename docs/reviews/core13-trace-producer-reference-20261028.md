# Core13 P1-C — manual trace producer, **synthetic reference execution only**

**Scope**: adds a real in-process read observation hook, plus a manual-only
GitHub Actions workflow to exercise it on a synthetic, isolated task fixture.
This does not execute a real EREI project, authenticate AI knowledge use, or
demonstrate improved engineering outcomes.

## Implementation

- `tools/learning_trace_reference_producer.py` adds
  `KnowledgeReadObserver`: the `read(relative_path, expected_sha256)`
  method performs an actual bounded read beneath `PROJECT/.erei/knowledge/`,
  checks an explicit expected digest, and records the observation only once
  *after* successfully reading bytes. Path traversal, external symlinks, empty
  or oversized files, and incorrect digests fail closed.
- `finish(intervention, selector, trace_ref)` requires the existing
  project Task Learning ledger and complete intervention cohort to match the
  authoritative source. Only the observed task gets a `learning_reuse`
  marker; all other eligible tasks have `capture_complete=false` and
  `exposed=null`. This avoids fabricating negative exposure. It rejects
  previously declared exposure and does not change project tasks or records.
- `produce_reference_fixture(framework_sha)` runs the read hook **before**
  persisting a synthetic Task Learning terminal event. The only task is a
  deterministic isolated reference. It then validates the resulting
  cohort/trace join and outputs the existing PR #120 V1 trace bundle.
- `.github/workflows/core13-learning-trace-export.yml` is
  `workflow_dispatch` **only**, with read-only repository permission, pinned
  actions, an exact HEAD-SHA equality guard, no provider key, no user-selected
  command or project, and upload of only `learning-traces.json`.
  Artifact name matches PR #121 verifier:
  `core13-learning-traces-{run_id}-{run_attempt}`.

The manual workflow runs only on `refs/heads/main`. GitHub will not make
this new workflow usable on default until it is independently reviewed and
merged under the normal governance process. The PR's automated CI tests the
functionality with **synthetic** fixtures and never dispatches the workflow.

## Security and evidence boundaries

A successful run can prove, to the extent the Actions provenance checker can
verify it, that an Actions job executed the **synthetic hook** and produced the
archive bytes. A `learning_reuse` marker from this fixture **does not prove**
that a real project model read knowledge, that the fix was adopted by a user
project, or that a later outcome was improved by the read.

The intervention/implementation/ref values in this reference are **synthetic**.
The producer presently supports only the explicit reference-fixture CLI mode.
There is no general external project caller or real project dispatch.

Flags stay unchanged:
`learning_exposure_independently_verified=false`,
`effectiveness=NOT_ESTABLISHED`,
`causation=NOT_ESTABLISHED`, and `stable_ready=false`.

No push trigger, periodic trigger, PR secret exposure, mutation in the
Framework working tree, arbitrary input path upload, Gemini API invocation,
auto-adoption, project pin change or frozen PR98 scorer modification.

## CI checks

```text
python -m unittest evals.tests.test_learning_trace_reference_producer -v
```

The next phase requires integrating the observer into an explicitly approved
**actual project runtime**, authenticating full trace completeness and exact
loaded code/knowledge bytes, and independently reviewing root-cause
recurrences and a prospectively selected comparable control group.
Instrumenting synthetic fixtures alone is not a valid effectiveness result.

Dependency: stacked draft PR #122 → #121 → #120 → #119 → #118 → #117 → #116 → #115.
