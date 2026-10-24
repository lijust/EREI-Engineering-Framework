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
import importlib.metadata, inspect, json, pathlib, runpy, sys, tempfile, types, unittest
requirements = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
if not isinstance(requirements, dict):
    raise RuntimeError("Pinned dependency manifest must be an object")
for package, expected in sorted(requirements.items()):
    if not isinstance(package, str) or not isinstance(expected, str) or not expected:
        raise RuntimeError("Invalid pinned dependency")
    observed = importlib.metadata.version(package)
    if observed != expected:
        raise RuntimeError("Pinned dependency mismatch: " + package +
                           " expected=" + expected + " observed=" + observed)
# Execute only pinned domain modules. The legacy core/desktop/extractors
# package initializers import unrelated desktop and optional online providers.
# Use namespace packages at these exact local paths without executing their
# __init__.py files. This is public calibration, not full-app integration.
root = pathlib.Path.cwd()
sys.path.insert(0, str(root))
for name in ("core", "core.ai", "desktop", "desktop.app", "extractors", "extractors.nawy"):
    location = root.joinpath(*name.split("."))
    if not location.is_dir():
        continue
    package = types.ModuleType(name)
    package.__path__ = [str(location)]
    package.__package__ = name
    sys.modules[name] = package
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


# Supplemental Framework-owned *public* behavioral oracle for APP-04.
# Unlike the pinned consumer's policy-string test, this calls the actual
# source function with an in-memory Master containing a numeric ID gap.
# The consumer test blob remains pinned and unmodified. No Sheets API calls.
APP04_NODE_ORACLE = r"""
'use strict';
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const source = fs.readFileSync(
  'apps/developer-validation-intake/MissingProjectInsertReadiness.gs', 'utf8'
);
const headers = [
  'developer_key', 'master_developer_id', 'developer_name_en',
  'developer_name_ar', 'mapping_status', 'source_developer_id',
  'source_developer_name', 'project_id', 'project_name_en',
  'project_name_ar', 'project_type', 'project_latitude', 'project_longitude'
];
const mockSheet = {
  getLastColumn: () => headers.length,
  getRange: () => ({getDisplayValues: () => [headers]})
};
const sandbox = {
  dviBuildState_: () => ({master: {getSheetByName: (name) =>
    name === 'developer_projects' ? mockSheet : null}}),
  dviRows_: () => [{project_id: '2'}, {project_id: '5'}],
  dviTrim_: (value) => String(value === null || value === undefined ? '' : value).trim()
};
vm.createContext(sandbox);
vm.runInContext(source, sandbox, {filename: 'MissingProjectInsertReadiness.gs', timeout: 1500});
const observed = vm.runInContext(
  'dviMissingProjectInsertMasterInventory_({})', sandbox, {timeout: 1500}
);
assert.strictEqual(observed.projectIdMin, 2);
assert.strictEqual(observed.projectIdMax, 5);
assert.strictEqual(observed.projectIdGapCount, 2);
assert.strictEqual(observed.projectIdNonblankAll, true);
assert.strictEqual(observed.projectIdUnique, true);
assert.strictEqual(observed.projectIdPositiveInteger, true);
assert.strictEqual(observed.projectIdNextCandidate, 6, 'APP04_MAX_PLUS_ONE_NO_GAP_REUSE');
// Extended public read-only oracle: test legitimate dense and gapped ID ranges,
// empty/blank, duplicates, invalid numeric IDs and safe-integer boundaries.
// This checks preview candidate arithmetic only, NOT concurrent locked writes.
const scenarios = [
  {name: 'dense', ids: ['1','2','3'], next: 4, gaps: 0},
  {name: 'singleton', ids: ['7'], next: 8, gaps: 0},
  {name: 'empty', ids: [], next: null, gaps: null},
  {name: 'duplicate', ids: ['1','1'], next: null, gaps: null},
  {name: 'blank', ids: ['1',''], next: null, gaps: 0},
  {name: 'leading_zero', ids: ['01','2'], next: null, gaps: null},
  {name: 'fractional', ids: ['1.5','2'], next: null, gaps: null},
  {name: 'zero', ids: ['0','2'], next: null, gaps: null},
  {name: 'safe_integer_limit', ids: ['9007199254740991'], next: null, gaps: 0},
  {name: 'unsafe_integer', ids: ['9007199254740992'], next: null, gaps: null},
  {name: 'multiple_holes', ids: ['4','9','12'], next: 13, gaps: 6},
];
for (const scenario of scenarios) {
  sandbox.dviRows_ = () => scenario.ids.map(project_id => ({project_id}));
  const value = vm.runInContext(
    'dviMissingProjectInsertMasterInventory_({})', sandbox, {timeout: 1500}
  );
  assert.strictEqual(value.projectIdNextCandidate, scenario.next,
                     'APP04_PREVIEW_CASE_' + scenario.name);
  assert.strictEqual(value.projectIdGapCount, scenario.gaps,
                     'APP04_GAP_CASE_' + scenario.name);
}
console.log('APP04_BEHAVIORAL_ORACLE_PASS');
"""


