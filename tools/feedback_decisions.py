#!/usr/bin/env python3
"""Validate central Framework feedback decisions and render REVIEW_QUEUE.md."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DECISION_ID_RE = re.compile(r"^EFD-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
FEEDBACK_ID_RE = re.compile(r"^EFF-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
CLUSTER_RE = re.compile(r"^FCL-[A-Z0-9-]+$")
SHA40_RE = re.compile(r"^[a-f0-9]{40}$")


class DecisionError(RuntimeError):
    pass


def _text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DecisionError(f"{label} must be a non-empty string")
    return value.strip()


def _datetime(value, label: str) -> str:
    text = _text(value, label)
    if "T" not in text or not (text.endswith("Z") or re.search(r"[+-][0-9]{2}:[0-9]{2}$", text)):
        raise DecisionError(f"{label} must be RFC3339 date-time with timezone")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DecisionError(f"invalid {label}") from exc
    if parsed.tzinfo is None:
        raise DecisionError(f"{label} must include timezone")
    return text


def _unique_texts(value, label: str, minimum: int = 0) -> list[str]:
    if not isinstance(value, list) or len(value) < minimum:
        raise DecisionError(f"{label} must contain at least {minimum} item(s)")
    result = [_text(item, f"{label} item") for item in value]
    if len(result) != len(set(result)):
        raise DecisionError(f"{label} must be unique")
    return result


def validate_decision(record: dict) -> None:
    if not isinstance(record, dict):
        raise DecisionError("decision must be an object")
    required = {
        "schema_version", "decision_id", "decided_at", "decision_revision", "source",
        "cluster_id", "review_state", "promotion_state", "decision_note", "evidence",
    }
    allowed = required | {"candidate_ref", "promotion_ref"}
    missing = sorted(required - set(record))
    unknown = sorted(set(record) - allowed)
    if missing:
        raise DecisionError("decision missing fields: " + ", ".join(missing))
    if unknown:
        raise DecisionError("decision unknown fields: " + ", ".join(unknown))
    if record["schema_version"] != 1:
        raise DecisionError("unsupported decision schema_version")
    if not isinstance(record["decision_id"], str) or not DECISION_ID_RE.fullmatch(record["decision_id"]):
        raise DecisionError("invalid decision_id")
    _datetime(record["decided_at"], "decided_at")
    if not isinstance(record["decision_revision"], str) or not SHA40_RE.fullmatch(record["decision_revision"]):
        raise DecisionError("decision_revision must be exact commit")
    source = record["source"]
    if not isinstance(source, dict) or set(source) != {"repository", "revision", "feedback_id"}:
        raise DecisionError("source must contain exactly repository/revision/feedback_id")
    _text(source["repository"], "source.repository")
    if not isinstance(source["revision"], str) or not SHA40_RE.fullmatch(source["revision"]):
        raise DecisionError("source.revision must be exact commit")
    if not isinstance(source["feedback_id"], str) or not FEEDBACK_ID_RE.fullmatch(source["feedback_id"]):
        raise DecisionError("invalid source.feedback_id")
    if not isinstance(record["cluster_id"], str) or not CLUSTER_RE.fullmatch(record["cluster_id"]):
        raise DecisionError("invalid cluster_id")
    if record["review_state"] not in {"triaged", "project_local", "needs_evidence", "clustered", "candidate", "promoted", "rejected"}:
        raise DecisionError("invalid review_state")
    if record["promotion_state"] not in {"not_promoted", "candidate", "promoted", "rejected"}:
        raise DecisionError("invalid promotion_state")
    _text(record["decision_note"], "decision_note")
    _unique_texts(record["evidence"], "evidence", 1)
    if "candidate_ref" in record and (not isinstance(record["candidate_ref"], str) or not SHA40_RE.fullmatch(record["candidate_ref"])):
        raise DecisionError("candidate_ref must be exact commit")
    if "promotion_ref" in record and (not isinstance(record["promotion_ref"], str) or not SHA40_RE.fullmatch(record["promotion_ref"])):
        raise DecisionError("promotion_ref must be exact commit")
    if record["promotion_state"] in {"candidate", "promoted"} and "candidate_ref" not in record:
        raise DecisionError("candidate promotion state requires candidate_ref")
    if record["promotion_state"] == "promoted" and "promotion_ref" not in record:
        raise DecisionError("promoted decision requires promotion_ref")


def load_decisions(path: Path) -> list[dict]:
    records: list[dict] = []
    seen_decisions: set[str] = set()
    seen_sources: set[tuple[str, str, str]] = set()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DecisionError(f"invalid JSON at line {number}: {exc}") from exc
        try:
            validate_decision(record)
        except DecisionError as exc:
            raise DecisionError(f"line {number}: {exc}") from exc
        if record["decision_id"] in seen_decisions:
            raise DecisionError(f"duplicate decision_id: {record['decision_id']}")
        source = record["source"]
        source_key = (source["repository"], source["revision"], source["feedback_id"])
        if source_key in seen_sources:
            raise DecisionError(f"source feedback has more than one current decision: {source_key}")
        seen_decisions.add(record["decision_id"])
        seen_sources.add(source_key)
        records.append(record)
    return records


def render(decisions: list[dict]) -> str:
    clusters: dict[str, list[dict]] = defaultdict(list)
    for record in decisions:
        clusters[record["cluster_id"]].append(record)
    lines = [
        "# Framework Feedback Review Queue",
        "",
        "`DECISIONS.jsonl` is the machine-readable source of truth for central review decisions. Raw project feedback remains authoritative in each source project's `.erei/feedback/` records.",
        "",
    ]
    for cluster_id in sorted(clusters):
        lines.extend([f"## {cluster_id}", ""])
        for record in sorted(clusters[cluster_id], key=lambda item: item["decision_id"]):
            source = record["source"]
            lines.extend([
                f"### {source['feedback_id']}",
                "",
                f"- Source project: `{source['repository']}`",
                f"- Source project ref: `{source['revision']}`",
                f"- Decision revision: `{record['decision_revision']}`",
                f"- Review state: `{record['review_state'].upper()}`",
                f"- Promotion state: `{record['promotion_state'].upper()}`",
                f"- Decision ID: `{record['decision_id']}`",
                "- Evidence:",
            ])
            lines.extend(f"  - `{item}`" for item in record["evidence"])
            lines.extend(["- Review note: " + record["decision_note"], ""])
    projects = {record["source"]["repository"] for record in decisions}
    lines.extend([
        "## Intake summary",
        "",
        f"- Source projects represented: `{len(projects)}`",
        f"- Feedback events ingested: `{len(decisions)}`",
        f"- Clusters created: `{len(clusters)}`",
        f"- Promoted decisions: `{sum(record['promotion_state'] == 'promoted' for record in decisions)}`",
        "- Source observations mutated by central intake: `0`",
        "",
    ])
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("ledger")
    render_cmd = sub.add_parser("render")
    render_cmd.add_argument("ledger")
    render_cmd.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        decisions = load_decisions(Path(args.ledger))
        if args.command == "render":
            output = Path(args.output)
            temp = output.with_suffix(output.suffix + ".tmp")
            temp.write_text(render(decisions), encoding="utf-8")
            temp.replace(output)
            payload = {"status": "rendered", "decisions": len(decisions), "output": str(output)}
        else:
            payload = {"status": "valid", "decisions": len(decisions), "clusters": len({item['cluster_id'] for item in decisions})}
        print(json.dumps(payload, sort_keys=True))
        return 0
    except (DecisionError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
