#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, tempfile
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = "1.0"
DEFAULT_MODEL = "gpt-5.4"
MAX_ARTIFACT_BYTES = 131072
ALLOWED_PREFIXES = ("skills/", "workflows/", "schemas/")
CANONICAL_DIRECTORY_FILES = ("SKILL.md", "SPEC.md", "WORKFLOW.md", "CONTRACT.md")
OPAQUE_ID_RE = re.compile(r"^blind-(suite|case)-[a-f0-9]{16}$")
RISK_LEVELS = {"L0", "L1", "L2", "L3"}
SAFE_INHERITED_ENV = {
    "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC",
    "TMP", "TEMP", "TMPDIR", "LANG", "LC_ALL",
    "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY",
    "SSL_CERT_FILE", "SSL_CERT_DIR", "NODE_EXTRA_CA_CERTS",
}
ROUTING_SKILLS = {"skills/impact-analysis": "impact-analysis"}

class CopilotExactTargetError(RuntimeError):
    pass

def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CopilotExactTargetError(f"{label} must be an object")
    return value

def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CopilotExactTargetError(f"{label} must be a non-empty string")
    return value.strip()

def validate_request(value: Any) -> dict[str, Any]:
    request = _object(value, "request")
    required = {"protocol_version", "suite_id", "case_id", "artifact", "input", "context"}
    if set(request) != required:
        raise CopilotExactTargetError("request must contain exactly protocol_version/suite_id/case_id/artifact/input/context")
    if request["protocol_version"] != PROTOCOL_VERSION:
        raise CopilotExactTargetError(f"protocol_version must be {PROTOCOL_VERSION}")
    suite_id = _text(request["suite_id"], "suite_id")
    case_id = _text(request["case_id"], "case_id")
    if not OPAQUE_ID_RE.fullmatch(suite_id) or not OPAQUE_ID_RE.fullmatch(case_id):
        raise CopilotExactTargetError("exact-target adapter requires blinded suite/case IDs")
    _text(request["artifact"], "artifact")
    _object(request["input"], "input")
    _object(request["context"], "context")
    return request

def _safe_component(root: Path, raw: str) -> Path:
    raw = _text(raw, "artifact component")
    normalized = raw.replace("\\", "/")
    if not normalized.startswith(ALLOWED_PREFIXES):
        raise CopilotExactTargetError(f"artifact path outside allowed Framework families: {raw}")
    relative = Path(normalized)
    if relative.is_absolute() or ".." in relative.parts or "." in relative.parts:
        raise CopilotExactTargetError(f"unsafe artifact path: {raw}")
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise CopilotExactTargetError(f"artifact escapes target root: {raw}") from exc
    return candidate

def _read_utf8(path: Path, root: Path) -> str:
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root.resolve())
    except (OSError, ValueError) as exc:
        raise CopilotExactTargetError(f"invalid artifact file: {path}") from exc
    if resolved.suffix.lower() != ".md":
        raise CopilotExactTargetError(f"only Markdown Framework artifacts are allowed: {path}")
    lowered_parts = {part.lower() for part in resolved.relative_to(root.resolve()).parts}
    if lowered_parts & {"evals", "tests", "fixtures", ".github"}:
        raise CopilotExactTargetError(f"evaluation/test content is forbidden from model context: {path}")
    try:
        return resolved.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise CopilotExactTargetError(f"unable to read artifact file: {path}") from exc

def resolve_artifact(root: Path, declaration: str, *, max_bytes: int = MAX_ARTIFACT_BYTES) -> list[tuple[str, str]]:
    root = root.resolve()
    if not root.is_dir():
        raise CopilotExactTargetError("target root must be an existing directory")
    components = [_text(item, "artifact component") for item in declaration.split(" + ")]
    resolved: list[tuple[str, str]] = []
    total = 0
    seen: set[str] = set()
    for raw in components:
        candidate = _safe_component(root, raw)
        if candidate.is_file():
            files = [candidate]
        elif candidate.is_dir():
            files = [candidate / name for name in CANONICAL_DIRECTORY_FILES if (candidate / name).is_file()]
            if not files:
                raise CopilotExactTargetError(f"artifact directory has no canonical contract files: {raw}")
        else:
            raise CopilotExactTargetError(f"artifact does not exist: {raw}")
        for path in files:
            rel = path.resolve().relative_to(root).as_posix()
            if rel in seen:
                continue
            text = _read_utf8(path, root)
            total += len(text.encode("utf-8"))
            if total > max_bytes:
                raise CopilotExactTargetError(f"artifact context exceeds {max_bytes} bytes")
            resolved.append((rel, text))
            seen.add(rel)
    if not resolved:
        raise CopilotExactTargetError("artifact resolution produced no context")
    return resolved

