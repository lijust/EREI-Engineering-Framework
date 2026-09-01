# Runtime Adapter Contract V1

**Status:** Stable V1  
**Architecture gate:** ADR-0003 Accepted

## Purpose

Define a provider-neutral boundary between EREI Engineering Framework governance and an external execution runtime such as Codex, Claude Code, OpenCode, Tutti, or another agent host.

A Runtime Adapter does **not** own the Framework Constitution, risk model, project truth, approval gates, release decision, or verification authority.

## Responsibility split

### Framework owns

- Constitution and policies,
- project Framework pin and context routing,
- role/skill/workflow selection,
- risk classification,
- required capabilities,
- mutation and approval policy,
- evidence requirements,
- specialist vetoes,
- convergence and release decision.

### Runtime owns

- provider/session/process lifecycle,
- task transport,
- runtime scheduling,
- provider-specific tool invocation,
- session persistence/resume when supported,
- shared workspace/runtime state when supported,
- runtime cancellation/recovery semantics,
- provider credentials and runtime authentication according to its own secure configuration model.

### Adapter owns

- capability declaration,
- translation from EREI invocation intent to runtime-native operations,
- translation from runtime-native status/output into normalized EREI result/evidence shape,
- enforcement of the invocation's declared mutation/tool/approval boundaries where the runtime provides such controls,
- fail-closed reporting when required capabilities cannot be guaranteed.

## Non-responsibilities

A Runtime Adapter must not:

- weaken or reinterpret the Constitution,
- downgrade risk to make execution possible,
- convert a required approval into an implicit approval,
- mark its own output as independently verified,
- invent project facts that are absent from project evidence,
- silently enable broader tools/filesystem/network access than requested,
- make production promotion decisions,
- treat runtime/provider correlation IDs as durable project or evidence identity unless explicitly mapped and recorded.

## Adapter manifest

Each adapter must have a machine-readable manifest conforming to `schemas/runtime-adapter.schema.json`.

Minimum identity:

- schema version,
- adapter id,
- display name,
- adapter version,
- maturity/status,
- runtime kind,
- supported transport/integration mode,
- declared capabilities.

Capabilities are declarations, not proof. Verification must confirm required behavior before a capability is trusted for high-risk work.

## Canonical capability vocabulary V1

Adapters may declare the following capabilities:

- `execute_task`
- `resume_session`
- `cancel_task`
- `read_workspace`
- `write_workspace`
- `shared_context`
- `artifact_handoff`
- `parallel_agents`
- `agent_handoff`
- `interactive_approval`
- `interactive_input`
- `tool_policy`
- `mutation_policy`
- `trace_export`
- `session_persistence`
- `runtime_recovery`

Unknown/additional capabilities may be declared under adapter-specific metadata, but Framework workflows must not depend on them until standardized or explicitly handled.

## Capability negotiation

Before execution:

1. Workflow states required capabilities.
2. Adapter manifest states available capabilities.
3. Adapter/runtime preflight confirms runtime readiness for the requested operation.
4. Missing required capability => `BLOCKED`.
5. A weaker substitute requires explicit workflow/approval handling; it must not be silently treated as equivalent.

Example:

If an L3 workflow requires `interactive_approval` and the selected runtime cannot pause safely for approval, the adapter cannot emulate approval by continuing and asking later.

## Invocation intent

The Framework should provide an invocation intent containing at least:

- invocation id,
- project identity,
- exact Framework ref,
- selected workflow,
- selected role,
- task/request,
- risk level,
- relevant project context references,
- required capabilities,
- mutation policy,
- allowed/required tools where applicable,
- approval state,
- verification/evidence expectations.

The semantic contract is transport-neutral. A concrete adapter may map this to CLI, HTTP/RPC, desktop daemon, SDK/native API, or another transport.

## Mutation policy

V1 recognizes these normalized mutation modes:

- `read_only`
- `workspace_write`
- `repository_write`
- `runtime_write`
- `production_impact`

An invocation may permit a subset. Runtime inability to constrain the requested boundary must be surfaced before execution for material-risk tasks.

`production_impact` never implies release approval; it only describes possible runtime side effects and therefore requires the appropriate Framework/project gates.

## Normalized lifecycle states

Adapters should map runtime state into:

- `accepted`
- `running`
- `waiting_approval`
- `waiting_input`
- `completed`
- `failed`
- `canceled`
- `unknown`

`unknown` is a first-class fail-closed state. Do not fabricate completion when provider/runtime outcome is uncertain.

## Normalized result

A completed adapter result should provide, where applicable:

- invocation id,
- normalized lifecycle status,
- user/agent-visible output,
- changed artifacts,
- evidence references,
- runtime/tool trace or trace reference,
- warnings,
- runtime metadata,
- error/uncertainty details.

Runtime self-reports are evidence inputs, not independent verification.

## Evidence and trace

When `trace_export` is declared, the adapter should preserve enough normalized trace to answer:

- which runtime/provider executed,
- which tools/capabilities were used,
- which files/artifacts changed,
- whether approval/input pauses occurred,
- whether execution reached a known terminal state.

Secrets, credentials and sensitive tokens must be redacted or excluded from exported traces.

## Trust and security

- Frontend/runtime UI state is not an authorization oracle.
- Adapter/runtime credentials remain runtime configuration, not project files.
- Project/Framework secrets must not be embedded in invocation fixtures or durable traces.
- A shared workspace runtime introduces a trust boundary; project and tenant isolation must be evaluated before sensitive work.
- Multi-agent/shared-context capability does not authorize every agent to access every project artifact.

## Relationship to Eval Adapter Protocol

`evals/adapters/PROTOCOL.md` is a testing boundary for executing eval cases.

The Runtime Adapter Contract is broader and governs real engineering task execution. A runtime adapter may also expose an Eval Adapter wrapper, but the two contracts must not be conflated.

## Adapter package shape

Recommended:

```text
adapters/<adapter-id>/
├── ADAPTER.md
├── adapter.json
├── SOURCES.md
├── evals/
└── implementation/     optional
```

Provider/runtime implementation code is optional. Some adapters may consist only of integration instructions and a stable external interface mapping.

## Maturity levels

- `experimental` — interface/prototype not trusted for project Stable workflows.
- `candidate` — contract-complete with focused verification but not yet broadly proven.
- `stable` — required conformance/evals passed and supported operational path documented.
- `deprecated` — retained for migration/compatibility only.

Project `runtime_adapters` should normally enable only Stable adapters for Candidate/Stable project engineering unless an explicit experimental workflow permits otherwise.

## Conformance requirements

Before an adapter becomes Stable, test at minimum:

1. capability declaration correctness,
2. fail-closed missing capability handling,
3. read-only mutation protection where supported/claimed,
4. known vs unknown terminal outcome handling,
5. cancel behavior,
6. approval/input behavior when declared,
7. trace/evidence normalization when declared,
8. recovery/resume behavior when declared,
9. secret-safe diagnostics,
10. project/Framework context loading at the exact pinned ref.

Multi-agent adapters additionally require conflict/handoff and shared-context isolation scenarios.

## Change control

Changes to capability semantics, trust boundaries, mutation modes, approval handling, lifecycle terminal semantics, or verification authority are L3 architecture changes and require explicit approval.