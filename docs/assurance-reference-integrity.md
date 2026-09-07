# Assurance Reference Integrity — Candidate

## Source feedback

This Candidate improvement responds to project feedback `EFF-20260907T110336Z-C1F01A84` from `lijust/EREI-App-Google` at exact source revision `23a7522544c1a36a36f1b3b81f7eccf002cb49cb`.

The observed failure mode was concrete: project assurance workflows referenced repository-local tests that did not exist, causing false CI failures after the underlying lifecycle controls were already passing.

## Contract

`tools/validate_project_assurance_refs.py` validates repository-local assurance references that can be proven statically without external dependencies:

- literal `tests/**` or `tools/**` script paths executed by Node, Python, Bash/Sh or PowerShell in workflow `run:` commands;
- literal local GitHub Action references using `uses: ./...`.

If a discovered literal input path does not exist in the target revision, the guard fails closed.

Dynamic paths, generated paths and arbitrary shell strings are deliberately not guessed. Ignoring a dynamic reference is not evidence that the reference is valid; it means the static guard has no proof and runtime/other validation remains responsible.

## Candidate boundary

This capability is Candidate only. It does not change the last Stable release, does not move any project Framework pin, and does not imply that all possible workflow references are statically resolvable.

## Adoption

A project adopting this Candidate control should bind the adoption to an exact Framework candidate commit and run the guard against the exact project revision in CI. Adoption evidence must remain separate from Stable Framework identity until normal promotion governance completes.
