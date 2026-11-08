# Core13 Pilot-B0 — Initial source-bound route inventory CI evidence (8 November 2026)

**Scope:** Frozen B0 source inspection, no execution of legacy Docker J4/J4S and no pilot advisory runtime.

## Verified

- **Formal Package A owner closure:** [Issue #308 owner post-run signoff #6713657840](https://github.com/lijust/EREI-3.2/issues/308#issuecomment-6713657840). Package A issue is CLOSED (completed). Source-bound real owner Docker GET-only [#42418179869](https://github.com/lijust/EREI-3.2/actions/runs/42418179869) PASSED as a **scoped** proof, not Stable.
- **B0 App draft PR:** [#315](https://github.com/lijust/EREI-3.2/pull/315), stacked on App Package A draft #314. **B0 Framework draft PR:** [#175](https://github.com/lijust/EREI-Engineering-Framework/pull/175), stacked on Framework #174.
- **B0 nonroot CI:** [GitHub Actions #42420127831](https://github.com/lijust/EREI-3.2/actions/runs/42420127831), job `128546552781`, **SUCCESS**: decoded log `Ran 15 tests` and `OK`. Source-only CLI route guard also succeeded.
- **Actual source binding:** 14/14 files directly fetched and matched their Git blob SHAs from the A-closed baseline. The manifest itself and mirrored Arabic B0 review are byte-identical across repositories as of file creation; the App adds a small offline source-pin validator and 15 test cases.
- **Source inventory names:** J4 direct Docker; J4S direct Docker attach; D2D2 migration source audit; D3B2A fixed host subprocess; D3B1 offline IPC broker; D3A typed lifecycle; F5B1B root POST; F5B1F owner fixed CREATE; A2 owner GET; selected Git source gate; offline consolidation gate; finite pilot contract gate; owner-only A2 workflow; offline consolidation CI.
- **Key negative finding:** J4 still uses `docker create` / `start --attach` / `rm` via host CLI, and J4S imports J4 and starts Docker via `subprocess.Popen`. The previously tested A2 only supplies protected GET on a private daemon. None is permitted from the future advisory-only pilot. Seven explicitly mutating/executing legacy paths are `DENIED` in the manifest.

## Nonclaims and blockers

The GitHub Compare search from `main` to the A branch returned a capped **300 files**; targeted source inspection does **not** prove whole-repository execution callgraph exhaustiveness or that unknown paths cannot reach the future B1 entrypoint.

`PILOT_B1_SINGLE_ENTRYPOINT=NOT_IMPLEMENTED`; therefore neither pilot reachability nor elimination of hidden execution paths is established. A2 does not grant permission to reuse Root for B, call J4/J4S or run model-generated code. No Docker/root commands or model calls were executed in B0 source CI.

**B0 formality:** `PRE_REVIEW_SOURCE_AND_15_NONROOT_TESTS_PASS`, but **NOT FORMALLY GATE_PASS** until [issue #309](https://github.com/lijust/EREI-3.2/issues/309) is owner-reviewed under the v1 contract. B1 may only begin after B0 signoff, with exactly one non-executing advisory entrypoint. Packages B/C are NOT CLOSED. Current **8/16 formal gates passed**; no new F5B1 letters.

`AI_ACCEPTANCE=BLOCK_AI_ACCEPTANCE`, `stable_ready=false`, `MODEL_EFFECTIVENESS=NOT_ESTABLISHED`.
