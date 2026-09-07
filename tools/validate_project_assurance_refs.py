#!/usr/bin/env python3
"""Fail closed on missing literal repository-local assurance workflow inputs.

The guard intentionally validates only references that can be proven statically:
- literal tests/** or tools/** script arguments executed from a workflow run command;
- literal local-action uses: ./... references.
Dynamic paths are not guessed. They require separate runtime evidence.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path

RUN_RE = re.compile(r"^(?P<indent>\s*)(?:-\s*)?run:\s*(?P<value>.*)$")
USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*[\"']?(?P<path>\./[A-Za-z0-9_./-]+)[\"']?\s*(?:#.*)?$")
SCRIPT_RE = re.compile(r"^(?:\./)?(?:tests|tools)/[A-Za-z0-9_.\-/]+\.(?:js|mjs|cjs|ts|py|ps1|sh)$")
INTERPRETERS = {"node", "nodejs", "python", "python3", "bash", "sh"}
POWERSHELL = {"pwsh", "powershell"}
SHELL_BOUNDARIES = {"&&", "||", ";", "|"}
BLOCK_MARKERS = {"|", "|-", "|+", ">", ">-", ">+"}


class ReferenceError(RuntimeError):
    pass


@dataclass(frozen=True)
class Reference:
    workflow: str
    line: int
    kind: str
    path: str


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _normalize_script(token: str) -> str | None:
    token = token.strip()
    if not SCRIPT_RE.fullmatch(token):
        return None
    return token[2:] if token.startswith("./") else token


def _tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, comments=True, posix=True)
    except ValueError:
        return []


def _script_refs_from_command(command: str) -> set[str]:
    tokens = _tokens(command)
    found: set[str] = set()
    for index, token in enumerate(tokens):
        lower = token.lower()
        if lower in INTERPRETERS:
            cursor = index + 1
            while cursor < len(tokens) and tokens[cursor].startswith("-"):
                cursor += 1
            if cursor < len(tokens):
                path = _normalize_script(tokens[cursor])
                if path:
                    found.add(path)
        elif lower in POWERSHELL:
            for cursor in range(index + 1, len(tokens) - 1):
                if tokens[cursor].lower() in {"-file", "-f"}:
                    path = _normalize_script(tokens[cursor + 1])
                    if path:
                        found.add(path)
                    break
        path = _normalize_script(token)
        if path and (index == 0 or tokens[index - 1] in SHELL_BOUNDARIES):
            found.add(path)
    return found


def _run_fragments(lines: list[str]):
    index = 0
    while index < len(lines):
        line = lines[index]
        match = RUN_RE.match(line)
        if not match:
            index += 1
            continue
        base_indent = len(match.group("indent"))
        value = match.group("value").strip()
        if value in BLOCK_MARKERS:
            cursor = index + 1
            while cursor < len(lines):
                current = lines[cursor]
                if current.strip() and _indent(current) <= base_indent:
                    break
                if current.strip():
                    yield cursor + 1, current.strip()
                cursor += 1
            index = cursor
            continue
        if value:
            yield index + 1, value
        index += 1


def scan_workflow(target: Path, workflow: Path) -> list[Reference]:
    try:
        text = workflow.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReferenceError(f"unable to read workflow {workflow}: {exc}") from exc
    lines = text.splitlines()
    relative_workflow = workflow.relative_to(target).as_posix()
    refs: set[Reference] = set()
    for line_no, command in _run_fragments(lines):
        for path in _script_refs_from_command(command):
            refs.add(Reference(relative_workflow, line_no, "run_script", path))
    for line_no, line in enumerate(lines, start=1):
        match = USES_RE.match(line)
        if match:
            path = match.group("path")[2:]
            refs.add(Reference(relative_workflow, line_no, "local_action", path))
    return sorted(refs, key=lambda item: (item.workflow, item.line, item.kind, item.path))


def scan_target(target: Path) -> dict:
    target = target.resolve()
    if not target.exists() or not target.is_dir():
        raise ReferenceError(f"target does not exist or is not a directory: {target}")
    workflow_dir = target / ".github" / "workflows"
    if not workflow_dir.exists() or not workflow_dir.is_dir():
        raise ReferenceError(f"missing workflow directory: {workflow_dir}")
    workflows = sorted(list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml")))
    references: list[Reference] = []
    for workflow in workflows:
        references.extend(scan_workflow(target, workflow))
    missing = [ref for ref in references if not (target / ref.path).exists()]
    return {
        "target": str(target),
        "workflow_count": len(workflows),
        "reference_count": len(references),
        "missing_count": len(missing),
        "references": [ref.__dict__ for ref in references],
        "missing": [ref.__dict__ for ref in missing],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default=".")
    args = parser.parse_args(argv)
    try:
        result = scan_target(Path(args.target))
    except ReferenceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if result["missing_count"]:
        print(json.dumps({"status": "invalid", **result}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps({"status": "valid", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
