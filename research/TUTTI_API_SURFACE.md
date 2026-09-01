# Tutti Local API Surface Map

**Date:** 2026-09-01  
**Repository:** `tutti-os/tutti`  
**Purpose:** Identify externally usable Tutti surfaces relevant to a future EREI Runtime Adapter without depending on Tutti internal lifecycle packages.

## Confidence labels

- **CONFIRMED_EXTERNAL** — present in Tutti's versioned local daemon API/generated client surface.
- **CONFIRMED_ARCHITECTURE** — behavior exists in Tutti architecture but EREI external mapping still needs conformance.
- **UNVERIFIED_FOR_EREI** — no claim yet that EREI policy semantics can be enforced through the surface.

## Base integration boundary

Tutti documents `services/tuttid/api/openapi/tuttid.v1.yaml` as a versioned local daemon API for desktop, CLI, and approved local integrations.

Observed properties:

- local server: `http://127.0.0.1:4545`,
- bearer authentication,
- daemon-owned context and authorization,
- generated TypeScript client,
- machine-readable CLI capability discovery and invocation.

### Capability discovery

**CONFIRMED_EXTERNAL**

- `GET /v1/cli/capabilities`
- daemon-owned visible command metadata
- optional workspace/session context
- integration-only capability discovery support

Potential EREI use:

- runtime preflight,
- version/capability discovery,
- avoid duplicating runtime command availability rules.

### Stable command invocation

**CONFIRMED_EXTERNAL**

- `POST /v1/cli/commands/{commandID}/invoke`
- daemon validates context and returns presentation-neutral output.

Potential EREI use:

- narrow runtime commands where a command capability maps cleanly to an EREI operation.

This endpoint alone is not sufficient for the full Runtime Adapter Contract because agent lifecycle and evidence semantics require richer mappings.

## Workspace Agent session operations

Tutti's generated `workspaceAgentClient.ts` and daemon routes expose a substantial agent-session surface.

### Create session

**CONFIRMED_EXTERNAL**

Generated client operation:

- `createWorkspaceAgentSession(workspaceID, request, requestOptions)`

Daemon route wiring confirms POST creation for workspace agent sessions.

EREI candidate mapping:

- start runtime execution context,
- `session_persistence` candidate,
- initial provider/agent selection.

### Read/list session state

**CONFIRMED_EXTERNAL**

Generated client includes:

- `getWorkspaceAgentSession`
- `listWorkspaceAgentSessions`
- message/session section reads
- generated-file reads

EREI candidate mapping:

- normalized lifecycle observation,
- evidence/artifact discovery,
- recovery/resume preflight.

### Send task/input

**CONFIRMED_EXTERNAL**

Generated client:

- `sendWorkspaceAgentSessionInput`

Documented route evidence:

- `POST /v1/workspaces/{workspaceID}/agent-sessions/{agentSessionID}/input`

EREI candidate mapping:

- `execute_task`,
- continuing an existing session.

### Cancel exact work

**CONFIRMED_EXTERNAL**

Generated client:

- `cancelWorkspaceAgentTurn`

Tutti architecture explicitly treats cancellation as exact-Turn behavior and distinguishes request, provider confirmation, and canonical settlement.

EREI candidate mapping:

- `cancel_task`,
- unknown/uncertain outcome handling.

### Interactive response / approval

**CONFIRMED_EXTERNAL surface; UNVERIFIED_FOR_EREI policy equivalence**

Generated client includes:

- `submitWorkspaceAgentInteractive`
- `submitWorkspaceAgentPlanDecision`
- Side-conversation interactive response operations.

EREI candidate mapping:

- `interactive_approval`,
- `interactive_input`.

Before claiming those EREI capabilities, conformance must prove that an EREI-required approval cannot be bypassed or converted into post-hoc confirmation.

### Goal/control lifecycle

**CONFIRMED_EXTERNAL**

Generated client includes:

- `goalControlWorkspaceAgentSession`
- `getWorkspaceAgentSessionGoal`
- `reconcileWorkspaceAgentSessionGoal`

This is richer than EREI Runtime Adapter V1 currently requires. It may support future durable task orchestration, but EREI should not expose Tutti-specific Goal semantics in Framework Core unless a generic need is proven.

### Fork / side-agent operations

**CONFIRMED_EXTERNAL**

Generated client includes:

- `forkWorkspaceAgentSession`
- side-conversation open/send/cancel/interactive operations

Potential EREI mapping:

- `agent_handoff`,
- `parallel_agents`,
- isolated specialist/reviewer work.

Do not claim those capabilities Stable until conflict/isolation/handoff conformance passes.

### Session persistence / recovery

**CONFIRMED_ARCHITECTURE with external session read/control surfaces**

Tutti Agent Host owns durable session/turn/goal/runtime-operation recovery. External clients can read/manage sessions, but EREI still needs to verify the exact reconnect/resume path required for its normalized `resume_session` and `runtime_recovery` capabilities.

## Workspace and artifact operations

Generated client evidence includes:

- generated files,
- workspace Git branches,
- managed worktrees,
- Git patch application,
- attachments,
- session recording/replay.

These are potentially useful for `read_workspace`, `write_workspace`, `artifact_handoff`, and `trace_export`, but EREI must define a deliberately narrow subset. Broad Tutti workspace capability must not automatically become broad EREI mutation authorization.

## Security / trust observations

Positive integration signals:

- local daemon boundary,
- bearer authentication,
- daemon-owned authorization/context,
- explicit workspace IDs,
- canonical lifecycle owner separated from adapters,
- uncertainty and recovery are modeled rather than collapsed into success.

Remaining EREI checks:

1. How an approved local integration securely discovers/receives the bearer token.
2. Exact workspace-to-project binding and isolation.
3. Whether read-only/repository-write EREI mutation modes can be enforced, not merely requested.
4. Tool allow/deny policy mapping.
5. Trace export/redaction behavior.
6. Terminal-state observation mechanism for long-running tasks.
7. Supported Tutti version range and compatibility strategy.
8. Multi-agent artifact visibility/isolation.

## Prototype recommendation after ADR-0003 approval

Build the first Tutti adapter as **experimental**, local-daemon based, with a deliberately small capability set:

1. `execute_task`
2. `cancel_task`
3. `read_workspace`
4. `session_persistence`
5. `interactive_input` / `interactive_approval` only after policy conformance
6. `trace_export` only after normalized evidence mapping

Delay `parallel_agents`, `agent_handoff`, and broad `write_workspace` until the single-agent trust/mutation model is proven.

## Conclusion

Tutti has a sufficiently concrete external/local API surface to justify an experimental EREI Runtime Adapter prototype. The remaining question is no longer whether an integration surface exists; it is whether EREI's governance, mutation, approval, isolation, lifecycle and evidence semantics can be mapped to that surface without weakening them.
