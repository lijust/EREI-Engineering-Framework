#!/usr/bin/env python3
"""Capture immutable project-local Framework feedback with a default-local export boundary."""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit
from uuid import uuid4

from validate_framework_feedback import ValidationError, expected_fingerprint, validate_event

FEEDBACK_TYPES = {
    "architecture_gap", "workflow_gap", "skill_gap", "role_gap", "security_gap",
    "data_gap", "verification_gap", "runtime_gap", "performance_gap", "context_gap",
    "integration_gap", "false_positive", "false_negative", "process_friction",
    "missing_pattern", "documentation_gap",
}
SEVERITIES = {"low", "medium", "high", "critical"}
GENERALIZABILITY = {"project_specific", "possible_generic", "likely_generic", "confirmed_multi_project"}
CONFIDENCE = {"low", "medium", "high"}
SENSITIVITY = {"public", "internal", "confidential", "restricted"}
REDACTION = {"not_required", "pending", "redacted", "approved"}
EXPORT = {"local_only", "review_required", "eligible"}

SECRET_PATTERNS = [
    re.compile(r"(?i)\b(password|passwd|api[_-]?key|client[_-]?secret|access[_-]?token|refresh[_-]?token)\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+\-/=]{16,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
]
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
SENSITIVE_QUERY_KEYS = {"token", "access_token", "api_key", "apikey", "key", "secret", "password", "signature", "sig"}


class FeedbackError(RuntimeError):
    pass


def _nonempty(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FeedbackError(f"{label} must not be empty")
    return value.strip()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _feedback_id(now: datetime) -> str:
    return f"EFF-{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8].upper()}"


def _contains_secret(text: str) -> bool:
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        return True
    for candidate in re.findall(r"https?://[^\s`<>]+", text):
        try:
            parts = urlsplit(candidate)
        except ValueError:
            continue
        for key, _ in parse_qsl(parts.query, keep_blank_values=True):
            if key.lower() in SENSITIVE_QUERY_KEYS:
                return True
    return False


def _privacy_defaults(args: argparse.Namespace, texts: list[str]) -> tuple[str, str, str]:
    if any(_contains_secret(text) for text in texts):
        raise FeedbackError("possible credential/secret detected; redact it before feedback capture")
    sensitivity = args.sensitivity_class
    if sensitivity is None:
        sensitivity = "confidential" if any(EMAIL_RE.search(text) for text in texts) else "internal"
    redaction = args.redaction_state
    if redaction is None:
        redaction = "not_required" if sensitivity == "public" else "pending"
    export = args.export_eligibility or "local_only"
    if sensitivity in {"confidential", "restricted"} and export == "eligible" and redaction != "approved":
        raise FeedbackError("confidential/restricted feedback cannot be export-eligible before approved redaction")
    return sensitivity, redaction, export


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
    negative_learning = args.negative_learning.strip() if args.negative_learning and args.negative_learning.strip() else None
    tags = sorted({tag.strip() for tag in args.tag if tag.strip()})
    texts = [observation, suggestion, *evidence]
    if source_artifact:
        texts.append(source_artifact)
    if negative_learning:
        texts.append(negative_learning)
    sensitivity, redaction, export = _privacy_defaults(args, texts)

    event = {
        "schema_version": 2,
        "feedback_id": args.feedback_id.strip() if args.feedback_id else _feedback_id(current),
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
        "sensitivity_class": sensitivity,
        "redaction_state": redaction,
        "export_eligibility": export,
    }
    if args.project_name and args.project_name.strip():
        event["project"]["name"] = args.project_name.strip()
    if source_artifact:
        event["source_artifact"] = source_artifact
    if negative_learning:
        event["negative_learning"] = negative_learning
    if tags:
        event["tags"] = tags
    event["fingerprint"] = expected_fingerprint(event)
    try:
        validate_event(event)
    except ValidationError as exc:
        raise FeedbackError(str(exc)) from exc
    return event


@contextmanager
def feedback_lock(directory: Path, *, timeout_seconds: float = 5.0):
    directory.mkdir(parents=True, exist_ok=True)
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


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FeedbackError(f"invalid JSON at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FeedbackError(f"feedback record at {path} is not an object")
    return value


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    values: list[dict] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise FeedbackError(f"invalid JSONL at {path}:{number}: {exc}") from exc
        if not isinstance(value, dict):
            raise FeedbackError(f"feedback event at {path}:{number} is not an object")
        values.append(value)
    return values


def _load_events(jsonl_path: Path, event_dir: Path) -> list[dict]:
    records = _read_jsonl(jsonl_path)
    if event_dir.exists():
        records.extend(_read_json(path) for path in sorted(event_dir.glob("*.json")))
    by_id: dict[str, dict] = {}
    for event in records:
        try:
            validate_event(event)
        except ValidationError as exc:
            raise FeedbackError(str(exc)) from exc
        feedback_id = event["feedback_id"]
        if feedback_id in by_id and by_id[feedback_id] != event:
            raise FeedbackError(f"conflicting duplicate feedback_id: {feedback_id}")
        by_id[feedback_id] = event
    return sorted(by_id.values(), key=lambda event: event["feedback_id"])


def _write_projection(path: Path, events: list[dict]) -> None:
    temp = path.with_suffix(".jsonl.tmp")
    temp.write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in events), encoding="utf-8")
    os.replace(temp, path)


def _write_immutable(path: Path, event: dict) -> None:
    if path.exists():
        existing = _read_json(path)
        if existing == event:
            return
        raise FeedbackError(f"immutable feedback record conflicts: {path}")
    temp = path.with_name(path.name + f".{uuid4().hex}.tmp")
    temp.write_text(json.dumps(event, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def _render_data(text: str) -> str:
    safe = html.escape(text, quote=False).replace("`", "\\`")
    return "\n".join(f"> {line}" for line in safe.splitlines()) or ">"


def _render_markdown(events: list[dict]) -> str:
    lines = [
        "# Framework Feedback",
        "",
        "Project-local observations. `FRAMEWORK_FEEDBACK.jsonl` is a generated view; V2 files under `events/` are authoritative.",
        "Export defaults to `local_only` and central promotion is a separate decision record.",
        "",
    ]
    if not events:
        return "\n".join(lines + ["No feedback events recorded yet.", ""])
    for event in reversed(events):
        lines.extend([
            f"## {event.get('feedback_id', 'UNKNOWN')}",
            "",
            f"- Status: `{event.get('status', 'unknown')}`",
            f"- Type: `{event.get('type', 'unknown')}`",
            f"- Severity: `{event.get('severity', 'unknown')}`",
            f"- Sensitivity: `{event.get('sensitivity_class', 'legacy')}`",
            f"- Export: `{event.get('export_eligibility', 'legacy')}`",
            f"- Framework ref: `{event.get('framework_ref', 'unknown')}`",
            "",
            "**Observation (rendered as data)**",
            "",
            _render_data(str(event.get("observation", ""))),
            "",
            "**Evidence**",
            "",
        ])
        lines.extend(f"- `{html.escape(str(item), quote=False)}`" for item in event.get("evidence", []))
        lines.extend([
            "",
            "**Suggested Framework improvement (rendered as data)**",
            "",
            _render_data(str(event.get("suggestion", ""))),
            "",
        ])
    return "\n".join(lines)


def capture(target: Path, event: dict) -> tuple[Path, Path, bool]:
    if not target.exists() or not target.is_dir():
        raise FeedbackError(f"target project does not exist or is not a directory: {target}")
    erei_dir = target / ".erei"
    if not (erei_dir / "framework.json").exists():
        raise FeedbackError("target is not an EREI-integrated project: missing .erei/framework.json")
    feedback_dir = erei_dir / "feedback"
    feedback_dir.mkdir(parents=True, exist_ok=True)
    event_dir = feedback_dir / "events"
    event_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = feedback_dir / "FRAMEWORK_FEEDBACK.jsonl"
    markdown_path = feedback_dir / "FRAMEWORK_FEEDBACK.md"

    try:
        validate_event(event)
    except ValidationError as exc:
        raise FeedbackError(str(exc)) from exc

    with feedback_lock(feedback_dir):
        events = _load_events(jsonl_path, event_dir)
        existing = next((item for item in events if item["feedback_id"] == event["feedback_id"]), None)
        if existing is not None:
            if existing["fingerprint"] != event["fingerprint"]:
                raise FeedbackError(f"feedback_id already exists with conflicting content: {event['feedback_id']}")
            _write_projection(jsonl_path, events)
            tmp_md = markdown_path.with_suffix(".md.tmp")
            tmp_md.write_text(_render_markdown(events), encoding="utf-8")
            os.replace(tmp_md, markdown_path)
            return jsonl_path, markdown_path, True

        candidate = events + [event]
        for item in candidate:
            try:
                validate_event(item)
            except ValidationError as exc:
                raise FeedbackError(str(exc)) from exc
        _write_immutable(event_dir / f"{event['feedback_id']}.json", event)
        persisted = _load_events(jsonl_path, event_dir)
        _write_projection(jsonl_path, persisted)
        tmp_md = markdown_path.with_suffix(".md.tmp")
        tmp_md.write_text(_render_markdown(persisted), encoding="utf-8")
        os.replace(tmp_md, markdown_path)
    return jsonl_path, markdown_path, False


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture project-local feedback about EREI Engineering Framework.")
    parser.add_argument("--target", required=True)
    parser.add_argument("--project-repository", required=True)
    parser.add_argument("--project-name")
    parser.add_argument("--framework-ref", required=True)
    parser.add_argument("--feedback-id")
    parser.add_argument("--type", required=True, choices=sorted(FEEDBACK_TYPES))
    parser.add_argument("--severity", required=True, choices=sorted(SEVERITIES))
    parser.add_argument("--source-artifact")
    parser.add_argument("--observation", required=True)
    parser.add_argument("--evidence", action="append", default=[], required=True)
    parser.add_argument("--suggestion", required=True)
    parser.add_argument("--negative-learning")
    parser.add_argument("--generalizability", required=True, choices=sorted(GENERALIZABILITY))
    parser.add_argument("--confidence", required=True, choices=sorted(CONFIDENCE))
    parser.add_argument("--sensitivity-class", choices=sorted(SENSITIVITY))
    parser.add_argument("--redaction-state", choices=sorted(REDACTION))
    parser.add_argument("--export-eligibility", choices=sorted(EXPORT))
    parser.add_argument("--tag", action="append", default=[])
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        event = build_event(args)
        jsonl_path, markdown_path, idempotent = capture(Path(args.target).resolve(), event)
    except (FeedbackError, ValidationError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "status": "already_captured" if idempotent else "captured",
        "feedback_id": event["feedback_id"],
        "fingerprint": event["fingerprint"],
        "sensitivity_class": event["sensitivity_class"],
        "export_eligibility": event["export_eligibility"],
        "jsonl": str(jsonl_path),
        "markdown": str(markdown_path),
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
