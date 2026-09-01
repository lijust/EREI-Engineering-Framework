# Tutti Adapter Assessment

**Status:** Assessment only — no enableable adapter yet  
**Runtime:** Tutti (`tutti-os/tutti`)  
**License:** Apache-2.0

## Purpose

Map publicly observed Tutti capabilities to EREI Runtime Adapter Contract V1 without pretending that an external supported integration surface has already been verified.

No `adapter.json` is provided intentionally. A project must not enable `tutti` as an EREI runtime adapter until an implementation passes conformance.

## Observed product/architecture fit

| EREI capability | Tutti evidence | External adapter surface verified? |
|---|---|---|
| `execute_task` | Agents/tasks are core product behavior | No |
| `resume_session` | Agent Host owns session resume lifecycle | No |
| `cancel_task` | Host owns cancellation semantics | No |
| `read_workspace` | Shared workspace exposes files/context/tasks | No |
| `write_workspace` | Agents and apps create shared outputs | No |
| `shared_context` | Primary product capability | No |
| `artifact_handoff` | Outputs can flow between agents/apps | No |
| `parallel_agents` | Multi-agent orchestration is a product goal | No |
| `agent_handoff` | Cross-agent continuation/handoff is documented | No |
| `interactive_approval` | Product surfaces actions waiting for user approval; Host models interactive states | No |
| `interactive_input` | Host owns interactive response lifecycle | No |
| `tool_policy` | Runtime/tool architecture exists | Not verified for EREI policy enforcement |
| `mutation_policy` | No EREI-compatible enforcement contract verified | No |
| `trace_export` | Runtime state is visible, but normalized export contract is unverified | No |
| `session_persistence` | Durable local state / Host lifecycle | No |
| `runtime_recovery` | Host explicitly owns recovery semantics | No |

## Important distinction

The middle column means the capability exists conceptually/product-wise in Tutti. It does **not** mean EREI can safely invoke or enforce it through a stable external API today.

## Integration gate

Before creating `adapters/tutti/adapter.json`:

1. identify a supported external Tutti integration surface,
2. verify authentication/credential handling,
3. map lifecycle states without inventing success on uncertainty,
4. prove EREI mutation/approval boundaries can be enforced or fail closed,
5. verify exact project workspace isolation,
6. normalize trace/evidence safely,
7. run single-agent conformance,
8. run multi-agent/shared-context conflict and isolation cases,
9. document supported Tutti versions and upgrade policy.

## Initial recommendation

Tutti should be evaluated first as an **experimental local/shared runtime adapter**, not as a dependency of Framework Core and not as the only supported runtime.
