# Tutti Adapter Assessment

**Status:** Assessment only — no enableable adapter yet  
**Runtime:** Tutti (`tutti-os/tutti`)  
**License:** Apache-2.0

## Purpose

Map publicly observed Tutti capabilities to EREI Runtime Adapter Contract V1 without pretending that a complete EREI-compatible implementation has already been verified.

No `adapter.json` is provided intentionally. A project must not enable `tutti` as an EREI runtime adapter until an implementation passes conformance.

## External integration surface now confirmed

Tutti exposes a versioned local daemon OpenAPI described for desktop, CLI and approved local integrations.

Observed integration properties:

- local daemon API,
- bearer authentication,
- daemon-owned authorization/context,
- machine-readable CLI capability discovery,
- stable command-id invocation endpoint,
- generated client surface.

This is sufficient evidence to treat a Tutti adapter as technically plausible without importing Tutti internal packages.

It is **not** yet sufficient to declare specific EREI capabilities Stable; the exact operations and enforcement semantics still need conformance mapping.

## Observed product/architecture fit

| EREI capability | Tutti evidence | EREI adapter mapping status |
|---|---|---|
| `execute_task` | Agents/tasks + local command invocation exist | Needs operation mapping |
| `resume_session` | Agent Host owns session resume lifecycle | External endpoint mapping not yet verified |
| `cancel_task` | Host owns cancellation semantics | External endpoint mapping not yet verified |
| `read_workspace` | Shared workspace + daemon APIs | Needs scope/isolation verification |
| `write_workspace` | Agents/apps create shared outputs | Needs mutation-policy verification |
| `shared_context` | Primary product capability | Strong candidate |
| `artifact_handoff` | Outputs flow between agents/apps | Strong candidate |
| `parallel_agents` | Multi-agent orchestration | Strong candidate |
| `agent_handoff` | Cross-agent continuation/handoff | Strong candidate |
| `interactive_approval` | Approval UI + Host interactive lifecycle | Endpoint semantics need mapping |
| `interactive_input` | Host interactive response lifecycle | Endpoint semantics need mapping |
| `tool_policy` | Daemon capability discovery/filtering | EREI policy equivalence not yet proven |
| `mutation_policy` | Daemon owns context/authorization | EREI normalized modes not yet proven |
| `trace_export` | Runtime state is visible | Normalized export path not yet proven |
| `session_persistence` | Durable local state / Host lifecycle | Strong candidate |
| `runtime_recovery` | Host explicitly owns recovery semantics | Strong candidate |

## Integration gate

Before creating `adapters/tutti/adapter.json`:

1. map EREI required operations to supported daemon API/CLI capabilities,
2. verify authentication/credential handling,
3. map lifecycle states without inventing success on uncertainty,
4. prove EREI mutation/approval boundaries can be enforced or fail closed,
5. verify exact project/workspace isolation,
6. normalize trace/evidence safely,
7. run single-agent conformance,
8. run multi-agent/shared-context conflict and isolation cases,
9. document supported Tutti versions and upgrade policy.

## Initial implementation direction

If ADR-0003 is approved, prototype Tutti as an **experimental local daemon adapter** using supported versioned API/CLI surfaces.

Do not fork Tutti Agent Host, import its internal lifecycle packages into Framework Core, or make Tutti mandatory for projects that only need a simpler runtime.
