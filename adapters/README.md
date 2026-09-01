# Runtime Adapters

Runtime adapters connect EREI Engineering Framework governance to concrete agent execution environments.

They are optional integration layers. Framework Core remains runtime-neutral.

## Rules

- Do not enable an adapter in Candidate/Stable project state unless the adapter itself is Stable, unless an explicit experimental workflow permits otherwise.
- An adapter cannot weaken Constitution/risk/approval/security/release rules.
- Runtime success is evidence input, not independent verification.
- Capability declarations must be verified by conformance tests before Stable promotion.
- Runtime credentials/secrets never belong in adapter manifests, eval fixtures, or project context.
- Multi-agent/shared-context runtimes require explicit isolation/conflict/handoff tests.

## Recommended package

```text
adapters/<adapter-id>/
├── ADAPTER.md
├── adapter.json
├── SOURCES.md
├── evals/
└── implementation/     optional
```

Assessment-only candidates may omit `adapter.json` intentionally so projects cannot enable them accidentally.

## Current state

No Runtime Adapter is Stable yet.

`tutti/ASSESSMENT.md` records Tutti as a strong candidate while its supported external integration surface is evaluated.
