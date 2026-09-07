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
- Candidate ref: `07460985d9984dbcf3833e6142709c0965a05967`
- Review note: The exact reference-integrity Candidate passed Framework CI and has now been adopted by the source project at merge 9f677504bafc3a2a8460f81b3b2088341a51a302 with provenance/reference validation and a terminal prospective adoption event. Promotion remains closed only with respect to this feedback item until a genuine later project task supplies a measured post-adoption outcome.

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

## Intake summary

- Source projects represented: `1`
- Feedback events ingested: `4`
- Clusters created: `3`
- Promoted decisions: `0`
- Source observations mutated by central intake: `0`
