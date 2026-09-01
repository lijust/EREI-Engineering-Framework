# Tutti Experimental Adapter — Conformance Cases V0.1

These cases are required before the adapter can advance beyond `experimental`.

## TUTTI-001 — Listener discovery

Given production defaults, resolve `~/.tutti/run/tuttid.listener.json`.

Given `TUTTI_ENV=development`, resolve `~/.tutti-dev/run/tuttid.listener.json`.

Given an explicit listener override, the explicit path wins.

## TUTTI-002 — Loopback boundary

A listener advertising `127.0.0.1` or `::1` may be accepted.

A listener advertising a non-loopback address must be rejected before any HTTP request.

## TUTTI-003 — Listener schema

Listener metadata must use version `1`, bearer auth, a non-empty token and a host/port address.

Unknown version/auth scheme => BLOCKED.

## TUTTI-004 — Secret-safe diagnostics

The per-run bearer token must not appear in:

- object representation,
- preflight output,
- durable error messages,
- test artifacts,
- project files.

HTTP response bodies are not copied into durable errors by V0.1.

## TUTTI-005 — Create text session

A text task creates a request at:

`POST /v1/workspaces/{workspaceID}/agent-sessions`

with caller-stable/generator IDs and the documented text `initialContent` shape.

## TUTTI-006 — Send task

A task sent to an existing session uses:

`POST /v1/workspaces/{workspaceID}/agent-sessions/{agentSessionID}/input`

with `clientSubmitId` and a text content block.

## TUTTI-007 — Exact Turn cancellation

Cancellation must target the exact supplied Turn:

`POST /v1/workspaces/{workspaceID}/agent-sessions/{agentSessionID}/turns/{turnID}/cancel`

The adapter must not infer cancellation of a different/current Turn.

## TUTTI-008 — Interactive response

Interactive input/approval responses use the exact request identity:

`POST /v1/workspaces/{workspaceID}/agent-sessions/{agentSessionID}/interactives/{requestID}/response`

A missing request identity must block locally.

## TUTTI-009 — Missing capability

A workflow requiring `mutation_policy`, `trace_export`, `parallel_agents` or another undeclared capability must be BLOCKED by Runtime Adapter capability negotiation.

The Tutti product having a conceptually similar feature is insufficient.

## TUTTI-010 — Unknown runtime outcome

Transport loss after submission must not be converted automatically to `completed` or `failed` without authoritative Tutti state.

V0.1 does not yet implement normalized recovery; therefore this remains a Candidate blocker.

## TUTTI-011 — Project/workspace isolation

Before Candidate promotion, prove that the selected Tutti workspace and `cwd` bind to the intended project and that one project invocation cannot silently operate in another project workspace.

Not yet satisfied by unit mocks.

## TUTTI-012 — Live daemon compatibility

Run create/read/send/cancel/interactive scenarios against a supported Tutti installation and record exact upstream version/commit/build evidence.

Not yet satisfied in Framework CI because no Tutti daemon is installed there.

## TUTTI-013 — Approval semantics

Before Candidate promotion, verify that an EREI approval-required invocation cannot continue through Tutti while approval is pending, rejected or unavailable.

Transport support for interactive responses alone is not enough to claim enforcement.

## TUTTI-014 — Trace/evidence normalization

Before declaring `trace_export`, map Tutti session/Turn/tool evidence to the EREI normalized result without including bearer tokens, provider credentials or unrelated shared-workspace content.

## TUTTI-015 — Multi-agent gate

Do not declare `parallel_agents`, `agent_handoff` or `shared_context` until single-agent trust/isolation conformance passes first.

Then test:

- parallel write conflicts,
- sequential handoff identity,
- cross-agent context scope,
- approval ownership,
- cancellation ownership,
- evidence provenance.