def _routing_skill_name(artifact_declaration: str) -> str | None:
    components = [item.strip().replace("\\", "/") for item in artifact_declaration.split(" + ")]
    matches = [ROUTING_SKILLS[item] for item in components if item in ROUTING_SKILLS]
    if not matches:
        return None
    if len(matches) != 1 or len(components) != 1:
        raise CopilotExactTargetError("routing-sensitive exact-target artifacts must be declared as one canonical skill")
    return matches[0]

def stage_routing_skill(target_root: Path, workspace: Path, artifact_declaration: str) -> str:
    skill_name = _routing_skill_name(artifact_declaration)
    if skill_name is None:
        raise CopilotExactTargetError("artifact is not configured for skill-routing mode")
    source = _safe_component(target_root.resolve(), artifact_declaration)
    if not source.is_dir():
        raise CopilotExactTargetError("routing skill artifact must be a directory")
    skill_text = _read_utf8(source / "SKILL.md", target_root.resolve())
    target_dir = workspace / ".github" / "skills" / skill_name
    target_dir.mkdir(parents=True, exist_ok=False)
    (target_dir / "SKILL.md").write_text(skill_text, encoding="utf-8")
    return skill_name

def build_direct_prompt(artifacts: list[tuple[str, str]], case_input: dict[str, Any], context: dict[str, Any]) -> str:
    artifact_text = "\n\n".join(
        f"--- BEGIN FRAMEWORK ARTIFACT: {path} ---\n{text}\n--- END FRAMEWORK ARTIFACT: {path} ---"
        for path, text in artifacts
    )
    return (
        "You are evaluating the behavior required by the supplied EREI Engineering Framework artifact.\n"
        "Use only the supplied Framework artifact, INPUT, and CONTEXT. Do not use outside knowledge, web access, repository files, hidden assumptions, or unstated scorer criteria.\n"
        "Answer the engineering request as the Framework artifact requires, preserving its exact policy/decision terminology when applicable. State relevant boundaries and required next action.\n"
        "Return exactly one JSON object and no markdown or commentary, with this shape:\n"
        '{"output":"concise Framework-grounded answer","metadata":{"risk":"L0|L1|L2|L3"}}\n'
        "Classify risk conservatively from the artifact and request. Do not expose private chain-of-thought.\n\n"
        f"{artifact_text}\n\nINPUT:\n{json.dumps(case_input, sort_keys=True, ensure_ascii=False)}\n\n"
        f"CONTEXT:\n{json.dumps(context, sort_keys=True, ensure_ascii=False)}\n"
    )

def build_routing_prompt(case_input: dict[str, Any], context: dict[str, Any]) -> str:
    return (
        "Evaluate the engineering request under the EREI Engineering Framework.\n"
        "A project skill may be available in the current workspace. Decide from the request itself whether any available skill is relevant; do not invoke a skill merely because it exists. Use no outside knowledge, web access, hidden assumptions, or unstated scorer criteria.\n"
        "If a skill is relevant, invoke it through the skill tool before answering. If no skill is relevant, answer proportionally without inventing a skill invocation.\n"
        "Return exactly one JSON object and no markdown or commentary, with this shape:\n"
        '{"output":"concise Framework-grounded answer","metadata":{"risk":"L0|L1|L2|L3"}}\n'
        "Do not expose private chain-of-thought.\n\n"
        f"INPUT:\n{json.dumps(case_input, sort_keys=True, ensure_ascii=False)}\n\n"
        f"CONTEXT:\n{json.dumps(context, sort_keys=True, ensure_ascii=False)}\n"
    )

def _parse_final_json(content: str) -> dict[str, Any]:
    fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", content, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        content = fence.group(1).strip()
    try:
        value = json.loads(content)
    except json.JSONDecodeError as exc:
        raise CopilotExactTargetError("Copilot assistant content is not a JSON object") from exc
    if not isinstance(value, dict) or set(value) != {"output", "metadata"}:
        raise CopilotExactTargetError("Copilot response must contain exactly output and metadata")
    output = _text(value["output"], "Copilot output")
    metadata = _object(value["metadata"], "Copilot metadata")
    if set(metadata) != {"risk"} or metadata.get("risk") not in RISK_LEVELS:
        raise CopilotExactTargetError("Copilot metadata must contain exactly risk=L0|L1|L2|L3")
    return {"output": output, "metadata": {"risk": metadata["risk"]}}

