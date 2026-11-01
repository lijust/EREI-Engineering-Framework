# Core13 J2 — prospective patch and verifier-result identity contract (P0 Candidate)

**Status: Source-only Draft · 1 Nov 2026 · No provider execution · No project activation**

## What this closes
A provider-neutral, bounded, deterministic **identity envelope** around a *prospective* repair task and a candidate diff. `tools/repair_evidence_contract.py` has two pure functions:

- `validate_patch(task, proposal)` checks the immutable `task_id` / `base_sha`, exact allowlisted existing source paths, bounded UTF-8 unified diff, SHA-256 of the actual diff text, and rejects test/CI/.git/.erei/doc edits, renames, binary/mode updates, path traversal and any extra model authority fields.
- `bind_reported_result(task, proposal, result)` checks exact `task/base/patch/oracle/worker-profile` identity against a *caller-reported*, **unattested** verifier receipt and verifies finite check/outcome consistency.

These are strict **preflight syntax/identity contracts**, not real Git-patch semantics, source-tree verification, or an attestation of a worker/verifier. They are deliberately narrow: existing-file-only, ASCII canonical paths, <=8 paths, and <=64 KiB diff. The project-specific patch adapter will later use `git apply --check` on a **disposable project snapshot**, independent of model code. A project may require tighter limits.

## Why this is not a new policy engine

Framework `learning_proposal_runtime.evaluate_proposal()` and `capability_activation.resolve_activation()` already exist in Framework main (merged PR #124). **They remain authoritative for their existing typed policy domains.** Those domains do not yet represent repair-patch execution, and this contract must **not** be described as an authorization substitute.

A successful `validate_patch` returns `PATCH_ENVELOPE_VALIDATED_NOT_AUTHORIZED`, and both `executed=false` / `acceptance_authorized=false`.

A syntactically perfect, yet fake, `pass` from a model or other untrusted source can at most return `RESULT_CLAIM_BOUND_NOT_INDEPENDENTLY_VERIFIED` and `REVIEW_REQUIRED`, **never** `ACCEPTED_FOR_REVIEW`, nor Stable, nor a Task Learning success. Even an entirely wrong patch can pass the envelope check. The future independent verifier must have its **own trusted result channel**, signed or otherwise origin-bound outside candidate control, and a separate deterministic acceptance reducer.

## Contracts

Task:
```json
{
  "contract": "erei-repair-task-v1",
  "task_id": "ERT-20261101-AB12CD34",
  "base_sha": "<40 lowercase hex>",
  "allowed_paths": ["src/example.py"],
  "oracle_sha256": "<64 lowercase hex>",
  "worker_profile_sha256": "<64 lowercase hex>",
  "max_patch_bytes": 65536
}
```

Patch proposal:
```json
{
  "contract": "erei-repair-patch-v1",
  "task_id": "ERT-20261101-AB12CD34",
  "base_sha": "<same base>",
  "diff": "<bounded unified git diff, existing file only>",
  "diff_sha256": "<sha256 of raw UTF-8 diff>",
  "changed_paths": ["src/example.py"]
}
```

Verifier-result **claim** (not attestation):
```json
{
  "contract": "erei-repair-verifier-result-v1",
  "task_id": "<same task>",
  "base_sha": "<same base>",
  "patch_sha256": "<same diff>",
  "oracle_sha256": "<same frozen oracle>",
  "worker_profile_sha256": "<same frozen worker profile>",
  "outcome": "pass",
  "checks": [{"id":"functional","passed":true}],
  "provenance": "caller_reported_unattested"
}
```

## Gate ordering (never infer missing stages)

```text
Task scope / immutable source SHA / sealed oracle ID chosen by project
  -> Model or human patch suggestion (NO EXECUTION)
  -> J2 envelope+identity checks  [THIS PR, source only]
  -> Existing project/Framework activation policy  [NOT YET WIRED]
  -> Project-specific `git apply --check` in disposable snapshot  [J3/J4]
  -> Independently controlled verifier/test authority  [J3/J4]
  -> Trusted result binding + deterministic ACCEPTED_FOR_REVIEW/REJECTED  [FUTURE]
  -> Authenticated, prospective terminal Task Learning event  [J5]
```

## Explicit non-goals and outcome language

- No model-generated code execution on Windows or Docker in this PR.
- No `subprocess`, no files touched, no worker startup, no provider/network calls, no project pin movement.
- No model output can set an authoritative state; no document/CI result may imply `independently_verified=true`.
- No hidden acceptance tests are embedded in the model-facing contract.
- No Sandbox certification. Preserve the existing trusted known-only Docker canary without widening its input domain.
- No learning effectiveness claim; `NOT_ESTABLISHED`, `BLOCK_AI_ACCEPTANCE`, `stable_promotable=false`.

## Verification

```powershell
python -m unittest evals.tests.test_core13_repair_evidence_contract -v
```

24 initial offline tests cover correct envelope without authority, wrong base/task, digest mismatch, forbidden paths, fake claims, incompatible verifier identity, outcome contradictions, and that syntax-valid but functionally wrong source is **not accepted**. **Record actual local/CI results separately; writing tests is not evidence they passed.**

**Next acceptance:** independent review of exact J2 sources, final J1 integration decision for selected #229/#230/#125, then project-owned J3 sealed independent oracle specification. Do not start real AI generation until J2–J5 security and attribution gates pass.
