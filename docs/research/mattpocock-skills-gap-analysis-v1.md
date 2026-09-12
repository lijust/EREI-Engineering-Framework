# Matt Pocock Skills → EREI Engineering Framework Gap Analysis V1

**Status:** Candidate research input  
**Date:** 2026-09-12  
**EREI baseline:** `0d3c8a96171a87c9a2d3cc7131af8f2ae354a829`  
**External source:** `mattpocock/skills@3cca18b368ae95cdbdebbff572ccafa662551015`  
**Source license:** MIT  

## Decision

Do **not** install or vendor `mattpocock/skills` as a second engineering operating system.

Use it as an external pattern source. Promote only evidence-backed gaps into EREI-native candidates that preserve the Framework's existing Constitution, risk model, Router, review/verification separation, learning system, immutable pinning, and project-integration contract.

## Why this source is relevant

`mattpocock/skills` is intentionally a small, composable skill library for coding agents. It emphasizes:

- explicit alignment before implementation,
- shared domain vocabulary,
- behavior-first testing,
- systematic debugging,
- deep modules and clean testing seams,
- architecture hotspot/deepening review,
- separate review against standards and specification,
- small implementation slices,
- portable skills rather than a mandatory runtime.

That philosophy is compatible with EREI's reusable Skills layer, but EREI already owns a materially broader engineering operating model.

## Comparison summary

| Area | EREI state | External pattern | Classification | Action |
|---|---|---|---|---|
| Requirement vs engineering review separation | Explicit `requirement-compliance-review` → `engineering-quality-review` → fresh verification | Two-axis Standards vs Spec review | **EREI stronger / equivalent intent** | Keep EREI model; no duplicate skill |
| Systematic debugging | Reproduction → boundary trace → hypotheses → confirmed root cause → regression guard | Similar diagnosis loop with feedback-first discipline | **Strong overlap** | Keep EREI; mine examples only |
| Vertical implementation slices | Present in feature workflow | Strong red→green vertical-slice discipline | **Partial gap** | Candidate `behavior-first-testing` |
| Test seams / public-interface test surface | Not currently explicit as a reusable concept | Explicit seam discipline and interface-as-test-surface | **Material gap** | Candidate `behavior-first-testing` + architecture skill |
| Deep module/interface design | Generic architecture-fit review exists | Deep module, seam, leverage, locality, deletion test | **Material gap** | Candidate `architecture-deepening-analysis` |
| Architecture hotspot survey | No dedicated recurring hotspot/deepening skill | Uses recent-change hotspots before proposing deepening | **Material gap** | Include in architecture candidate |
| Domain vocabulary maintenance | Project/Data/Architecture context exists | Active glossary discipline + contradiction checks | **Partial gap** | Candidate `domain-language-modeling` |
| Project discovery | Strong durable discovery and risk/context bootstrap | Grilling/shared-language flow | **EREI stronger structurally** | Add language-modeling only; do not copy interview framework |
| Spec creation | Feature workflow persists material spec/acceptance | `/to-spec` | **Covered** | No new skill |
| Ticket decomposition | Technical plan requires ordered independently verifiable tasks | `/to-tickets` with blocking edges | **Mostly covered** | Observe; no candidate yet |
| Implementation orchestration | Feature/bug/security workflows + Router + roles | `/implement` | **EREI stronger** | No duplicate |
| Research discipline | No dedicated generic primary-source research skill in stable skills | Dedicated research skill | **Possible gap, lower priority** | Backlog candidate after top three |
| Merge conflict resolution | No dedicated skill | Intent-driven conflict resolution | **Possible gap, lower priority** | Backlog candidate |
| Prototype discipline | No dedicated throwaway-prototype skill | Prototype skill | **Possible gap, lower priority** | Backlog candidate |
| Huge-work planning | Router/workflows exist; no explicit multi-session decision map | `wayfinder` | **Possible gap, context-dependent** | Backlog; do not add without evidence |
| Issue triage | Not core current need | Triage state machine | **Out of scope / low value now** | Reject for current Framework scope |
| Human setup wizard | Project/bootstrap tooling already exists | Interactive wizard | **Overlap / lower value** | Do not promote now |
| Learning / feedback | Task Learning, Learning Review, Framework Feedback, Knowledge Promotion | Much lighter skill library model | **EREI materially stronger** | Preserve EREI system |
| Eval harness | Provider-neutral EREI harness with deterministic evidence | No equivalent operating layer | **EREI materially stronger** | Preserve EREI system |
| Framework versioning/upgrades | Immutable pin + upgrade workflow | Installer/update model | **EREI materially stronger** | Never substitute external installer |

