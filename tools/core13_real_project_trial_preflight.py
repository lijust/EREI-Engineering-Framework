"""Read-only real-project Core13 trial preflight: never activate a capability.

Purpose: run on exact project Git objects. BLOCK is a truthful, auditable
result, not a failed CI build. Never read customer payloads, call providers,
alter a project pin, create adoption, or silently upgrade Stable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools import capability_activation as activation

_SHA = re.compile(r"^[0-9a-f]{40}$")
_ALLOWED_CAP = "learning_pattern_analysis"
_MAX_CONFIG_BYTES = 256 * 1024


def _safe_json(root: Path, path: Path) -> dict | None:
    # Reject external symlinked trust roots, and malformed/oversized configs.
    if path.is_symlink() or path.parent.is_symlink():
        return None
    try:
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(root) or not resolved.is_file():
            return None
        if resolved.stat().st_size > _MAX_CONFIG_BYTES:
            return None
        raw = resolved.read_bytes()
        if len(raw) > _MAX_CONFIG_BYTES:
            return None
        value = json.loads(raw)
        if type(value) is dict:
            return value
    except (OSError, ValueError, UnicodeError, RecursionError, OverflowError):
        pass
    return None


def _sha256_file(path: Path) -> str | None:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > _MAX_CONFIG_BYTES:
            return None
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, ValueError):
        return None


def _git_head(root: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=root, capture_output=True, text=True, check=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = proc.stdout.strip()
    return value if _SHA.fullmatch(value) else None


def inspect_trial_admission(
    project_root: Path | str, expected_project_sha: str,
    candidate_framework_sha: str, *,
    now: datetime,
) -> dict:
    """Read only exact source, report blockers, *never* approve activation."""
    base = {
        "kind": "CORE13_REAL_PROJECT_TRIAL_PREFLIGHT_V1",
        "status": "BLOCKED", "admission_authorized": False,
        "real_project_trial_executed": False,
        "knowledge_consumption_verified": False,
        "effectiveness": "NOT_ESTABLISHED",
        "stable_ready": False,
        "files_written": False,
    }
    if (type(project_root) not in (Path, str)
            or type(expected_project_sha) is not str
            or _SHA.fullmatch(expected_project_sha) is None
            or type(candidate_framework_sha) is not str
            or _SHA.fullmatch(candidate_framework_sha) is None
            or type(now) is not datetime or now.tzinfo is None
            or now.utcoffset() is None):
        return {**base, "blockers": ["INPUT_INVALID"]}
    try:
        root = Path(project_root).resolve(strict=True)
        if not root.is_dir():
            return {**base, "blockers": ["PROJECT_DIRECTORY_INVALID"]}
        actual_head = _git_head(root)
        if actual_head != expected_project_sha:
            return {**base, "blockers": ["PROJECT_COMMIT_NOT_AT_EXPECTED_SHA"]}
        manifest_path = root / ".erei" / "framework.json"
        adoption_path = root / ".erei" / "CANDIDATE_CAPABILITIES.json"
        manifest = _safe_json(root, manifest_path)
        blockers = []
        pin = None
        if manifest is None:
            blockers.append("PROJECT_MANIFEST_UNAVAILABLE")
        else:
            try:
                fw = activation._validate_manifest(manifest)
                pin = fw["ref"]
                if fw["ref_type"] != "commit" or not _SHA.fullmatch(pin):
                    blockers.append("PROJECT_NOT_COMMIT_PINNED")
                elif pin != candidate_framework_sha:
                    blockers.append("PROJECT_PIN_DIFFERS_FROM_CANDIDATE")
            except (activation.ActivationError, TypeError, ValueError, KeyError, AttributeError):
                blockers.append("PROJECT_MANIFEST_INVALID")
        adoption = _safe_json(root, adoption_path)
        if adoption is None:
            blockers.append("CANDIDATE_ADOPTION_NOT_PRESENT_OR_INVALID")
        else:
            try:
                entries = activation._validate_adoptions(adoption)
                if (adoption["framework_ref"] != candidate_framework_sha or
                        not any(x["capability"] == _ALLOWED_CAP and
                                x["_approved"] <= now.astimezone(timezone.utc) <
                                x["_expires"] for x in entries)):
                    blockers.append("NO_ACTIVE_MATCHING_CANDIDATE_ADOPTION")
            except (activation.ActivationError, TypeError, ValueError, KeyError, AttributeError):
                blockers.append("CANDIDATE_ADOPTION_NOT_PRESENT_OR_INVALID")
        knowledge_root = root / ".erei" / "knowledge"
        if (knowledge_root.is_symlink() or
                not knowledge_root.is_dir() or
                knowledge_root.resolve(strict=True) != knowledge_root):
            blockers.append("PROJECT_KNOWLEDGE_ARTIFACT_NOT_PRESENT")
        else:
            # Do not inspect the content or emit file names/sensitive data.
            if not any(p.is_file() and not p.is_symlink()
                       for p in knowledge_root.iterdir()):
                blockers.append("PROJECT_KNOWLEDGE_ARTIFACT_NOT_PRESENT")
        if not blockers:
            # A project pin/adoption/knowledge file is not proof of deployed
            # code, authentic owner approval, prospective task selection or
            # runtime consumption. Never return a self-authorizing PASS.
            blockers.append("INDEPENDENT_TRIAL_AUTHORIZATION_NOT_ESTABLISHED")
        return {
            **base, "project_commit_verified": True,
            "project_ref": actual_head,
            "manifest_sha256": _sha256_file(manifest_path),
            "adoption_sha256": _sha256_file(adoption_path),
            "declared_pin": pin,
            "candidate_framework_sha": candidate_framework_sha,
            "blockers": sorted(set(blockers)),
        }
    except (OSError, TypeError, ValueError, AttributeError, RecursionError) as exc:
        return {**base, "blockers": ["SOURCE_INSPECTION_UNAVAILABLE"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Read-only Core13 project admission preflight")
    ap.add_argument("--project-root", type=Path, required=True)
    ap.add_argument("--project-sha", required=True)
    ap.add_argument("--framework-sha", required=True)
    opts = ap.parse_args(argv)
    result = inspect_trial_admission(
        opts.project_root, opts.project_sha, opts.framework_sha,
        now=datetime.now(timezone.utc),
    )
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    # Expected BLOCKED is not a false test failure. Missing source verification
    # or a trusted commit is a hard failure.
    return 0 if result.get("project_commit_verified") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
