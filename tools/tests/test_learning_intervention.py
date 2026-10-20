"""Exposure and outcome accounting must not turn adoption into effectiveness."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
from contextlib import redirect_stdout
from unittest.mock import patch

from tools import learning_effectiveness as eff
from tools.tests.test_learning_effectiveness_validation import report


def task(number, exposed=True, recurred=False, basis="prospective"):
    prefix = "EOCC" if basis == "prospective" else "ETASK"
    return {
        "occurrence_id": f"{prefix}-20261020T010000Z-{number:08X}",
        "identity_basis": basis, "exposed": exposed, "recurred": recurred,
        "evidence": [f"fixture:task-{number}"],
    }


def intervention(tasks=None):
    return {
        "schema_version": 1, "intervention_id": "fixture-intervention",
        "finding_refs": ["fixture:finding"], "root_cause": "fixture-root-cause",
        "development_output_ref": "fixture:development-output",
        "implementation": {"repository": "example/framework", "ref": "a" * 40},
        "adoption": {
            "repository": "example/project", "ref": "b" * 40,
            "implementation_ref": "a" * 40, "evidence": ["fixture:adoption"],
        },
        "cohort": {
            "repository": "example/project", "ref": "c" * 40,
            "ledger_sha256": "d" * 64, "epoch_id": "EPOCH-TEST",
            "eligibility_rule": "All material tasks in the declared fixture epoch",
            "selection_ref": "e" * 40,
            "tasks": tasks if tasks is not None else [task(1)],
        },
    }


class InterventionEvidenceTests(unittest.TestCase):
    def test_counts_derive_from_unique_exposed_assessed_occurrences(self):
        data = intervention([task(1, recurred=True), task(2), task(3, recurred=None),
                             task(4, exposed=False), task(5, exposed=None)])
        frozen = copy.deepcopy(data)
        result = eff.assess_intervention(data)
        self.assertEqual(result["prospective"], {
            "eligible": 5, "exposure_assessed": 4, "exposed": 3,
            "outcome_assessed_exposed": 2, "recurrences": 1,
            "exposure_assessment_coverage": 4 / 5,
            "outcome_assessment_coverage": 2 / 3,
            "recurrence_rate_among_assessed_exposed": 1 / 2,
        })
        self.assertEqual(result["status"], "PARTIAL_OUTCOME_ASSESSMENT")
        self.assertEqual(data, frozen)
        json.dumps(result, allow_nan=False)

    def test_adoption_without_eligible_tasks_is_not_success(self):
        result = eff.assess_intervention(intervention([]))
        self.assertEqual(result["status"], "NO_PROSPECTIVE_ELIGIBLE_TASKS")
        self.assertIsNone(result["prospective"]["recurrence_rate_among_assessed_exposed"])
        self.assertIsNone(result["prospective"]["exposure_assessment_coverage"])

    def test_unknown_exposure_and_unknown_outcome_are_not_zero_rates(self):
        for row, status in ((task(1, exposed=None, recurred=None), "EXPOSURE_UNASSESSED"),
                            (task(1, exposed=False), "NO_RECORDED_EXPOSURE"),
                            (task(1, recurred=None), "OUTCOMES_UNASSESSED")):
            with self.subTest(status=status):
                result = eff.assess_intervention(intervention([row]))
                self.assertEqual(result["status"], status)
                self.assertIsNone(result["prospective"]["recurrence_rate_among_assessed_exposed"])

    def test_legacy_assumptions_cannot_dilute_prospective_recurrence(self):
        result = eff.assess_intervention(intervention([
            task(1, recurred=True), task(2, basis="legacy_assumed"),
        ]))
        self.assertEqual(result["legacy_assumed_count"], 1)
        self.assertEqual(result["prospective"]["eligible"], 1)
        self.assertEqual(result["prospective"]["recurrence_rate_among_assessed_exposed"], 1)

    def test_missing_adoption_never_establishes_effectiveness(self):
        data = intervention([task(1, exposed=None, recurred=None)])
        data["adoption"] = None
        result = eff.assess_intervention(data)
        self.assertEqual(result["adoption_status"], "NOT_RECORDED")
        data["cohort"]["tasks"][0]["exposed"] = True
        with self.assertRaises(eff.EffectivenessError):
            eff.assess_intervention(data)

    def test_a_v2_identity_does_not_upgrade_legacy_evidence(self):
        row = task(1)
        row["identity_basis"] = "legacy_assumed"
        result = eff.assess_intervention(intervention([row]))
        self.assertEqual(result["legacy_assumed_count"], 1)
        self.assertEqual(result["prospective"]["eligible"], 0)

    def test_even_complete_observations_do_not_establish_causation_or_authenticity(self):
        result = eff.assess_intervention(intervention())
        self.assertEqual(result["status"], "OBSERVED_OUTCOMES_ONLY")
        self.assertEqual(result["effectiveness"], "NOT_ESTABLISHED")
        self.assertEqual(result["causation"], "NOT_ESTABLISHED")
        self.assertEqual(result["evidence_authenticity"], "NOT_VERIFIED")

    def test_duplicate_occurrences_and_unknown_fields_fail(self):
        cases = []
        duplicate = intervention([task(1), task(1)])
        cases.append(duplicate)
        for location in ("top", "cohort", "task"):
            bad = intervention()
            obj = bad if location == "top" else bad["cohort"] if location == "cohort" else bad["cohort"]["tasks"][0]
            obj["claimed_success_rate"] = 1.0
            cases.append(bad)
        for data in cases:
            with self.subTest(data=data), self.assertRaises(eff.EffectivenessError):
                eff.assess_intervention(data)

    def test_project_source_and_adoption_identity_mismatches_fail(self):
        for field, value in (("repository", "example/other"), ("implementation_ref", "f" * 40), ("ref", "main")):
            data = intervention()
            data["adoption"][field] = value
            with self.subTest(field=field), self.assertRaises(eff.EffectivenessError):
                eff.assess_intervention(data)
        data = intervention()
        data["cohort"]["ledger_sha256"] = "unbound"
        with self.assertRaises(eff.EffectivenessError):
            eff.assess_intervention(data)

    def test_identity_basis_and_tri_state_fields_are_strict(self):
        for field, value in (("exposed", 1), ("recurred", 0), ("exposed", "true"),
                             ("recurred", float("nan")), ("identity_basis", "backfilled"),
                             ("occurrence_id", "ETASK-20261020T010000Z-00000001")):
            data = intervention()
            data["cohort"]["tasks"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(eff.EffectivenessError):
                eff.assess_intervention(data)

    def test_required_trace_fields_and_version_cannot_be_omitted_or_forged(self):
        for field in intervention():
            data = intervention()
            del data[field]
            with self.subTest(field=field), self.assertRaises(eff.EffectivenessError):
                eff.assess_intervention(data)
        data = intervention()
        data["schema_version"] = True
        with self.assertRaises(eff.EffectivenessError):
            eff.assess_intervention(data)

    def test_loader_rejects_duplicate_keys_and_nonfinite_constants(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "intervention.json"
            for raw in ('{"schema_version":1,"schema_version":1}', '{"x":NaN}', '{"x":Infinity}'):
                path.write_text(raw, encoding="utf-8")
                with self.subTest(raw=raw), self.assertRaises(eff.EffectivenessError):
                    eff._load_intervention(path)

    def test_dispatch_denies_before_reading_any_artifact(self):
        with patch.object(eff.capability_activation, "require_active", side_effect=eff.capability_activation.ActivationError("denied")), \
             patch.object(eff, "_load") as reports, patch.object(eff, "_load_intervention") as record:
            with self.assertRaises(eff.capability_activation.ActivationError):
                eff.compare_target(Path("missing"), Path("before"), Path("after"), Path("intervention"))
            reports.assert_not_called()
            record.assert_not_called()

    def test_optional_cli_record_keeps_comparison_and_record_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            path, record_path = Path(directory) / "report.json", Path(directory) / "intervention.json"
            path.write_text(json.dumps(report()), encoding="utf-8")
            record_path.write_text(json.dumps(intervention()), encoding="utf-8")
            source_bytes = (path.read_bytes(), record_path.read_bytes())
            with patch.object(eff.capability_activation, "require_active") as activation, redirect_stdout(io.StringIO()) as output:
                code = eff.main(["--target", directory, "--before", str(path), "--after", str(path), "--intervention", str(record_path)])
            self.assertEqual(code, 0)
            activation.assert_called_once()
            result = json.loads(output.getvalue())
            self.assertEqual(result["status"], "COMPARABLE_DIRECTIONAL_ONLY")
            self.assertEqual(result["intervention"]["effectiveness"], "NOT_ESTABLISHED")
            self.assertEqual((path.read_bytes(), record_path.read_bytes()), source_bytes)


    def test_file_import_works_without_repository_on_module_search_path(self):
        script = "import importlib.util,sys; s=importlib.util.spec_from_file_location('effectiveness',sys.argv[1]); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); assert callable(m.assess_intervention)"
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, "-I", "-B", "-c", script, eff.__file__],
                                    cwd=directory, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
