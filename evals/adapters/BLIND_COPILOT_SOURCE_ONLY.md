# Blind Copilot CLI adapter — source-only candidate

This adaptation rebases the standalone CLI adapter and its simulated tests from historical PR #42 onto the current Framework after PR #58. It does **not** authorize or run Copilot, install packages, import evidence, move Stable/RC pins, or imply release readiness.

The external adapter request contains only artifact, task input/context, protocol version and **unpredictable per-invocation opaque IDs**. Scorer expectations, case tags and canonical suite/case identities stay in the trusted harness. The adapter itself rejects non-blinded requests and excludes test/eval material from its model context.

**Current catalog:** 16 suites / 75 reference cases; 74 behavioral external cases; one `harness_only` case.

The existing `evals/exact_target_run.py` manifest is V1/digest-only and remains **insufficient for V2 Stable**. Reconstructible V2 evidence, package identity, governed importer, pinned Copilot package integrity, live telemetry probe and target-bound security approval from historical PR #42 are **not included in this slice**; they require separate independent hardening, review and source-only PRs before any live run.

### Verification
`python -m unittest discover -s evals/tests -p 'test_*.py' -v` plus Framework tooling tests and all 75 reference-contract cases, on an exact GitHub SHA.