def parse_copilot_jsonl(stdout: str) -> dict[str, Any]:
    final_messages: list[str] = []
    invoked_skills: list[str] = []
    for index, raw in enumerate(stdout.splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CopilotExactTargetError(f"Copilot JSONL line {index} is invalid JSON") from exc
        if not isinstance(event, dict):
            raise CopilotExactTargetError(f"Copilot JSONL line {index} must be an object")
        event_type = event.get("type")
        data = event.get("data")
        if event_type == "assistant.message":
            if not isinstance(data, dict):
                raise CopilotExactTargetError("assistant.message event requires object data")
            content = data.get("content")
            if content is not None and not isinstance(content, str):
                raise CopilotExactTargetError("assistant.message data.content must be a string when present")
            tool_requests = data.get("toolRequests", [])
            if tool_requests is not None and not isinstance(tool_requests, list):
                raise CopilotExactTargetError("assistant.message data.toolRequests must be an array")
            if isinstance(content, str) and content.strip() and not tool_requests:
                final_messages.append(content.strip())
        elif event_type == "skill.invoked":
            if not isinstance(data, dict):
                raise CopilotExactTargetError("skill.invoked event requires object data")
            invoked_skills.append(_text(data.get("name"), "skill.invoked name"))
    if len(final_messages) != 1:
        raise CopilotExactTargetError(f"expected exactly one final assistant.message event, got {len(final_messages)}")
    response = _parse_final_json(final_messages[0])
    response["trace"] = [{"type": "tool", "name": name} for name in invoked_skills]
    return response

def _copilot_environment(workspace: Path) -> dict[str, str]:
    source = os.environ
    token = source.get("COPILOT_GITHUB_TOKEN")
    if not token:
        raise CopilotExactTargetError("dedicated COPILOT_GITHUB_TOKEN is required; GITHUB_TOKEN fallback is forbidden")
    env = {key: source[key] for key in SAFE_INHERITED_ENV if key in source}
    env["COPILOT_GITHUB_TOKEN"] = token
    env["HOME"] = str(workspace)
    env["COPILOT_HOME"] = str(workspace / "copilot-home")
    env["COPILOT_CACHE_HOME"] = str(workspace / "copilot-cache")
    env["COPILOT_AUTO_UPDATE"] = "false"
    env["GITHUB_COPILOT_PROMPT_MODE_EXTENSIONS"] = "false"
    env["GITHUB_COPILOT_PROMPT_MODE_REPO_HOOKS"] = "false"
    env["GITHUB_COPILOT_PROMPT_MODE_WORKSPACE_MCP"] = "false"
    return env

def invoke_copilot(prompt: str, *, model: str, copilot_bin: str, timeout: float, workspace: Path, routing_mode: bool) -> dict[str, Any]:
    model = _text(model, "model")
    copilot_bin = _text(copilot_bin, "copilot binary")
    if timeout <= 0:
        raise CopilotExactTargetError("timeout must be > 0")
    available_tools = "skill" if routing_mode else "ask_user"
    args = [
        copilot_bin, "-p", prompt, "--output-format=json", f"--model={model}",
        "--no-ask-user", "--no-auto-update", "--no-custom-instructions",
        "--disable-builtin-mcps", "--no-remote", "--no-remote-export",
        "--no-experimental", "--no-banner", "--no-color",
        f"--available-tools={available_tools}", "-C", str(workspace),
    ]
    try:
        process = subprocess.run(
            args, text=True, capture_output=True, timeout=timeout, check=False,
            env=_copilot_environment(workspace),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CopilotExactTargetError(f"Copilot CLI execution failed: {exc}") from exc
    if process.returncode != 0:
        raise CopilotExactTargetError(f"Copilot CLI exited {process.returncode}: {process.stderr.strip()[:1000]}")
    return parse_copilot_jsonl(process.stdout)

def run_adapter(request: dict[str, Any], *, target_root: Path, model: str, copilot_bin: str, timeout: float) -> dict[str, Any]:
    request = validate_request(request)
    target_root = target_root.resolve()
    routing_skill = _routing_skill_name(request["artifact"])
    with tempfile.TemporaryDirectory(prefix="erei-copilot-exact-target-") as tmp:
        workspace = Path(tmp)
        (workspace / "copilot-home").mkdir()
        (workspace / "copilot-cache").mkdir()
        if routing_skill is not None:
            stage_routing_skill(target_root, workspace, request["artifact"])
            prompt = build_routing_prompt(request["input"], request["context"])
            return invoke_copilot(prompt, model=model, copilot_bin=copilot_bin, timeout=timeout, workspace=workspace, routing_mode=True)
        artifacts = resolve_artifact(target_root, request["artifact"])
        prompt = build_direct_prompt(artifacts, request["input"], request["context"])
        return invoke_copilot(prompt, model=model, copilot_bin=copilot_bin, timeout=timeout, workspace=workspace, routing_mode=False)

def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-root", default=".")
    parser.add_argument("--model", default=os.environ.get("EREI_COPILOT_MODEL", DEFAULT_MODEL))
    parser.add_argument("--copilot-bin", default=os.environ.get("EREI_COPILOT_BIN", "copilot"))
    parser.add_argument("--timeout", type=float, default=240.0)
    args = parser.parse_args(argv)
    try:
        request = json.loads(sys.stdin.read())
        response = run_adapter(request, target_root=Path(args.target_root), model=args.model, copilot_bin=args.copilot_bin, timeout=args.timeout)
    except (json.JSONDecodeError, CopilotExactTargetError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(response, sort_keys=True, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
