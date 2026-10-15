#!/usr/bin/env python3
"""Create the EREI project-integration skeleton in an existing repository.

V1 deliberately uses only the Python standard library. Existing files are not
replaced unless --force is supplied. Target project code is never executed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


FRAMEWORK_REPOSITORY_DEFAULT = "lijust/EREI-Engineering-Framework"
TEMPLATE_ROOT = Path(__file__).resolve().parents[1] / "templates" / "project-bootstrap"

TEMPLATE_MAP = {
    "AGENTS.md.template": "AGENTS.md",
    ".erei/framework.json.template": ".erei/framework.json",
    ".erei/PROJECT_PROFILE.md.template": ".erei/PROJECT_PROFILE.md",
    ".erei/ARCHITECTURE.md.template": ".erei/ARCHITECTURE.md",
    ".erei/SECURITY_MODEL.md.template": ".erei/SECURITY_MODEL.md",
    ".erei/DATA_MODEL.md.template": ".erei/DATA_MODEL.md",
    ".erei/PERFORMANCE_BUDGET.md.template": ".erei/PERFORMANCE_BUDGET.md",
    ".erei/PROJECT_RULES.md.template": ".erei/PROJECT_RULES.md",
    ".erei/feedback/README.md.template": ".erei/feedback/README.md",
    ".erei/feedback/FRAMEWORK_FEEDBACK.md.template": ".erei/feedback/FRAMEWORK_FEEDBACK.md",
    ".erei/learning/README.md.template": ".erei/learning/README.md",
    ".erei/learning/LEARNING_SUMMARY.md.template": ".erei/learning/LEARNING_SUMMARY.md",
    ".erei/learning/development-outputs/README.md.template": ".erei/learning/development-outputs/README.md",
    "adr/ADR_TEMPLATE.md.template": "adr/ADR_TEMPLATE.md",
}


class BootstrapError(RuntimeError):
    pass


def current_framework_baseline() -> str:
    baseline_path = Path(__file__).resolve().parents[1] / "BASELINE.json"
    try:
        data = json.loads(baseline_path.read_text(encoding="utf-8"))
        value = data.get("baseline")
        if isinstance(value, str) and value:
            return value
    except (OSError, json.JSONDecodeError):
        pass
    return "unknown"


def detect_git_commit() -> str | None:
    framework_root = Path(__file__).resolve().parents[1]
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=framework_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        value = proc.stdout.strip()
        return value or None
    except (OSError, subprocess.SubprocessError):
        return None


def render(text: str, values: dict[str, str]) -> str:
    rendered = text
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    unresolved = [part.split("}}", 1)[0] for part in rendered.split("{{")[1:] if "}}" in part]
    if unresolved:
        raise BootstrapError("Unresolved template variables: " + ", ".join(sorted(set(unresolved))))
    return rendered


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap EREI Framework integration into an existing project repository.")
    parser.add_argument("--target", required=True, help="Path to the target project repository.")
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--project-repository", default="unknown")
    parser.add_argument("--project-lifecycle", choices=["greenfield", "brownfield", "unknown"], default="unknown")
    parser.add_argument("--framework-repository", default=FRAMEWORK_REPOSITORY_DEFAULT)
    parser.add_argument("--framework-baseline", default=current_framework_baseline())
    parser.add_argument("--framework-ref-type", choices=["commit", "tag", "branch"], default="commit")
    parser.add_argument("--framework-ref", help="Pinned Framework ref. If omitted for commit mode, git HEAD is detected.")
    parser.add_argument("--overlay", action="append", default=[], help="Enable a Framework overlay. Repeatable.")
    parser.add_argument("--runtime-adapter", action="append", default=[], help="Declare a runtime adapter preference. Repeatable.")
    parser.add_argument("--dry-run", action="store_true", help="Report planned writes/conflicts without modifying files.")
    parser.add_argument("--force", action="store_true", help="Explicitly replace existing integration files.")
    return parser.parse_args(argv)


def resolve_framework_ref(args: argparse.Namespace) -> str:
    if args.framework_ref:
        return args.framework_ref
    if args.framework_ref_type == "commit":
        detected = detect_git_commit()
        if detected:
            return detected
    raise BootstrapError("A Framework ref is required. Supply --framework-ref or run from a Git checkout where commit HEAD can be detected.")


def build_values(args: argparse.Namespace, framework_ref: str) -> dict[str, str]:
    return {
        "PROJECT_NAME": args.project_name,
        "PROJECT_REPOSITORY": args.project_repository,
        "PROJECT_LIFECYCLE": args.project_lifecycle,
        "FRAMEWORK_REPOSITORY": args.framework_repository,
        "FRAMEWORK_BASELINE": args.framework_baseline,
        "FRAMEWORK_REF_TYPE": args.framework_ref_type,
        "FRAMEWORK_REF": framework_ref,
        "OVERLAYS_JSON": json.dumps(args.overlay, ensure_ascii=False),
        "RUNTIME_ADAPTERS_JSON": json.dumps(args.runtime_adapter, ensure_ascii=False),
    }


def plan(target: Path, values: dict[str, str]) -> list[tuple[Path, str, bool]]:
    if not target.exists() or not target.is_dir():
        raise BootstrapError(f"Target does not exist or is not a directory: {target}")
    planned: list[tuple[Path, str, bool]] = []
    for template_rel, destination_rel in TEMPLATE_MAP.items():
        template_path = TEMPLATE_ROOT / template_rel
        if not template_path.exists():
            raise BootstrapError(f"Missing Framework template: {template_path}")
        destination = target / destination_rel
        content = render(template_path.read_text(encoding="utf-8"), values)
        if destination_rel == ".erei/framework.json":
            json.loads(content)
        planned.append((destination, content, destination.exists()))
    return planned


def execute(planned: list[tuple[Path, str, bool]], *, dry_run: bool, force: bool) -> int:
    conflicts = [path for path, _, exists in planned if exists]

    for path, _, exists in planned:
        action = "REPLACE" if exists else "CREATE"
        prefix = "DRY-RUN " if dry_run else ""
        print(f"{prefix}{action}: {path}")

    if conflicts and not force:
        label = "DRY-RUN CONFLICT" if dry_run else "CONFLICT"
        print(f"{label}: existing files would be replaced; no files were written.", file=sys.stderr)
        for path in conflicts:
            print(f"  - {path}", file=sys.stderr)
        if not dry_run:
            print("Use --dry-run to inspect or --force for explicit replacement.", file=sys.stderr)
        return 3

    if dry_run:
        return 0

    for path, content, _ in planned:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        framework_ref = resolve_framework_ref(args)
        values = build_values(args, framework_ref)
        planned = plan(Path(args.target).resolve(), values)
        return execute(planned, dry_run=args.dry_run, force=args.force)
    except BootstrapError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: rendered framework manifest is invalid JSON: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
