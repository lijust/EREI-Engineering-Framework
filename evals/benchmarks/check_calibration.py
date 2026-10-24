"""Opt-in, offline feasibility check for pinned public calibration recipes.

Runs reviewed consumer tests on temporary copies, never on the supplied exports.
This is not a sandbox for model-submitted code or an AI benchmark runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile


CATALOG = Path(__file__).with_name("calibration-packages.json")
# These pinned Python files use plain assertions and only the tmp_path fixture.
# Execute their unchanged functions using unittest, without a pytest dependency.
PYTHON_CHECK = r"""
import inspect, json, pathlib, runpy, sys, tempfile, unittest
sys.path.insert(0, str(pathlib.Path.cwd()))
namespace = runpy.run_path(sys.argv[1])
names = json.loads(sys.argv[2])
assert sorted(names) == sorted(k for k in namespace if k.startswith("test_"))
suite = unittest.TestSuite()
def invoke(function):
    parameters = list(inspect.signature(function).parameters)
    if not parameters:
        return function()
    if parameters != ["tmp_path"]:
        raise RuntimeError("Unsupported fixture signature")
    with tempfile.TemporaryDirectory(prefix="fixture-", dir=".") as folder:
        function(pathlib.Path(folder))
for name in names:
    function = namespace[name]
    suite.addTest(unittest.FunctionTestCase(
        lambda f=function: invoke(f), description=name))
result = unittest.TestResult()
suite.run(result)
print(json.dumps({
    "tests": result.testsRun,
    "failures": [case.shortDescription() for case, _ in result.failures],
    "errors": [case.shortDescription() for case, _ in result.errors],
    "skipped": len(result.skipped),
}))
sys.exit(0 if result.wasSuccessful() else 1)
"""


def relative_path(value: str) -> Path:
    posix = PurePosixPath(value)
    if (not value or "\\" in value or ":" in value or posix.is_absolute()
            or ".." in posix.parts or str(posix) != value):
        raise ValueError(f"Unsafe recipe path: {value}")
    return Path(*posix.parts)


def read_inputs(package: dict, exports: Path) -> dict[str, bytes]:
    root = (exports / relative_path(package["source"]["export_directory"])).resolve()
    inputs = {}
    for item in package["files"]:
        name = item["path"]
        if name in inputs:
            raise ValueError("Duplicate input")
        source = (root / relative_path(name)).resolve()
        if not source.is_relative_to(root):
            raise ValueError("Input escapes source export")
        data = source.read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if blob != item["git_blob"]:
            raise ValueError(f"Source blob mismatch: {name}")
        inputs[name] = data
    if package["test_path"] not in inputs:
        raise ValueError("Test is not a pinned input")
    return inputs


def starter_inputs(package: dict, reference: dict[str, bytes]) -> dict[str, bytes]:
    mutation = package["mutation"]
    name = mutation["path"]
    if name == package["test_path"]:
        raise ValueError("Mutation cannot change the test")
    before, after = mutation["before"].encode(), mutation["after"].encode()
    if not before or before == after or reference[name].count(before) != 1:
        raise ValueError("Mutation must change exactly one source occurrence")
    starter = dict(reference)
    starter[name] = reference[name].replace(before, after, 1)
    hashes = {key: hashlib.sha256(data).hexdigest() for key, data in starter.items()}
    if hashes != package["starter_file_sha256"]:
        raise ValueError("Starter fixture digest mismatch")
    return starter


def run_copy(package: dict, inputs: dict[str, bytes], node: str | None) -> dict:
    with tempfile.TemporaryDirectory(prefix="erei-calibration-") as folder:
        root = Path(folder)
        for name, data in inputs.items():
            target = root / relative_path(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        if package["runtime"] == "node":
            if not node:
                raise ValueError("Node executable is required for App calibration")
            command = [node, package["test_path"]]
        elif package["runtime"] == "python":
            command = [sys.executable, "-I", "-S", "-B", "-c", PYTHON_CHECK,
                       package["test_path"], json.dumps(package["python_tests"])]
        else:
            raise ValueError("Unsupported calibration runtime")
        # Avoid NODE_OPTIONS, PYTHONPATH, provider credentials and test plugins.
        env = {key: value for key, value in os.environ.items()
               if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "COMSPEC"}}
        env.update(TEMP=folder, TMP=folder, TMPDIR=folder)
        result = subprocess.run(command, cwd=root, env=env, shell=False,
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=30)
        record = {"returncode": result.returncode, "stdout": result.stdout,
                  "stderr": result.stderr}
        if package["runtime"] == "python":
            record["checks"] = json.loads(result.stdout)
        return record


def assess(package: dict, reference: dict, starter: dict) -> bool:
    if reference["returncode"] != 0 or starter["returncode"] != 1:
        return False
    if package["runtime"] == "node":
        line = package.get("expected_assertion_line")
        if type(line) is not int or line <= 0:
            return False
        # The test blob is pinned: bind detection to its expected assertion site,
        # not any unrelated ERR_ASSERTION from another line or source file.
        location = re.escape("/" + package["test_path"]) + f":{line}:" + r"\d+\)?\s*$"
        stderr = starter["stderr"].replace("\\", "/")
        return ("AssertionError [ERR_ASSERTION]" in stderr
                and package["expected_assertion"] in stderr
                and re.search(r"(?m)^ +at [^\r\n]*" + location, stderr) is not None)
    expected_count = len(package["python_tests"])
    for record in (reference, starter):
        checks = record["checks"]
        if checks["tests"] != expected_count or checks["errors"] or checks["skipped"]:
            return False
    # Reject off-target assertion failures: a mutant failing the intended
    # regression *and* another test is not isolated calibration evidence.
    return (not reference["checks"]["failures"]
            and starter["checks"]["failures"] == [package["expected_assertion"]])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-exports", type=Path, required=True,
                        help="Directory containing pinned app/ and py/ exports")
    parser.add_argument("--task", help="One package ID; default checks all prepared packages")
    parser.add_argument("--node", default=shutil.which("node"))
    args = parser.parse_args()
    catalog_bytes = CATALOG.read_bytes()
    packages = json.loads(catalog_bytes)["packages"]
    if args.task:
        packages = [p for p in packages if p["task_id"] == args.task]
        if not packages:
            parser.error("Task has no prepared calibration recipe")
    # Preflight every selected input before executing any consumer code.
    prepared = []
    for package in packages:
        reference = read_inputs(package, args.source_exports)
        prepared.append((package, reference, starter_inputs(package, reference)))
    records = []
    for package, reference, starter in prepared:
        baseline = run_copy(package, reference, args.node)
        mutant = run_copy(package, starter, args.node)
        records.append({"task_id": package["task_id"], "reference": baseline,
                        "starter": mutant, "calibration_passed": assess(package, baseline, mutant)})
    report = {"kind": "PUBLIC_CALIBRATION_ONLY", "model_executions": 0,
              "independent_review": "NOT_PERFORMED",
              "effectiveness": "NOT_ESTABLISHED", "python": sys.version,
              "catalog_sha256": hashlib.sha256(catalog_bytes).hexdigest(), "results": records}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if records and all(r["calibration_passed"] for r in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
