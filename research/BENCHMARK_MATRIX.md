# Benchmark Matrix

**Status:** V0.1

Scoring:
- **5** = excellent / core strength
- **4** = strong
- **3** = useful
- **2** = partial
- **1** = weak/not central
- **?** = requires deeper validation

> Scores measure usefulness of the observed design for EREI, not overall project quality.

| Source | Governance | Roles | Skills | Orchestration | Context Efficiency | Verification/Evals | Security Rigor | Portability | Brownfield | EREI Use |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| GitHub Spec Kit | 5 | 2 | 4 | 5 | 4 | 4 | 3 | 5 | 4 | Core governance patterns |
| Agent Skills format | 2 | 1 | 5 | 2 | 5 | 3 | 2 | 5 | 3 | Native skill format |
| Superpowers | 4 | 4 | 5 | 5 | 4 | 5 | 3 | 5 | 4 | Execution discipline |
| Sentry Skills | 4 | 3 | 5 | 4 | 5 | 5 | 4 | 5 | 4 | Skill lifecycle/evidence |
| Sentry dotagents | 3 | 4 | 5 | 4 | 4 | 4 | 4 | 5 | 4 | Distribution/trust model |
| BMAD Method | 4 | 5 | 4 | 5 | 3 | 3 | 3 | 4 | 5 | Role/workflow concepts |
| Agent OS | 3 | 2 | 4 | 3 | 5 | 3 | 2 | 4 | 5 | Context discovery/injection |
| SteveVitali skills | 4 | 4 | 5 | 5 | 5 | 5 | 4 | 4 | 5 | Durable/evidence principles |
| Trail of Bits Skills | 3 | 4 | 5 | 4 | 4 | 5 | 5 | 4 | 4 | Security rigor concepts |
| OpenAI Plugins | 3 | 5 | 5 | 4 | 4 | 4 | 4 | 5 | 4 | Capability separation |
| AGENTS.md | 3 | 1 | 2 | 1 | 5 | 2 | 2 | 5 | 5 | Project-local context |
| Supabase Skills | 3 | 3 | 5 | 3 | 5 | 4 | 5 | 4 | 4 | Technology overlay model |

---

## Best observed approach by problem

| Problem | Best observed direction | EREI decision |
|---|---|---|
| Governing principles | Spec Kit constitution | Adopt + extend with risk/security/data policies |
| Skill portability | Agent Skills | Adopt compatible SKILL.md structure |
| Skill lifecycle | Sentry | Add SPEC/evidence/evals/provenance |
| Engineering roles | BMAD + plugin ecosystems | Separate role from skill |
| Workflow execution | Superpowers + Spec Kit | Compose workflows with checkpoints and convergence |
| Context management | Agent OS + AGENTS.md | Discover, index, route, progressively disclose |
| Verification | Superpowers + Sentry | Evidence-first, independent review, evals |
| Security rigor | Trail of Bits | Risk-proportional strictness + veto/rationalization rejection |
| Technology expertise | Supabase model | Modular project/technology overlays |
| Runtime portability | Agent Skills + plugins | Framework core + adapters |
| Durable state | SteveVitali + repo artifacts | Disk/repo state over chat memory |
| Brownfield onboarding | BMAD + Agent OS | Dedicated workflow, inspect before changing |
| Distribution | dotagents/plugins | Study existing mechanisms before building new tooling |

---

## Gaps not sufficiently solved by one external source

EREI should build stronger native solutions for:

1. Cross-role impact analysis before implementation.
2. Security veto integrated into general release governance.
3. Multi-tenant SaaS isolation as a reusable security pattern.
4. Performance budgets tied to definition of done.
5. Promotion of reusable project lessons into framework core.
6. Evidence taxonomy across code/docs/tests/tools/user confirmation.
7. Refactoring gate: benefit must exceed migration risk.
8. Risk-level-driven workflow selection.
9. Project-to-framework knowledge promotion with provenance.
10. Explicit separation of stable/candidate/release evidence in AI-assisted engineering.
