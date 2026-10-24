"""One-task, private, opt-in source calibration with automatic byte cleanup.

This is a local operator command, NOT a public hosted-GitHub-Actions job.
Requires an authenticated local GitHub CLI with permission to read the pinned
private source repositories. No model/API trial, promotion, merge or release.
The immutable original consumer code runs only in temp folders; output is
published only after the calibration checker removes original stdout/stderr.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile

import check_calibration
import prepare_private_exports

TASK_ID = re.compile(r"(?:APP|PY)-0[1-6]\Z")


def run_one(task: str) -> dict:
    if not TASK_ID.fullmatch(task):
        raise ValueError("Expected one explicit pinned APP-0X or PY-0X task")
    catalog_bytes = check_calibration.CATALOG.read_bytes()
    catalog = json.loads(catalog_bytes)
    matched = [p for p in catalog["packages"] if p["task_id"] == task]
    if len(matched) != 1:
        raise ValueError("Missing or duplicate pinned task")
    package = matched[0]
    # Never let any consumer bytes, error traces or private auth metadata
    # become an artifact inside a public Git checkout.
    with tempfile.TemporaryDirectory(prefix="erei-operator-private-") as directory:
        outer = Path(directory).resolve()
        if outer.is_relative_to(Path(__file__).resolve().parents[2]):
            raise ValueError("System temp cannot be inside public checkout")
        private_dir = outer / "pinned-original-sources"
        exporter_report = prepare_private_exports.prepare(private_dir, task)
        if exporter_report["file_count"] != len(package["files"]):
            raise ValueError("Unexpected private file inventory")
        originals = check_calibration.read_inputs(package, private_dir)
        mutants = check_calibration.starter_inputs(package, originals)
        node = check_calibration.shutil.which("node")
        reference = check_calibration.run_copy(package, originals, node)
        mutant = check_calibration.run_copy(package, mutants, node)
        qualified = check_calibration.assess(package, reference, mutant)
        # All raw consumer traces stay inside this process; exported report
        # contains only public-safe aggregates, return codes, stdout digests.
        return {
            "kind": "SELF_REPORTED_PRIVATE_SOURCE_CALIBRATION",
            "task_id": task,
            "catalog_sha256": hashlib.sha256(catalog_bytes).hexdigest(),
            "pinned_files_verified": exporter_report["file_count"],
            "reference": check_calibration.sanitized_result(reference),
            "starter": check_calibration.sanitized_result(mutant),
            "public_calibration_passed": qualified,
            "private_export_cleaned_on_exit": True,
            "original_consumer_test_blob_unchanged": True,
            "model_executions": 0,
            "independent_review": "NOT_PERFORMED",
            "hidden_acceptance": "NOT_PERFORMED",
            "effectiveness": "NOT_ESTABLISHED",
            "release_authorized": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True,
                        help="One task at a time, e.g. PY-04; never batch by default")
    args = parser.parse_args()
    try:
        result = run_one(args.task)
    except Exception as exc:
        # Do not emit original private exception message, file path, test
        # stderr, provider credential, gh stderr, or traceback.
        print(json.dumps({
            "kind": "PRIVATE_CALIBRATION_FAIL_CLOSED",
            "error_type": type(exc).__name__,
            "model_executions": 0,
            "release_authorized": False,
        }), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["public_calibration_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
