# VNext Release Candidate Freeze and Closure

A VNext release target is frozen on a dedicated `release/**` branch. `main` remains available for later Framework development; the release branch is the immutable evidence-closure lane for the selected candidate.

## Selection

1. Merge all release-control tooling before selecting the target.
2. Validate `releases/VNEXT_RELEASE_SCOPE.json` with `python tools/release_scope.py --repo-root .`. The scope must be part of the target tree before freeze; changing scope after freeze requires a new RC.
3. Select an exact `main` commit that has a successful push-side **Framework Assurance Gate**.
4. Create `release/vnext-rcN` from that exact commit.
5. Add `releases/VNEXT_TARGET.json` on the release branch with the exact commit, exact target tree, successful push assurance run ID, current Stable baseline, and `promotion_authorized=false`.
6. Never rewrite the target file. If the target is wrong or behavior must change, abandon that RC and select a new `vnext-rcN+1`.

## Fixed evidence closure

After target selection, the release branch may change only:

- `releases/VNEXT_TARGET.json` — first selection write only;
- `evals/exact-target-runs/*.json` — immutable exact-target run manifests;
- `evals/EXECUTION_EVIDENCE.*.json` — immutable V2 execution-evidence snapshots;
- `security/ASSURANCE_ENFORCEMENT.json` — one post-freeze enforcement truth update;
- `releases/approvals/*.json` — immutable final approval records after pre-approval gates pass;
- `releases/vnext-assurance-v2-stable.json` — one final Stable manifest write.

Any other path, any deletion, or any second write to a closure artifact fails the release-target validator. A required behavior/tool/schema/eval-case change means a new RC.

Validate with:

```bash
python tools/release_target.py --repo-root . --require-target --validate-closure
python tools/stable_readiness.py --repo-root .
```

When `releases/VNEXT_TARGET.json` exists, Stable readiness automatically uses its frozen `framework_ref`; it does not confuse evidence-carrier commits with the code revision under evaluation.

## Exact-target evidence

The frozen `releases/VNEXT_RELEASE_SCOPE.json` defines which behavioral eval suites belong to this release. Stable readiness must require exact-target evidence for **every case in those suites**, without requiring unrelated Candidate eval suites merely because they coexist elsewhere in the Framework tree.

Check out the frozen `framework_ref` in the execution environment and run `evals/exact_target_run.py` against a genuine independent coding-agent/model runtime for the required scope. Commit the produced run manifest and V2 execution-evidence file to the release branch without modifying the frozen Framework code.

This scoping may reduce unrelated evidence burden, but it may never weaken the assurance level, exact target binding, independent-runtime requirement, pass requirement, or immutable evidence rules for in-scope cases.

## Enforcement and approvals

The release branch does not substitute for GitHub server enforcement. `stable_enforcement_satisfied` must still become true through server branch/status-check enforcement or an independently verified equivalent fallback.

Architecture/security approval records remain deferred until the prospective, exact-target, and enforcement gates all pass. Only then may final approval commits and the V2 Stable manifest be added to the closure.
