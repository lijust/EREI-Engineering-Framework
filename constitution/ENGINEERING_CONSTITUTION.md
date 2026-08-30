# EREI Engineering Constitution

**Status:** Draft V1  
**Authority:** Highest framework policy layer  
**Applies to:** Framework Core, project integrations, roles, skills, workflows, overlays, adapters, and generated engineering artifacts.

## 1. Purpose

The Constitution defines non-negotiable engineering principles. Roles, skills, workflows, project rules, and runtime adapters may specialize behavior, but they may not silently violate this document.

When principles conflict, safety, security, data correctness, and explicit user-approved architecture take precedence over convenience or speed.

## 2. Core Principles

### C-001 — The frontend is untrusted
UI state, hidden controls, disabled inputs, client-supplied identities, tenant identifiers, and role claims are not security boundaries. Critical authorization and invariants must be validated server-side.

### C-002 — Tenant boundaries are hard boundaries
Cross-tenant access, leakage, mutation, inference, or accidental aggregation is release-blocking unless explicitly designed and authorized.

### C-003 — Durable state beats conversational memory
Any fact required for future correctness must live in durable project/framework artifacts, not only in chat history or transient model context.

### C-004 — Evidence beats claims
"Done", "fixed", "safe", "tested", and similar claims require appropriate observable evidence. Self-assessment alone is insufficient for material changes.

### C-005 — Deterministic verification precedes probabilistic judgment
When a compiler, test, schema validator, static analysis rule, benchmark, script, or direct runtime check can decide a question reliably, use it before relying on model judgment.

### C-006 — Security correctness beats convenience
Known critical security weaknesses cannot be accepted merely to preserve UX, schedule, compatibility, or implementation simplicity.

### C-007 — Data correctness beats apparent success
A successful response or UI outcome does not justify corrupted, overwritten, duplicated, mis-scoped, or unverifiable data.

### C-008 — Measure before optimizing
Performance work begins with evidence. Optimize the measured bottleneck, then benchmark the result and check regression risk.

### C-009 — Complexity requires justification
Prefer the simplest architecture that satisfies current requirements and known constraints. New abstractions, frameworks, dependencies, services, agents, and workflows require a measurable purpose.

### C-010 — Refactor only when measurable benefit exceeds migration risk
Large structural refactors require a defined benefit and explicit assessment of regression, migration, compatibility, and rollback risk.

### C-011 — Critical operations must be observable
Security-sensitive, data-sensitive, production-critical, and high-latency operations require sufficient logging/telemetry to diagnose failures without exposing secrets or sensitive data.

### C-012 — Architectural decisions must be durable and explainable
Material architecture, security, data, and release decisions must be recorded in durable artifacts such as ADRs, specs, threat models, or runbooks.

### C-013 — Rigor increases with risk
A typo and an authorization migration must not pay the same process cost. Workflow strictness, review independence, testing depth, approval gates, and evidence requirements scale with risk.

### C-014 — Stable is changed through controlled release
The default release path is DEV → Candidate → QA → Stable. Production-impacting changes require verification evidence and rollback strategy. Direct Stable edits are exceptional, auditable emergency actions only.

### C-015 — Framework Core remains project-neutral
Project-specific assumptions, business rules, technologies, and temporary workarounds must not silently become universal framework policy. Reusable lessons require a promotion process.

### C-016 — Project repositories are project truth
Project-specific architecture, standards, business rules, risks, ADRs, and runtime state belong with the project repository. Chat custom instructions should remain a lightweight bootstrap layer.

### C-017 — Independent review for material changes
For material changes, critical judgment should be separated from authoring context when practical. Requirement compliance and engineering quality are distinct review questions.

### C-018 — Dependencies are liabilities until justified
New dependencies require a clear benefit, maintenance assessment, provenance/license check, security consideration, and compatibility rationale appropriate to risk.

### C-019 — External knowledge requires provenance
Imported code, templates, prompts, rules, and significant external patterns require source/provenance awareness. Direct reuse must respect licensing and attribution obligations.

### C-020 — No silent uncertainty escalation
Inferred assumptions must not be presented as confirmed facts. Material evidence should distinguish confirmed, inferred, and unknown states.

## 3. Approved Baseline Performance Contract

Unless a project explicitly defines a stricter or justified alternative budget:

- UI feedback: **< 100 ms**
- Simple search: **< 1 s**
- Normal search: **< 2 s**
- Heavy operation: **< 5 s**

Prefer percentile behavior, especially P95, over best-case latency.

## 4. Governance

### Amendment rule
Changing this Constitution is an architectural governance action. It requires explicit approval and a durable rationale.

### Lower-layer conflict rule
If a role, skill, workflow, overlay, adapter, project instruction, or generated artifact conflicts with the Constitution, the conflict must be surfaced rather than silently resolved in favor of the lower layer.

### Security veto
A critical security finding may block release until resolved, explicitly mitigated, or consciously accepted by an authorized decision-maker with durable documentation.

### Data veto
A credible risk of material data corruption, destructive overwrite, or cross-tenant mutation may block release under the same rule.

## 5. Completion Principle

Writing code is not completion. Completion means that the applicable requirement, architecture, security, data, testing, performance, observability, review, evidence, convergence, and rollback conditions have been satisfied or explicitly dispositioned.