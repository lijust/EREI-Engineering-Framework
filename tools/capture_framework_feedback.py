#!/usr/bin/env python3
"""Capture evidence-backed Framework feedback inside a project repository.

V1 uses only the Python standard library. It never edits Framework Core and never
promotes a suggestion automatically. It appends project-local observations under
`.erei/feedback/` using a small exclusive lock to avoid concurrent lost updates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


FEEDBACK_TYPES = {
    "architecture_gap", "workflow_gap", "skill_gap", "role_gap", "security_gap",
    "data_gap", "verification_gap", "runtime_gap", "performance_gap", "context_gap",
    "integration_gap", "false_positive", "false_negative", "process_friction",
    "missing_pattern", "documentation_gap",
}
SEVERITIES = {"low", "medium", "high", "critical"}
GENERALIZABILITY = {"project_specific", "possible_generic", "likely_generic", "confirmed_multi_project"}
CONFIDENCE = {"low", "medium", "high"}


class FeedbackError(RuntimeError):
    pass


def _nonempty(value: str, label: str) -> str:
    value = value.strip()
    if not value:
        raise FeedbackError(f"{label} must not be empty")
    return value


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _feedback_id(now: datetime) -> str:
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    return f"EFF-{stamp}-{uuid4().hex[:8].upper()}"


def _fingerprint(*, project_repository: str, framework_ref: str, feedback_type: str,
                 source_artifact: str | None, observation: str, suggestion: str) -> str:
    payload = {
        "project_repository": project_repository,
        "framework_ref": framework_ref,
        "type": feedback_type,
        "source_artifact": source_artifact or "",
        "observation": observation,
        "suggestion": suggestion,
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_event(args: argparse.Namespace, *, now: datetime | None = None) -> dict:
    current = now or _utc_now()
    project_repository = _nonempty(args.project_repository, "project repository")
    framework_ref = _nonempty(args.framework_ref, "framework ref")
    observation = _nonempty(args.observation, "observation")
    suggestion = _nonempty(args.suggestion, "suggestion")
    evidence = sorted({_nonempty(item, "evidence") for item in args.evidence})
    if not evidence:
        raise FeedbackError("at least one evidence reference is required")

    source_artifact = args.source_artifact.strip() if args.source_artifact else None
    event = {
        "schema_version": 1,
        "feedback_id": _feedback_id(current),
        "recorded_at": current.isoformat().replace("+00:00", "Z"),
        "project": {"repository": project_repository},
        "framework_ref": framework_ref,
        "type": args.type,
        "severity": args.severity,
        "observation": observation,
        "evidence": evidence,
        "suggestion": suggestion,
        "generalizability": args.generalizability,
        "confidence": args.confidence,
        "status": "new",
        "fingerprint": _fingerprint(
            project_repository=project_repository,
            framework_ref=framework_ref,
            feedback_type=args.type,
            source_artifact=source_artifact,
            observation=observation,
            suggestion=suggestion,
        ),
    }
    if args.project_name and args.project_name.strip():
        event["project"]["name"] = args.project_name.strip()
    if source_artifact:
        event["source_artifact"] = source_artifact
    if args.negative_learning and args.negative_learning.strip():
        event["negative_learning"] = args.negative_learning.strip()
    tags = sorted({tag.strip() for tag in args.tag if tag.strip()})
    if tags:
        event["tags"] = tags
    return event


@contextmanager
def feedback_lock(directory: Path, *, timeout_seconds: float = 5.0):
    lock_path = directory / ".feedback.lock"
    deadline = time.monotonic() + timeout_seconds
    fd = None
    while fd is None:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(fd, f"pid={os.getpid()}\n".encode("utf-8"))
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise FeedbackError(f"feedback ledger is busy: {lock_path}")
            time.sleep(0.05)
    try:
        yield
    finally:
        if fd is not None:
            os.close(fd)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _read_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    events: list[dict] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise FeedbackError(f"invalid JSONL at {path}:{number}: {exc}") from exc
        if not isinstance(value, dict):
            raise FeedbackError(f"feedback event at {path}:{number} is not an object")
        events.append(value)
    return events


def _render_markdown(events: list[dict]) -> str:
    lines = [
        "# Framework Feedback",
        "",
        "Project-local observations about limitations, friction or reusable lessons discovered while using EREI Engineering Framework.",
        "",
        "`FRAMEWORK_FEEDBACK.jsonl` is the machine-readable source of truth. This file is a generated human-readable view.",
        "",
    ]
    if not events:
        lines.extend(["No feedback events recorded yet.", ""])
        return "\n".join(lines)
    for event in reversed(events):
        lines.extend([
            f"## {event.get('feedback_id', 'UNKNOWN')}",
            "",
            f"- Status: `{event.get('status', 'unknown')}`",
            f"- Type: `{event.get('type', 'unknown')}`",
            f"- Severity: `{event.get('severity', 'unknown')}`",
            f"- Framework ref: `{event.get('framework_ref', 'unknown')}`",
            f"- Generalizability: `{event.get('generalizability', 'unknown')}`",
            f"- Confidence: `{event.get('confidence', 'unknown')}`",
        ])
        if event.get("source_artifact"):
            lines.append(f"- Source artifact: `{event['source_artifact']}`")
        lines.extend([
            "",
            "**Observation**",
            "",
            str(event.get("observation", "")),
            "",
            "**Evidence**",
            "",
        ])
        for evidence in event.get("evidence", []):
            lines.append(f"- `{evidence}`")
        lines.extend([
            "",
            "**Suggested Framework improvement**",
            "",
            str(event.get("suggestion", "")),
            "",
        ])
        if event.get("negative_learning"):
            lines.extend(["**Negative learning**", "", str(event["negative_learning"]), ""])
    return "\n".join(lines)


def capture(target: Path, event: dict) -> tuple[Path, Path]:
    if not target.exists() or not target.is_dir():
        raise FeedbackError(f"target project does not exist or is not a directory: {target}")
    erei_dir = target / ".erei"
    if not (erei_dir / "framework.json").exists():
        raise FeedbackError("target is not an EREI-integrated project: missing .erei/framework.json")
    feedback_dir = erei_dir / "feedback"
    feedback_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = feedback_dir / "FRAMEWORK_FEEDBACK.jsonl"
    markdown_path = feedback_dir / "FRAMEWORK_FEEDBACK.md"

    with feedback_lock(feedback_dir):
        events = _read_events(jsonl_path)
        events.append(event)
        jsonl_content = "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in events)
        tmp_jsonl = jsonl_path.with_suffix(".jsonl.tmp")
        tmp_md = markdown_path.with_suffix(".md.tmp")
        tmp_jsonl.write_text(jsonl_content, encoding="utf-8")
        tmp_md.write_text(_render_markdown(events), encoding="utf-8")
        os.replace(tmp_jsonl, jsonl_path)
        os.replace(tmp_md, markdown_path)
    return jsonl_path, markdown_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture project-local feedback about EREI Engineering Framework.")
    parser.add_argument("--target", required=True, help="Project repository path")
    parser.add_argument("--project-repository", required=True)
    parser.add_argument("--project-name")
    parser.add_argument("--framework-ref", required=True)
    parser.add_argument("--type", required=True, choices=sorted(FEEDBACK_TYPES))
    parser.add_argument("--severity", required=True, choices=sorted(SEVERITIES))
    parser.add_argument("--source-artifact")
    parser.add_argument("--observation", required=True)
    parser.add_argument("--evidence", action="append", default=[], required=True)
    parser.add_argument("--suggestion", required=True)
    parser.add_argument("--negative-learning")
    parser.add_argument("--generalizability", required=True, choices=sorted(GENERALIZABILITY))
    parser.add_argument("--confidence", required=True, choices=sorted(CONFIDENCE))
    parser.add_argument("--tag", action="append", default=[])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        event = build_event(args)
        jsonl_path, markdown_path = capture(Path(args.target).resolve(), event)
    except FeedbackError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "status": "captured",
        "feedback_id": event["feedback_id"],
        "fingerprint": event["fingerprint"],
        "jsonl": str(jsonl_path),
        "markdown": str(markdown_path),
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
