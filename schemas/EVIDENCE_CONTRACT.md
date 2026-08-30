# Evidence Contract

**Status:** Draft V1

## Purpose

Material engineering claims must state the basis on which they are considered true.

## Evidence taxonomy

- `CODE_CONFIRMED` — established directly from source code.
- `DOC_CONFIRMED` — established from authoritative documentation.
- `TEST_CONFIRMED` — established by an executed test and observed result.
- `TOOL_CONFIRMED` — established by deterministic tool output.
- `RUNTIME_CONFIRMED` — established by live runtime observation.
- `USER_CONFIRMED` — explicitly established by user statement or approval.
- `INFERRED` — a reasoned conclusion not directly verified.
- `UNKNOWN` — insufficient evidence.

## Rules

1. `INFERRED` must not be silently presented as confirmed.
2. Critical decisions should prefer direct evidence over inference.
3. Evidence must be recent enough for the decision being made.
4. Evidence must identify material scope limitations.
5. `Tests passed` requires the relevant executed check and observed result, not a bare assertion.
6. Verification should be reproducible where practical.
7. Contradictory evidence must be surfaced rather than hidden.

## Minimum evidence record

```text
Claim:
Evidence type:
Source/check:
Observed result:
Scope:
Version/time when material:
Limitations/unknowns:
```

## Default evidence depth by risk

- L0: direct inspection may be sufficient.
- L1: inspection plus targeted verification.
- L2: targeted tests/tool evidence plus review.
- L3: independent evidence across affected security/data boundaries.
- L4: strongest available deterministic/runtime evidence plus explicit approval and rollback validation.

## Conflict handling

When evidence conflicts:
1. Surface the conflict.
2. Rank sources by directness, authority, recency, and scope fit.
3. Identify an additional check that can resolve the disagreement.
4. Preserve `UNKNOWN` when resolution is not justified.