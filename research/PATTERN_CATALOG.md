# Pattern Catalog

**Status:** V0.1

Each pattern has:
- Problem
- Pattern
- Why it matters
- EREI decision
- Intended layer

---

## P-001 — Constitution Before Implementation

**Problem:** Agents optimize locally and can violate system-wide engineering principles.

**Pattern:** A small set of governing principles outranks local workflow convenience.

**EREI decision:** KEEP.

**Layer:** Constitution.

---

## P-002 — Role / Skill / Workflow Separation

**Problem:** Flat skill catalogs confuse accountability, procedure, and orchestration.

**Pattern:**
- **Agent/Role** = perspective, accountability, expertise.
- **Skill** = reusable procedure.
- **Workflow** = ordered composition of roles, skills, tools, gates, and artifacts.

**EREI decision:** KEEP. Foundational.

**Layer:** Architecture.

---

## P-003 — Progressive Context Disclosure

**Problem:** Loading all standards and knowledge increases cost, ambiguity, and instruction conflicts.

**Pattern:** Load metadata first, detailed instructions only when relevant, references only when needed.

**EREI decision:** KEEP.

**Layer:** Context system / Skills.

---

## P-004 — Context Routing, Not Context Dumping

**Problem:** Project-specific rules become giant prompts.

**Pattern:** Index project standards and route only relevant context based on task, path, technology, risk, and role.

**EREI decision:** KEEP + EXTEND.

**Layer:** Project context.

---

## P-005 — Durable State Over Conversation State

**Problem:** Long sessions compact, reset, drift, or lose assumptions.

**Pattern:** Anything required for future correctness is written into repository artifacts.

**EREI decision:** KEEP. Constitution candidate.

**Layer:** Governance / Artifacts.

---

## P-006 — Evidence Over Claims

**Problem:** "Done", "fixed", and "tests passed" can be unsupported agent assertions.

**Pattern:** Completion requires observable evidence appropriate to the task.

**EREI decision:** KEEP. Constitution candidate.

**Layer:** QA / Governance.

---

## P-007 — Verification Before Completion

**Problem:** Implementation success and actual system correctness are different.

**Pattern:** Run verification after implementation and before declaring completion.

**EREI decision:** KEEP.

**Layer:** Workflow / QA.

---

## P-008 — Two-Stage Review

**Problem:** Technically elegant code may violate the spec; spec-compliant code may be poor engineering.

**Pattern:**
1. Specification/requirement compliance review.
2. Engineering/code-quality review.

**EREI decision:** KEEP.

**Layer:** Review workflow.

---

## P-009 — Fresh/Independent Review Context

**Problem:** The authoring agent is biased toward its own decisions.

**Pattern:** Critical review should use fresh or explicitly independent context where feasible.

**EREI decision:** KEEP for L2+ changes; recommended for lower risk when cheap.

**Layer:** QA / Review.

---

## P-010 — Risk-Proportional Rigor

**Problem:** One workflow cannot efficiently handle both a typo and an auth migration.

**Pattern:** Process strictness increases with change risk.

**EREI decision:** KEEP.

**Target levels:**
- L0 cosmetic/isolated
- L1 normal/local feature
- L2 cross-layer
- L3 auth/data/security/architecture
- L4 production-critical/destructive

**Layer:** Chief Engineer / Workflow router.

---

## P-011 — Security Veto

**Problem:** Product/UX correctness cannot justify a known critical security failure.

**Pattern:** Critical security findings can block release.

**EREI decision:** KEEP.

**Layer:** Governance / Release.

---

## P-012 — Rationalizations to Reject

**Problem:** Agents may know a rule but bypass it using plausible shortcuts.

**Pattern:** High-risk skills explicitly list common unsafe justifications and require rejection.

**EREI decision:** KEEP for security, migration, production, destructive operations.

**Layer:** High-risk skills.

---

## P-013 — Deterministic Before Probabilistic

**Problem:** LLM reasoning is slower and less reproducible for checks a script/compiler/test can decide.

