# Self-Hosted CI Default

The EREI Engineering Framework uses the repository self-hosted GitHub Actions runner as the default execution path for assurance-critical CI.

## Scope

The initial self-hosted conversion covers:

- Framework Assurance Gate;
- Framework Evals;
- Project Bootstrap Tests;
- Runtime Adapter Tests.

GitHub-hosted runners are not required for these gates and are treated as fallback capacity only.

## Current runner contract

The current default runner contract is explicit and fail-closed:

- labels: `self-hosted`, `Windows`, `X64`;
- Python 3.11 and Python 3.12 are preinstalled local toolchain requirements;
- workflows select those interpreters through the Windows Python launcher (`py`);
- assurance-critical jobs do not install Python dynamically through `actions/setup-python`;
- Node.js, npm, Git, and a writable isolated `RUNNER_TEMP` are preflight requirements.

A different self-hosted operating system or architecture requires an explicit workflow/toolchain migration rather than silently matching the current jobs.

## Boundary

- CI remains read-only with respect to repository contents unless a workflow explicitly declares a separately governed mutation path.
- The self-hosted runner must provide an isolated writable `RUNNER_TEMP` boundary.
- The preflight workflow verifies runner identity and the required Git/Python/Node/npm toolchain before broader adoption.
- No Stable identity, release target, approval, App pin, cloud resource, database, or deployment is changed by this CI routing decision.
