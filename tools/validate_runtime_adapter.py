#!/usr/bin/env python3
"""Strict dependency-free validation for EREI Runtime Adapter V1 manifests."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validation_contract import ContractValidationError, validate_runtime_adapter_shape


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
    try:
        validate_runtime_adapter_shape(data)
    except ContractValidationError as exc:
        raise ValidationError(str(exc)) from exc
    return {
        "adapter_id": data["adapter_id"],
        "status": data["status"],
        "transport": data["transport"],
        "capabilities": sorted(data["capabilities"]),
        "valid": True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    args = parser.parse_args(argv)
    try:
        result = validate_manifest(load(args.manifest))
    except ValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