## Findings

### F1 — Review separation is already stronger in EREI

EREI already asks three independent questions:

1. Did we implement the accepted requirement?
2. Is the implementation technically sound?
3. What fresh evidence proves completion?

This is more explicit than importing a combined two-axis code-review skill. Adding another review abstraction would create duplicate governance and ambiguous authority.

**Decision:** reject direct adoption of external `code-review`; retain its smell vocabulary only as optional future review heuristics if evidence shows value.

### F2 — Systematic debugging is already strong

EREI's `systematic-debugging` already requires precise symptom definition, reproduction/equivalent evidence, boundary tracing, bounded hypotheses, one-variable checks, root-cause confirmation, invariant identification, smallest safe fix, regression guard, and fresh verification.

**Decision:** no new debugging skill. External material may inform future eval cases, not architecture.

### F3 — Testing seam discipline is missing

EREI's feature workflow already prefers vertical slices and targeted verification, but it does not define a reusable testing discipline for:

- selecting the observable public test seam,
- rejecting implementation-coupled tests,
- requiring red-before-green when behavior can be expressed as a deterministic test,
- implementing one tracer slice at a time,
- keeping expected values independent from implementation logic,
- escalating when the desired test seam implies a structural architecture decision.

This gap matters because growing contract/static/integration suites can themselves become coupled to implementation details and slow future refactoring.

**Candidate:** `behavior-first-testing`.

### F4 — Deep-module / seam design is a genuine architecture gap

`engineering-quality-review` checks architecture fit, coupling/cohesion, contracts, duplication and testability, but EREI has no dedicated reusable design vocabulary/procedure for deciding:

- what the module interface should expose,
- where the changeable seam should live,
- whether an adapter is justified by real variation,
- whether a module is shallow pass-through indirection,
- whether a design increases locality and caller leverage,
- whether tests and callers use the same stable surface.

This is especially valuable in AI-assisted codebases because agents can rapidly create many small wrappers, adapters and helper layers that increase navigation cost without hiding complexity.

**Candidate:** `architecture-deepening-analysis`.

### F5 — Architecture hotspot review can integrate with Task Learning

A dedicated architecture survey should not refactor the entire repository by taste. It should prioritize evidence-backed hotspots:

- frequently changed paths,
- repeated rework,
- repeated verification failures,
- recurring framework feedback,
- manual workaround/context-gap clusters,
- hard-to-test interfaces.

EREI can improve on the external pattern by using Task Learning and review evidence, not only Git history, to identify where architectural deepening is worth considering.

**Candidate integration:** `architecture-deepening-analysis` consumes both project history and `.erei/learning/` signals when available.

### F6 — Domain language is durable context but not yet actively maintained

EREI persists project profile, architecture, security and data-model truth, but there is no focused skill for maintaining canonical domain terminology and detecting conflicts such as:

- `client` meaning both CRM contact and authenticated user,
- `request` meaning both business requirement and HTTP request,
- `project` meaning both real-estate development and software project,
- a term in the accepted spec disagreeing with code/test naming.

The value is not another large document. The value is a lazily-created glossary used by specs, module names, tests and reviews.

**Candidate:** `domain-language-modeling`, with project-local `.erei/DOMAIN_LANGUAGE.md` created only when useful.

## Candidates to promote now

### C1 — `architecture-deepening-analysis` — Priority P1

Purpose: identify and assess high-value architectural deepening opportunities without turning architecture review into aesthetic refactoring.

Core concepts:

- **module** — implementation hidden behind an interface,
- **interface** — everything callers must know to use the module correctly,
- **seam** — location where behavior may vary without editing callers,
- **adapter** — implementation satisfying a seam,
- **depth** — useful behavior hidden behind a small interface,
- **leverage** — capability gained by callers per interface learned,
- **locality** — change/knowledge/verification concentrated in one place.

Required safeguards:

- evidence-backed hotspot before proposing broad refactor,
- existing ADR/project architecture outrank generic design taste,
- one adapter does not automatically justify an abstraction seam,
- never use line-count ratios as a depth metric,
- structural changes still obey EREI risk/approval gates,
- output recommendations, not automatic refactors.

### C2 — `behavior-first-testing` — Priority P1

Purpose: make implementation feedback fast and behavior-oriented while protecting architecture from test coupling.

Required rules:

- define the observable behavior and test seam before writing the test,
- use an existing/approved seam whenever possible,
- if a new seam materially changes architecture, route through the architecture/risk gate,
- red before green when a deterministic automated test is practical,
- one vertical tracer slice at a time,
- test public behavior, not private implementation details,
- expected result must come from requirement/worked example/independent oracle, not recomputation by the same algorithm,
- targeted checks during implementation; fresh broader verification still required at completion.

