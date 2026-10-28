# Core13 — real-project source preflight (read-only, blocked)

**Checked:** 2026-10-28 UTC. **No project files modified, no project task
executed, no AI/provider called, no candidate adoption or pin upgrade.**

This is an audit of **real, immutable GitHub source snapshots**, not proof of a
real runtime intervention. It is deliberately separate from the synthetic
results of PR #123.

## Pinned real-project sources

| Source | EREI-App-Google | EREI-3.2 |
| --- | --- | --- |
| GitHub repository | `lijust/EREI-App-Google` | `lijust/EREI-3.2` |
| inspected `main` commit | `6d32e7a14a4324dbdea228f695d6b75e0b8bd246` | `87d730ddc3547f863de2a6895e91f9b83e9c6e72` |
| `.erei/framework.json` pin type | `commit` | `commit` |
| pinned Framework commit | `69079018606750312344cb3c648952b9ab72d35b` | `69079018606750312344cb3c648952b9ab72d35b` |
| `.erei/CANDIDATE_CAPABILITIES.json` | **absent** in exact Git tree | **absent** in exact Git tree |
| `.erei/knowledge/` | **no files in exact Git tree** | **no files in exact Git tree** |
| `.erei/learning/events/` V2 immutable files | **none in Git tree** | **none in Git tree** |
| `TASK_EVENTS.jsonl` present | yes | yes |
| total task-event JSONL rows | **155** | **2** |
| schema V1 / V2 rows | **120 / 35** | **2 / 0** |
| material event rows | **155** | **2** |
| last event timestamp in ledger | **2026-10-12T14:50:13Z** | **2026-10-15T18:17:24Z** |
| declared local epoch | `EPOCH-024` | `EPOCH-001` |
| current epoch tasks in `LEARNING_STATE.json` | **0** | **2** |

The `EREI-App-Google` ledger contains **101 verified successes, 47
successes with deferred verification, 3 blocked and 4 failed**. These are
historical **project events**, not trials of Core13 PR #123. The 35 V2 schema
rows have occurrence IDs in the JSONL projection, but the inspected Git tree
contains **no canonical `.erei/learning/events/` files**; do not represent
them as independently authenticated prospective captures.

Repository source references (immutable commit views):

- `https://github.com/lijust/EREI-App-Google/blob/6d32e7a14a4324dbdea228f695d6b75e0b8bd246/.erei/framework.json`
- `https://github.com/lijust/EREI-App-Google/blob/6d32e7a14a4324dbdea228f695d6b75e0b8bd246/.erei/learning/LEARNING_STATE.json`
- `https://github.com/lijust/EREI-App-Google/blob/6d32e7a14a4324dbdea228f695d6b75e0b8bd246/.erei/learning/TASK_EVENTS.jsonl`
- `https://github.com/lijust/EREI-3.2/blob/87d730ddc3547f863de2a6895e91f9b83e9c6e72/.erei/framework.json`
- `https://github.com/lijust/EREI-3.2/blob/87d730ddc3547f863de2a6895e91f9b83e9c6e72/.erei/learning/LEARNING_STATE.json`
- `https://github.com/lijust/EREI-3.2/blob/87d730ddc3547f863de2a6895e91f9b83e9c6e72/.erei/learning/TASK_EVENTS.jsonl`

## Go/no-go — both projects are **BLOCKED**

**Reason:** neither project is pinned to the candidate Core13 source chain.
Both are explicitly pinned to the **older Stable commit `69079018...`**.
They have no `.erei/CANDIDATE_CAPABILITIES.json` and no project-owned
approved knowledge file in the inspected immutable snapshot. Existing
`learning_pattern_analysis` is a Candidate in the current Framework
registry; the code being piloted is *not* part of either project's pinned
Stable installation. Therefore PR #123 cannot be applied as if already
authorized.

Do **not** silently change a project pin to PR #123, auto-create an adoption,
interpret historical V1/V2 ledger rows as a trial, pull private/customer data,
or run a provider/model. Even an explicit project candidate adoption would
require normal project governance: exact Framework commit and capability
version, approved limited trial, real task capture and readback, and rollback.
For App Google, the active Production-First/PRD-05 path and MAIN_ONLY_SERIAL
mode in `AGENTS.md` also prevent quietly prioritizing unrelated integrations
over its authorized release-critical work.

## Minimal real-trial path after authorization

1. Land the source-only stacked Candidate PRs through the normal security,
   independent review, CI and dependency sequence **without changing Stable**.
2. Select one suitable project, get a **specific project-local bounded
   Candidate authorization**, and pin exactly the accepted Framework commit.
3. Establish one approved non-sensitive knowledge artifact and a genuine task
   runner call-site that passes `session.read()` bytes to its consumer;
   capture every terminal attempt, including failure/blocked.
4. Verify actual source artifacts, selection precommit, intervention adoption,
   trace capture completeness and independent root-cause outcomes.
5. Only then assess full-denominator intervention results against a comparable
   non-treated cohort. Keep `effectiveness=NOT_ESTABLISHED` otherwise.

This preflight proves the blockers by **current source snapshot**, rather than
pretending that passing 12 isolated unit tests constitutes a real project
runtime trial. Future changes to either mutable `main` must be rechecked
against a new exact immutable commit.

**Decision: REAL_PROJECT_TRIAL_NOT_AUTHORIZED / NO_PROJECT_WRITES /
NO_EFFECTIVENESS_CLAIM / STABLE_BLOCKED.**

## Reproducible offline preflight contract and private GitHub access boundary

The Framework implementation now includes the read-only command:

```text
python -m tools.core13_real_project_trial_preflight \
  --project-root <already-authorized-clean-project-checkout> \
  --project-sha <exact-project-Git-SHA> \
  --framework-sha <exact-candidate-Framework-Git-SHA>
```

The command verifies `git rev-parse HEAD` **and a completely clean Git
working tree**, checks the literal project pin, validates any candidate
adoption shape/time against the existing Framework adoption schema, inspects
the presence (not content) of project-local knowledge artifacts and returns
explicit block reasons. It never grants authorization even when all source
prerequisites match: owner approval, genuine runtime identity, a prospective
task selection and consumer use remain outside this source preflight.

Both `EREI-App-Google` and `EREI-3.2` are **private** repositories. The
normal `GITHUB_TOKEN` of the public Framework repository is not authorized
to clone them. An attempted GitHub Actions cross-repository checkout failed
with `Repository not found` during run `40652665872`, **before any real
project files were fetched or inspected inside that runner**. The job has
been replaced with an offline Git-backed synthetic regression suite:
`.github/workflows/core13-real-project-source-check.yml`. It does not
attempt external private checkouts or request/bypass a private access token.
This inability to clone is an access boundary, not evidence that the
private project snapshot does not exist.

The immutable-revision project facts in the preceding table were read using
an authenticated GitHub connector with project access. They are **not** a
successful independent GitHub Actions source-trial artifact. Do not conflate
these two access models.

**Latest decision:** PRIVATE_PROJECT_RUNTIME_TRIAL_NOT_ATTEMPTED /
CROSS_REPO_ACTIONS_ACCESS_UNAVAILABLE / OFFLINE_CONTRACT_TESTABLE /
STABLE_UNCHANGED.
