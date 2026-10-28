"""Source-only GitHub Actions provenance gate for future Core13 learning traces.

This reuses the repository's existing authenticated GitHub API reader; it
does not run GitHub Actions, create traces, or attest learning behavior.
An authenticated artifact is NOT a trusted execution environment or proof
that an intervention was loaded by the project.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
import zlib
from pathlib import Path
from typing import Any

from tools import github_actions_artifact_provenance as actions
from tools import learning_exposure_traces

REPOSITORY = actions.REPOSITORY
WORKFLOW_PATH = ".github/workflows/core13-learning-trace-export.yml"
WORKFLOW_NAME = "Core13 Learning Trace Export"
MEMBER = "learning-traces.json"
MAX_ARCHIVE_BYTES = 4 * 1024 * 1024
MAX_MEMBER_BYTES = 2 * 1024 * 1024
SHA40 = re.compile(r"^[a-f0-9]{40}$")
SHA256 = re.compile(r"^sha256:([a-f0-9]{64})$")


class TraceOriginError(ValueError):
    pass


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict:
    value = {}
    for key, item in pairs:
        if key in value:
            raise TraceOriginError("TRACE_JSON_DUPLICATE_KEY")
        value[key] = item
    return value


def _bad_constant(_: str) -> Any:
    raise TraceOriginError("TRACE_JSON_NONFINITE")


def _decode_json(raw: bytes) -> Any:
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_object_pairs,
                          parse_constant=_bad_constant)
    except (UnicodeError, ValueError, RecursionError, OverflowError) as exc:
        raise TraceOriginError("TRACE_JSON_INVALID") from exc


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False,
                          allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (ValueError, TypeError, OverflowError, RecursionError) as exc:
        raise TraceOriginError("TRACE_BUNDLE_INVALID") from exc


def _read_archive(archive: Path | str) -> tuple[bytes, dict]:
    if not isinstance(archive, (Path, str)) or not str(archive).strip():
        raise TraceOriginError("TRACE_ARCHIVE_REQUIRED")
    try:
        path = Path(archive)
        if path.stat().st_size > MAX_ARCHIVE_BYTES:
            raise TraceOriginError("TRACE_ARCHIVE_TOO_LARGE")
        raw = path.read_bytes()
        if len(raw) > MAX_ARCHIVE_BYTES:
            raise TraceOriginError("TRACE_ARCHIVE_TOO_LARGE")
        with zipfile.ZipFile(io.BytesIO(raw)) as handle:
            files = handle.infolist()
            if len(files) != 1 or files[0].filename != MEMBER:
                raise TraceOriginError("TRACE_ARCHIVE_FILE_SET_INVALID")
            entry = files[0]
            kind = (entry.external_attr >> 16) & 0o170000
            if (entry.is_dir() or kind == 0o120000 or entry.flag_bits & 1
                    or entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                    or entry.file_size > MAX_MEMBER_BYTES):
                raise TraceOriginError("TRACE_ARCHIVE_UNSAFE_MEMBER")
            with handle.open(entry) as file:
                payload = file.read(MAX_MEMBER_BYTES + 1)
            if len(payload) > MAX_MEMBER_BYTES:
                raise TraceOriginError("TRACE_ARCHIVE_UNSAFE_MEMBER")
    except TraceOriginError:
        raise
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError,
            ValueError, EOFError, zlib.error, RecursionError, OverflowError) as exc:
        raise TraceOriginError("TRACE_ARCHIVE_INVALID") from exc
    bundle = _decode_json(payload)
    if type(bundle) is not dict:
        raise TraceOriginError("TRACE_BUNDLE_INVALID")
    return raw, bundle


def _identity(value: Any) -> dict:
    if type(value) is not dict or set(value) != {
        "repository", "run_id", "run_attempt", "framework_sha",
    }:
        raise TraceOriginError("ACTIONS_IDENTITY_INVALID")
    if (value["repository"] != REPOSITORY or
            type(value["run_id"]) is not int or value["run_id"] <= 0 or
            type(value["run_attempt"]) is not int or value["run_attempt"] <= 0 or
            type(value["framework_sha"]) is not str or
            SHA40.fullmatch(value["framework_sha"]) is None):
        raise TraceOriginError("ACTIONS_IDENTITY_INVALID")
    return value


def verify_actions_trace_origin(
    archive: Path | str, expected_bundle: Any, identity: Any, *,
    token: str | None,
) -> dict:
    """Authenticate artifact *origin metadata and bytes*, not trace semantics.

    The producer workflow is a predeclared interface and is NOT installed
    by this module. All tests mock GitHub; no credentials/provider calls in CI.
    """
    if type(token) is not str or not token.strip():
        raise TraceOriginError("ACTIONS_READ_TOKEN_REQUIRED")
    record = _identity(identity)
    raw, bundle = _read_archive(archive)
    if _canonical(bundle) != _canonical(expected_bundle):
        raise TraceOriginError("TRACE_BUNDLE_DIFFERS_FROM_ARCHIVE")
    run_id, attempt = record["run_id"], record["run_attempt"]
    try:
        run = actions._api_json(
            f"https://api.github.com/repos/{REPOSITORY}/actions/runs/{run_id}",
            token,
        )
        if (
            type(run.get("id")) is not int or run["id"] != run_id or
            type(run.get("run_attempt")) is not int or
            run["run_attempt"] != attempt or
            run.get("event") != "workflow_dispatch" or
            run.get("status") != "completed" or
            run.get("conclusion") != "success" or
            run.get("path") != WORKFLOW_PATH or
            run.get("name") != WORKFLOW_NAME or
            run.get("head_sha") != record["framework_sha"] or
            not isinstance(run.get("repository"), dict) or
            run["repository"].get("full_name") != REPOSITORY
        ):
            raise TraceOriginError("ACTIONS_RUN_NOT_APPROVED_SOURCE")
        metadata = actions._api_json(
            f"https://api.github.com/repos/{REPOSITORY}/actions/runs/{run_id}/artifacts?per_page=100",
            token,
        )
        if type(metadata.get("artifacts")) is not list:
            raise TraceOriginError("ACTIONS_ARTIFACT_METADATA_INVALID")
        expected_name = f"core13-learning-traces-{run_id}-{attempt}"
        matching = [
            a for a in metadata["artifacts"] if type(a) is dict
            and a.get("name") == expected_name and a.get("expired") is False
            and type(a.get("workflow_run")) is dict
            and type(a["workflow_run"].get("id")) is int
            and a["workflow_run"]["id"] == run_id
            and a["workflow_run"].get("head_sha") == record["framework_sha"]
        ]
        if len(matching) != 1 or type(matching[0].get("id")) is not int:
            raise TraceOriginError("ACTIONS_ARTIFACT_NOT_UNIQUE")
        match = SHA256.fullmatch(str(matching[0].get("digest")))
        if match is None or hashlib.sha256(raw).hexdigest() != match.group(1):
            raise TraceOriginError("ACTIONS_ARTIFACT_DIGEST_INVALID")
    except actions.ActionsProvenanceError as exc:
        raise TraceOriginError("ACTIONS_METADATA_UNAVAILABLE") from exc

    return {
        "status": "GITHUB_ACTIONS_ARTIFACT_ORIGIN_VERIFIED",
        "repository": REPOSITORY,
        "run_id": run_id,
        "run_attempt": attempt,
        "framework_sha": record["framework_sha"],
        "artifact_id": matching[0]["id"],
        "archive_sha256": match.group(1),
        "bundle_sha256": hashlib.sha256(_canonical(bundle)).hexdigest(),
        "artifact_origin_metadata_verified": True,
        "trusted_producer_code_verified": False,
        "trace_semantics_verified": False,
        "learning_exposure_independently_verified": False,
        "effectiveness": "NOT_ESTABLISHED",
        "causation": "NOT_ESTABLISHED",
        "stable_ready": False,
    }


def reconcile_actions_trace_evidence(
    project_root: Path | str, intervention: Any, selection: Any,
    archive: Path | str, identity: Any, *, token: str | None,
) -> dict:
    """Require authenticated artifact bytes BEFORE existing local trace join."""
    try:
        _raw, bundle = _read_archive(archive)
        source = verify_actions_trace_origin(
            archive, bundle, identity, token=token,
        )
    except (TraceOriginError, TypeError, KeyError, AttributeError):
        return {
            "status": "DENIED", "reason_code": "TRACE_ORIGIN_UNVERIFIED",
            "artifact_origin_metadata_verified": False,
            "learning_exposure_independently_verified": False,
            "effectiveness": "NOT_ESTABLISHED", "causation": "NOT_ESTABLISHED",
            "stable_ready": False,
        }
    result = learning_exposure_traces.reconcile_learning_trace_claims(
        project_root, intervention, selection, bundle,
    )
    if result["status"] != "UNVERIFIED_TRACE_CLAIMS_RECONCILED":
        return {
            "status": "DENIED", "reason_code": result.get("reason_code", "TRACE_JOIN_FAILED"),
            "artifact_origin_metadata_verified": True,
            "learning_exposure_independently_verified": False,
            "effectiveness": "NOT_ESTABLISHED", "causation": "NOT_ESTABLISHED",
            "stable_ready": False,
        }
    if result["trace_bundle_sha256"] != source["bundle_sha256"]:
        return {
            "status": "DENIED", "reason_code": "TRACE_JOIN_DIGEST_MISMATCH",
            "artifact_origin_metadata_verified": True,
            "learning_exposure_independently_verified": False,
            "effectiveness": "NOT_ESTABLISHED", "causation": "NOT_ESTABLISHED",
            "stable_ready": False,
        }
    return {
        **result,
        "status": "ACTIONS_ORIGIN_VERIFIED_TRACE_CLAIMS_RECONCILED",
        "origin": source,
    }
