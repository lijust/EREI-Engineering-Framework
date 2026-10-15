# Framework Feedback Review Queue

`DECISIONS.jsonl` is the machine-readable source of truth for central review decisions. Raw project feedback remains authoritative in each source project's `.erei/feedback/` records.

## FCL-ASSURANCE-REFERENCE-INTEGRITY-001

### EFF-20260907T110336Z-C1F01A84

- Source project: `lijust/EREI-App-Google`
- Source project ref: `23a7522544c1a36a36f1b3b81f7eccf002cb49cb`
- Decision revision: `07460985d9984dbcf3833e6142709c0965a05967`
- Review state: `CANDIDATE`
- Promotion state: `CANDIDATE`
- Decision ID: `EFD-20260907T110819Z-C1F01A84`
- Evidence:
  - `github-pr:84`
  - `github-pr:85`
  - `github-actions:34107892973`
  - `github-actions:34113250077`
  - `app-review:ELR-20260907T110207Z-C1A57F01`
  - `framework-candidate:07460985d9984dbcf3833e6142709c0965a05967`
  - `github-actions:34116080178`
  - `github-actions:34116080202`
  - `github-pr:87`
  - `app-merge:9f677504bafc3a2a8460f81b3b2088341a51a302`
  - `task:ETASK-20260907T112848Z-C1AD0A87`
  - `github-actions:34116935307`
  - `github-pr:88`
  - `app-merge:9adf44b92f1994304ccfad5d3d553f967c1436df`
  - `github-actions:34118146756`
  - `github-pr:89`
  - `app-merge:5a90d0c05934341c79fb79740ae15edff049f167`
  - `github-actions:34118499862`
- Candidate ref: `07460985d9984dbcf3833e6142709c0965a05967`
- Review note: The reference-integrity Candidate completed the full feedback-specific prospective loop. After source adoption at 9f677504bafc3a2a8460f81b3b2088341a51a302, genuine downstream App PR #88 ran Task Learning Lifecycle Gate 34118146756 with Candidate provenance and repository-local reference validation both PASS; independent downstream PR #89 repeated the same PASS in run 34118499862. The measured post-adoption outcome is therefore satisfied for this feedback item. Promotion remains Candidate because Framework-wide Stable gates such as exact-target-runtime eval coverage, release enforcement, and final immutable approvals are separate.

## FCL-CONFORMANCE-LADDER-001

### EFF-20260907T010601Z-41B9942F

- Source project: `lijust/EREI-App-Google`
- Source project ref: `a862f1e24fe25cc43d208b8ef26861977a767617`
- Decision revision: `066270a770adbe8bc2c73622fe7b1bce6f03af08`
- Review state: `CLUSTERED`
- Promotion state: `NOT_PROMOTED`
- Decision ID: `EFD-20260907T011016Z-41B9942F`
- Evidence:
  - `project:.erei/learning/RETROSPECTIVE_SUMMARY.md`
  - `github-pr:41`
  - `github-pr:67`
  - `github-pr:70`
  - `github-pr:8`
- Review note: Static/generic-engine, managed-provider, exact target-runtime and convergence evidence are distinct assurance dimensions. One project provides several independent examples; promotion remains gated by candidate spec/evals and preferably additional project evidence.

## FCL-VERIFICATION-MODEL-001

### EFF-20260907T010601Z-51FBCEB9

- Source project: `lijust/EREI-App-Google`
- Source project ref: `a862f1e24fe25cc43d208b8ef26861977a767617`
- Decision revision: `066270a770adbe8bc2c73622fe7b1bce6f03af08`
- Review state: `CLUSTERED`
- Promotion state: `NOT_PROMOTED`
- Decision ID: `EFD-20260907T011016Z-51FBCEB9`
- Evidence:
  - `project:.erei/learning/RETROSPECTIVE_SUMMARY.md`
  - `github-pr:7`
  - `github-pr:9`
- Review note: Deterministic acceptance rules can themselves be invalidated by runtime evidence. Product failure and acceptance-model failure need separate semantics before this becomes a Framework candidate.

### EFF-20260907T010601Z-88D7BF2F

