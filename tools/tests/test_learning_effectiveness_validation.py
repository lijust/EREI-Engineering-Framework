"""Regression tests for numeric integrity of effectiveness evidence."""
import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools import learning_effectiveness as eff


def report():
    epoch = {"material_tasks": 10, "risks": {"L2": 10},
             "workflows": {"bug-fix": 10}, "outcomes": {"verified_success": 10}}
    epoch.update({key: 0.0 for key in eff.PRIMARY + eff.SECONDARY})
    epoch.update({key: 1.0 for key in eff.COVERAGE_BY_METRIC.values()})
    return {"current_epoch": epoch}


class NumericEvidenceTests(unittest.TestCase):
    def test_valid_comparison_preserves_direction_and_inputs(self):
        before, after = report(), report()
        before["current_epoch"]["verification_escape_task_rate"] = 0.2
        frozen = copy.deepcopy((before, after))
        result = eff.compare(before, after)
        self.assertEqual(result["status"], "COMPARABLE_DIRECTIONAL_ONLY")
        self.assertEqual(result["primary_quality_signals"]["verification_escape_task_rate"], "improved")
        self.assertEqual(result["causation"], "NOT_ESTABLISHED")
        self.assertEqual((before, after), frozen)
        json.dumps(result, allow_nan=False)

    def test_invalid_rates_and_coverage_rejected(self):
        for key in eff.PRIMARY + eff.SECONDARY + tuple(set(eff.COVERAGE_BY_METRIC.values())):
            for invalid in (float("nan"), float("inf"), -float("inf"), True, -0.1, 1.1, "0.2"):
                with self.subTest(key=key, value=invalid):
                    bad = report()
                    bad["current_epoch"][key] = invalid
                    with self.assertRaises(eff.EffectivenessError):
                        eff.compare(report(), bad)

    def test_invalid_counts_rejected_without_coercion(self):
        for invalid in (True, -1, 1.5, "10", float("nan"), float("inf")):
            with self.subTest(value=invalid):
                bad = report()
                bad["current_epoch"]["material_tasks"] = invalid
                with self.assertRaises(eff.EffectivenessError):
                    eff.compare(bad, report())
                for field in ("risks", "workflows", "outcomes"):
                    bad = report()
                    bad["current_epoch"][field] = {"entry": invalid}
                    with self.assertRaises(eff.EffectivenessError):
                        eff.compare(report(), bad)

    def test_invalid_report_and_distribution_shapes_rejected(self):
        for bad in (None, [], {}, {"current_epoch": []}):
            with self.subTest(bad=bad), self.assertRaises(eff.EffectivenessError):
                eff.compare(bad, report())
        for field in ("risks", "workflows", "outcomes"):
            bad = report()
            bad["current_epoch"][field] = ["not", "counts"]
            with self.assertRaises(eff.EffectivenessError):
                eff.compare(bad, report())

    def test_missing_primary_is_unknown_not_held_or_comparable(self):
        for key in eff.PRIMARY:
            for missing in ("absent", "null"):
                bad = report()
                if missing == "absent":
                    del bad["current_epoch"][key]
                else:
                    bad["current_epoch"][key] = None
                result = eff.compare(report(), bad)
                self.assertEqual(result["status"], "NEEDS_COMPARABILITY_REVIEW")
                self.assertEqual(result["primary_quality_signals"][key], "not_comparable")
                self.assertNotIn(key, result["metric_deltas"])

    def test_missing_sample_count_is_not_zero(self):
        bad = report()
        del bad["current_epoch"]["material_tasks"]
        result = eff.compare(bad, report())
        self.assertIsNone(result["samples"]["before_material_tasks"])
        self.assertIn("material_task_count_unavailable", result["comparability"]["reasons"])

    def test_missing_coverage_stays_unknown(self):
        bad = report()
        del bad["current_epoch"]["verification_escape_assessment_coverage_rate"]
        result = eff.compare(report(), bad)
        self.assertEqual(result["status"], "NEEDS_COMPARABILITY_REVIEW")
        self.assertEqual(result["primary_quality_signals"]["verification_escape_task_rate"], "not_comparable")

    def test_json_nonfinite_constants_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "report.json"
            for constant in ("NaN", "Infinity", "-Infinity", "1e999"):
                path.write_text('{"current_epoch":{"material_tasks":10,"verification_escape_task_rate":' + constant + '}}', encoding="utf-8")
                with self.subTest(constant=constant), self.assertRaises(eff.EffectivenessError):
                    eff.compare(eff._load(path), report())

    def test_cli_rejects_invalid_evidence_with_valid_json_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "report.json"
            bad = report()
            bad["current_epoch"]["verification_escape_task_rate"] = float("nan")
            path.write_text(json.dumps(bad), encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output), patch.object(eff.capability_activation, "require_active"):
                # Numeric-only test: real activation boundaries have separate coverage.
                code = eff.main(["--target", temporary, "--before", str(path), "--after", str(path)])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(output.getvalue())["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()
