# Research Ledger

**Status:** V0.1  
**Rule:** Ideas may be studied broadly. Direct code/template reuse requires deliberate license/provenance review.

| Source | Repository / ecosystem | Research use | License/provenance status | Direct reuse status |
|---|---|---|---|---|
| GitHub Spec Kit | `github/spec-kit` | Constitution, SDD lifecycle, presets/extensions/bundles, convergence | GitHub metadata observed MIT | Candidate only after file-level review |
| Agent Skills | `agentskills/agentskills` ecosystem | Portable SKILL.md, progressive disclosure | Verify exact spec/code license before reuse | Structure compatibility preferred |
| Superpowers | `obra/superpowers` | Execution discipline, reviews, debugging, evals | GitHub metadata observed MIT | Candidate with attribution review |
| Sentry Skills | `getsentry/skills` | SKILL/SPEC separation, skill maintenance | Verify repository/file license | Concept adoption approved |
| Sentry dotagents | `getsentry/dotagents` | Manifest/lock/trust/sync | Verify before reuse | Study before implementation |
| BMAD Method | `bmad-code-org/BMAD-METHOD` | Roles, orchestration, brownfield | GitHub API reported non-standard/NOASSERTION metadata in research pass | Concepts only until license verified |
| Agent OS | `buildermethods/agent-os` | Standards discovery/context injection | Verify current repository license | Concept adoption approved |
| SteveVitali agent-skills | `SteveVitali/agent-skills` | Durable state, independent review, deterministic first, proportional rigor | Verify current repository license | Concept adoption approved |
| Trail of Bits Skills | `trailofbits/skills` | Security rigor, rationalizations-to-reject | Treat as license-sensitive; verify exact current license/terms | No direct content copying by default |
| OpenAI Plugins | `openai/plugins` | Agent/skill/tool/hook/plugin separation | Verify component licenses before reuse | Architectural concepts only |
| AGENTS.md | `agentsmd/agents.md` ecosystem | Project-local hierarchical instructions | Format/ecosystem research | Compatible use encouraged |
| Supabase Agent Skills | `supabase/agent-skills` | Technology overlay and impact classification | Verify exact license | Concepts/structure inspiration |

## Provenance rules

Before any external code, prompt text, template, or script enters EREI:

1. Record original repository.
2. Record exact file/path and commit/tag where practical.
3. Record license.
4. Determine whether reuse is:
   - concept only,
   - adapted,
   - copied with attribution,
   - prohibited.
5. Preserve required notices.
6. Add an eval proving the imported pattern benefits EREI.
7. Prefer independent reimplementation of concepts when licensing or portability is ambiguous.

## Current warning

The research phase intentionally distinguishes **architecture inspiration** from **content reuse**. No external repository should become an undeclared dependency merely because its design was influential.
