# Runtime Adapter Contracts

EREI Engineering Framework is runtime-neutral. Runtime integration is optional.

This area documents the provider-neutral boundary used when an external agent/runtime executes work under EREI governance. Concrete runtime implementations are outside Framework Core by ADR-0004.

## Framework owns

- semantic Runtime Adapter Contract,
- standardized capability vocabulary,
- generic manifest/schema validation,
- generic conformance requirements,
- evidence/verification rules,
- project/runtime selection constraints.

## Framework does not own

- Tutti/Codex/Claude/OpenCode-specific clients,
- provider-specific endpoint discovery or credentials,
- provider/session/process lifecycle,
- provider-specific adapter CI,
- mandatory multi-agent/shared-workspace infrastructure.

A project does not need a Runtime Adapter to use the Framework.

## Rules

- Runtime capability never outranks Constitution, risk, approval, security, data or release rules.
- Missing required capability fails closed.
- Runtime success is evidence input, not independent verification.
- Concrete integrations should be created only when a real project requirement justifies them.
- Concrete integration placement is decided when that requirement exists; no adapter repository is pre-created by default.
- Runtime-specific research may live under `research/` without making that runtime part of Framework Core or the roadmap.

## Canonical artifacts

- `schemas/RUNTIME_ADAPTER_CONTRACT.md`
- `schemas/runtime-adapter.schema.json`
- `tools/validate_runtime_adapter.py`
- `tools/tests/test_validate_runtime_adapter.py`
- `evals/cases/runtime-adapter-contract.eval.json`
- `adr/ADR-0003-RUNTIME-ADAPTER-CONTRACT.md`
- `adr/ADR-0004-CONCRETE-RUNTIME-IMPLEMENTATIONS-OUT-OF-SCOPE.md`