- Source project: `lijust/EREI-App-Google`
- Source project ref: `a862f1e24fe25cc43d208b8ef26861977a767617`
- Decision revision: `066270a770adbe8bc2c73622fe7b1bce6f03af08`
- Review state: `CLUSTERED`
- Promotion state: `NOT_PROMOTED`
- Decision ID: `EFD-20260907T011016Z-88D7BF2F`
- Evidence:
  - `project:.erei/learning/RETROSPECTIVE_SUMMARY.md`
  - `github-pr:48`
  - `github-pr:49`
  - `github-pr:54`
- Review note: Pre-release deterministic catches should not be conflated with escaped defects in Framework health metrics. Evidence is strong inside one project; cross-project confirmation is still pending.


## FCL-CONFORMANCE-LADDER-001 — October extension

### EFF-20261015T175500Z-7477B0A5

- Source project: `lijust/EREI-App-Google`
- Source project ref: `a11f8911644118bc936037b154be7984f0354ca5`
- Decision revision: `f1f9d4966f085868caa08829800c8955436eb6e4`
- Review state: `CANDIDATE`
- Promotion state: `CANDIDATE`
- Decision ID: `EFD-20261015T181500Z-7477B0A5`
- Candidate: `skills/execution-conformance-ladder/`
- Evidence:
  - `app-review:ELR-20261015T175500Z-23A155E1`
  - `github-pr:480`
  - `task:ETASK-20261011T180543Z-F480A151`
  - `github-pr:497`
  - `app-merge:a11f8911644118bc936037b154be7984f0354ca5`
  - `framework-candidate:f1f9d4966f085868caa08829800c8955436eb6e4`
- Review note: This observation corroborates the existing conformance ladder but adds an exact-execution-environment rung. PowerShell 7/source success cannot silently prove Windows PowerShell 5.1 native process semantics.

## FCL-EXCLUSIVE-CLAIM-001

### EFF-20261015T175500Z-8110D1B7

- Source project: `lijust/EREI-App-Google`
- Source project ref: `a11f8911644118bc936037b154be7984f0354ca5`
- Decision revision: `f1f9d4966f085868caa08829800c8955436eb6e4`
- Review state: `CANDIDATE`
- Promotion state: `CANDIDATE`
- Decision ID: `EFD-20261015T181500Z-8110D1B7`
- Candidate: `skills/exclusive-claim-analysis/`
- Evidence:
  - `app-review:ELR-20261015T175500Z-23A155E1`
  - `github-pr:486`
  - `task:ETASK-20261012T013734Z-A15D0486`
  - `github-pr:497`
  - `app-merge:a11f8911644118bc936037b154be7984f0354ca5`
  - `framework-candidate:f1f9d4966f085868caa08829800c8955436eb6e4`
- Review note: Random/per-attempt uniqueness is not mutual exclusion. The Candidate separates attempt identity from one canonical atomic claim and requires authority/fencing/recovery analysis.

## FCL-SEMANTIC-ASSURANCE-FRICTION-001

### EFF-20261015T180800Z-A29B7B59

- Source project: `lijust/EREI-App-Google`
- Source project ref: `a11f8911644118bc936037b154be7984f0354ca5`
- Decision revision: `f1f9d4966f085868caa08829800c8955436eb6e4`
- Review state: `CANDIDATE`
- Promotion state: `CANDIDATE`
- Decision ID: `EFD-20261015T181500Z-A29B7B59`
- Candidate: `skills/semantic-assurance-design/`
- Evidence:
  - `app-review:ELR-20261015T175500Z-23A155E1`
  - `github-pr:497`
  - `app-merge:a11f8911644118bc936037b154be7984f0354ca5`
  - `framework-candidate:f1f9d4966f085868caa08829800c8955436eb6e4`
- Review note: Repeated pre-runtime catches protected real invariants but recurring stale bindings, allowlists, incidental source-text assertions and process/provenance mechanics show avoidable harness friction. Candidate work must reduce this cost without reducing escape protection.

## Intake summary

- Source projects represented with feedback: `1`
- Feedback events ingested: `7`
- Clusters represented: `5`
- Candidate feedback decisions: `4`
- Promoted decisions: `0`
- Source observations mutated by central intake: `0`
- Second brownfield integration pending/active: `lijust/EREI-3.2` (no synthetic feedback/events)
