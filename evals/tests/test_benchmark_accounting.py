import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "evals/benchmark_accounting.py"
spec = importlib.util.spec_from_file_location("benchmark_accounting", TOOL)
accounting = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accounting)


class BenchmarkAccountingTests(unittest.TestCase):
    def setUp(self):
        self.plan = accounting.strict_json((ROOT / "evals/benchmarks/v1-v2-pilot.json").read_text(encoding="utf-8"))
        self.schedule = accounting.schedule(self.plan)
        self.records = {"plan_sha256": accounting.digest(self.plan), "evidence_kind": "synthetic", "runs": []}

    def row(self, scheduled, *, passed=True, status="completed", cost=1):
        return {
            "run_id": scheduled["run_id"], "status": status,
            "first_candidate_passed": passed,
            "independent_completion_passed": passed,
            "review_evidence": ["synthetic:review"],
            "attempts": [self.attempt(1, cost)],
        }

    def attempt(self, number, cost):
        return {"attempt_no": number, "evidence_ref": "synthetic:attempt", "wall_seconds": 10,
                "model_usd": cost, "tools_usd": 0, "ci_usd": 0, "human_usd": 0}

    def fill(self, passed=True):
        self.records["runs"] = [self.row(item, passed=passed) for item in self.schedule]

    def test_schedule_has_48_unique_slots_and_counterbalances_each_task(self):
        self.assertEqual(len(self.schedule), 48)
        self.assertEqual(len({row["run_id"] for row in self.schedule}), 48)
        for task in self.plan["tasks"]:
            rows = [r for r in self.schedule if r["task_id"] == task["task_id"]]
            first = [r["arm"] for r in rows if r["repetition"] == 1]
            second = [r["arm"] for r in rows if r["repetition"] == 2]
            self.assertEqual(first, second[::-1])
            self.assertEqual(set(first), {"V1", "V2"})

    def test_schedule_is_deterministic_and_independent_of_task_list_order(self):
        original = accounting.schedule(self.plan)
        self.plan["tasks"].reverse()
        self.assertEqual(accounting.schedule(self.plan), original)

    def test_duplicate_task_and_wrong_repetition_count_rejected(self):
        for change in ("duplicate", "bool", "one"):
            plan = copy.deepcopy(self.plan)
            if change == "duplicate":
                plan["tasks"][1] = plan["tasks"][0]
            else:
                plan["repetitions"] = True if change == "bool" else 1
            with self.subTest(change=change), self.assertRaises(ValueError):
                accounting.schedule(plan)

    def test_empty_plan_does_not_claim_zero_failure_or_free_completion(self):
        report = accounting.summarize(self.plan)
        self.assertFalse(report["execution_authorized"])
        self.assertEqual(report["evidence_kind"], "no_observations")
        for arm in accounting.ARMS:
            item = report["arms"][arm]
            self.assertEqual(item["assigned_runs"], 24)
            self.assertEqual(item["first_candidate"]["unknown"], 24)
            self.assertIsNone(item["first_candidate"]["rate"])
            self.assertEqual(item["first_candidate"]["missing_data_bounds"], [0, 1])
            self.assertIsNone(item["total_cost_usd"])
            self.assertIsNone(item["cost_per_declared_verified_run_usd"])

    def test_missing_run_stays_in_denominator_and_withholds_final_rate(self):
        self.fill()
        removed = self.records["runs"].pop()
        report = accounting.summarize(self.plan, self.records)
        arm = self.schedule[-1]["arm"]
        result = report["arms"][arm]
        self.assertIn(removed["run_id"], result["missing_run_ids"])
        self.assertEqual(result["declared_independent_completion"]["assigned"], 24)
        self.assertEqual(result["declared_independent_completion"]["unknown"], 1)
        self.assertIsNone(result["declared_independent_completion"]["rate"])
        self.assertIsNone(result["total_cost_usd"])

    def test_unknown_assessment_stays_unknown_even_for_terminal_status(self):
        self.fill()
        row = self.records["runs"][0]
        row.update(first_candidate_passed=None, independent_completion_passed=None, review_evidence=[])
        result = accounting.summarize(self.plan, self.records)["arms"][self.schedule[0]["arm"]]
        self.assertIsNone(result["declared_independent_completion"]["rate"])
        self.assertEqual(result["declared_independent_completion"]["assessed"], 23)
        self.assertIsNone(result["cost_per_declared_verified_run_usd"])

    def test_all_failures_have_zero_success_and_no_cost_per_success(self):
        self.fill(passed=False)
        for row in self.records["runs"]:
            row["status"] = "failed"
        for item in accounting.summarize(self.plan, self.records)["arms"].values():
            self.assertEqual(item["declared_independent_completion"]["rate"], 0)
            self.assertEqual(item["total_cost_usd"], 24)
            self.assertIsNone(item["cost_per_declared_verified_run_usd"])

    def test_retries_and_terminal_failure_costs_are_included(self):
        self.fill()
        failed = self.records["runs"][0]
        failed.update(status="timeout", first_candidate_passed=False, independent_completion_passed=False)
        failed["attempts"].append(self.attempt(2, 4))
        arm = self.schedule[0]["arm"]
        item = accounting.summarize(self.plan, self.records)["arms"][arm]
        self.assertEqual(item["attempts"], 25)
        self.assertEqual(item["total_cost_usd"], 28)
        self.assertEqual(item["cost_per_declared_verified_run_usd"], 28 / 23)
        self.assertEqual(item["known_attempt_wall_seconds_sum"], 250)

    def test_missing_cost_component_prevents_full_cost_claim(self):
        self.fill()
        self.records["runs"][0]["attempts"][0]["human_usd"] = None
        arm = self.schedule[0]["arm"]
        item = accounting.summarize(self.plan, self.records)["arms"][arm]
        self.assertEqual(item["known_cost_subtotal_usd"], 24)
        self.assertEqual(item["cost_complete_attempts"], 23)
        self.assertIsNone(item["total_cost_usd"])
        self.assertIsNone(item["cost_per_declared_verified_run_usd"])

    def test_invalid_numbers_are_rejected_in_every_numeric_field(self):
        for field in ("wall_seconds", *accounting.COSTS):
            for value in (True, -1, "1", float("nan"), float("inf"), 10 ** 400):
                self.records["runs"] = [self.row(self.schedule[0])]
                self.records["runs"][0]["attempts"][0][field] = value
                with self.subTest(field=field, value_type=type(value).__name__), self.assertRaises(ValueError):
                    accounting.summarize(self.plan, self.records)

    def test_overflow_of_finite_components_is_rejected(self):
        row = self.row(self.schedule[0])
        row["attempts"][0].update(model_usd=1e308, tools_usd=1e308)
        self.records["runs"] = [row]
        with self.assertRaises(ValueError):
            accounting.summarize(self.plan, self.records)

    def test_duplicate_unknown_and_out_of_plan_runs_are_rejected(self):
        row = self.row(self.schedule[0])
        for runs in ([row, row], [dict(row, run_id="unknown")], [dict(row, unexpected=True)]):
            self.records["runs"] = runs
            with self.assertRaises(ValueError):
                accounting.summarize(self.plan, self.records)
        self.records["runs"] = [row]
        self.records["plan_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            accounting.summarize(self.plan, self.records)

    def test_attempt_sequence_evidence_and_outcome_contradictions_rejected(self):
        mutations = [
            lambda r: r["attempts"][0].update(attempt_no=2),
            lambda r: r["attempts"][0].update(attempt_no=True),
            lambda r: r["attempts"][0].update(evidence_ref=""),
            lambda r: r.update(review_evidence=[]),
            lambda r: r.update(status="failed"),
            lambda r: r.update(independent_completion_passed=False),
            lambda r: r.update(first_candidate_passed=1),
            lambda r: r.update(attempts=[]),
            lambda r: r.update(status="started"),
        ]
        for mutate in mutations:
            row = self.row(self.schedule[0])
            mutate(row)
            self.records["runs"] = [row]
            with self.subTest(mutation=mutations.index(mutate)), self.assertRaises(ValueError):
                accounting.summarize(self.plan, self.records)

    def test_started_run_remains_incomplete_and_retains_observed_cost(self):
        row = self.row(self.schedule[0], passed=None, status="started")
        self.records["runs"] = [row]
        item = accounting.summarize(self.plan, self.records)["arms"][self.schedule[0]["arm"]]
        self.assertEqual(item["status_counts"]["started"], 1)
        self.assertEqual(item["known_cost_subtotal_usd"], 1)
        self.assertIsNone(item["total_cost_usd"])

    def test_strict_json_rejects_duplicate_keys_and_nonfinite_constants(self):
        for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.assertRaises(ValueError):
                accounting.strict_json(raw)

    def test_source_records_never_prove_authority_or_effectiveness(self):
        self.fill()
        self.records["evidence_kind"] = "observed_unverified"
        result = accounting.summarize(self.plan, self.records)
        self.assertEqual(result["comparability"], "NOT_VERIFIED")
        self.assertEqual(result["evidence_authenticity"], "NOT_VERIFIED")
        self.assertEqual(result["effectiveness"], "NOT_ESTABLISHED")
        self.assertFalse(result["execution_authorized"])

    def test_cli_is_read_only_and_emits_json_for_empty_draft(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "plan.json"
            target.write_text(json.dumps(self.plan), encoding="utf-8")
            before = target.read_bytes()
            result = subprocess.run([sys.executable, "-B", str(TOOL), "--plan", str(target)],
                                    capture_output=True, text=True, cwd=temporary)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(json.loads(result.stdout)["scheduled_runs"]), 48)
            self.assertEqual(target.read_bytes(), before)
            self.assertEqual([item.name for item in Path(temporary).iterdir()], ["plan.json"])


if __name__ == "__main__":
    unittest.main()
