#!/usr/bin/env python3
"""Validate EREI Runtime Adapter V1 manifests without third-party dependencies."""

import argparse
import json
import sys
from pathlib import Path

CAPABILITIES = {
    "execute_task", "resume_session", "cancel_task", "read_workspace", "write_workspace",
    "shared_context", "artifact_handoff", "parallel_agents", "agent_handoff",
    "interactive_approval", "interactive_input", "tool_policy", "mutation_policy",
    "trace_export", "session_persistence", "runtime_recovery"
}
STATUSES = {"experimental", "candidate", "stable", "deprecated"}
TRANSPORTS = {"cli", "http", "rpc", "desktop-daemon", "native", "instructions"}
REQUIRED = {"schema_version", "adapter_id", "display_name", "version", "status", "runtime_kind", "transport", "capabilities"}


class ValidationError(Exception):
    pass


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON: {path}: {exc}") from exc


def validate_manifest(data):
    if not isinstance(data, dict):
        raise ValidationError("manifest must be a JSON object")
    missing = sorted(REQUIRED - set(data))
    if missing:
        raise ValidationError("missing required fields: " + ", ".join(missing))
    if data["schema_version"] != 1:
        raise ValidationError("unsupported schema_version")
    aid = data["adapter_id"]
    if not isinstance(aid, str) or not aid or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in aid) or not aid[0].isalnum():
        raise ValidationError("invalid adapter_id")
    if data["status"] not in STATUSES:
        raise ValidationError("invalid status")
    if data["transport"] not in TRANSPORTS:
        raise ValidationError("invalid transport")
    caps = data["capabilities"]
    if not isinstance(caps, list) or len(caps) != len(set(caps)):
        raise ValidationError("capabilities must be a unique array")
    unknown = sorted(set(caps) - CAPABILITIES)
    if unknown:
        raise ValidationError("unknown standardized capabilities: " + ", ".join(unknown))
    if data["status"] == "stable" and not data.get("sources"):
        raise ValidationError("stable adapters require a sources reference")
    return {
        "adapter_id": data["adapter_id"],
        "status": data["status"],
        "transport": data["transport"],
        "capabilities": sorted(caps),
        "valid": True
    }


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("manifest")
    args = p.parse_args(argv)
    try:
        result = validate_manifest(load(args.manifest))
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
