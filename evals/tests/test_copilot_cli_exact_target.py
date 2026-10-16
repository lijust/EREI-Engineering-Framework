import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from evals.adapters import copilot_cli_exact_target as adapter


class CopilotCliExactTargetTests(unittest.TestCase):
    def request(self, artifact="skills/example"):
        return {
            "protocol_version": "2.0",
            "suite_id": "blind-suite-0123456789abcdef",
            "case_id": "blind-case-fedcba9876543210",
            "artifact": artifact,
            "input": {"prompt": "Apply the policy."},
            "context": {"known": "value"},
        }

    def make_root(self, root: Path):
        skill = root / "skills" / "example"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("SKILL POLICY\n", encoding="utf-8")
        (skill / "SPEC.md").write_text("SPEC CONTRACT\n", encoding="utf-8")
        (skill / "CASES.md").write_text("FORBIDDEN CASE HINT\n", encoding="utf-8")
        evals = skill / "evals"
        evals.mkdir()
        (evals / "secret.eval.json").write_text('{"expected":"LEAK"}', encoding="utf-8")
        impact = root / "skills" / "impact-analysis"
        impact.mkdir(parents=True)
        (impact / "SKILL.md").write_text(
            "---\nname: impact-analysis\ndescription: Analyze impact when relevant.\n---\nIMPACT POLICY\n",
            encoding="utf-8",
        )
        workflow = root / "workflows" / "review"
        workflow.mkdir(parents=True)
        (workflow / "WORKFLOW.md").write_text("WORKFLOW POLICY\n", encoding="utf-8")
        schemas = root / "schemas"
        schemas.mkdir()
        (schemas / "CONTRACT.md").write_text("SCHEMA CONTRACT\n", encoding="utf-8")

    def final_event(self, output="Framework answer", risk="L3"):
        payload = json.dumps({"output": output, "metadata": {"risk": risk}})
        return {"type": "assistant.message", "data": {"content": payload, "toolRequests": []}}

    def skill_events(self, *, name="impact-analysis", path=".github/skills/impact-analysis/SKILL.md", success=True):
        return [
            {
                "type": "assistant.message",
                "data": {
                    "content": "",
                    "toolRequests": [{"toolCallId": "skill-1", "name": "skill", "arguments": {}}],
                },
            },
            {
                "type": "tool.execution_start",
                "data": {"toolCallId": "skill-1", "toolName": "skill", "arguments": {}},
            },
            {"type": "skill.invoked", "data": {"name": name, "path": path, "content": "POLICY"}},
            {
                "type": "tool.execution_complete",
                "data": {"toolCallId": "skill-1", "success": success},
            },
        ]

    def _create_staged_workspace(self, root: Path, skill_name="impact-analysis") -> Path:
        staged = root / ".github" / "skills" / skill_name
        staged.mkdir(parents=True, exist_ok=True)
        (staged / "SKILL.md").write_text("POLICY", encoding="utf-8")
        return root

    def _parse_routing_events(self, text: str, skill_name="impact-analysis"):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = self._create_staged_workspace(Path(tmp), skill_name)
            return adapter.parse_copilot_jsonl(
                text, allowed_skill_names={skill_name}, workspace=workspace
            )

    def test_request_requires_blinded_ids_and_no_extra_fields(self):
        valid = self.request()
        self.assertEqual(adapter.validate_request(valid), valid)
        with self.assertRaisesRegex(adapter.CopilotExactTargetError, "protocol_version"):
            adapter.validate_request(dict(valid, protocol_version="1.0"))
        bad = dict(valid, tags=["L3"])
        with self.assertRaisesRegex(adapter.CopilotExactTargetError, "exactly"):
            adapter.validate_request(bad)
        bad = dict(valid, suite_id="impact-analysis-v1")
        with self.assertRaisesRegex(adapter.CopilotExactTargetError, "blinded"):
            adapter.validate_request(bad)

    def test_artifact_resolution_loads_only_canonical_contract_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root)
            resolved = adapter.resolve_artifact(root, "skills/example")
            paths = [path for path, _ in resolved]
            text = "\n".join(content for _, content in resolved)
            self.assertEqual(paths, ["skills/example/SKILL.md", "skills/example/SPEC.md"])
            self.assertIn("SKILL POLICY", text)
            self.assertIn("SPEC CONTRACT", text)
            self.assertNotIn("FORBIDDEN CASE HINT", text)
            self.assertNotIn("LEAK", text)

    def test_artifact_resolution_supports_composite_and_schema_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root)
            composite = adapter.resolve_artifact(root, "skills/example + workflows/review")
            self.assertEqual(
                [path for path, _ in composite],
                ["skills/example/SKILL.md", "skills/example/SPEC.md", "workflows/review/WORKFLOW.md"],
            )
            schema = adapter.resolve_artifact(root, "schemas/CONTRACT.md")
            self.assertEqual(schema, [("schemas/CONTRACT.md", "SCHEMA CONTRACT\n")])

    def test_artifact_resolution_blocks_eval_content_and_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root)
            with self.assertRaisesRegex(adapter.CopilotExactTargetError, "forbidden"):
                adapter.resolve_artifact(root, "skills/example/evals/secret.eval.json")
            with self.assertRaises(adapter.CopilotExactTargetError):
                adapter.resolve_artifact(root, "skills/../schemas/CONTRACT.md")
            with self.assertRaisesRegex(adapter.CopilotExactTargetError, "allowed Framework families"):
                adapter.resolve_artifact(root, "evals/cases/impact-analysis.eval.json")

    def test_direct_prompt_contains_artifact_input_context_but_no_transport_identity(self):
        prompt = adapter.build_direct_prompt(
            [("skills/example/SKILL.md", "POLICY")],
            {"prompt": "USER INPUT"},
            {"context": "VALUE"},
        )
        self.assertIn("POLICY", prompt)
        self.assertIn("USER INPUT", prompt)
        self.assertIn("VALUE", prompt)
        self.assertNotIn("blind-suite", prompt)
        self.assertNotIn("blind-case", prompt)
        self.assertNotIn("expectations", prompt.lower())
        self.assertNotIn("tags", prompt.lower())

    def test_routing_skill_stages_only_exact_skill_contract(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as work:
            root = Path(tmp)
            workspace = Path(work)
            self.make_root(root)
            name = adapter.stage_routing_skill(root, workspace, "skills/impact-analysis")
            self.assertEqual(name, "impact-analysis")
            staged = workspace / ".github" / "skills" / "impact-analysis"
            self.assertEqual(
                (staged / "SKILL.md").read_text(encoding="utf-8"),
                (root / "skills" / "impact-analysis" / "SKILL.md").read_text(encoding="utf-8"),
            )
            self.assertEqual([p.name for p in staged.iterdir()], ["SKILL.md"])
            with self.assertRaisesRegex(adapter.CopilotExactTargetError, "routing-sensitive"):
                adapter.stage_routing_skill(root, workspace, "skills/impact-analysis + workflows/review")

    def test_jsonl_parser_uses_authoritative_skill_invocation_as_trace(self):
        stdout = "\n".join(json.dumps(event) for event in [
            {"type": "session.start", "data": {"id": "x"}},
            *self.skill_events(),
            self.final_event(),
        ])
        self.assertEqual(
            self._parse_routing_events(stdout),
            {
                "output": "Framework answer",
                "metadata": {"risk": "L3"},
                "trace": [{"type": "tool", "name": "impact-analysis"}],
            },
        )

    def test_jsonl_parser_rejects_skill_activity_without_named_invocation_event(self):
        events = self.skill_events()
        events = [event for event in events if event["type"] != "skill.invoked"]
        stdout = "\n".join(json.dumps(event) for event in [*events, self.final_event()])
        with self.assertRaisesRegex(adapter.CopilotExactTargetError, "authoritative skill.invoked"):
            self._parse_routing_events(stdout)

    def test_jsonl_parser_rejects_wrong_skill_name_or_path(self):
        wrong_name = "\n".join(json.dumps(event) for event in [
            *self.skill_events(name="other-skill", path=".github/skills/other-skill/SKILL.md"),
            self.final_event(),
        ])
        with self.assertRaisesRegex(adapter.CopilotExactTargetError, "outside staged routing boundary"):
            self._parse_routing_events(wrong_name)

        wrong_path = "\n".join(json.dumps(event) for event in [
            *self.skill_events(path="/tmp/other/impact-analysis/SKILL.md"),
            self.final_event(),
        ])
        with self.assertRaisesRegex(adapter.CopilotExactTargetError, "does not resolve to the staged"):
            self._parse_routing_events(wrong_path)

    def test_jsonl_parser_rejects_failed_skill_completion_after_invocation(self):
        stdout = "\n".join(json.dumps(event) for event in [
            *self.skill_events(success=False),
            self.final_event(),
        ])
        with self.assertRaisesRegex(adapter.CopilotExactTargetError, "execution failed"):
            self._parse_routing_events(stdout)

    def test_jsonl_parser_rejects_skill_invocation_outside_routing_mode(self):
        stdout = "\n".join(json.dumps(event) for event in [
            {"type": "skill.invoked", "data": {
                "name": "impact-analysis",
                "path": ".github/skills/impact-analysis/SKILL.md",
                "content": "POLICY",
            }},
            self.final_event(output="answer", risk="L1"),
        ])
        with self.assertRaisesRegex(adapter.CopilotExactTargetError, "outside staged routing boundary"):
            adapter.parse_copilot_jsonl(stdout, allowed_skill_names=set())

    def test_jsonl_parser_rejects_request_start_correlation_mismatch(self):
        events = self.skill_events()
        for event in events:
            if event["type"] == "tool.execution_start":
                event["data"]["toolCallId"] = "other-id"
        stdout = "\n".join(json.dumps(event) for event in [*events, self.final_event()])
        with self.assertRaisesRegex(adapter.CopilotExactTargetError, "request/start correlation"):
            self._parse_routing_events(stdout)

    def test_jsonl_parser_rejects_ambiguous_final_answer_and_invalid_jsonl(self):
        payload = json.dumps({"output": "answer", "metadata": {"risk": "L1"}})
        duplicated = "\n".join([
            json.dumps({"type": "assistant.message", "data": {"content": payload, "toolRequests": []}}),
            json.dumps({"type": "assistant.message", "data": {"content": payload, "toolRequests": []}}),
        ])
        with self.assertRaisesRegex(adapter.CopilotExactTargetError, "exactly one"):
            adapter.parse_copilot_jsonl(duplicated, allowed_skill_names=set())
        with self.assertRaisesRegex(adapter.CopilotExactTargetError, "invalid JSON"):
            adapter.parse_copilot_jsonl("not-json", allowed_skill_names=set())

    def test_rejects_tools_not_in_active_mode_allowlist(self):
        final = self.final_event(output="ok", risk="L1")
        for name in ("shell", "write", "read", "ask_user"):
            for event in (
                {"type": "assistant.message", "data": {
                    "content": "", "toolRequests": [{
                        "toolCallId": "tool-1", "name": name, "arguments": {}
                    }]
                }},
                {"type": "tool.execution_start", "data": {
                    "toolCallId": "tool-1", "toolName": name, "arguments": {}
                }},
            ):
                with self.subTest(tool=name, event=event["type"]):
                    stdout = "\n".join(json.dumps(v) for v in [event, final])
                    with self.assertRaisesRegex(adapter.CopilotExactTargetError, "unauthorized Copilot tool"):
                        self._parse_routing_events(stdout)
                    with self.assertRaisesRegex(adapter.CopilotExactTargetError, "unauthorized Copilot tool"):
                        adapter.parse_copilot_jsonl(stdout, allowed_skill_names=set())

    def test_skill_invocation_cannot_claim_staged_skill_from_other_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = self._create_staged_workspace(Path(tmp) / "legitimate")
            other = self._create_staged_workspace(Path(tmp) / "untrusted")
            for path in (
                (other / ".github/skills/impact-analysis/SKILL.md").as_posix(),
                "/untrusted/.github/skills/impact-analysis/SKILL.md",
                "../.github/skills/impact-analysis/SKILL.md",
            ):
                with self.subTest(path=path):
                    records = [*self.skill_events(path=path), self.final_event()]
                    stdout = "\n".join(json.dumps(v) for v in records)
                    with self.assertRaisesRegex(adapter.CopilotExactTargetError, "does not resolve to the staged"):
                        adapter.parse_copilot_jsonl(stdout, allowed_skill_names={"impact-analysis"}, workspace=workspace)

    def test_skill_invocation_requires_real_staged_workspace(self):
        stdout = "\n".join(json.dumps(v) for v in [*self.skill_events(), self.final_event()])
        with self.assertRaisesRegex(adapter.CopilotExactTargetError, "authenticated staged workspace"):
            adapter.parse_copilot_jsonl(stdout, allowed_skill_names={"impact-analysis"})

    def test_child_environment_requires_dedicated_pat_and_drops_unrelated_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            with mock.patch.dict(
                os.environ,
                {
                    "PATH": "/safe/bin",
                    "COPILOT_GITHUB_TOKEN": "dedicated-token",
                    "GITHUB_TOKEN": "must-not-be-used",
                    "AWS_SECRET_ACCESS_KEY": "must-not-leak",
                    "DATABASE_PASSWORD": "must-not-leak",
                    "GH_TOKEN": "must-not-leak",
                },
                clear=True,
            ):
                env = adapter._copilot_environment(workspace)
            self.assertEqual(env["PATH"], "/safe/bin")
            self.assertEqual(env["COPILOT_GITHUB_TOKEN"], "dedicated-token")
            self.assertNotIn("GITHUB_TOKEN", env)
            self.assertNotIn("AWS_SECRET_ACCESS_KEY", env)
            self.assertNotIn("DATABASE_PASSWORD", env)
            self.assertNotIn("GH_TOKEN", env)
            self.assertEqual(env["GITHUB_COPILOT_PROMPT_MODE_EXTENSIONS"], "false")
            self.assertEqual(env["GITHUB_COPILOT_PROMPT_MODE_REPO_HOOKS"], "false")
            self.assertEqual(env["GITHUB_COPILOT_PROMPT_MODE_WORKSPACE_MCP"], "false")

    def test_child_environment_rejects_github_token_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"PATH": "/safe/bin", "GITHUB_TOKEN": "ordinary-token"}, clear=True):
                with self.assertRaisesRegex(adapter.CopilotExactTargetError, "fallback is forbidden"):
                    adapter._copilot_environment(Path(tmp))

    def test_invoke_copilot_direct_mode_has_no_effective_model_tools(self):
        payload = json.dumps({"output": "answer", "metadata": {"risk": "L1"}})
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps({"type": "assistant.message", "data": {"content": payload, "toolRequests": []}}) + "\n",
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            with mock.patch.dict(os.environ, {"PATH": "/safe/bin", "COPILOT_GITHUB_TOKEN": "token"}, clear=True):
                with mock.patch.object(adapter.subprocess, "run", return_value=completed) as run:
                    result = adapter.invoke_copilot(
                        "PROMPT", model="gpt-5.4", copilot_bin="copilot", timeout=30,
                        workspace=workspace, expected_skill=None,
                    )
        self.assertEqual(result, {"output": "answer", "metadata": {"risk": "L1"}, "trace": []})
        args = run.call_args.args[0]
        self.assertIn("--available-tools=ask_user", args)
        self.assertIn("--no-ask-user", args)
        self.assertIn("--no-custom-instructions", args)
        self.assertIn("--disable-builtin-mcps", args)
        self.assertNotIn("--allow-all", args)
        self.assertNotIn("--yolo", args)
        self.assertEqual(args[args.index("-p") + 1], "PROMPT")
        self.assertEqual(run.call_args.kwargs["env"]["COPILOT_GITHUB_TOKEN"], "token")

    def test_invoke_copilot_routing_mode_exposes_only_skill_tool(self):
        payload = json.dumps({"output": "analysis", "metadata": {"risk": "L3"}})
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="\n".join(json.dumps(event) for event in [
                *self.skill_events(),
                {"type": "assistant.message", "data": {"content": payload, "toolRequests": []}},
            ]) + "\n",
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            workspace = self._create_staged_workspace(Path(tmp))
            with mock.patch.dict(os.environ, {"PATH": "/safe/bin", "COPILOT_GITHUB_TOKEN": "token"}, clear=True):
                with mock.patch.object(adapter.subprocess, "run", return_value=completed) as run:
                    result = adapter.invoke_copilot(
                        "PROMPT", model="gpt-5.4", copilot_bin="copilot", timeout=30,
                        workspace=workspace, expected_skill="impact-analysis",
                    )
        self.assertEqual(result["trace"], [{"type": "tool", "name": "impact-analysis"}])
        args = run.call_args.args[0]
        self.assertIn("--available-tools=skill", args)
        self.assertIn("--no-ask-user", args)

    def test_run_adapter_routing_mode_does_not_inject_skill_text_or_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root)
            request = self.request("skills/impact-analysis")

            def fake_invoke(prompt, *, model, copilot_bin, timeout, workspace, expected_skill):
                self.assertEqual(expected_skill, "impact-analysis")
                self.assertTrue((workspace / ".github" / "skills" / "impact-analysis" / "SKILL.md").is_file())
                self.assertNotIn("IMPACT POLICY", prompt)
                self.assertNotIn(request["suite_id"], prompt)
                self.assertNotIn(request["case_id"], prompt)
                return {
                    "output": "analysis",
                    "metadata": {"risk": "L3"},
                    "trace": [{"type": "tool", "name": "impact-analysis"}],
                }

            with mock.patch.object(adapter, "invoke_copilot", side_effect=fake_invoke):
                result = adapter.run_adapter(
                    request, target_root=root, model="gpt-5.4", copilot_bin="copilot", timeout=30
                )
            self.assertEqual(result["trace"], [{"type": "tool", "name": "impact-analysis"}])

    def test_run_adapter_direct_mode_injects_only_canonical_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root)
            request = self.request("skills/example")

            def fake_invoke(prompt, *, model, copilot_bin, timeout, workspace, expected_skill):
                self.assertIsNone(expected_skill)
                self.assertIn("SKILL POLICY", prompt)
                self.assertIn("SPEC CONTRACT", prompt)
                self.assertNotIn("FORBIDDEN CASE HINT", prompt)
                self.assertNotIn(request["suite_id"], prompt)
                self.assertNotIn(request["case_id"], prompt)
                return {"output": "answer", "metadata": {"risk": "L1"}, "trace": []}

            with mock.patch.object(adapter, "invoke_copilot", side_effect=fake_invoke):
                result = adapter.run_adapter(
                    request, target_root=root, model="gpt-5.4", copilot_bin="copilot", timeout=30
                )
            self.assertEqual(result["trace"], [])

    def test_skill_event_transport_probe_requires_exact_authoritative_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root)

            def fake_invoke(prompt, *, model, copilot_bin, timeout, workspace, expected_skill):
                self.assertEqual(expected_skill, "impact-analysis")
                self.assertNotIn("impact-analysis", prompt.lower())
                self.assertTrue((workspace / ".github" / "skills" / "impact-analysis" / "SKILL.md").is_file())
                return {
                    "output": "skill telemetry probe complete",
                    "metadata": {"risk": "L0"},
                    "trace": [{"type": "tool", "name": "impact-analysis"}],
                }

            with mock.patch.object(adapter, "invoke_copilot", side_effect=fake_invoke):
                name = adapter.probe_skill_event_transport(
                    target_root=root,
                    artifact_declaration="skills/impact-analysis",
                    model="gpt-5.4",
                    copilot_bin="copilot",
                    timeout=30,
                )
            self.assertEqual(name, "impact-analysis")

    def test_skill_event_transport_probe_fails_without_named_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root)
            with mock.patch.object(
                adapter,
                "invoke_copilot",
                return_value={"output": "probe", "metadata": {"risk": "L0"}, "trace": []},
            ):
                with self.assertRaisesRegex(adapter.CopilotExactTargetError, "did not observe exactly one"):
                    adapter.probe_skill_event_transport(
                        target_root=root,
                        artifact_declaration="skills/impact-analysis",
                        model="gpt-5.4",
                        copilot_bin="copilot",
                        timeout=30,
                    )


if __name__ == "__main__":
    unittest.main()
