#!/usr/bin/env python3
"""Plan prospective Task Learning imports without writing project files.

This is a diagnostic, not migration authority. Original ledger bytes/order and all
validation failures are retained; no fingerprint, identity or review is repaired.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

try:
    from . import task_learning as learning
except ImportError:  # Direct CLI execution.
    import task_learning as learning


def _file_identity(path: Path, target: Path) -> dict:
    if not path.exists():
        return {"path": path.relative_to(target).as_posix(), "exists": False}
    raw = path.read_bytes()
    return {
        "path": path.relative_to(target).as_posix(),
        "exists": True,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "git_blob_sha1": hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest(),
        "bytes": len(raw),
    }


def _content_digest(record: dict) -> str:
    serialized = json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    # Match Path.write_text's native newline translation in the existing writer.
    raw = serialized.replace("\n", os.linesep).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def plan(target: Path) -> dict:
    target = target.resolve()
    report = {
        "schema_version": 1,
        "mode": "DRY_RUN_ONLY",
        "status": "BLOCKED",
        "apply_supported": False,
        "proposed_file_newline": "CRLF" if os.linesep == "\r\n" else "LF",
        "source_files": [],
        "missing_immutable_authority": [],
        "proposed_immutable_files": [],
        "legacy_review_memberships": [],
        "issues": [],
        "boundary": "Separate reviewed migration authorization is required. Preserve original ledger bytes and order; never infer missing historical order or repair anomalies automatically.",
    }
    issues = report["issues"]
    proposals = []
    try:
        paths = learning._paths(target)
        before = learning._ledger_generation(paths)
        source_paths = [target / ".erei/framework.json", paths["events"], paths["reviews"]]
        report["source_files"] = [_file_identity(path, target) for path in source_paths]
        learning._read_json(source_paths[0])
        events = learning._read_jsonl(paths["events"])
        reviews = learning._read_jsonl(paths["reviews"])
        immutable_events = learning._immutable_records(paths["event_dir"], learning._occurrence, "event")
        immutable_reviews = learning._immutable_records(paths["review_dir"], learning._review_identity, "review")
        report["source_generation"] = before
        report["event_counts"] = {
            "projection_records": len(events),
            "v1": sum(e.get("schema_version") == 1 for e in events),
            "v2": sum(e.get("schema_version") == 2 for e in events),
            "immutable_records": len(immutable_events),
        }

        def inspect(projection, immutable, key_fn, validate, label, destination):
            authorities = {key_fn(row): row for row in immutable}
            seen = set()
            combined = list(projection)
            for index, row in enumerate(projection, start=1):
                try:
                    validate(row)
                    key = key_fn(row)
                    if key in seen:
                        raise learning.LearningError("duplicate " + label + " projection identity: " + key)
                    seen.add(key)
                    authority = authorities.get(key)
                    if authority is not None and authority != row:
                        raise learning.LearningError(label + " projection differs from immutable authority: " + key)
                    if row["schema_version"] == 2 and authority is None:
                        proposed = {
                            "path": (destination / (key + ".json")).relative_to(target).as_posix(),
                            "source_record_index": index,
                            "content_sha256": _content_digest(row),
                        }
                        report["missing_immutable_authority"].append({"kind": label, "identity": key, "source_record_index": index})
                        proposals.append(proposed)
                except (learning.LearningError, learning.ContractValidationError, KeyError, TypeError, ValueError) as exc:
                    issues.append({"kind": label, "source_record_index": index, "error": str(exc)})
            for row in immutable:
                try:
                    validate(row)
                    if row["schema_version"] != 2:
                        raise learning.LearningError("immutable " + label + " must use schema_version 2")
                    if key_fn(row) not in seen:
                        combined.append(row)
                except (learning.LearningError, learning.ContractValidationError, KeyError, TypeError, ValueError) as exc:
                    issues.append({"kind": "immutable_" + label, "error": str(exc)})
            return combined

        combined_events = inspect(events, immutable_events, learning._occurrence, learning.validate_event, "event", paths["event_dir"])
        combined_reviews = inspect(reviews, immutable_reviews, learning._review_identity, learning.validate_learning_review_shape, "review", paths["review_dir"])
        # Mirror _load_reviews: epoch validation must use canonical review-ID order,
        # not the possibly noncanonical source JSONL projection order.
        combined_reviews.sort(key=learning._review_identity)
        if any(row.get("schema_version") == 1 for row in combined_reviews) and len(combined_events) != len(events):
            issues.append({
                "kind": "legacy_order",
                "error": "Legacy positional reviews coexist with immutable-only events; establish original projection order from retained evidence before planning.",
            })
        if not issues:
            # The ordinary validator remains strict: this only evaluates the hypothetical
            # addition of missing immutable authority, without creating any authority.
            state = learning.derive_state(combined_events, combined_reviews)
            seen_tasks = set()
            repositories = set()
            for row in combined_events:
                if row["task_id"] in seen_tasks:
                    raise learning.LearningError("duplicate task_id across occurrences: " + row["task_id"])
                seen_tasks.add(row["task_id"])
                repositories.add(row["project"]["repository"])
            if len(repositories) > 1:
                raise learning.LearningError("prospective event ledger contains multiple source projects")
            report["project_repositories"] = sorted(repositories)
            cutoff = 0
            for review in reviews:
                if review["schema_version"] == 1:
                    selected = events[cutoff:review["through_event_count"]]
                    report["legacy_review_memberships"].append({
                        "review_id": review["review_id"],
                        "epoch_id": review["epoch_id"],
                        "source_start_index": cutoff + 1,
                        "through_event_count": review["through_event_count"],
                        "reviewed_occurrence_ids": [learning._occurrence(e) for e in selected],
                        "event_digest": learning._event_digest(selected),
                    })
                    cutoff = review["through_event_count"]
            report["derived_summary"] = {
                "epoch_id": state["epoch_id"],
                "total_events": state["total_events"],
                "reviewed_occurrence_count": state["reviewed_occurrence_count"],
                "unreviewed_tasks": state["metrics_since_last_review"]["tasks"],
            }
        if learning._ledger_generation(paths) != before or [_file_identity(path, target) for path in source_paths] != report["source_files"]:
            issues.append({"kind": "source_changed", "error": "source changed during read-only planning; discard this plan"})
    except (OSError, UnicodeError, learning.LearningError, learning.ContractValidationError, KeyError, TypeError, ValueError) as exc:
        issues.append({"kind": "validation", "error": str(exc)})
    if not issues:
        report["status"] = "REVIEW_REQUIRED" if proposals else "NO_IMPORT_REQUIRED"
        report["proposed_immutable_files"] = proposals
    else:
        # Partial diagnostics are useful; partial authorization is never issued.
        report["legacy_review_memberships"] = []
        report.pop("derived_summary", None)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="Project to inspect; no files are changed.")
    args = parser.parse_args(argv)
    report = plan(Path(args.target))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 2 if report["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())

