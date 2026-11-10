# Experiment / engineering evidence record — template

> **Use only for material engineering work.** Reuse an existing Issue/PR when it already captures the facts; do not manufacture an event for an explanation-only conversation. A record is an archive and a future-release planning input, **not a training event or authorization to execute**.

## Identity and declared scope
- Experiment / issue ID:
- Date (UTC):
- Repository and exact commit/ref:
- Owner / implementer / reviewer (different where independent review is claimed):
- Concrete problem and evidence of reproducibility:
- Explicit hypothesis (if any):
- Predeclared success / stop / safety limits:
- Authorized permissions and data-sharing boundary:

## Evidence ledger

| Evidence ID | Category | Exact artifact / commit / file / test | SHA-256 or immutable revision | Provenance and verification |
| --- | --- | --- | --- | --- |
| | SOURCE / INPUT / OUTPUT / TEST / EVENT | | | OBSERVED / OPERATOR_REPORTED / TESTED / HUMAN_REVIEWED |

## Execution and results
- Number of actual attempts, including failures and non-retries:
- Tool / model versions and input configurations:
- Result by acceptance criterion (**PASS / FAIL / BLOCKED / UNVERIFIED**):
- Model response **verbatim reference** (do not confuse with a verified diagnosis):
- Independently verified outcome / actual observed effect:
- Adverse behavior, limitations, missing evidence and deviations:
- Time and resource consumption (**measured / provider-reported / unknown**, not estimated as verified):
- Safety checks performed and unperformed:

## Decision for this experiment
- **Decision:** ACCEPT / REJECT / NO-GO / NEEDS-INDEPENDENT-REVIEW
- **Decision owner and date:**
- **Scope of accepted claim:** (which facts are proven, which remain unknown?)
- **Is the overall product feature accepted?** NO unless separate evidence establishes it.
- **Closure condition met?** yes/no, with concrete evidence.

## Candidate future work (not automatically scheduled)
- Specific improvement and why it may matter:
- User/product impact and supporting evidence:
- Lowest-cost proof needed:
- Risk, constraints, opportunity cost and rollback:
- Priority and explicit owner decision: **BACKLOG / NOT_PLANNED / APPROVED_FOR_SEPARATE_WORK**
- Candidate future release / issue link:
- **No work starts or code changes occur solely because a record exists.**

## Integrity and retention
Never embed API keys, personal secrets, private reasoning, private customer/production data or unapproved source redistribution. Preserve source references and immutable hashes; do not edit historical evidence to match later interpretations. If an interpretation changes, append a dated correction and retain the original.
