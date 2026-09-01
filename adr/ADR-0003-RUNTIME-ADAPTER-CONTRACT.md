# ADR-0003 — Provider-Neutral Runtime Adapter Contract

**Status:** Proposed  
**Date:** 2026-09-01  
**Risk:** L3 — Runtime execution boundary

## Context

EREI Engineering Framework now has stable governance, project integration, evaluation and Framework-upgrade mechanisms, but it intentionally does not yet own a runtime for executing work through Codex, Claude Code, OpenCode, Tutti or other agent systems.

Building a full agent host inside Framework Core would duplicate provider/session lifecycle, process management, shared state, recovery and transport concerns already solved by specialist runtimes. It would also create vendor/runtime lock-in and dramatically expand Framework Core's trusted computing base.

Current Tutti repository architecture reinforces this separation: its provider-neutral Agent Host owns canonical session/turn/goal/runtime-operation lifecycle while transport/product surfaces act as adapters. EREI's concern is different: governance, project context, risk, capability requirements, evidence and release acceptance.

## Decision proposed

Adopt `schemas/RUNTIME_ADAPTER_CONTRACT.md` and `schemas/runtime-adapter.schema.json` as the canonical EREI Runtime Adapter V1 boundary.

### 1. Framework remains runtime-neutral

Framework Core does not own provider session lifecycle or shared workspace implementation.

A concrete runtime may be local, cloud, CLI, API, daemon, desktop workspace or multi-agent host.

### 2. Capability negotiation before execution

Workflows state required runtime capabilities. Adapters declare standardized capabilities and must fail closed when a required capability cannot be guaranteed.

V1 capabilities cover task execution, workspace access, session persistence/resume, cancellation, interactive approval/input, trace export, mutation policy and optional multi-agent/shared-context behavior.

### 3. Governance always outranks runtime capability

A runtime supporting broad write access does not authorize broad writes.

The Framework-selected risk/workflow/mutation/approval policy remains controlling. An adapter cannot downgrade or bypass it.

### 4. Runtime output is evidence, not independent verification

Runtime/provider success claims may be normalized into evidence and trace data, but Framework/project verification remains separate.

### 5. Transport semantics are not hard-coded into Core

The Runtime Adapter Contract is semantic, not CLI-specific.

Concrete adapters may map to CLI, HTTP/RPC, desktop daemon, SDK/native APIs or documented manual integration instructions.

The existing Eval Adapter Protocol remains a separate testing boundary and may wrap the same runtime when useful.

### 6. Adapters have explicit maturity

Adapters are `experimental`, `candidate`, `stable`, or `deprecated`.

Candidate/Stable projects should normally enable only Stable runtime adapters unless an explicit experimental workflow permits otherwise.

### 7. Multi-agent runtimes are optional capability providers

Shared workspace and multi-agent orchestration are not Framework Core requirements.

A runtime such as Tutti may satisfy capabilities such as `shared_context`, `parallel_agents`, `agent_handoff`, `interactive_approval` and `session_persistence` without becoming a Framework dependency.

## Tutti position

Tutti is classified as a strong Runtime Adapter candidate, not Framework Core.

Before implementing a Tutti adapter, verify a supported external integration surface for the capabilities EREI needs. Internal Tutti package APIs demonstrate architecture but are not assumed to be public stable integration contracts.

No Tutti source code is copied by this ADR.

## Consequences

### Benefits

- preserves runtime/provider portability,
- avoids rebuilding a full agent host,
- allows simple single-agent and advanced multi-agent runtimes behind one governance model,
- keeps security/risk/release authority in Framework,
- supports gradual adapter maturity and conformance testing,
- lets project manifests declare runtime preferences without owning runtime internals.

### Costs

- each runtime requires mapping/conformance work,
- capability semantics become maintained Framework architecture,
- some runtime features will not map perfectly to the common vocabulary,
- high-risk workflows may be blocked on runtimes that cannot enforce required boundaries.

## Rejected alternatives

### Build EREI's own complete multi-agent runtime first

Rejected as unnecessary scope and duplication. Framework should first integrate with existing runtimes through a narrow contract.

### Make Tutti mandatory

Rejected because it would couple Framework Core to one runtime/product and weaken portability.

### Use only the Eval Adapter Protocol for real work

Rejected because eval invocation is intentionally minimal and does not model real task mutation, approval, lifecycle, workspace, recovery or release concerns.

### Let every adapter define its own capability names

Rejected because workflows could not reason portably about runtime requirements.

### Trust runtime success as completion

Rejected because it violates evidence/verification separation and permits self-certification.

## Approval gate

This ADR creates a new runtime/trust boundary and standardized capability semantics. Promotion to Framework Stable requires explicit L3 architecture approval.
