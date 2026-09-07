# VNext Stable Readiness

The immutable VNext Candidate manifest records the blockers that existed at that Candidate snapshot. It is not rewritten as later evidence arrives.

Current readiness is derived from live machine-readable sources with:

```bash
python tools/stable_readiness.py --repo-root .
```

The report has four gates:

1. **Prospective cycle** — must be `complete` in `learning/PROSPECTIVE_CYCLE_STATUS.json`.
2. **Exact-target runtime evidence** — all published eval cases must pass at `exact_target_runtime`, be bound to exact-target run manifests, and target the selected immutable Framework revision.
3. **Release enforcement** — server enforcement or an independently verified equivalent fallback must satisfy `security/ASSURANCE_ENFORCEMENT.json`.
4. **Final architecture/security approvals** — exact approval refs are intentionally deferred until the first three gates pass and then must bind the final immutable Stable candidate revision.

## Target revision resolution

A GitHub pull-request checkout uses a synthetic merge commit as `git HEAD`. That synthetic commit is not the Framework candidate under review. On pull requests, the readiness tool therefore resolves `pull_request.head.sha` from `GITHUB_EVENT_PATH` and uses that exact commit as the target revision.

On ordinary push runs, the checked-out Git commit is the default target.

For release closure, evidence and release metadata may be committed after the code-under-test has been frozen. Use an explicit immutable target so the evidence carrier commit is not confused with the Framework revision that was actually evaluated:

```bash
python tools/stable_readiness.py --repo-root . --target-ref <40-char-candidate-sha>
```

The target must resolve to a fetched Git commit.

`ready_for_final_approvals=true` means gates 1–3 pass. It does **not** mean Stable.

`stable_ready=true` means all four gates pass. The release manifest must still pass `tools/release_assurance.py`.

For a release branch, use the frozen target revision and make readiness fail closed:

```bash
python tools/stable_readiness.py --repo-root . --target-ref <40-char-candidate-sha> --require-ready-for-final-approvals
python tools/stable_readiness.py --repo-root . --target-ref <40-char-candidate-sha> --require-stable-ready
```
