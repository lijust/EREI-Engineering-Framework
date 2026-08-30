# Anti-Patterns

**Status:** V0.1

These are patterns EREI Engineering Framework should actively detect and discourage.

| ID | Anti-pattern | Why rejected | Counter-pattern |
|---|---|---|---|
| A-001 | Flat skill catalog | Confuses roles, procedures, orchestration | Role/Skill/Workflow separation |
| A-002 | Agent persona for every micro-task | Routing complexity, fake specialization | Fewer strong roles + reusable skills |
| A-003 | Giant global prompt | Context pollution and conflicts | Progressive disclosure + context routing |
| A-004 | Load all standards every time | Token waste and ambiguity | Task-relevant standard injection |
| A-005 | Chat memory as source of truth | Compaction/drift/loss | Durable repo artifacts |
| A-006 | Agent self-certifies completion | Confirmation bias | External evidence + verification |
| A-007 | Same agent is sole critical reviewer | Judgment coupling | Independent/fresh review |
| A-008 | LLM used for deterministic checks | Cost and nondeterminism | Script/compiler/test first |
| A-009 | Strict heavy workflow for every change | Bureaucracy | Risk-proportional rigor |
| A-010 | Code immediately from user idea | Requirement loss | Spec/plan discipline |
| A-011 | No post-implementation convergence | Silent requirement drift | Converge against durable artifacts |
| A-012 | Frontend authorization | Trivially bypassable | Server-side authorization |
| A-013 | Hidden button = security | UI state is not a security boundary | Backend permission enforcement |
| A-014 | Tenant ID trusted from client | Cross-tenant risk | Resolve/validate tenant server-side |
| A-015 | Big refactor because design is cleaner | Regression/migration risk | Benefit > migration risk gate |
| A-016 | Production edited directly | Weak rollback/traceability | DEV → Candidate → QA → Stable |
| A-017 | "Tests passed" without recorded evidence | Unverifiable completion | Evidence artifacts |
| A-018 | Security checklist without threat model | Misses trust boundaries/attack paths | Threat-driven analysis |
| A-019 | Community skill trusted automatically | Supply-chain risk | Provenance/license/trust review |
| A-020 | Copy popular repo architecture blindly | Cargo cult engineering | Pattern-level benchmark |
| A-021 | Skill without evals | Unknown trigger/behavior quality | Trigger + behavior evals |
| A-022 | Skill contains all references inline | Poor context efficiency | References + progressive disclosure |
| A-023 | Technology rules in framework core | Pollutes portability | Technology overlays |
| A-024 | Project-specific rule promoted immediately | Core contamination | Evidence-based knowledge promotion |
| A-025 | Dependency added for convenience | Supply chain/maintenance cost | Dependency benefit + security review |
| A-026 | Security/process bypassed because task is urgent | Urgency becomes vulnerability | Explicit rationalizations-to-reject |
| A-027 | Performance optimized before measurement | Wrong bottleneck risk | Measure → diagnose → optimize |
| A-028 | Error hidden/retried indefinitely | Masks systemic failure | Bounded retry + observable error taxonomy |
| A-029 | Architecture decision only in chat | No durable rationale | ADR |
| A-030 | Framework tied to one model/vendor | Lock-in and brittle evolution | Core format + runtime adapters |
