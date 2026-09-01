# Tutti Runtime Assessment

**Date:** 2026-09-01  
**Repository:** `tutti-os/tutti`  
**License:** Apache-2.0  
**Reuse classification:** concept/integration study; no Tutti source copied into EREI Framework

## Question

Should EREI Engineering Framework implement its own multi-agent shared runtime, or define a provider-neutral Runtime Adapter boundary that can integrate with runtimes such as Tutti?

## Observed Tutti architecture

Current public repository evidence shows:

- Tutti is a local-first desktop monorepo.
- `services/tuttid` owns daemon/product rules and durable local state.
- `packages/agent/host` is a provider-neutral agent lifecycle application core.
- transport/product surfaces translate their own shapes into the Host contract.
- the Host owns session/turn/goal/runtime-operation lifecycle semantics and recovery.
- new lifecycle semantics require Host-level conformance scenarios rather than adapter-side reimplementation.
- Tutti exposes shared workspace concepts across multiple agents and providers.
- connector architecture separates contracts, daemon core, runtime execution and renderer concerns.

This is materially broader than EREI Framework's intended responsibility.

## External integration surface evidence

Tutti also exposes `services/tuttid/api/openapi/tuttid.v1.yaml` as a versioned local daemon API described for:

- Tutti desktop,
- CLI,
- approved local integrations.

Observed characteristics include:

- local daemon server on `127.0.0.1`,
- bearer authentication,
- versioned OpenAPI contract,
- daemon-owned context/authorization,
- `GET /v1/cli/capabilities` for machine-readable capability discovery,
- `POST /v1/cli/commands/{commandID}/invoke` for stable command invocation,
- generated client code derived from the API contract.

This materially improves Tutti's viability as an EREI adapter target because an external/local integration boundary exists. It does **not** yet prove that every EREI-required session/task/approval/mutation operation is available or stable through that boundary.

## Architectural implication for EREI

EREI should not duplicate:

- provider session lifecycle,
- turn dispatch/recovery,
- shared workspace state,
- provider process management,
- multi-agent runtime scheduling,
- provider-specific transport handling.

Those are runtime responsibilities.

EREI should own:

- Constitution and governance,
- risk classification,
- workflow/role/skill selection,
- project context and immutable Framework pinning,
- capability requirements,
- mutation/approval policy passed to a runtime,
- evidence/trace normalization requirements,
- independent verification and release gates.

## Why Tutti is a strong candidate

Tutti's provider-neutral Host boundary and adapter-oriented architecture align with EREI's portability goals. Its shared workspace and multi-agent coordination could provide runtime capabilities that EREI does not need to rebuild.

Potential useful capabilities include:

- multiple provider agents in one workspace,
- shared context/files/tasks,
- session persistence/resume,
- agent handoffs,
- parallel/sequential task execution,
- interactive approval/input states,
- runtime state visibility.

The versioned local daemon API gives us a plausible adapter transport without requiring EREI to import Tutti internals.

## Integration caution

EREI should not couple Framework Core to Tutti-specific DTOs, database state, UI concepts or lifecycle internals.

Before implementing a real Tutti adapter, map the required EREI operations against the supported local daemon API and verify:

- agent session creation/resume/send/cancel,
- workspace selection/isolation,
- approval/input pauses,
- mutation/tool policy enforcement or fail-closed handling,
- trace/evidence export,
- terminal/unknown outcome semantics,
- supported version compatibility.

Internal package APIs remain architecture evidence, not a substitute for the supported integration contract.

## Licensing

The repository root `LICENSE` is Apache License 2.0. Direct reuse would require compliance with that license and preservation of required notices. V1 recommendation is integration/adaptation rather than copying source.

## Decision recommendation

**KEEP TUTTI AS A HIGH-PRIORITY RUNTIME ADAPTER CANDIDATE. DO NOT MAKE IT FRAMEWORK CORE.**

Build the provider-neutral Runtime Adapter Contract first, then prototype Tutti against its versioned local daemon API rather than forking or embedding Tutti's core lifecycle.

## EREI differentiation

Tutti answers primarily:

> Where and how do agents share runtime state and work together?

EREI Framework answers primarily:

> Under which engineering rules, roles, risk gates, evidence requirements and project constraints should that work be performed and accepted?

The systems are complementary when kept behind a clean adapter boundary.
