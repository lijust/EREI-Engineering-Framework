# Tutti Adapter Sources

**Assessment date:** 2026-09-01  
**Upstream:** `tutti-os/tutti`  
**Observed upstream revision:** `f330b71d2637c8bf0e4f11d16d7c4133099e7cb4`  
**Upstream license:** Apache-2.0

## Reuse classification

**Integration / independent adapter implementation.**

No Tutti source file is copied into EREI Engineering Framework. The adapter independently implements a small client against documented/publicly exposed daemon behavior and request shapes.

## Primary evidence

- `README.md` — Tutti product/runtime positioning and multi-agent workspace behavior.
- `LICENSE` — Apache License 2.0.
- `AGENTS.md` — local-first architecture and provider-neutral Agent Host boundary.
- `packages/agent/host/README.md` — canonical session/turn/goal/runtime-operation lifecycle ownership.
- `services/tuttid/api/openapi/tuttid.v1.yaml` — versioned local daemon API for desktop, CLI and approved local integrations; bearer auth.
- `services/tuttid/api/routes_workspace_agent_sessions.go` — workspace agent session/create/send/cancel/interactive routing.
- `packages/clients/tuttid-ts/src/generated/sdk.gen.ts` — generated daemon API paths/security.
- `packages/clients/tuttid-ts/src/workspaceAgentClient.ts` — client-visible workspace-agent operations.
- `packages/agent/activity-tuttid-adapter/src/requests.ts` — request mapping for create-session and send-input text content.
- `docs/conventions/local-state-storage.md` — production/development state roots, listener metadata path, environment overrides, bearer listener metadata.
- `apps/cli/internal/daemon/endpoint_test.go` — listener metadata V1 shape with loopback address and bearer token.

## Confirmed external surface used by V0.1

- listener metadata: `<state-dir>/run/tuttid.listener.json`
- listener metadata version: `1`
- auth scheme: bearer
- daemon base address: loopback HTTP
- health: `GET /v1/health`
- create session: `POST /v1/workspaces/{workspaceID}/agent-sessions`
- read session: `GET /v1/workspaces/{workspaceID}/agent-sessions/{agentSessionID}`
- send input: `POST /v1/workspaces/{workspaceID}/agent-sessions/{agentSessionID}/input`
- exact Turn cancel: `POST /v1/workspaces/{workspaceID}/agent-sessions/{agentSessionID}/turns/{turnID}/cancel`
- interactive response: `POST /v1/workspaces/{workspaceID}/agent-sessions/{agentSessionID}/interactives/{requestID}/response`

## Source-handling rules

- Upstream behavior must be re-verified before Candidate promotion.
- Exact supported Tutti version/range is not established by V0.1.
- Internal Host APIs are architectural evidence only; the EREI adapter uses the daemon boundary.
- New capability declarations require a source/evidence update and conformance case.
- If direct upstream source reuse is introduced later, Apache-2.0 notice/redistribution requirements must be reviewed explicitly.