**Pattern:** Prefer deterministic tool/script checks before LLM judgment.

**EREI decision:** KEEP. Constitution candidate.

**Layer:** Tools / QA.

---

## P-014 — Spec → Plan → Tasks → Implement → Converge

**Problem:** Coding directly from an idea loses requirements and makes progress unverifiable.

**Pattern:** Separate lifecycle artifacts and perform convergence after implementation.

**EREI decision:** KEEP with proportional shortcuts for low-risk work.

**Layer:** Feature workflows.

---

## P-015 — Brownfield Onboarding

**Problem:** Existing systems contain hidden conventions, dependencies, and production constraints.

**Pattern:** Inspect architecture, tests, runtime, data, deployment, standards, and risks before changing code.

**EREI decision:** KEEP as dedicated workflow.

**Layer:** Workflow.

---

## P-016 — Technology Overlay

**Problem:** Generic engineering rules cannot encode every platform's quotas, hazards, and APIs.

**Pattern:** Keep core engineering universal; package technology-specific rules separately.

**EREI decision:** KEEP.

**Examples:**
- Google Apps Script
- Google Sheets
- PostgreSQL
- React
- FastAPI
- Cloud environments

**Layer:** Overlays.

---

## P-017 — Skill Runtime / Skill Specification Separation

**Problem:** Runtime instructions become polluted with maintenance history, evaluation theory, and source provenance.

**Pattern:**
- `SKILL.md`: executable agent instructions.
- `SPEC.md`: intent, scope, constraints, evidence model, eval model, maintenance.
- Optional `SOURCES.md`: provenance/currentness.

**EREI decision:** KEEP for substantial skills.

**Layer:** Skill standard.

---

## P-018 — Skill Evals

**Problem:** A well-written skill may fail to trigger correctly or fail behaviorally.

**Pattern:** Test:
- Should-trigger cases.
- Should-not-trigger cases.
- Behavior/quality cases.
- Regression cases.

**EREI decision:** KEEP.

**Layer:** Evals.

---

## P-019 — Project Local Source of Truth

**Problem:** Chat memory and custom instructions drift from actual code.

**Pattern:** Durable project rules live with project source, e.g. AGENTS.md/project profile/ADR/standards.

**EREI decision:** KEEP.

**Layer:** Project integration.

---

## P-020 — Knowledge Promotion

**Problem:** Project lessons are either lost or copied prematurely into global policy.

**Pattern:** A project pattern is promoted to Framework Core only after:
1. Evidence of repeated usefulness.
2. Project-specific assumptions removed.
3. Security/licensing/provenance reviewed.
4. Eval coverage exists.

**EREI decision:** EREI-NATIVE.

**Layer:** Framework governance.

---

## P-021 — Refactoring Benefit Gate

**Problem:** AI agents over-refactor because cleaner architecture is appealing.

**Pattern:** Significant refactoring is allowed only when measurable benefit exceeds migration/regression risk.

**EREI decision:** KEEP; already approved.

**Layer:** Refactoring workflow.

---

## P-022 — Frontend Is Untrusted

**Problem:** UI restrictions can be bypassed.

**Pattern:** Identity, authorization, tenant scope, validation, and critical business invariants must be revalidated server-side.

**EREI decision:** KEEP; non-negotiable.

**Layer:** Security constitution.

---

## P-023 — Performance Budget as Contract

**Problem:** "Feels fast" is not an engineering target.

**Pattern:** Define operation budgets and measure percentile behavior where practical.

**EREI decision:** KEEP.

**Approved baseline:**
- UI feedback <100 ms
- Simple search <1 s
- Normal search <2 s
- Heavy operation <5 s
- Prefer P95 analysis over best-case latency

**Layer:** Performance / DoD.

---

## P-024 — Stable Is Released Through Evidence

**Problem:** Direct production edits destroy rollback certainty and traceability.

**Pattern:** DEV → Candidate → QA → Stable, with rollback artifact.

**EREI decision:** KEEP.

**Layer:** Release governance.
