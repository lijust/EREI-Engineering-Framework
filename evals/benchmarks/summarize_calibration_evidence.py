"""Conservative, public-only T15 source-evidence status summarizer.

Reads pinned public recipes + sanitized, self-reported observations only.
This is NOT an independent acceptance evaluator or model benchmark engine.
No network, consumer code execution, private file access or model calls.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "calibration-packages.json"
RECEIPT = ROOT / "public-source-oracle-observation.2026-10-24.json"

FULL = "ORIGINAL_CONSUMER_FILE_SELF_REPORTED_OFFLINE"
PARTIAL = "ORIGINAL_CONSUMER_FUNCTION_PARTIAL_SELF_REPORTED"
V8 = "ORIGINAL_JS_TEST_TEXT_V8_SHIMS_ONLY"
METHOD = "DIRECT_PINNED_SOURCE_METHOD_ONLY"
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
            if (task not in {"PY-02", "PY-05"}
                    or original["mutant"].get("failed") != 1
                    or original["mutant"].get("passed") != original["tests_defined"] - 1
                    or original["reference"]["passed"] != original["tests_defined"]):
                raise ValueError("Invalid Python original consumer evidence")
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
              for state in (FULL, PARTIAL, V8, METHOD, STRUCTURAL, NONE)}
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


def main() -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    print(json.dumps(summarize(catalog, receipt), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
