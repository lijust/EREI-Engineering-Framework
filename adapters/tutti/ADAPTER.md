# Tutti Local Runtime Adapter

**Status:** Experimental V0.1  
**Adapter ID:** `tutti-local`  
**Transport:** local desktop daemon HTTP API

## Purpose

Provide a narrow EREI Runtime Adapter implementation against Tutti's documented local daemon surface without making Tutti a Framework dependency.

This package is experimental. It must not be enabled for Candidate/Stable project workflows yet.

## V0.1 supported surface

The implementation can:

- discover `tuttid.listener.json`,
- require listener metadata version 1,
- require bearer authentication,
- require an explicit loopback IP listener,
- call daemon health,
- read one workspace agent session,
- create a text-initialized workspace agent session,
- submit a text task to an existing workspace agent session,
- cancel an exact Turn,
- submit an interactive response payload.

## Declared EREI capabilities

`adapter.json` declares only:

- `execute_task`
- `cancel_task`
- `interactive_approval`
- `interactive_input`
- `session_persistence`

These remain **experimental claims**, not Stable proof.

The adapter intentionally does **not** declare yet:

- `resume_session`
- `read_workspace`
- `write_workspace`
- `shared_context`
- `artifact_handoff`
- `parallel_agents`
- `agent_handoff`
- `tool_policy`
- `mutation_policy`
- `trace_export`
- `runtime_recovery`

Existing Tutti product capabilities are not automatically EREI adapter capabilities. Each one must be mapped and pass conformance before declaration.

## Credential handling

The adapter reads the per-run bearer token from Tutti listener metadata and keeps it in memory only.

Rules:

- token is never written to project files,
- token is excluded from object `repr`,
- token is not printed by preflight,
- HTTP error bodies are not included in durable adapter errors,
- non-loopback listener endpoints are rejected,
- the adapter never reads `tuttid.db` directly.

## Listener discovery

Order:

1. `TUTTID_LISTENER_INFO_PATH`
2. `TUTTID_RUN_DIR/tuttid.listener.json`
3. `TUTTI_STATE_DIR/run/tuttid.listener.json`
4. production default `~/.tutti/run/tuttid.listener.json`
5. development default `~/.tutti-dev/run/tuttid.listener.json` when `TUTTI_ENV=development`

The implementation never starts a daemon automatically.

## Experimental CLI

```text
python adapters/tutti/implementation/tutti_adapter.py preflight
python adapters/tutti/implementation/tutti_adapter.py health
python adapters/tutti/implementation/tutti_adapter.py get-session <workspace> <session>
python adapters/tutti/implementation/tutti_adapter.py create-session <workspace> <agent-target> "task" --cwd <repo>
python adapters/tutti/implementation/tutti_adapter.py send-task <workspace> <session> "task"
python adapters/tutti/implementation/tutti_adapter.py cancel-turn <workspace> <session> <turn>
python adapters/tutti/implementation/tutti_adapter.py interactive <workspace> <session> <request> '<json>'
```

These commands expose transport primitives only. They do not perform Framework risk selection, approvals, verification or release decisions.

## Trust boundary

EREI Framework remains authoritative for:

- selected workflow and role,
- risk,
- allowed mutation scope,
- approval state,
- required evidence,
- specialist veto,
- verification and release acceptance.

The experimental adapter currently cannot prove fine-grained `mutation_policy` enforcement. Therefore any workflow requiring runtime-enforced mutation boundaries must remain blocked on this adapter.

## Promotion gate

Before Candidate:

1. test against a real supported Tutti installation,
2. confirm supported Tutti version range,
3. prove create/send/cancel/interactive semantics against the live daemon,
4. normalize known/unknown terminal states,
5. add trace/evidence extraction,
6. test secret-safe failures,
7. prove exact project/workspace binding,
8. test approval/input lifecycle,
9. decide whether runtime mutation constraints are enforceable,
10. run EREI Runtime Adapter conformance.

Multi-agent capabilities have a separate later gate.