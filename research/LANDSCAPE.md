# Landscape Research

**Status:** V0.1  
**Purpose:** Convert external research into durable design inputs for EREI Engineering Framework.

## Research objective

The objective is **not** to select a single framework and clone it.

The objective is to identify:
- Strong reusable patterns.
- Weak or dangerous patterns.
- Mature interoperability standards.
- Proven workflow structures.
- Security and evaluation practices.
- Context-management techniques.
- Licensing/provenance constraints.

Every external pattern is classified as **KEEP**, **ADAPT**, **STUDY**, or **REJECT** before it can influence the framework.

---

## 1. GitHub Spec Kit

### Observed strengths
- Constitution-driven development.
- Explicit `what/why` specification before implementation detail.
- Technical planning separated from requirements.
- Task generation from plan.
- Implementation phase.
- Convergence phase that compares code against spec/plan/tasks.
- Extensions, presets, bundles, project-local overrides.
- Broad coding-agent integration.

### EREI decision
**KEEP + ADAPT**

Keep:
- Constitution.
- Spec → Plan → Tasks → Implement → Converge separation.
- Project-local override concept.
- Bundle/preset concept.

Adapt:
- EREI workflows must support risk-based gates, engineering roles, security veto, and brownfield systems more explicitly.
- EREI must not depend on the Spec Kit runtime.

---

## 2. Agent Skills open format

### Observed strengths
- Portable `SKILL.md` convention.
- Progressive disclosure.
- Optional `references/`, `scripts/`, and `assets/`.
- Skills are reusable procedural capabilities rather than giant global prompts.

### EREI decision
**KEEP**

EREI reusable skills should remain compatible with the open `SKILL.md` model wherever practical.

---

## 3. obra/superpowers

### Observed strengths
- Design before implementation.
- Isolated execution/worktree thinking.
- Detailed implementation plans.
- Systematic debugging.
- Verification before completion.
- Evidence over claims.
- Two-stage review:
  1. Spec compliance.
  2. Code quality.
- Skill behavior evaluation.
- Fresh subagent execution/review.

### EREI decision
**KEEP + ADAPT**

Keep:
- Evidence over claims.
- Verification before completion.
- Systematic debugging.
- Independent review.
- Separate compliance review from code-quality review.

Adapt:
- Do not enforce strict TDD for every task.
- Testing/process rigor must scale with risk.

---

## 4. Sentry skills / dotagents

### Observed strengths
- Runtime instructions separated from design intent.
- `SKILL.md` for execution behavior.
- `SPEC.md` for purpose, evidence, evaluation, maintenance, limitations.
- Provenance and source management.
- Manifest/lock/trust concepts for managed agent assets.

### EREI decision
**KEEP + STUDY**

Adopt:
- `SKILL.md + SPEC.md` for substantial skills.
- Explicit provenance and evaluation requirements.

Study before building tooling:
- Manifest and lock formats.
- Installation/sync/trust behavior.

Do not build an EREI package manager until the need is measurable.

---

## 5. BMAD Method

### Observed strengths
- Explicit personas/engineering roles.
- Orchestrated workflows.
- Greenfield and brownfield distinctions.
- Proportional workflow complexity.

### EREI decision
**ADAPT**

Key lesson:
**Agent/Role is not the same thing as Skill.**

Use engineering roles as perspectives/accountabilities; use skills as reusable procedures.

Licensing requires careful verification before any direct reuse.

---

## 6. Agent OS

### Observed strengths
- Discover conventions/standards from an existing codebase.
- Inject only standards relevant to the current task.

### EREI decision
**KEEP + EXTEND**

EREI should implement **context routing**, not context dumping.

Project onboarding should:
1. Inspect codebase.
2. Extract standards.
3. Classify standards.
4. Build an index.
5. Load only task-relevant standards.

---

## 7. SteveVitali/agent-skills

### Observed strengths
- Durable state over conversational memory.
- External verification over self-assessment.
- Independent/fresh review context.
- Deterministic automation before LLM reasoning.
- Proportional rigor.

### EREI decision
**PROMOTE TO CONSTITUTION CANDIDATES**

These principles are strong enough to be framework-level policies.

---

## 8. Trail of Bits skills

### Observed strengths
- Prescriptiveness increases with risk.
- Security workflows reject dangerous shortcuts/rationalizations.
- Strong evidence discipline.

### EREI decision
**CONCEPTUAL ADOPTION ONLY UNTIL LICENSE REVIEW**

Use the concepts:
- High-risk procedures must be stricter.
- Security skills should explicitly list rationalizations that must be rejected.
- Security may block release.

Avoid direct content reuse until license obligations are deliberately handled.

---

## 9. OpenAI plugin architecture

### Observed strengths
- Separates skills, agents, commands, hooks, tools/MCP, assets, and plugins.
- A plugin can bundle capabilities without conflating them.

### EREI decision
**KEEP AS ARCHITECTURAL SEPARATION**

This reinforces:
`Agent ≠ Skill ≠ Workflow ≠ Tool ≠ Hook ≠ Adapter`

---

## 10. AGENTS.md ecosystem

### Observed strengths
- Durable project-local instructions.
- Hierarchical/scoped context.
- Instructions live with the code.

### EREI decision
**KEEP**

Project repository is the source of truth for project-specific context.

ChatGPT/agent runtime instructions should be a small bootstrap pointer, not the permanent project knowledge base.

---

## 11. Supabase agent skills

### Observed strengths
- Technology-specific best practices.
- Rules grouped by domain and impact.
- Critical security/performance rules are distinguishable from lower-impact guidance.

### EREI decision
**KEEP AS OVERLAY MODEL**

Technology overlays should be modular and impact-aware.

Example:
`google-apps-script/` should be decomposed into concurrency, quotas, caching, deployment, security, Sheets access, etc., rather than one giant "Apps Script Expert" prompt.

---

# Central conclusion

The strongest framework architecture is a **hybrid layered system**:

1. Constitution / Policies
2. Agents / Engineering Roles
3. Skills / Reusable Procedures
4. Workflows / Orchestration
5. Project Context / Standards
6. Durable Evidence / Artifacts
7. Runtime Adapters / Distribution

This replaces the earlier flat model where Frontend, Backend, Security, Code Review, and Debugging were all treated as the same type of "skill".