# Supplemental public APP-05 behavioral calibration oracle. This deliberately
# evaluates the generated *candidate* from pinned builder bytes, NOT the live
# consumer source or the original static builder test. Never calls buildCandidate:
# no Git HEAD check, source copy, Apps Script, deployment or filesystem mutation.
APP05_NODE_ORACLE = r"""
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

const original = fs.readFileSync('src/11_ErrorService.gs', 'utf8');
const builder = fs.readFileSync('tools/build-error-catalog-repository-candidate.js', 'utf8');
const candidateModule = {exports: {}};
vm.runInNewContext(builder, {
  module: candidateModule, require, console,
  __dirname: path.resolve('tools')
}, {filename: 'pinned-error-repository-builder.js', timeout: 1500});
const candidate = candidateModule.exports.candidateErrorServiceSource();
const repoPrefix = 'const ErrorCatalogRepository = (function() {';
const servicePrefix = 'const ErrorService = (function() {';
assert(candidate.startsWith(repoPrefix), 'APP05_REPOSITORY_STRUCTURE');
assert(candidate.includes(servicePrefix), 'APP05_REPOSITORY_STRUCTURE');
const serviceScope = candidate.slice(candidate.indexOf(servicePrefix));
assert(!/openSheetById_|getTable_|SpreadsheetApp|CacheService/.test(serviceScope),
       'APP05_REPOSITORY_STRUCTURE');
const repoScope = candidate.slice(0, candidate.indexOf(servicePrefix));
assert(repoScope.includes('openSheetById_') && repoScope.includes('getTable_'),
       'APP05_REPOSITORY_STRUCTURE');
assert(serviceScope.includes('ErrorCatalogRepository.catalog()'),
       'APP05_REPOSITORY_STRUCTURE');

const vectors = [
  ['SEARCH_LIMIT', {request_id: 'R1'}],
  ['NOT_FOUND', null],
  ['AUTH_LOGIN_REQUIRED', {reason: 'expired'}],
  ['SOMETHING_UNKNOWN', null],
  ['INTERNAL_ERROR', {trace: false}]
];
function run(source) {
  const counts = {open: 0, table: 0};
  const rows = [
    ['SEARCH_LIMIT', 'Search limit reached'],
    ['NOT_FOUND', 'Not found'],
    ['INTERNAL_ERROR', 'Internal fallback']
  ];
  const ctx = {
    EREI: {ADMIN_SHEETS: {ERRORS: '01_Errors'}},
    getAdminId_: () => 'ADMIN-ID',
    openSheetById_: (id, name) => {
      counts.open += 1;
      return {id, name};
    },
    getTable_: () => {
      counts.table += 1;
      return {headers: ['error_code', 'user_message'], rows: rows.map(r => r.slice())};
    },
    rowToObject_: (headers, row) =>
      Object.fromEntries(headers.map((h, i) => [h, row[i]])),
    normalizeString_: v => v === null || v === undefined ? '' : String(v).trim(),
    EreiError_: function(code, message, details, http) {
      this.code = code;
      this.message = message;
      this.details = details;
      this.http = http;
    }
  };
  vm.createContext(ctx);
  new vm.Script(source, {filename: '11_ErrorService.gs'}).runInContext(ctx, {timeout: 1500});
  const output = [];
  vectors.forEach(([code, details]) => {
    ctx.__code = code; ctx.__details = details;
    const item = vm.runInContext(
      '(function(){var e=ErrorService.fromCode(__code,__details);' +
      'return {code:e.code,message:e.message,details:e.details,http:e.http};})()',
      ctx, {timeout: 1500}
    );
    output.push(JSON.parse(JSON.stringify(item)));
  });
  return {output, counts};
}
const before = run(original);
const after = run(candidate);
assert.deepStrictEqual(after.output, before.output, 'APP05_OUTPUT_PARITY');
assert.deepStrictEqual(after.counts, {open: 1, table: 1},
                       'APP05_CACHE_LOAD_ONCE');
assert.deepStrictEqual(after.counts, before.counts, 'APP05_PROVIDER_PARITY');
console.log('APP05_BEHAVIORAL_ORACLE_PASS');
"""


