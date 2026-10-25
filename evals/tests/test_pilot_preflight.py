"""Regression suite for a *non-authorizing*, offline 48-slot T15 preflight."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "evals/benchmarks/preflight_pilot.py"
PLAN = ROOT / "evals/benchmarks/v1-v2-pilot.json"
spec = importlib.util.spec_from_file_location("t15_pilot_preflight", TOOL)
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


class PilotPreflightTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(PLAN.read_text(encoding="utf-8"))

    def test_draft_has_48_unrun_slots_and_exact_missing_authorities(self):
        r = preflight.preflight(self.plan)
        self.assertEqual((r["required_pairs"], r["required_slots"]), (24, 48))
        self.assertEqual(r["observed_slots"], 0)
        self.assertEqual(r["missing_slots"], 48)
        self.assertFalse(r["model_execution_authorized"])
        self.assertFalse(r["independent_acceptance_verified"])
        self.assertFalse(r["hidden_acceptance_verified"])
        self.assertFalse(r["model_effectiveness_established"])
        self.assertFalse(r["stable_ready"])
        self.assertIn("V2_FRAMEWORK_SHA_MISSING", r["blocking_preparation_fields"])
        self.assertIn("EXECUTION_MODEL_ID_MISSING", r["blocking_preparation_fields"])
        self.assertIn("EXECUTION_TOTAL_BUDGET_USD_MISSING", r["blocking_preparation_fields"])
        self.assertIn("INDEPENDENT_REVIEWER_MISSING", r["blocking_preparation_fields"])
        for name in ("APP-01", "APP-06", "PY-01", "PY-06"):
            self.assertIn(f"TASK_{name}_HIDDEN_ACCEPTANCE_MISSING",
                          r["blocking_preparation_fields"])

    def test_invalid_authorization_or_claim_of_executable_plan_fails_closed(self):
        for value in (True, 1, "true", None):
            p = copy.deepcopy(self.plan)
            p["execution"]["authorized"] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "authorization"):
                preflight.preflight(p)
        p = copy.deepcopy(self.plan)
        p["state"] = "EXECUTION_APPROVED"
        with self.assertRaisesRegex(ValueError, "only for non-executable draft"):
            preflight.preflight(p)

    def test_wrong_task_universe_cannot_hide_missing_benchmark_cases(self):
        for change in ("remove", "rename"):
            p = copy.deepcopy(self.plan)
            if change == "remove":
                p["tasks"] = p["tasks"][:-1]
            else:
                p["tasks"][0]["task_id"] = "EX-01"
            with self.subTest(change=change), self.assertRaises(ValueError):
                preflight.preflight(p)

    def test_missing_or_fake_budget_cannot_create_budget_approval(self):
        for value in (0, -1, 0.0, "100", True):
            p = copy.deepcopy(self.plan)
            p["execution"]["total_budget_usd"] = value
            result = preflight.preflight(p)
            self.assertIn("EXECUTION_TOTAL_BUDGET_USD_MISSING",
                          result["blocking_preparation_fields"])
            self.assertFalse(result["model_execution_authorized"])
        # Infinity is not a JSON-representable plan value at all: reject,
        # rather than convert to a missing-field report or zero cost.
        p = copy.deepcopy(self.plan)
        p["execution"]["total_budget_usd"] = float("inf")
        with self.assertRaises(ValueError):
            preflight.preflight(p)

    def test_filled_fields_not_release_authority_or_independent_acceptance(self):
        p = copy.deepcopy(self.plan)
        p["framework_refs"]["V2"] = "a" * 40
        p["execution"].update(
            model_id="synthetic-model-name",
            model_revision="synthetic-revision",
            runtime_digest="b" * 64,
            environment_digest="c" * 64,
            tool_permissions_digest="d" * 64,
            per_run_token_cap=10000,
            per_run_time_cap_seconds=300,
            total_budget_usd=1,
            budget_approval_ref="synthetic-nonauthoritative",
        )
        p["review"].update(
            independent_reviewer="synthetic-not-a-real-reviewer",
            hidden_acceptance_package_sha256="e" * 64,
            analysis_preregistration_sha256="f" * 64,
        )
        for t in p["tasks"]:
            t["hidden_acceptance_sha256"] = "0" * 64
        result = preflight.preflight(p)
        self.assertTrue(result["preparation_fields_complete"])
        self.assertEqual(result["next_step"], "OWNER_AND_INDEPENDENT_SOURCE_REVIEW_REQUIRED")
        for authority in (
            "model_execution_authorized",
            "hidden_acceptance_verified",
            "independent_acceptance_verified",
            "model_effectiveness_established", "stable_ready"
        ):
            self.assertFalse(result[authority])
        self.assertEqual(result["observed_slots"], 0)

    def test_all_48_synthetic_records_are_zero_real_model_runs(self):
        from evals import benchmark_accounting as accounting
        planned = accounting.schedule(self.plan)
        synthetic = {
            "plan_sha256": accounting.digest(self.plan),
            "evidence_kind": "synthetic",
            "runs": [{
                "run_id": slot["run_id"],
                "status": "completed",
                "first_candidate_passed": True,
                "independent_completion_passed": True,
                "review_evidence": ["synthetic:not-independent"],
                "attempts": [{
                    "attempt_no": 1,
                    "evidence_ref": "synthetic:fake-execution",
                    "wall_seconds": 1,
                    "model_usd": 0,
                    "tools_usd": 0,
                    "ci_usd": 0,
                    "human_usd": 0,
                }],
            } for slot in planned],
        }
        result = preflight.preflight(self.plan, synthetic)
        self.assertEqual(result["evidence_kind"], "synthetic")
        self.assertEqual(result["synthetic_record_slots"], 48)
        self.assertEqual(result["submitted_unverified_record_slots"], 0)
        self.assertEqual(result["independently_verified_model_slots"], 0)
        self.assertEqual(result["observed_slots"], 0)
        self.assertEqual(result["missing_slots"], 48)
        self.assertEqual(result["required_slots"], 48)
        self.assertFalse(result["model_execution_authorized"])
        self.assertFalse(result["independent_acceptance_verified"])
        self.assertFalse(result["stable_ready"])

        submitted = copy.deepcopy(synthetic)
        submitted["evidence_kind"] = "observed_unverified"
        report = preflight.preflight(self.plan, submitted)
        self.assertEqual(report["evidence_kind"], "observed_unverified")
        self.assertEqual(report["synthetic_record_slots"], 0)
        self.assertEqual(report["submitted_unverified_record_slots"], 48)
        self.assertEqual(report["independently_verified_model_slots"], 0)
        self.assertEqual(report["observed_slots"], 0)
        self.assertEqual(report["missing_slots"], 48)
        self.assertFalse(report["independent_acceptance_verified"])

    def test_unclassified_or_invalid_evidence_kind_rejected(self):
        from evals import benchmark_accounting as accounting
        records = {
            "plan_sha256": accounting.digest(self.plan),
            "evidence_kind": "synthetic",
            "runs": [],
        }
        for change in ("missing", "invalid", "null"):
            mutated = copy.deepcopy(records)
            if change == "missing":
                del mutated["evidence_kind"]
            elif change == "invalid":
                mutated["evidence_kind"] = "verified"
            else:
                mutated["evidence_kind"] = None
            with self.subTest(change=change), self.assertRaises(ValueError):
                preflight.preflight(self.plan, mutated)

    def test_wrong_assessment_evidence_and_wrong_plan_digest_rejected(self):
        p = copy.deepcopy(self.plan)
        record = {
            "plan_sha256": "0" * 64,
            "evidence_kind": "observed_unverified",
            "runs": [],
        }
        with self.assertRaisesRegex(ValueError, "records do not bind"):
            preflight.preflight(p, record)

    def test_cli_no_write_no_models_and_refuses_duplicate_json(self):
        with tempfile.TemporaryDirectory() as temp:
            plan_path = Path(temp) / "plan.json"
            plan_path.write_text(json.dumps(self.plan), encoding="utf-8")
            before = plan_path.read_bytes()
            completed = subprocess.run(
                [sys.executable, "-B", str(TOOL), "--plan", str(plan_path)],
                text=True, capture_output=True, cwd=temp,
                check=False, timeout=20
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            r = json.loads(completed.stdout)
            self.assertEqual((r["required_slots"], r["observed_slots"]), (48, 0))
            self.assertEqual(plan_path.read_bytes(), before)
            self.assertEqual([x.name for x in Path(temp).iterdir()], ["plan.json"])
            plan_path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
            malformed = subprocess.run(
                [sys.executable, "-B", str(TOOL), "--plan", str(plan_path)],
                text=True, capture_output=True, cwd=temp,
                check=False, timeout=20
            )
            self.assertEqual(malformed.returncode, 2)
            self.assertIn("duplicate JSON key", malformed.stderr)


if __name__ == "__main__":
    unittest.main()
