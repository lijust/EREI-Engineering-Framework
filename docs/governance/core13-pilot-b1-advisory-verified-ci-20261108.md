# Core13 PILOT-B1 — Single Advisory-only Entrypoint | CI evidence and review packet

**8 November 2026 | Scope: B1 source-bound advisory only | Formal B1 gate: owner post-run review PENDING**

## Owner authorization and why we can proceed

[Owner-approved B0 close + B1 implementation authorization #6713825884](https://github.com/lijust/EREI-3.2/issues/309#issuecomment-6713825884) explicitly accepts the 14-route inventory, 15 passing B0 tests and its limitations. Current formal closed gates **G0–G3, A0–A3, B0 = 9/16**. Package A closed separately; B is not yet closed.

## B1 actual implemented artifact

A **single** read-only CLI: `tools/core13_pilot_b1_advisory_only.py` with **two explicit operations only**:
- `guardrails` → returns the fixed 14-route review, seven known-denied legacy/root execution paths, and policy prohibitions. No Docker APIs, no network, no model, no shell/patch writes.
- `inspect_route` + exact `route_id` from the 14 reviewed IDs → returns source path, reviewed Git blob, static evidence, one policy label, and a fixed advisory action. Inspecting a denied route **does not execute it**.

The CLI rejects unapproved operations (`execute`, `run`, `docker`, `apply_patch`, `model`, `fetch`), unknown route IDs, duplicate JSON keys, extraneous fields such as `code`, `command`, `url`, `patch`, control characters, malformed JSON and requests above **1024 bytes**. It fails with `exit=2` and sanitized DENY, without echoing input data.

**Source boundary:** Before answering, it verifies the fixed B0 contract Git blob `814e7194dc5ebd95557616a68117138ee880da3e` and all **14 original files** against individually pinned blob SHAs. Only standard-library `argparse`, `hashlib`, `json`, `pathlib`, `stat` are imported. There are no imports from legacy J4/J4S, F5/root, socket, Docker, subprocess, network clients or a model runtime.

**Not an AI evaluator:** advisory actions are deterministic policy reports from frozen source evidence; they are not claims about independent model reasoning, patch quality, autonomous developer behavior or task-learning effectiveness.

## Reproducible test evidence

- First run [#42420845722](https://github.com/lijust/EREI-3.2/actions/runs/42420845722) was **FAIL**: B0 **15/15 PASS**, B1 had **one test failure** due to an error-code mismatch. The parser safely denied an `inspect_route` request containing an additional malicious `patch` field, but emitted the generic `B1_UNREVIEWED_ROUTE_DENIED` rather than the explicit `B1_REQUEST_EXTRA_FIELDS_DENIED`. The denial was functional; the classifier was imprecise.
- Corrected B1 parser to check exact allowed JSON keys *before* checking route ID, preserving deny-by-default semantics and no new operations.
- [Final GitHub Actions #42420906980](https://github.com/lijust/EREI-3.2/actions/runs/42420906980), job **128548922605**: **SUCCESS**, logs `Ran 15 tests ... OK` + `Ran 25 tests ... OK` = **40/40 PASS**.
- The 25 B1 tests include real subprocess CLI invocation **of this harmless advisory program only**; no candidate subprocess or Docker is called by the CLI itself. They check actual allowed JSON, all 14 reports, every known denied path, malformed/duplicate JSON, unknown operation/route, oversize, source hash tamper, AST import allowlist and 0 side-effect counters.
- CI runs nonroot, `persist-credentials=false`, pinned source/manifest Git SHA. No root job, no Docker daemon, no model execution.

## Strict limitations and acceptance gate

**B1 technical preview is implemented and verified** as a source-bound advisory-only CLI. **B1 formal GATE_PASS is NOT recorded yet** because an explicit **post-run owner review** is required in [Issue #309](https://github.com/lijust/EREI-3.2/issues/309).

The static import graph of this CLI contains no legacy execution module. However, that **does not eliminate the independent J4/J4S CLI programs** elsewhere in the repository, and does not establish whole-repo runtime isolation or model-code sandbox security. The B0 inventory itself covers only 14 source paths; GitHub compare hit a 300-file cap. **B2 must record the exact local entrypoint-only reachability and rollback evidence**, without deleting historical J4/J4S or inventing a new Root broker.

Next allowed step after B1 owner signoff: B2 scoped source/rollback consolidation; not C and not model execution.

```text
PACKAGE_A=CLOSED_PASS_SCOPED_READONLY
B0=GATE_PASS
B1=SOURCE_AND_CI_PASS_OWNER_SIGNOFF_PENDING
FORMAL_GATES_PASSED=9/16
WHOLE_REPOSITORY_CALL_GRAPH=NOT_ESTABLISHED
MODEL_EFFECTIVENESS=NOT_ESTABLISHED
AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE
stable_ready=false
```