# PY-03: a bounded Framework-owned public oracle for the exact pinned
# Nawy boundary class. Avoid importing the entire extractor stack or network
# clients. This exercises the unmodified class method AST with a minimal
# inherited _clean_text fixture; it is NOT the full original consumer test.
PY03_BOUNDARY_CHECK = r"""
import ast
import json
from pathlib import Path
from typing import Iterable
import unittest

path = Path('extractors/nawy/payment_section_boundary_extractor.py')
tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
classes = [item for item in tree.body
           if isinstance(item, ast.ClassDef) and item.name == 'NawyExtractor']
if len(classes) != 1:
    raise ValueError('Pinned payment boundary class not found exactly once')
method_names = {item.name for item in classes[0].body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))}
if method_names != {'_normalized_boundary_text', '_trim_payment_page_chrome',
                    '_payment_section_lines'}:
    raise ValueError('Unexpected payment boundary method inventory')
class _PaymentNawyExtractor:
    @staticmethod
    def _clean_text(value):
        # The public fixture contains plain text only: no HTML parsing or
        # higher-layer extractor dependencies are claimed here.
        return str(value).strip()
scope = {'Iterable': Iterable, '_PaymentNawyExtractor': _PaymentNawyExtractor}
module = ast.fix_missing_locations(ast.Module(body=classes, type_ignores=[]))
exec(compile(module, str(path), 'exec'), scope)
NawyExtractor = scope['NawyExtractor']

class BoundaryCases(unittest.TestCase):
    def test_exact_english_marker(self):
        lines = ['Original Plan', '5% Down Payment', '8 Years',
                 'Location on Map', 'Call Us', 'Top Searches']
        self.assertEqual(NawyExtractor._trim_payment_page_chrome(lines, locale='en'),
                         lines[:3])

    def test_exact_arabic_marker(self):
        lines = ['خطة الدفع الاصليه', '5% مقدم', '8 سنوات',
                 'الموقع على الخريطة', 'اتصل بنا', 'مناطق']
        self.assertEqual(NawyExtractor._trim_payment_page_chrome(lines, locale='ar'),
                         lines[:3])

    def test_exact_not_substring_boundary(self):
        lines = ['Original Plan', '5% Down Payment', '8 Years',
                 'Location on Map benefit included in project access',
                 'Call Us', 'Top Searches']
        self.assertEqual(
            NawyExtractor._trim_payment_page_chrome(lines, locale='en'),
            lines[:4], 'PY03_EXACT_NOT_SUBSTRING_BOUNDARY'
        )

suite = unittest.defaultTestLoader.loadTestsFromTestCase(BoundaryCases)
result = unittest.TestResult()
suite.run(result)
print(json.dumps({
    'tests': result.testsRun,
    'failures': [case.id().split('.')[-1] for case, _ in result.failures],
    'errors': [case.id().split('.')[-1] for case, _ in result.errors],
    'skipped': len(result.skipped),
}))
raise SystemExit(0 if result.wasSuccessful() else 1)
"""



