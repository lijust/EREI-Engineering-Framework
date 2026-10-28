# Core13 — Private project trial admission boundary

**Status (2026-10-28): BLOCKED. This file intentionally contains no private
project names, commit IDs, project files, record counts, customer details,
source URLs or secrets.**

## Verified permission and deployment boundary

Read-only checks through an authorized GitHub connector identified existing
project integration configurations that do not activate the Candidate code
under review. No project source was altered, no project Task Learning events
were generated, no candidate adoption or pin modification was performed, and
no production runtime was touched.

These private project checks are **not** independent runtime evidence and
must not be used as Learning Pattern improvement measurements. Detailed
project-specific working observations belong with the owner inside the
private project repository, not in the **public** Framework repository.

The Framework project's own `GITHUB_TOKEN` does not have permission to
clone the selected private project repositories. An attempted Actions
cross-repository source check failed at the GitHub checkout access boundary,
**before source retrieval**. That job was replaced with an offline,
no-network Git-backed contract suite. It does not request any additional
token or project access.

## Implemented reusable read-only preflight

`tools/core13_real_project_trial_preflight.py` checks an **already accessible,
explicitly authorized** local checkout for:

- Exact 40-character project commit and clean Git worktree, so source files
  cannot silently differ from the inspected commit.
- A valid project manifest with exact immutable candidate Framework pin.
- Bounded and time-valid project-owned adoption record.
- Presence of a local knowledge artifact (no content emitted).
- A mandatory independent authorization stop, even if local prerequisites
  all appear to match.

No preflight outcome authorizes a trial; the script is limited to explicit
`BLOCKED` results. The tests use disposable synthetic Git repositories and
do not contact any private project or provider.

```text
python -m unittest evals.tests.test_core13_real_project_trial_preflight -v
```

## Required before real trial

Obtain explicit project-local approval, close the Candidate PR dependency
chain, choose a properly authorized and source-pinned project checkout, and
instrument a real selected task at the genuine knowledge consumption seam.
Capture failed and blocked tasks as well as successful tasks; independently
verify usage and outcomes before making an effectiveness claim.

**Verdict: PRIVATE_PROJECT_RUNTIME_TRIAL_NOT_AUTHORIZED /
NO_PRIVATE_SOURCE_EXPORTED / NO_PROJECT_WRITES /
NO_EFFECTIVENESS_CLAIM / STABLE_BLOCKED.**
