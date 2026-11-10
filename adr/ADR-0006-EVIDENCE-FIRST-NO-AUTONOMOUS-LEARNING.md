# ADR-0006 — Evidence-first engineering; no autonomous learning

**Status:** Accepted owner-directed scope decision  
**Decision date:** 2026-11-10  
**Scope:** EREI Engineering Framework and future opt-in project integrations  
**Risk:** L2 — product scope / documentation and governance; no immediate runtime migration

## Context and objective

The Framework exists to help engineers diagnose and repair real software defects, verify the result, and retain auditable evidence. Its usefulness must be established by independently checked results, not the number of safety components or learning events.

The previous terminology **Task Learning**, **Learning Review** and **Knowledge Promotion** can imply that the Framework changes itself. In the current pinned V1, these mechanisms are actually project-local evidence capture, deterministic review signals and *human-approved* Framework version changes. They are not self-training. Keep that distinction rather than deleting working history.

The owner has chosen to **remove autonomous learning and autonomous self-improvement from the Framework product objective and active roadmap**. They are not prerequisites to its success. A future change to this decision requires a new explicit owner decision/ADR with evidence of value; do not schedule speculative learning phases.

## Decision

The target capability is:

> AI-assisted engineering that diagnoses and proposes bounded repairs, permits execution only when separately authorized, verifies outcomes independently, and records evidence, mistakes, experiments and human decisions for future *human-directed* development and releases.

Four operating responsibilities remain:

1. **Diagnose and propose:** cite code revisions, observable symptoms, uncertainty and a small safe correction; do not claim correctness from model confidence.
2. **Controlled execution and verification:** maintain the existing permission, isolation and acceptance boundaries; a test pass proves only the asserted test boundary.
3. **Evidence capture:** retain original source references, model outputs, attempts, test/witness results, hashes, failures, restrictions, and decisions. Avoid unnecessary raw transcripts, credentials, private reasoning and sensitive data.
4. **Human-directed improvement:** use past evidence to prioritize a backlog and design *future versions*, with explicit review, tests, releases and project-pin upgrades.

**Out of scope (not planned):** model weight training/fine-tuning/online RL within Framework; automatic behavioral/prompt/policy changes inferred from task history; self-modifying agents or skills; autonomous promotion of "lessons" to verified truth; automatic repository changes, releases or project pin movements triggered by learning signals; always-on memory injection/RAG as an assumed dependency.

Read-only lookup of archived evidence for a **specific explicitly approved task** is permissible as reference material. It does not imply automatic knowledge injection or a self-learning loop. No autonomous capability is authorized through this exception.

## Treatment of existing V1 contracts

- **Keep:** `.erei/learning/TASK_EVENTS.jsonl` (record of executions), `LEARNING_REVIEWS.jsonl` (documented review decisions), `LEARNING_STATE.json` / `LEARNING_SUMMARY.md` (derived observability), and Framework feedback records. Existing names remain for compatibility and provenance, **not** as evidence of automated model learning.
- **Keep:** deterministic review indicators if already used. They may suggest human attention only; they never initiate an automatic learning or release action.
- **Keep:** existing safety guards, evaluations, permission checks and immutable project Framework pins.
- **Do not:** delete historical records, rewrite signed/hashed witnesses, change schemas, remove CI gates, change pinned Stable refs, or refactor operational code solely to rename "learning".
- **Defer indefinitely:** promotion-loop expansion, automatic knowledge selection/injection, cross-project learning systems and prospective "Learning Effectiveness" work unless separately justified by a new decision. Existing manual Knowledge Promotion/Upgrade workflows remain optional release-governance mechanisms, not active requirements for demonstrating AI utility.

This ADR **clarifies and narrows the product objective** of ADR-0005; it does not falsify or erase ADR-0005's historical accepted capture contract.

## Minimum reusable record

For material experiments or defect investigations, prefer an existing issue/PR plus a short record using `research/EXPERIMENT_RECORD_TEMPLATE.md`. Capture: identity and intent; predeclared acceptance; exact source/model/tool revision; inputs/outputs with source and SHA references; attempts, costs/usage if verified; safety limits; independent test result; human review status; actual outcome; unresolved gaps; and a **specific future release/backlog proposal, if warranted**.

Distinct labels must be maintained: `OBSERVED`, `OPERATOR_REPORTED`, `TESTED`, `HUMAN_REVIEWED`, `HYPOTHESIS`, `NOT_ESTABLISHED`, `BLOCKED`. An experimental failure or a prepared test is not a successful feature.

No separate learning database, ingestion service, training dataset or automation is required to adopt this policy. Reuse GitHub, existing ledgers, Git object IDs, artifact hashes and current experiment reports.

## Decision gates and completion

- **Now:** document this decision in Framework and at the active EREI-3.2 integration, without changing executable behavior.
- **Next measurable priority:** show safe diagnostic/repair usefulness on new source-backed defects with preregistered criteria, a minimal human baseline and independent outcome checking. Do not inflate scope into a new execution platform or learning subsystem.
- **Completion for this ADR:** two repository policy documents link to it; the old V1 behavior and immutable pins remain unchanged; no learning code is deleted or deployed.
- **No implication:** success on documentation or Pilot-C's advisory guard tests does not set `ai_acceptance` or `stable_ready` to true.

## Why not merely rename Task Learning?

The existing Task Learning mechanism already **records** observations and does not self-modify. Rewriting its files and tests would create compatibility risk without serving the objective. We change *purpose, roadmap and usage policy*, while retaining proven audit mechanisms.

## Reversibility

Autonomous learning is **not an assumed future milestone**. Should a future owner explicitly seek it, require a fresh ADR, independent causal benefit evidence and an entirely new authorization/acceptance boundary. Do not silently resurrect it in normal maintenance.
