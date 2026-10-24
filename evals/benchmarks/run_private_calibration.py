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
import os
import platform
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import check_calibration
import prepare_private_exports

TASK_ID = re.compile(r"(?:APP|PY)-0[1-6]\Z")
GIT_SHA = re.compile(r"[a-f0-9]{40}\Z")
FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]


def verified_framework_checkout() -> str:
    """Bind evidence to an exact clean checkout without inherited Git redirection."""
    # GIT_DIR/GIT_WORK_TREE override -C repository selection. All inherited
    # GIT_* variables are unnecessary for local read-only source attestation,
    # including GIT_INDEX_FILE and injected Git config/alternate object stores.
    isolated_env = {
        key: value for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
    }
    expected_root = FRAMEWORK_ROOT.resolve()
    for args in (("rev-parse", "--show-toplevel"),
                 ("rev-parse", "--verify", "HEAD"),
                 ("status", "--porcelain", "--untracked-files=all")):
        result = subprocess.run(
            ["git", "-C", str(FRAMEWORK_ROOT), *args],
            shell=False, stdin=subprocess.DEVNULL, capture_output=True,
            timeout=15, check=False, env=isolated_env,
        )
        if result.returncode:
            raise ValueError("Cannot bind calibration to a Git checkout")
        if args[1] == "--show-toplevel":
            toplevel = result.stdout.decode("utf-8", errors="replace").strip()
            if not toplevel or Path(toplevel).resolve() != expected_root:
                raise ValueError("Git checkout root is not Framework")
        elif args[0] == "rev-parse":
            head = result.stdout.decode("ascii", errors="replace").strip()
            if not GIT_SHA.fullmatch(head):
                raise ValueError("Invalid Framework HEAD SHA")
        elif result.stdout.strip():
            raise ValueError("Framework checkout must be clean before calibration")
    return head


def execution_scope(package: dict) -> str:
    if package.get("behavioral_oracle"):
        return "FRAMEWORK_OWNED_BOUNDED_SOURCE_BEHAVIOR_ORACLE"
    if package["runtime"] == "python":
        return "UNCHANGED_ORIGINAL_CONSUMER_FUNCTIONS_OFFLINE_UNITTEST_ADAPTER"
    return "UNCHANGED_ORIGINAL_NODE_CONSUMER_TEST"



def run_one(task: str) -> dict:
    if not TASK_ID.fullmatch(task):
        raise ValueError("Expected one explicit pinned APP-0X or PY-0X task")
    catalog_bytes = check_calibration.CATALOG.read_bytes()
    catalog = json.loads(catalog_bytes)
    matched = [p for p in catalog["packages"] if p["task_id"] == task]
    if len(matched) != 1:
        raise ValueError("Missing or duplicate pinned task")
    package = matched[0]
    framework_commit = verified_framework_checkout()
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
            "framework_commit_sha": framework_commit,
            "consumer_source_repository": package["source"]["repository"],
            "consumer_source_commit_sha": package["source"]["commit"],
            "python_runtime_version": platform.python_version(),
            "host_os_family": platform.system(),
            "execution_scope": execution_scope(package),
            "task_id": task,
            "catalog_sha256": hashlib.sha256(catalog_bytes).hexdigest(),
            "pinned_files_verified": exporter_report["file_count"],
            "reference": check_calibration.sanitized_result(reference),
            "starter": check_calibration.sanitized_result(mutant),
            "public_calibration_passed": qualified,
            "private_export_cleaned_on_exit": True,
            "original_consumer_test_blob_unchanged": True,
            "original_consumer_test_executed": not bool(package.get("behavioral_oracle")),
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
        result = run_one(args.task.strip().upper())
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
