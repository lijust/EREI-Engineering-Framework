# Assurance Enforcement Boundary

## Status

VNext assurance hardening provides repository-enforced validation gates, but GitHub branch-level enforcement is not currently available for this private repository on the active GitHub plan.

## In-repository enforcement

The Framework carries an always-running `Framework Assurance Gate` for pull requests and for pushes to `main`, `hardening/**`, and `release/**`.

It verifies, at minimum:

- Python compilation for Framework tooling;
- parseability of published JSON contracts;
- all Framework tool unit tests;
- eval harness unit tests;
- validation of every machine-readable eval suite;
- execution of all 44 published eval cases at the explicitly labeled `reference_contract` assurance level;
- a separate report of retained `exact_target_runtime` behavioral evidence coverage;
- structured central feedback decisions;
- the last Stable release manifest;
- the Stable/Candidate capability registry.

The workflow is intentionally not path-filtered. A governance-only change cannot avoid this aggregate gate.

## External enforcement limitation

As observed on 2026-09-07:

- `main` reports `protected=false` and required status-check enforcement is off;
- repository ruleset access returns GitHub HTTP 403 with the platform response: `Upgrade to GitHub Pro or make this repository public to enable this feature.`

Therefore the repository can define and run CI gates, but cannot currently prove that GitHub itself prevents a maintainer from bypassing them when writing/merging to `main`.

This limitation is **not** treated as an application or Framework code defect, and it must not be hidden by describing CI presence as branch protection.

## Release consequence

Until branch/ruleset enforcement becomes available and is enabled, the next assurance release remains `candidate`.

A future V2 Stable declaration also requires all other V2 Stable gates, including complete independent `exact_target_runtime` behavioral evidence and one genuine prospective learning cycle from capture through measured post-adoption outcome.

## Safe fallback while unavailable

Until GitHub enforcement becomes available:

1. use pull requests for Framework changes;
2. require the aggregate Assurance Gate to be green before an approved merge;
3. keep VNext status machine-readably `candidate`;
4. never treat a successful direct push as equivalent to an approved release;
5. record any exceptional bypass explicitly in release evidence rather than silently normalizing it.
