# VNext Stable Readiness

The immutable VNext Candidate manifest records the blockers that existed at that Candidate snapshot. It is not rewritten as later evidence arrives.

Current readiness is derived from live machine-readable sources with:

```bash
python tools/stable_readiness.py --repo-root .
```

The report has four gates:

1. **Prospective cycle** — must be `complete` in `learning/PROSPECTIVE_CYCLE_STATUS.json`.
2. **Exact-target runtime evidence** — all published eval cases must pass at `exact_target_runtime`, be bound to exact-target run manifests, and target the current immutable Framework revision.
3. **Release enforcement** — server enforcement or an independently verified equivalent fallback must satisfy `security/ASSURANCE_ENFORCEMENT.json`.
4. **Final architecture/security approvals** — exact approval refs are intentionally deferred until the first three gates pass and then must bind the final immutable Stable candidate revision.

`ready_for_final_approvals=true` means gates 1–3 pass. It does **not** mean Stable.

`stable_ready=true` means all four gates pass. The release manifest must still pass `tools/release_assurance.py`.

For a release branch, the same command can be made fail-closed with:

```bash
python tools/stable_readiness.py --repo-root . --require-ready-for-final-approvals
python tools/stable_readiness.py --repo-root . --require-stable-ready
```
