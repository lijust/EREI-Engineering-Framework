#!/usr/bin/env python3
"""Validate a frozen VNext release target and its evidence-only closure."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from .validation_contract import (
        ContractValidationError,
        require_bool,
        require_datetime,
        require_enum,
        require_exact_fields,
        require_int,
        require_object,
        require_pattern,
        require_text,
    )
except ImportError:
    from validation_contract import (
        ContractValidationError,
        require_bool,
        require_datetime,
        require_enum,
        require_exact_fields,
        require_int,
        require_object,
        require_pattern,
        require_text,
    )

SHA40_RE = re.compile(r"^[a-f0-9]{40}$")
TARGET_ID_RE = re.compile(r"^vnext-rc[0-9]+$")
DEFAULT_TARGET = Path("releases/VNEXT_TARGET.json")
FINAL_STABLE_MANIFEST = "releases/vnext-assurance-v2-stable.json"
CLOSURE_EXACT = {
    "releases/VNEXT_TARGET.json",
    "security/ASSURANCE_ENFORCEMENT.json",
    FINAL_STABLE_MANIFEST,
}


class ReleaseTargetError(RuntimeError):
    pass


def _git(repo_root: Path, args: list[str]) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=repo_root, text=True, stderr=subprocess.STDOUT
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "output", "") or str(exc)
        raise ReleaseTargetError(f"git {' '.join(args)} failed: {detail.strip()}") from exc


def _sha(value: Any, label: str) -> str:
    try:
        return require_pattern(value, SHA40_RE, label)
    except ContractValidationError as exc:
        raise ReleaseTargetError(str(exc)) from exc


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseTargetError(f"unable to load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseTargetError(f"{path} must contain a JSON object")
    return value


def validate_manifest_shape(data: Any) -> dict[str, Any]:
    try:
        value = require_object(data, "release target")
        fields = {
            "schema_version", "target_id", "status", "framework_ref", "target_tree",
            "selected_at", "source_branch", "assurance", "stable_baseline", "promotion_authorized",
        }
        require_exact_fields(value, required=fields, allowed=fields, label="release target")
        if value["schema_version"] != 1:
            raise ContractValidationError("release target schema_version must be 1")
        require_pattern(value["target_id"], TARGET_ID_RE, "target_id")
        require_enum(value["status"], {"frozen_candidate"}, "release target status")
        require_pattern(value["framework_ref"], SHA40_RE, "framework_ref")
        require_pattern(value["target_tree"], SHA40_RE, "target_tree")
        require_datetime(value["selected_at"], "selected_at")
        require_enum(value["source_branch"], {"main"}, "source_branch")
        if require_bool(value["promotion_authorized"], "promotion_authorized") is not False:
            raise ContractValidationError("promotion_authorized must remain false for a frozen Candidate target")

        assurance = require_object(value["assurance"], "assurance")
        assurance_fields = {"workflow", "run_id", "event", "conclusion"}
        require_exact_fields(assurance, required=assurance_fields, allowed=assurance_fields, label="assurance")
        if require_text(assurance["workflow"], "assurance.workflow") != "Framework Assurance Gate":
            raise ContractValidationError("assurance.workflow must be Framework Assurance Gate")
        require_int(assurance["run_id"], "assurance.run_id", minimum=1)
        require_enum(assurance["event"], {"push"}, "assurance.event")
        require_enum(assurance["conclusion"], {"success"}, "assurance.conclusion")

        stable = require_object(value["stable_baseline"], "stable_baseline")
        stable_fields = {"baseline", "framework_ref"}
        require_exact_fields(stable, required=stable_fields, allowed=stable_fields, label="stable_baseline")
        require_text(stable["baseline"], "stable_baseline.baseline")
        require_pattern(stable["framework_ref"], SHA40_RE, "stable_baseline.framework_ref")
    except ContractValidationError as exc:
        raise ReleaseTargetError(str(exc)) from exc
    return value


def _git_head(repo_root: Path) -> str:
    return _sha(_git(repo_root, ["rev-parse", "HEAD"]), "git HEAD")


def _tree_for(repo_root: Path, revision: str) -> str:
    return _sha(_git(repo_root, ["rev-parse", f"{revision}^{{tree}}"]), "target tree")


def _assert_ancestor(repo_root: Path, ancestor: str, descendant: str) -> None:
    try:
        subprocess.check_output(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=repo_root,
            text=True,
            stderr=subprocess.STDOUT,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseTargetError(
            f"frozen target {ancestor} must be an ancestor of closure HEAD {descendant}"
        ) from exc


def load_and_validate_target(repo_root: Path, path: Path = DEFAULT_TARGET) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    path = path if path.is_absolute() else repo_root / path
    value = validate_manifest_shape(_load_json(path))
    target_ref = value["framework_ref"]
    try:
        _git(repo_root, ["cat-file", "-e", f"{target_ref}^{{commit}}"])
    except ReleaseTargetError as exc:
        raise ReleaseTargetError(f"framework_ref does not resolve to a fetched commit: {target_ref}") from exc
    actual_tree = _tree_for(repo_root, target_ref)
    if actual_tree != value["target_tree"]:
        raise ReleaseTargetError(
            f"target_tree mismatch: manifest={value['target_tree']} actual={actual_tree}"
        )
    head = _git_head(repo_root)
    _assert_ancestor(repo_root, target_ref, head)

    capabilities = _load_json(repo_root / "CAPABILITIES.json")
    stable = capabilities.get("stable_release")
    if not isinstance(stable, dict):
        raise ReleaseTargetError("CAPABILITIES.json missing stable_release object")
    if value["stable_baseline"]["baseline"] != stable.get("baseline"):
        raise ReleaseTargetError("stable_baseline.baseline does not match CAPABILITIES stable release")
    if value["stable_baseline"]["framework_ref"] != stable.get("framework_ref"):
        raise ReleaseTargetError("stable_baseline.framework_ref does not match CAPABILITIES stable release")
    if target_ref == value["stable_baseline"]["framework_ref"]:
        raise ReleaseTargetError("frozen VNext target must differ from the current Stable ref")
    return value


def allowed_closure_path(path: str) -> bool:
    if path in CLOSURE_EXACT:
        return True
    if path.startswith("evals/exact-target-runs/") and path.endswith(".json"):
        return True
    if path.startswith("evals/EXECUTION_EVIDENCE.") and path.endswith(".json"):
        return True
    if path.startswith("releases/approvals/") and path.endswith(".json"):
        return True
    return False


def _closure_changes(repo_root: Path, target_ref: str, head_ref: str) -> list[tuple[str, str]]:
    output = _git(repo_root, ["diff", "--name-status", "--no-renames", f"{target_ref}..{head_ref}"])
    rows: list[tuple[str, str]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            raise ReleaseTargetError(f"unexpected git diff name-status row: {line}")
        status, path = parts
        rows.append((status, path))
    return rows


def _blob(repo_root: Path, revision: str, path: str) -> str:
    return _git(repo_root, ["rev-parse", f"{revision}:{path}"])


def _assert_first_change_immutable(repo_root: Path, target_ref: str, head_ref: str, path: str) -> None:
    commits = _git(
        repo_root,
        ["log", "--reverse", "--format=%H", f"{target_ref}..{head_ref}", "--", path],
    ).splitlines()
    commits = [item.strip() for item in commits if item.strip()]
    if not commits:
        raise ReleaseTargetError(f"unable to resolve first closure change for {path}")
    first_blob = _blob(repo_root, commits[0], path)
    current_blob = _blob(repo_root, head_ref, path)
    if first_blob != current_blob:
        raise ReleaseTargetError(
            f"closure artifact {path} changed after its first post-freeze write; restart the RC instead of rewriting evidence"
        )


def validate_closure(repo_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    target_ref = manifest["framework_ref"]
    head_ref = _git_head(repo_root)
    _assert_ancestor(repo_root, target_ref, head_ref)
    changes = _closure_changes(repo_root, target_ref, head_ref)
    for status, path in changes:
        if status not in {"A", "M"}:
            raise ReleaseTargetError(f"release closure forbids status {status} for {path}")
        if not allowed_closure_path(path):
            raise ReleaseTargetError(
                f"release closure contains behavior/governance drift outside the fixed allowlist: {path}"
            )
        _assert_first_change_immutable(repo_root, target_ref, head_ref, path)
    return {
        "target_ref": target_ref,
        "closure_head": head_ref,
        "changed_paths": [path for _, path in changes],
        "changed_count": len(changes),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--target", default=str(DEFAULT_TARGET))
    parser.add_argument("--if-present", action="store_true")
    parser.add_argument("--require-target", action="store_true")
    parser.add_argument("--validate-closure", action="store_true")
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    target_path = Path(args.target)
    resolved = target_path if target_path.is_absolute() else repo_root / target_path
    if not resolved.exists():
        if args.require_target:
            print(f"ERROR: required frozen release target is missing: {target_path}", file=sys.stderr)
            return 2
        if args.if_present:
            print(json.dumps({"status": "not_selected", "target": str(target_path)}, sort_keys=True))
            return 0
        print(f"ERROR: frozen release target is missing: {target_path}", file=sys.stderr)
        return 2
    try:
        manifest = load_and_validate_target(repo_root, target_path)
        closure = validate_closure(repo_root, manifest) if args.validate_closure else None
    except ReleaseTargetError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    result = {
        "status": "valid",
        "target_id": manifest["target_id"],
        "framework_ref": manifest["framework_ref"],
        "promotion_authorized": manifest["promotion_authorized"],
    }
    if closure is not None:
        result["closure"] = closure
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