### C3 — `domain-language-modeling` — Priority P2

Purpose: establish and maintain a canonical project vocabulary so agents, humans, code, specs and tests refer to the same domain concepts.

Required rules:

- glossary is domain language, not implementation documentation,
- create `.erei/DOMAIN_LANGUAGE.md` lazily,
- challenge overloaded/fuzzy terms,
- cross-check domain claims against durable project truth and code behavior,
- contradictions become explicit decisions rather than silent renames,
- ADR only when the decision is hard to reverse, non-obvious, and based on a real trade-off.

## Deferred candidates

The following are potentially useful but do not currently justify new Framework surface area without project evidence:

- primary-source engineering research,
- intent-based merge-conflict resolution,
- throwaway prototype discipline,
- multi-session wayfinding/decision maps,
- formal issue triage.

They should enter the Framework only through normal Feedback → Learning Review → Knowledge Promotion or a separately approved capability proposal.

## Rejected adoption paths

Do not:

- run the external installer inside EREI projects as part of the Framework,
- duplicate EREI Router/workflows with `/implement`, `/to-spec`, or a second orchestration layer,
- replace `.erei/` context with external `CONTEXT.md` conventions wholesale,
- replace EREI review/verification with a generic code-review command,
- let external skill updates alter a project behind its immutable EREI Framework pin,
- import every external skill because it exists.

## Eval strategy

Each candidate must prove both positive behavior and proportional non-trigger behavior.

### Architecture-deepening eval themes

- repeated-change shallow wrapper cluster → identify deepening candidate,
- one adapter only → do not invent a speculative seam,
- existing ADR intentionally preserves current split → respect ADR unless evidence justifies reopening,
- cosmetic/local change → do not trigger architecture survey,
- repeated Task Learning rework → use as hotspot evidence rather than refactor everything.

### Behavior-first-testing eval themes

- new business rule → select public seam and require red→green vertical slice,
- private helper temptation → reject private-method test,
- expected value recomputes implementation → flag tautological test,
- cross-layer feature → tracer behavior through the approved seam rather than disconnected test batches,
- L0 copy change → avoid heavyweight TDD ceremony.

### Domain-language eval themes

- overloaded `client` term → force disambiguation,
- established canonical term → use it consistently,
- code contradicts asserted domain behavior → surface contradiction,
- implementation detail → keep out of glossary,
- trivial wording issue → do not create glossary bureaucracy.

## Promotion gates

A candidate may become Stable only after:

1. candidate skill text exists,
2. deterministic eval cases exist,
3. harness/schema validation passes,
4. no conflict with Constitution/Router/accepted ADRs,
5. project impact is reviewed,
6. at least one real or fixture-backed use case demonstrates value over current Stable behavior,
7. review/verification confirms no duplicate-governance ambiguity,
8. Stable promotion follows normal Framework governance.

## Recommended implementation order

```text
C1 architecture-deepening-analysis
        +
C2 behavior-first-testing
        ↓
Eval and use on a real brownfield slice
        ↓
Task Learning / feedback evidence
        ↓
C3 domain-language-modeling
        ↓
Re-evaluate deferred external patterns only from evidence
```

## Source material consulted

External repository:

- `README.md`
- `skills/engineering/codebase-design/SKILL.md`
- `skills/engineering/improve-codebase-architecture/SKILL.md`
- `skills/engineering/tdd/SKILL.md`
- `skills/engineering/code-review/SKILL.md`
- `skills/engineering/domain-modeling/SKILL.md`
- `skills/engineering/implement/SKILL.md`

EREI comparison material:

- `README.md`
- `CAPABILITIES.json`
- `skills/engineering-quality-review/SKILL.md`
- `skills/requirement-compliance-review/SKILL.md`
- `skills/systematic-debugging/SKILL.md`
- `skills/project-discovery/SKILL.md`
- `workflows/feature-development/WORKFLOW.md`
- `workflows/review-and-verification/WORKFLOW.md`
- `evals/cases/impact-analysis.eval.json`

## Conclusion

The external repository is high-value as a pattern mine, but direct installation would weaken EREI's single source of engineering authority. The highest-value imports are not its orchestration commands; they are the missing disciplines around **deep module/seam design**, **behavior-first testing through stable seams**, and **active domain-language maintenance**.

Those concepts should enter EREI only as native candidates with EREI risk, evidence, eval, learning and promotion controls.
