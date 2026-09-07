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
            "protocol_version": "1.0",
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

    def test_request_requires_blinded_ids_and_no_extra_fields(self):
        valid = self.request()
        self.assertEqual(adapter.validate_request(valid), valid)
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

    def test_jsonl_parser_uses_observed_skill_invocation_as_trace(self):
        payload = json.dumps({"output": "Framework answer", "metadata": {"risk": "L3"}})
        stdout = "\n".join([
            json.dumps({"type": "session.start", "data": {"id": "x"}}),
            json.dumps({
                "type": "assistant.message",
                "data": {"content": "", "toolRequests": [{"toolCallId": "1", "name": "skill", "arguments": {}}]},
            }),
            json.dumps({
                "type": "skill.invoked",
                "data": {"name": "impact-analysis", "path": ".github/skills/impact-analysis/SKILL.md"},
            }),
            json.dumps({
                "type": "assistant.message",
                "data": {"content": f"```json\n{payload}\n```", "toolRequests": []},
            }),
            json.dumps({"type": "result", "data": {"ok": True}}),
        ])
        self.assertEqual(
            adapter.parse_copilot_jsonl(stdout),
            {"output": "Framework answer", "metadata": {"risk": "L3"}, "trace": [{"type": "tool", "name": "impact-analysis"}]},
        )

    def test_jsonl_parser_rejects_ambiguous_final_answer_and_invalid_jsonl(self):
        payload = json.dumps({"output": "answer", "metadata": {"risk": "L1"}})
        duplicated = "\n".join([
            json.dumps({"type": "assistant.message", "data": {"content": payload, "toolRequests": []}}),
            json.dumps({"type": "assistant.message", "data": {"content": payload, "toolRequests": []}}),
        ])
        with self.assertRaisesRegex(adapter.CopilotExactTargetError, "exactly one"):
            adapter.parse_copilot_jsonl(duplicated)
        with self.assertRaisesRegex(adapter.CopilotExactTargetError, "invalid JSON"):
            adapter.parse_copilot_jsonl("not-json")

    def test_child_environment_drops_unrelated_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            with mock.patch.dict(
                os.environ,
                {"PATH": "/safe/bin", "GITHUB_TOKEN": "token-value", "AWS_SECRET_ACCESS_KEY": "must-not-leak", "DATABASE_PASSWORD": "must-not-leak", "GH_TOKEN": "must-not-leak"},
                clear=True,
            ):
                env = adapter._copilot_environment(workspace)
            self.assertEqual(env["PATH"], "/safe/bin")
            self.assertEqual(env["COPILOT_GITHUB_TOKEN"], "token-value")
            self.assertNotIn("AWS_SECRET_ACCESS_KEY", env)
            self.assertNotIn("DATABASE_PASSWORD", env)
            self.assertNotIn("GH_TOKEN", env)
            self.assertEqual(env["GITHUB_COPILOT_PROMPT_MODE_EXTENSIONS"], "false")
            self.assertEqual(env["GITHUB_COPILOT_PROMPT_MODE_REPO_HOOKS"], "false")
            self.assertEqual(env["GITHUB_COPILOT_PROMPT_MODE_WORKSPACE_MCP"], "false")

    def test_invoke_copilot_direct_mode_has_no_effective_model_tools(self):
        payload = json.dumps({"output": "answer", "metadata": {"risk": "L1"}})
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps({"type": "assistant.message", "data": {"content": payload, "toolRequests": []}}) + "\n", stderr="")
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            with mock.patch.dict(os.environ, {"PATH": "/safe/bin", "GITHUB_TOKEN": "token"}, clear=True):
                with mock.patch.object(adapter.subprocess, "run", return_value=completed) as run:
                    result = adapter.invoke_copilot("PROMPT", model="gpt-5.4", copilot_bin="copilot", timeout=30, workspace=workspace, routing_mode=False)
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
            args=[], returncode=0,
            stdout="\n".join([
                json.dumps({"type": "skill.invoked", "data": {"name": "impact-analysis", "path": ".github/skills/impact-analysis/SKILL.md"}}),
                json.dumps({"type": "assistant.message", "data": {"content": payload, "toolRequests": []}}),
            ]) + "\n",
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            with mock.patch.dict(os.environ, {"PATH": "/safe/bin", "GITHUB_TOKEN": "token"}, clear=True):
                with mock.patch.object(adapter.subprocess, "run", return_value=completed) as run:
                    result = adapter.invoke_copilot("PROMPT", model="gpt-5.4", copilot_bin="copilot", timeout=30, workspace=workspace, routing_mode=True)
        self.assertEqual(result["trace"], [{"type": "tool", "name": "impact-analysis"}])
        args = run.call_args.args[0]
        self.assertIn("--available-tools=skill", args)
        self.assertIn("--no-ask-user", args)

    def test_run_adapter_routing_mode_does_not_inject_skill_text_or_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root)
            request = self.request("skills/impact-analysis")
            def fake_invoke(prompt, *, model, copilot_bin, timeout, workspace, routing_mode):
                self.assertTrue(routing_mode)
                self.assertTrue((workspace / ".github" / "skills" / "impact-analysis" / "SKILL.md").is_file())
                self.assertNotIn("IMPACT POLICY", prompt)
                self.assertNotIn(request["suite_id"], prompt)
                self.assertNotIn(request["case_id"], prompt)
                return {"output": "analysis", "metadata": {"risk": "L3"}, "trace": [{"type": "tool", "name": "impact-analysis"}]}
            with mock.patch.object(adapter, "invoke_copilot", side_effect=fake_invoke):
                result = adapter.run_adapter(request, target_root=root, model="gpt-5.4", copilot_bin="copilot", timeout=30)
            self.assertEqual(result["trace"], [{"type": "tool", "name": "impact-analysis"}])

    def test_run_adapter_direct_mode_injects_only_canonical_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_root(root)
            request = self.request("skills/example")
            def fake_invoke(prompt, *, model, copilot_bin, timeout, workspace, routing_mode):
                self.assertFalse(routing_mode)
                self.assertIn("SKILL POLICY", prompt)
                self.assertIn("SPEC CONTRACT", prompt)
                self.assertNotIn("FORBIDDEN CASE HINT", prompt)
                self.assertNotIn(request["suite_id"], prompt)
                self.assertNotIn(request["case_id"], prompt)
                return {"output": "answer", "metadata": {"risk": "L1"}, "trace": []}
            with mock.patch.object(adapter, "invoke_copilot", side_effect=fake_invoke):
                result = adapter.run_adapter(request, target_root=root, model="gpt-5.4", copilot_bin="copilot", timeout=30)
            self.assertEqual(result["trace"], [])


if __name__ == "__main__":
    unittest.main()
