"""Conservative, public-only T15 source-evidence status summarizer.

Reads pinned public recipes + sanitized, self-reported observations only.
This is NOT an independent acceptance evaluator or model benchmark engine.
No network, consumer code execution, private file access or model calls.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "calibration-packages.json"
RECEIPT = ROOT / "public-source-oracle-observation.2026-10-24.json"
LATEST_INDEX = ROOT / "public-operator-calibration-index.2026-10-25.json"

FULL = "ORIGINAL_CONSUMER_FILE_SELF_REPORTED_OFFLINE"
PARTIAL = "ORIGINAL_CONSUMER_FUNCTION_PARTIAL_SELF_REPORTED"
V8 = "ORIGINAL_JS_TEST_TEXT_V8_SHIMS_ONLY"
METHOD = "DIRECT_PINNED_SOURCE_METHOD_ONLY"
STUBBED_METHOD = "PINNED_PYTHON_SOURCE_METHOD_WITH_DEPENDENCY_STUBS"
STRUCTURAL = "PINNED_SOURCE_STRUCTURAL_INTERPRETATION_ONLY"
NONE = "NO_SOURCE_EXECUTION_RECORDED"


def summarize(catalog: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    if catalog.get("execution_authorized") is not False:
        raise ValueError("Public catalog unexpectedly authorizes execution")
    authority = receipt.get("authority", {})
    if (authority.get("execution_authorized") is not False
            or authority.get("model_executions") != 0
            or authority.get("independent_review") != "NOT_PERFORMED"
            or authority.get("stable_release") != "BLOCKED"
            or authority.get("sampled_study_runs") != "0/48"
            or authority.get("exact_target_runtime_evidence") != "0/13"):
        raise ValueError("Public observations may not upgrade study/release authority")
    if receipt.get("classification") != "SELF_REPORTED_UNATTESTED_SOURCE_EXECUTION":
        raise ValueError("Only unreviewed source observations may be summarized")
    packages = catalog["packages"]
    ids = [p["task_id"] for p in packages]
    if len(ids) != 12 or len(set(ids)) != 12 or not all(
            p["state"] == "PUBLIC_CALIBRATION_ONLY" for p in packages):
        raise ValueError("Expected twelve distinct public-only pinned recipes")
    records = receipt.get("source_executions", [])
    observed = {r["task_id"]: r for r in records}
    if len(observed) != len(records) or not set(observed).issubset(ids):
        raise ValueError("Duplicate or unknown source observation")
    structural_records = receipt.get("source_structural_observations", [])
    structural = {r["task_id"]: r for r in structural_records}
    if (len(structural) != len(structural_records)
            or not set(structural).issubset(ids)
            or set(structural).intersection(observed)):
        raise ValueError("Duplicate, overlapping or unknown structural source observation")
    statuses: dict[str, str] = {}
    for task in ids:
        r = observed.get(task)
        if r is None and task in structural:
            entry = structural[task]
            snapshot = entry.get("observation", {})
            if not (task == "PY-04"
                    and entry.get("source_invoked") == "NOT_EXECUTED_PYTHON_SOURCE"
                    and entry.get("original_consumer_test_executed") is False
                    and entry.get("python_runtime_executed") is False
                    and snapshot.get("registry_tokens") == 20
                    and snapshot.get("baseline_full_tokens") == 20
                    and snapshot.get("mutant_full_tokens") == 19
                    and snapshot.get("registry_tokens_unique") is True
                    and snapshot.get("reference_equals_registry") is True
                    and snapshot.get("mutant_equals_registry") is False
                    and snapshot.get("mutation_exact_one_occurrence") is True
                    and snapshot.get("original_consumer_assertion_present") is True):
                raise ValueError("Structural PY-04 evidence may not count as runtime execution")
            status = STRUCTURAL
        elif r is None:
            status = NONE
        elif r.get("original_consumer_run", {}).get("reference_exit_code") == 0:
            if (task != "APP-06"
                    or r["original_consumer_run"].get("mutant_exit_code") != 1):
                raise ValueError("Unrecognized complete Node consumer evidence")
            status = FULL
        elif r.get("original_consumer_run", {}).get("reference", {}).get("passed") in (4, 6):
            original = r["original_consumer_run"]
            if (task not in {"PY-02", "PY-04", "PY-05"}
                    or original["mutant"].get("failed") != 1
                    or original["mutant"].get("passed") != original["tests_defined"] - 1
                    or original["reference"]["passed"] != original["tests_defined"]
                    or original["reference"].get("failed") != 0
                    or original["reference"].get("errors") != 0
                    or original["mutant"].get("errors") != 0):
                raise ValueError("Invalid Python original consumer evidence")
            if task == "PY-04":
                rejected = original.get("initial_mutant_rejected", {})
                expected = "test_full_project_details_preset_tracks_registry_without_duplicate_allowlist"
                if (original.get("tests_defined") != 6
                        or original.get("python_version") != "3.13.5"
                        or rejected.get("failed") != 2
                        or original["mutant"].get("failed_name") != expected
                        or original["mutant"].get("starter_sha256") !=
                        "1a78015a1acc1ce4225b406c232c81de5aac9f05d46452aa7cc0e7e57b879ff0"
                        or r.get("original_consumer_test_executed") is not True
                        or r.get("independent_reviewer") is not False):
                    raise ValueError("PY-04 original consumer calibration must document rejected off-target mutant")
            status = FULL
        elif task == "PY-03":
            limited = r.get("unchanged_original_consumer_test", {})
            if limited.get("executed") != 1 or limited.get("total_defined") != 3:
                raise ValueError("Incorrect partial Python consumer coverage")
            status = PARTIAL
        elif task in {"APP-01", "APP-02", "APP-03"}:
            if not (r.get("unchanged_original_consumer_test_text_executed") is True
                    and r.get("full_node_runtime_executed") is False
                    and r.get("reference", {}).get("status") == "PASS"
                    and r.get("single_mutant", {}).get("status") == "FAIL"):
                raise ValueError("Cannot promote virtualized JS consumer run")
            status = V8
        elif task in {"PY-01", "PY-06"}:
            original_method = {
                "PY-01": ("SemanticPaymentPlanNormalizer.normalize", 2900, "ba77f4a0",
                          "provider_specific_failure"),
                "PY-06": ("_validate_grounding", 1825, "9177ac80",
                          "derived_8years_to_96months"),
            }[task]
            excerpt = r.get("source_excerpt", {})
            checks = r.get("checks", {})
            if (r.get("source_method") != original_method[0]
                    or excerpt.get("length_bytes_ascii") != original_method[1]
                    or excerpt.get("weak_fnv1a32") != original_method[2]
                    or excerpt.get("method_executed_with_original_function_body") is not True
                    or excerpt.get("isolated_private_temp_deleted") is not True
                    or r.get("original_consumer_test_executed") is not False
                    or checks.get("total") != 5 or checks.get("reference_pass") != 5
                    or checks.get("expected_mutant_discrimination") != 1
                    or checks.get("mutant_different_in_only_case") != original_method[3]
                    or checks.get("unchanged_negative_controls") != 4
                    or not r.get("stubbed_dependencies")
                    or r.get("independent_reviewer") is not False):
                raise ValueError("Pinned Python method smoke cannot become full consumer acceptance")
            status = STUBBED_METHOD
        elif task in {"APP-04", "APP-05"}:
            if task == "APP-04":
                test = r.get("original_unchanged_consumer_test_probe", {})
                if not (test.get("mutant_detected") is False
                        and test.get("mutant_result") == "PASS"
                        and test.get("behavioral_oracle_catches_mutation") is True):
                    raise ValueError("APP-04 original consumer false-negative not acknowledged")
            status = METHOD
        else:
            raise ValueError("Unrecognized evidence must not promote task")
        statuses[task] = status
    counts = {state: sum(item == state for item in statuses.values())
              for state in (FULL, PARTIAL, V8, METHOD, STUBBED_METHOD, STRUCTURAL, NONE)}
    if sum(counts.values()) != 12:
        raise ValueError("Evidence denominator changed")
    return {
        "kind": "PUBLIC_T15_EVIDENCE_CLASSIFICATION",
        "recipe_preparation": "12/12",
        "source_behavior_observations": f"{len(observed)}/12",
        "source_structural_observations": f"{len(structural)}/12",
        "source_evidence_coverage": f"{len(observed) + len(structural)}/12",
        "task_states": statuses,
        "stage_counts": counts,
        "independent_full_source_calibrations": "0/12",
        "independent_acceptance": "NOT_PERFORMED",
        "model_comparisons": "0/48",
        "exact_target_runtime_evidence": "0/13",
        "effectiveness": "NOT_ESTABLISHED",
        "stable_release": "BLOCKED",
        "release_authorized": False,
    }



def summarize_current_operator(catalog: dict[str, Any], index: dict[str, Any],
                               catalog_bytes: bytes) -> dict[str, Any]:
    """Count sanitized, SHA-bound *operator claims* without promoting authority.

    The 2026-10-24 source-oracle file remains historical and immutable.
    Origin (original versus Framework oracle) and environment (offline
    emulator versus function adapter) remain separate dimensions.
    """
    # The Windows operator receipt hashed the raw catalog *CRLF* bytes;
    # GitHub's canonical blob is LF and valid Linux checkouts also use LF.
    # Keep BOTH fixed SHA-256 identities (not just a caller-chosen digest).
    # Normalizing only line endings does not permit modified JSON semantics.
    lf_catalog = catalog_bytes.replace(b"\r\n", b"\n")
    if b"\r" in lf_catalog:
        raise ValueError("Unbound or untrusted operator observation index")
    actual_lf = hashlib.sha256(lf_catalog).hexdigest()
    actual_original_crlf = hashlib.sha256(
        lf_catalog.replace(b"\n", b"\r\n")
    ).hexdigest()
    if (catalog.get("execution_authorized") is not False
            or index.get("kind") != "SELF_REPORTED_OPERATOR_CALIBRATION_INDEX"
            or index.get("schema_version") != 1
            or index.get("evidence_origin")
            != "OPERATOR_SUPPLIED_SANITIZED_CLI_OUTPUT_NOT_INDEPENDENTLY_WITNESSED"
            or actual_lf
            != "9039f6bd9e3a8bff54f9cb13dcd712bac9aaa61ac3069902c96cafda35aeb1ef"
            or index.get("catalog_canonical_lf_sha256") != actual_lf
            or actual_original_crlf
            != "53eb055dd5b1f3d174ac0fe52d44a304b3f39118b984e5b15b6485f8a1d69b4a"
            or index.get("catalog_sha256") != actual_original_crlf
            or index.get("framework_commit_sha")
            != "8bc26deddcb9ebd10c24d5cb482b6b8e50827d9d"):
        raise ValueError("Unbound or untrusted operator observation index")

    forbidden_authority = {
        "execution_authorized": False, "model_executions": 0,
        "independent_review": "NOT_PERFORMED",
        "hidden_acceptance": "NOT_PERFORMED",
        "model_comparisons": "0/48",
        "exact_target_runtime_evidence": "0/13",
        "internal_admission": "HOLD_NOT_ADMITTED",
        "stable_release": "BLOCKED",
        "release_authorized": False,
        "effectiveness": "NOT_ESTABLISHED",
    }
    if index.get("authority") != forbidden_authority:
        raise ValueError("Operator data cannot grant review, pilot or release authority")
    expected = {package["task_id"]: package for package in catalog["packages"]}
    records = index.get("observations")
    if (len(expected) != 12 or not isinstance(records, list)
            or len(records) != 12):
        raise ValueError("Expected twelve immutable source calibration tasks")
    source_env = {
        "APP-01": ("ORIGINAL_CONSUMER_TEST_FILE",
                   "NODE_OFFLINE_WITH_APPS_SCRIPT_SHIMS", False, None),
        "APP-02": ("ORIGINAL_CONSUMER_TEST_FILE",
                   "NODE_OFFLINE_WITH_APPS_SCRIPT_SHIMS", False, None),
        "APP-03": ("ORIGINAL_CONSUMER_TEST_FILE",
                   "NODE_OFFLINE_WITH_APPS_SCRIPT_SHIMS", False, None),
        "APP-04": ("FRAMEWORK_OWNED_BOUNDED_ORACLE",
                   "NODE_OFFLINE_VM_SOURCE_BEHAVIOR", False, None),
        "APP-05": ("FRAMEWORK_OWNED_BOUNDED_ORACLE",
                   "NODE_OFFLINE_VM_SOURCE_BEHAVIOR", False, None),
        "APP-06": ("ORIGINAL_CONSUMER_TEST_FILE",
                   "NODE_OFFLINE_ORIGINAL_CONSUMER_TEST", True, None),
        "PY-01": ("ORIGINAL_CONSUMER_TEST_FILE",
                   "PYTHON_OFFLINE_UNITTEST_FUNCTION_ADAPTER", True, 20),
        "PY-02": ("ORIGINAL_CONSUMER_TEST_FILE",
                   "PYTHON_OFFLINE_UNITTEST_FUNCTION_ADAPTER", True, 4),
        "PY-03": ("FRAMEWORK_OWNED_BOUNDED_ORACLE",
                   "PYTHON_OFFLINE_AST_BOUNDARY_METHOD_ORACLE", False, 3),
        "PY-04": ("ORIGINAL_CONSUMER_TEST_FILE",
                   "PYTHON_OFFLINE_UNITTEST_FUNCTION_ADAPTER", True, 6),
        "PY-05": ("ORIGINAL_CONSUMER_TEST_FILE",
                   "PYTHON_OFFLINE_UNITTEST_FUNCTION_ADAPTER", True, 6),
        "PY-06": ("ORIGINAL_CONSUMER_TEST_FILE",
                   "PYTHON_OFFLINE_UNITTEST_FUNCTION_ADAPTER", True, 4),
    }
    if set(source_env) != set(expected):
        raise ValueError("Changed current operator task denominator")
    hex_digits = frozenset("0123456789abcdef")
    seen: set[str] = set()
    summary: dict[str, dict[str, Any]] = {}
    for record in records:
        task = record["task_id"]
        if task in seen or task not in source_env:
            raise ValueError("Duplicate or unknown current operator task")
        seen.add(task)
        origin, environment, full_offline, tests = source_env[task]
        if (record.get("test_origin") != origin
                or record.get("execution_environment") != environment
                or record.get("complete_original_consumer_offline") is not full_offline
                or record.get("verified_pinned_file_count")
                != len(expected[task]["files"])
                or record.get("public_calibration_passed") is not True
                or record.get("independently_verified") is not False
                or record.get("consumer_integration_executed") is not False
                or record.get("production_writes") != 0):
            raise ValueError("Unsupported current operator scope or promotion")
        baseline, mutant = record["reference"], record["mutant"]
        digest = baseline.get("stdout_sha256")
        if (not isinstance(digest, str) or len(digest) != 64
                or any(char not in hex_digits for char in digest)
                or baseline.get("returncode") != 0
                or baseline.get("tests") != tests
                or baseline.get("failures") != 0
                or baseline.get("errors") != 0
                or baseline.get("skipped") != 0
                or mutant.get("returncode") != 1
                or mutant.get("expected_assertion_detected") is not True
                or mutant.get("failures") != (None if tests is None else 1)
                or mutant.get("errors") != (None if tests is None else 0)
                or mutant.get("skipped") != (None if tests is None else 0)):
            raise ValueError("Unqualified operator baseline or mutant receipt")
        summary[task] = {
            "test_origin": origin,
            "execution_environment": environment,
            "complete_original_consumer_offline": full_offline,
            "consumer_integration_executed": False,
        }
    if seen != set(expected):
        raise ValueError("Incomplete operator observations")
    original_count = sum(r["test_origin"] == "ORIGINAL_CONSUMER_TEST_FILE"
                         for r in summary.values())
    full_count = sum(r["complete_original_consumer_offline"]
                     for r in summary.values())
    if original_count != 9 or full_count != 6:
        raise ValueError("Operator evidence tiers changed unexpectedly")
    return {
        "kind": "CURRENT_SELF_REPORTED_OPERATOR_CALIBRATION",
        "bound_framework_commit": index["framework_commit_sha"],
        "catalog_sha256": index["catalog_sha256"],
        "self_reported_local_baseline_mutant_pass": "12/12",
        "original_consumer_test_files_invoked": "9/12",
        "complete_original_consumer_offline": "6/12",
        "original_js_tests_with_app_shims": "3/12",
        "framework_owned_bounded_oracles": "3/12",
        "task_scope": summary,
        "operator_evidence_independently_verified": False,
        "independent_source_acceptance": "0/12",
        "model_comparisons": "0/48",
        "exact_target_runtime_evidence": "0/13",
        "internal_admission": "HOLD_NOT_ADMITTED",
        "stable_release": "BLOCKED",
        "release_authorized": False,
    }


def main() -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    current = json.loads(LATEST_INDEX.read_text(encoding="utf-8"))
    historical = summarize(catalog, receipt)
    historical["current_operator_snapshot"] = summarize_current_operator(
        catalog, current, CATALOG.read_bytes()
    )
    print(json.dumps(historical, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
