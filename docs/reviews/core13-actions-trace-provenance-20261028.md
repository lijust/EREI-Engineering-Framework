# Core13 P1-C — authenticated GitHub Actions *artifact origin*, not intervention effectiveness

**Status:** source-only, opt-in evidence importer. It is not a deployed trace
producer, an operational execution verifier, or proof that Learning Pattern
reduced failures. Stacked on PR #120 (and #119–#115). No GitHub Actions workflow
is installed or dispatched by this PR.

## Scope

New module: `tools/learning_trace_actions_provenance.py`.

`verify_actions_trace_origin(archive, expected_bundle, identity, token=...)`
checks the original unmodified ZIP against **authenticated GitHub API metadata**
using the existing `tools.github_actions_artifact_provenance._api_json()`.
Unlike passing an arbitrary `trace_ref`, this binds actual ZIP bytes to
GitHub metadata for one controlled workflow identity.

Required identity, supplied by an authorized *caller*, not the AI:

```json
{
  "repository": "lijust/EREI-Engineering-Framework",
  "run_id": 123456,
  "run_attempt": 1,
  "framework_sha": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

The named producer is a **future controlled interface**:
`.github/workflows/core13-learning-trace-export.yml` /
`Core13 Learning Trace Export`. Its verified manual workflow_dispatch run
must be completed/successful on the specified exact 40-character Framework
SHA. The API must return exactly one unexpired artifact named
`core13-learning-traces-{run_id}-{attempt}`, with matching run ID/head SHA,
valid SHA-256 archive digest, and ZIP containing **exactly one** flat
`learning-traces.json`. Archive size and uncompressed member size are bounded,
with invalid ZIP, duplicate JSON keys, nonfinite numbers, unexpected files,
encrypted/symlink members and mismatched bundle content rejected.

`reconcile_actions_trace_evidence(project_root, intervention, selection,
archive, identity, token=...)` authenticates the ZIP and then calls the
existing PR #120 read-only ledger/trace join. Thus metadata authenticity
**does not bypass** failed task inclusion, exact task fingerprints, cohort
membership, or declared-exposure consistency.

## Output claims: deliberately narrow

Successful verification may set:

- `artifact_origin_metadata_verified=true` (GitHub Actions run metadata and
  original archive digest verified against the API).
- `status=GITHUB_ACTIONS_ARTIFACT_ORIGIN_VERIFIED` (origin check alone), or
  `ACTIONS_ORIGIN_VERIFIED_TRACE_CLAIMS_RECONCILED` after the original PR #120
  source-bound trace join.

It **must not** set:

- `trusted_producer_code_verified=true` — workflow source immutability,
  permissions and review are separate.
- `trace_semantics_verified=true` — a successful Actions run can upload
  fabricated or incomplete observations.
- `learning_exposure_independently_verified=true` — a marker does not prove
  a running agent loaded/used a given intervention.
- `effectiveness`, `causation`, `stable_ready` — all remain false / not
  established. This integration never modifies the original model score,
  frozen PR98 cases, or public live evidence.

The **producer workflow does not exist in this source-only slice**.
Therefore there is currently no genuine live artifact eligible for admission.
All offline tests mock GitHub responses; test fixtures are synthetic.

## Regression, audit and next gating stage

```text
python -m unittest evals.tests.test_learning_trace_actions_provenance -v
```

Checks include exact authorized run metadata, workflow name/path/ref, artifact
digest and uniqueness, ZIP file limits, JSON integrity, missing token,
reconciliation with real local synthetic task ledger, and refusal to excuse
omitted failed occurrences. CI makes no provider API requests.

Before this could verify *real* learning exposure, add a separately reviewed,
manual-only, read-only trace-producing workflow with pinned code, no arbitrary
command execution, immutable per-task occurrence/artifact IDs, authentic
runtime observation and explicit incomplete-capture handling. Verify workflow
source and GitHub run/job permissions, and include independent outcome/root
cause adjudication plus a predeclared holdout/control cohort. None of these
steps should silently change a project pin, adopt a candidate, execute Gemini
or promote Stable.

**Exit boundary for this PR:** CI success and independent review of its exact
head; no production use, no standalone learning-quality improvement claim.