def forbid_checkout_local_exports(exports: Path) -> None:
    """Prevent private consumer source copies from living under public Framework git."""
    framework_checkout = Path(__file__).resolve().parents[2]
    resolved = exports.resolve()
    if resolved.is_relative_to(framework_checkout):
        raise ValueError(
            "Private consumer source exports must remain outside the public "
            "Framework checkout; never commit or upload them as CI artifacts"
        )


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
            if package.get("behavioral_oracle") == "APP04_PROJECT_ID_MAX_PLUS_ONE":
                command = [node, "-e", APP04_NODE_ORACLE]
            elif package.get("behavioral_oracle") == "APP05_REPOSITORY_CACHE_PARITY":
                command = [node, "-e", APP05_NODE_ORACLE]
            elif "behavioral_oracle" in package:
                raise ValueError("Unknown public behavioral oracle")
            else:
                command = [node, package["test_path"]]
        elif package["runtime"] == "python":
            if package.get("behavioral_oracle") == "PY03_NAWY_EXACT_BOUNDARY":
                command = [sys.executable, "-I", "-S", "-B", "-c", PY03_BOUNDARY_CHECK]
            elif "behavioral_oracle" in package:
                raise ValueError("Unknown public Python behavioral oracle")
            else:
                dependencies = package.get("dependency_versions", {})
                if not isinstance(dependencies, dict):
                    raise ValueError("dependency_versions must be a pinned mapping")
                for name, version in dependencies.items():
                    if (not isinstance(name, str) or not isinstance(version, str)
                            or not name or not version):
                        raise ValueError("invalid pinned dependency")
                isolation = ["-I", "-B"] if dependencies else ["-I", "-S", "-B"]
                command = [sys.executable, *isolation, "-c", PYTHON_CHECK,
                           package["test_path"], json.dumps(package["python_tests"]),
                           json.dumps(dependencies, sort_keys=True)]
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
        if package.get("behavioral_oracle") in (
                "APP04_PROJECT_ID_MAX_PLUS_ONE", "APP05_REPOSITORY_CACHE_PARITY"):
            required = {
                "APP04_PROJECT_ID_MAX_PLUS_ONE": (
                    "APP04_BEHAVIORAL_ORACLE_PASS", "APP04_MAX_PLUS_ONE_NO_GAP_REUSE"),
                "APP05_REPOSITORY_CACHE_PARITY": (
                    "APP05_BEHAVIORAL_ORACLE_PASS", "APP05_CACHE_LOAD_ONCE"),
            }[package["behavioral_oracle"]]
            success, expected_assertion = required
            if package.get("expected_assertion") != expected_assertion:
                return False
            # A visible expected token anywhere in stderr is not enough:
            # tie the one expected assertion to an actual Node -e eval frame,
            # and reject unrelated structure/parity assertions and startup errors.
            error = (r"(?m)^AssertionError \[ERR_ASSERTION\]: "
                     + re.escape(expected_assertion) + r"\r?$")
            frame = r"(?m)^ +at (?:[^\r\n]*\()?\[eval\]:\d+:\d+\)?\r?$"
            stderr = starter.get("stderr", "")
            return (reference.get("stdout", "").strip() == success
                    and not reference.get("stderr", "")
                    and len(re.findall(error, stderr)) == 1
                    and re.search(frame, stderr) is not None)
        if "behavioral_oracle" in package:
            return False
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



def sanitized_result(record: dict) -> dict:
    """Only export digests/counts, never private consumer output or trace text."""
    output = {"returncode": record["returncode"]}
    for channel in ("stdout", "stderr"):
        raw = record.get(channel, "")
        output[channel + "_sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        output[channel + "_nonempty"] = bool(raw)
    checks = record.get("checks")
    if checks is not None:
        output["checks"] = {
            "tests": checks["tests"],
            "failed_count": len(checks["failures"]),
            "error_count": len(checks["errors"]),
            "skipped_count": checks["skipped"],
        }
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-exports", type=Path, required=True,
                        help="Directory containing pinned app/ and py/ exports")
    parser.add_argument("--task", help="One package ID; default checks all prepared packages")
    parser.add_argument("--node", default=shutil.which("node"))
    args = parser.parse_args()
    try:
        forbid_checkout_local_exports(args.source_exports)
    except ValueError as exc:
        parser.exit(2, f"calibration source boundary: {exc}\n")
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
        records.append({
            "task_id": package["task_id"],
            "reference": sanitized_result(baseline),
            "starter": sanitized_result(mutant),
            "calibration_passed": assess(package, baseline, mutant),
        })
    report = {"kind": "PUBLIC_CALIBRATION_ONLY", "model_executions": 0,
              "independent_review": "NOT_PERFORMED",
              "effectiveness": "NOT_ESTABLISHED", "python": sys.version,
              "catalog_sha256": hashlib.sha256(catalog_bytes).hexdigest(), "results": records}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if records and all(r["calibration_passed"] for r in records) else 1


def entrypoint() -> int:
    """Never spill original consumer paths/data/tracebacks via CLI exceptions."""
    try:
        return main()
    except Exception as exc:
        # Keep diagnostics in a separately authorized private session. Output
        # includes no exception message, traceback, export path or source data.
        print(json.dumps({
            "kind": "PUBLIC_CALIBRATION_ERROR",
            "status": "FAIL_CLOSED",
            "error_type": type(exc).__name__,
            "model_executions": 0,
            "independent_review": "NOT_PERFORMED",
        }), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(entrypoint())
