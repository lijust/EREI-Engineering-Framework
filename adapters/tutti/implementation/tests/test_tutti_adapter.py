import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tutti_adapter import (  # noqa: E402
    TuttiClient,
    TuttiEndpointError,
    TuttiProtocolError,
    load_endpoint,
    resolve_listener_path,
)


class Handler(BaseHTTPRequestHandler):
    requests = []

    def _handle(self):
        length = int(self.headers.get("content-length", "0"))
        body = self.rfile.read(length) if length else b""
        Handler.requests.append(
            {
                "method": self.command,
                "path": self.path,
                "auth": self.headers.get("Authorization"),
                "body": json.loads(body) if body else None,
            }
        )
        if self.path == "/error":
            self.send_response(500)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"secret response should not leak"}')
            return
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def log_message(self, *_args):
        pass


class AdapterTests(unittest.TestCase):
    def setUp(self):
        Handler.requests = []
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]
        self.tmp = tempfile.TemporaryDirectory()
        self.listener = Path(self.tmp.name) / "tuttid.listener.json"
        self.listener.write_text(
            json.dumps(
                {
                    "version": 1,
                    "addr": f"127.0.0.1:{self.port}",
                    "auth": {"scheme": "bearer", "token": "top-secret-token"},
                }
            ),
            encoding="utf-8",
        )
        self.client = TuttiClient(load_endpoint(self.listener), timeout_seconds=2)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tmp.cleanup()

    def test_listener_path_resolution(self):
        home = Path("/home/example")
        self.assertEqual(
            resolve_listener_path({}, home=home),
            home / ".tutti" / "run" / "tuttid.listener.json",
        )
        self.assertEqual(
            resolve_listener_path({"TUTTI_ENV": "development"}, home=home),
            home / ".tutti-dev" / "run" / "tuttid.listener.json",
        )
        self.assertEqual(
            resolve_listener_path({"TUTTI_STATE_DIR": "/state"}, home=home),
            Path("/state/run/tuttid.listener.json"),
        )
        self.assertEqual(
            resolve_listener_path({"TUTTID_LISTENER_INFO_PATH": "/x/listener.json"}, home=home),
            Path("/x/listener.json"),
        )

    def test_non_loopback_listener_is_rejected(self):
        self.listener.write_text(
            json.dumps(
                {
                    "version": 1,
                    "addr": "192.0.2.10:4545",
                    "auth": {"scheme": "bearer", "token": "secret"},
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaises(TuttiEndpointError):
            load_endpoint(self.listener)

    def test_endpoint_repr_does_not_expose_token(self):
        endpoint = load_endpoint(self.listener)
        self.assertNotIn("top-secret-token", repr(endpoint))

    def test_create_text_session_uses_documented_request_shape(self):
        result = self.client.create_text_session(
            "ws",
            "codex",
            "Build the feature",
            cwd="/repo",
            agent_session_id="session-1",
            client_submit_id="submit-1",
            title="EREI task",
        )
        self.assertEqual(result, {"ok": True})
        request = Handler.requests[-1]
        self.assertEqual(request["path"], "/v1/workspaces/ws/agent-sessions")
        self.assertEqual(request["body"]["agentSessionId"], "session-1")
        self.assertEqual(request["body"]["agentTargetId"], "codex")
        self.assertEqual(
            request["body"]["initialContent"],
            [{"type": "text", "text": "Build the feature"}],
        )
        self.assertEqual(request["body"]["cwd"], "/repo")
        self.assertIsNone(request["body"]["model"])

    def test_send_task_uses_bearer_and_expected_shape(self):
        result = self.client.send_task(
            "ws 1",
            "session/1",
            "Implement the fix",
            client_submit_id="inv-1",
        )
        self.assertEqual(result, {"ok": True})
        request = Handler.requests[-1]
        self.assertEqual(request["auth"], "Bearer top-secret-token")
        self.assertEqual(
            request["path"],
            "/v1/workspaces/ws%201/agent-sessions/session%2F1/input",
        )
        self.assertEqual(
            request["body"],
            {
                "clientSubmitId": "inv-1",
                "content": [{"type": "text", "text": "Implement the fix"}],
                "displayPrompt": "Implement the fix",
            },
        )

    def test_cancel_and_interactive_use_exact_paths(self):
        self.client.cancel_turn("ws", "session", "turn")
        self.client.submit_interactive(
            "ws",
            "session",
            "req",
            {"decision": "approve"},
        )
        self.assertEqual(
            Handler.requests[-2]["path"],
            "/v1/workspaces/ws/agent-sessions/session/turns/turn/cancel",
        )
        self.assertEqual(
            Handler.requests[-1]["path"],
            "/v1/workspaces/ws/agent-sessions/session/interactives/req/response",
        )
        self.assertEqual(Handler.requests[-1]["body"], {"decision": "approve"})

    def test_http_error_does_not_leak_token_or_body(self):
        with self.assertRaises(TuttiProtocolError) as ctx:
            self.client._request("GET", "/error")
        message = str(ctx.exception)
        self.assertNotIn("top-secret-token", message)
        self.assertNotIn("secret response should not leak", message)
        self.assertIn("HTTP 500", message)


if __name__ == "__main__":
    unittest.main()
