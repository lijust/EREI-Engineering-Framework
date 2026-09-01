#!/usr/bin/env python3
"""Experimental EREI Runtime Adapter client for the local Tutti daemon.

Python standard library only. This adapter is intentionally narrow and fail-closed.
It never starts Tutti, never reads Tutti's database, and never persists bearer tokens.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
from uuid import uuid4


class TuttiAdapterError(RuntimeError):
    pass


class TuttiEndpointError(TuttiAdapterError):
    pass


class TuttiProtocolError(TuttiAdapterError):
    def __init__(self, message: str, *, status: int | None = None):
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class TuttiEndpoint:
    base_url: str
    source_path: str
    token: str = field(repr=False)


def resolve_listener_path(
    environ: Mapping[str, str] | None = None,
    *,
    home: Path | None = None,
) -> Path:
    env = dict(os.environ if environ is None else environ)
    explicit = env.get("TUTTID_LISTENER_INFO_PATH", "").strip()
    if explicit:
        return Path(explicit).expanduser()

    run_dir = env.get("TUTTID_RUN_DIR", "").strip()
    if run_dir:
        return Path(run_dir).expanduser() / "tuttid.listener.json"

    state_dir = env.get("TUTTI_STATE_DIR", "").strip()
    if state_dir:
        root = Path(state_dir).expanduser()
    else:
        root_home = Path.home() if home is None else home
        suffix = ".tutti-dev" if env.get("TUTTI_ENV", "").strip().lower() == "development" else ".tutti"
        root = root_home / suffix
    return root / "run" / "tuttid.listener.json"


def _loopback_host(addr: str) -> tuple[str, int]:
    parsed = urlparse(f"http://{addr}")
    host = parsed.hostname
    port = parsed.port
    if not host or port is None:
        raise TuttiEndpointError("Tutti listener address must contain host and port")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError as exc:
        raise TuttiEndpointError("Tutti listener host must be an explicit loopback IP") from exc
    if not ip.is_loopback:
        raise TuttiEndpointError("Tutti listener must be loopback-only")
    return host, port


def load_endpoint(path: Path) -> TuttiEndpoint:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TuttiEndpointError(f"Tutti listener metadata not found: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise TuttiEndpointError(f"Cannot read Tutti listener metadata: {path}") from exc

    if raw.get("version") != 1:
        raise TuttiEndpointError("Unsupported Tutti listener metadata version")
    addr = raw.get("addr")
    auth = raw.get("auth")
    if not isinstance(addr, str) or not isinstance(auth, dict):
        raise TuttiEndpointError("Invalid Tutti listener metadata")
    if auth.get("scheme") != "bearer":
        raise TuttiEndpointError("Unsupported Tutti listener authentication scheme")
    token = auth.get("token")
    if not isinstance(token, str) or not token:
        raise TuttiEndpointError("Missing Tutti bearer token")

    host, port = _loopback_host(addr)
    host_for_url = f"[{host}]" if ":" in host else host
    return TuttiEndpoint(
        base_url=f"http://{host_for_url}:{port}",
        source_path=str(path),
        token=token,
    )


class TuttiClient:
    def __init__(self, endpoint: TuttiEndpoint, *, timeout_seconds: float = 30.0):
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    @classmethod
    def discover(
        cls,
        environ: Mapping[str, str] | None = None,
        *,
        home: Path | None = None,
        timeout_seconds: float = 30.0,
    ) -> "TuttiClient":
        return cls(
            load_endpoint(resolve_listener_path(environ, home=home)),
            timeout_seconds=timeout_seconds,
        )

    def _request(self, method: str, path: str, body: Any | None = None) -> Any:
        if not path.startswith("/"):
            raise TuttiProtocolError("Tutti API path must be absolute")
        payload = None
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.endpoint.token}",
        }
        if body is not None:
            payload = json.dumps(body, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(
            self.endpoint.base_url + path,
            data=payload,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                data = response.read()
                if not data:
                    return None
                content_type = response.headers.get("content-type", "")
                if "json" not in content_type.lower():
                    raise TuttiProtocolError(
                        f"Tutti returned non-JSON response for {method} {path}",
                        status=response.status,
                    )
                return json.loads(data.decode("utf-8"))
        except HTTPError as exc:
            # Do not include response bodies or authorization material in durable errors.
            raise TuttiProtocolError(
                f"Tutti API request failed: {method} {path} -> HTTP {exc.code}",
                status=exc.code,
            ) from exc
        except URLError as exc:
            raise TuttiProtocolError(
                f"Tutti API unavailable for {method} {path}: {exc.reason}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise TuttiProtocolError(
                f"Tutti returned invalid JSON for {method} {path}"
            ) from exc

    @staticmethod
    def _segment(value: str, name: str) -> str:
        value = value.strip()
        if not value:
            raise TuttiProtocolError(f"Missing {name}")
        return quote(value, safe="")

    def health(self) -> Any:
        return self._request("GET", "/v1/health")

    def get_session(self, workspace_id: str, agent_session_id: str) -> Any:
        w = self._segment(workspace_id, "workspace_id")
        s = self._segment(agent_session_id, "agent_session_id")
        return self._request("GET", f"/v1/workspaces/{w}/agent-sessions/{s}")

    def create_text_session(
        self,
        workspace_id: str,
        agent_target_id: str,
        task: str,
        *,
        cwd: str | None,
        agent_session_id: str | None = None,
        client_submit_id: str | None = None,
        title: str | None = None,
        visible: bool = True,
    ) -> Any:
        task = task.strip()
        if not task:
            raise TuttiProtocolError("Task text must not be empty")
        w = self._segment(workspace_id, "workspace_id")
        target = agent_target_id.strip()
        if not target:
            raise TuttiProtocolError("agent_target_id must not be empty")
        session_id = (agent_session_id or f"erei-session-{uuid4()}").strip()
        submit_id = (client_submit_id or f"erei-{uuid4()}").strip()
        body = {
            "agentSessionId": session_id,
            "agentTargetId": target,
            "clientSubmitId": submit_id,
            "cwd": cwd,
            "initialContent": [{"type": "text", "text": task}],
            "initialDisplayPrompt": task,
            "model": None,
            "permissionModeId": None,
            "planMode": None,
            "reasoningEffort": None,
            "speed": None,
            "title": title,
            "visible": visible,
        }
        return self._request("POST", f"/v1/workspaces/{w}/agent-sessions", body)

    def send_task(
        self,
        workspace_id: str,
        agent_session_id: str,
        task: str,
        *,
        client_submit_id: str | None = None,
        display_prompt: str | None = None,
    ) -> Any:
        task = task.strip()
        if not task:
            raise TuttiProtocolError("Task text must not be empty")
        w = self._segment(workspace_id, "workspace_id")
        s = self._segment(agent_session_id, "agent_session_id")
        submit_id = (client_submit_id or f"erei-{uuid4()}").strip()
        if not submit_id:
            raise TuttiProtocolError("client_submit_id must not be empty")
        body = {
            "clientSubmitId": submit_id,
            "content": [{"type": "text", "text": task}],
            "displayPrompt": display_prompt if display_prompt is not None else task,
        }
        return self._request("POST", f"/v1/workspaces/{w}/agent-sessions/{s}/input", body)

    def cancel_turn(self, workspace_id: str, agent_session_id: str, turn_id: str) -> Any:
        w = self._segment(workspace_id, "workspace_id")
        s = self._segment(agent_session_id, "agent_session_id")
        t = self._segment(turn_id, "turn_id")
        return self._request(
            "POST",
            f"/v1/workspaces/{w}/agent-sessions/{s}/turns/{t}/cancel",
        )

    def submit_interactive(
        self,
        workspace_id: str,
        agent_session_id: str,
        request_id: str,
        response_payload: Mapping[str, Any],
    ) -> Any:
        if not isinstance(response_payload, Mapping):
            raise TuttiProtocolError("Interactive response must be an object")
        w = self._segment(workspace_id, "workspace_id")
        s = self._segment(agent_session_id, "agent_session_id")
        r = self._segment(request_id, "request_id")
        return self._request(
            "POST",
            f"/v1/workspaces/{w}/agent-sessions/{s}/interactives/{r}/response",
            dict(response_payload),
        )


def _cli() -> int:
    parser = argparse.ArgumentParser(description="EREI experimental Tutti runtime adapter")
    parser.add_argument("--listener", help="Explicit tuttid.listener.json path")
    parser.add_argument("--timeout", type=float, default=30.0)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("preflight")
    sub.add_parser("health")

    get_session = sub.add_parser("get-session")
    get_session.add_argument("workspace_id")
    get_session.add_argument("agent_session_id")

    create = sub.add_parser("create-session")
    create.add_argument("workspace_id")
    create.add_argument("agent_target_id")
    create.add_argument("task")
    create.add_argument("--cwd")
    create.add_argument("--agent-session-id")
    create.add_argument("--client-submit-id")
    create.add_argument("--title")

    send = sub.add_parser("send-task")
    send.add_argument("workspace_id")
    send.add_argument("agent_session_id")
    send.add_argument("task")
    send.add_argument("--client-submit-id")

    cancel = sub.add_parser("cancel-turn")
    cancel.add_argument("workspace_id")
    cancel.add_argument("agent_session_id")
    cancel.add_argument("turn_id")

    interactive = sub.add_parser("interactive")
    interactive.add_argument("workspace_id")
    interactive.add_argument("agent_session_id")
    interactive.add_argument("request_id")
    interactive.add_argument("json_payload")

    args = parser.parse_args()
    env = dict(os.environ)
    if args.listener:
        env["TUTTID_LISTENER_INFO_PATH"] = args.listener
    client = TuttiClient.discover(env, timeout_seconds=args.timeout)

    if args.command == "preflight":
        result = {
            "status": "ready",
            "transport": "desktop-daemon",
            "base_url": client.endpoint.base_url,
            "listener": client.endpoint.source_path,
            "credential_exposed": False,
        }
    elif args.command == "health":
        result = client.health()
    elif args.command == "get-session":
        result = client.get_session(args.workspace_id, args.agent_session_id)
    elif args.command == "create-session":
        result = client.create_text_session(
            args.workspace_id,
            args.agent_target_id,
            args.task,
            cwd=args.cwd,
            agent_session_id=args.agent_session_id,
            client_submit_id=args.client_submit_id,
            title=args.title,
        )
    elif args.command == "send-task":
        result = client.send_task(
            args.workspace_id,
            args.agent_session_id,
            args.task,
            client_submit_id=args.client_submit_id,
        )
    elif args.command == "cancel-turn":
        result = client.cancel_turn(args.workspace_id, args.agent_session_id, args.turn_id)
    else:
        payload = json.loads(args.json_payload)
        result = client.submit_interactive(
            args.workspace_id,
            args.agent_session_id,
            args.request_id,
            payload,
        )

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
