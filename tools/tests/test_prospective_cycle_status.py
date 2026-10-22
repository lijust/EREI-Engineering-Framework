import copy
import json
from pathlib import Path
import unittest

from tools.prospective_cycle_status import CycleStatusError, STEP_ORDER, validate


SHA_A = "a" * 40
SHA_B = "b" * 40


def completed(ref=SHA_A):
    return {"status": "completed", "repository": "lijust/repo", "ref": ref, "evidence": ["github-pr:1"]}


def valid_status():
    steps = {name: completed() for name in STEP_ORDER[:-1]}
    steps["measured_outcome"] = {"status": "pending", "reason": "No real post-adoption task has occurred yet."}
    return {
        "schema_version": 1,
        "cycle_id": "PLC-20260907-C1F01A84",
        "updated_at": "2026-09-07T11:33:52Z",
        "status": "awaiting_measured_outcome",
        "stable_framework_ref": SHA_A,
        "framework_candidate_ref": SHA_B,
        "source_project": {"repository": "lijust/EREI-App-Google"},
        "steps": steps,
        "blockers": ["measured_post_adoption_outcome_pending"],
    }


class ProspectiveCycleStatusTests(unittest.TestCase):
    def test_valid_awaiting_measurement(self):
        result = validate(valid_status())
        self.assertEqual(result["completed_steps"], 5)
        self.assertEqual(result["pending_steps"], 1)

    def test_unknown_top_level_field_fails(self):
        data = valid_status()
        data["extra"] = True
        with self.assertRaises(CycleStatusError):
            validate(data)

    def test_pending_step_must_not_claim_ref(self):
        data = valid_status()
        data["steps"]["measured_outcome"]["ref"] = SHA_A
        with self.assertRaises(CycleStatusError):
            validate(data)

    def test_later_completed_step_after_pending_fails(self):
        data = valid_status()
        data["steps"]["feedback"] = {"status": "pending", "reason": "missing"}
        with self.assertRaises(CycleStatusError):
            validate(data)

    def test_complete_requires_measurement_and_no_blockers(self):
        data = valid_status()
        data["status"] = "complete"
        with self.assertRaises(CycleStatusError):
            validate(data)
        data["steps"]["measured_outcome"] = completed(SHA_B)
        data["blockers"] = []
        result = validate(data)
        self.assertEqual(result["status"], "complete")

    def test_same_stable_and_candidate_ref_fails(self):
        data = valid_status()
        data["framework_candidate_ref"] = SHA_A
        with self.assertRaises(CycleStatusError):
            validate(data)

    def test_invalid_datetime_fails(self):
        data = valid_status()
        data["updated_at"] = "2026-09-07"
        with self.assertRaises(CycleStatusError):
            validate(data)

    def test_duplicate_blockers_fail(self):
        data = valid_status()
        data["blockers"].append("measured_post_adoption_outcome_pending")
        with self.assertRaises(CycleStatusError):
            validate(data)

    def test_complete_step_references_do_not_establish_effectiveness(self):
        data = valid_status()
        data["status"] = "complete"
        data["steps"]["measured_outcome"] = completed(SHA_B)
        data["blockers"] = []
        result = validate(data)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["evidence_level"], "DECLARED_STEP_REFERENCES")
        self.assertEqual(result["cohort_exposure"], "NOT_ASSESSED")
        self.assertEqual(result["effectiveness"], "NOT_ESTABLISHED")
        self.assertEqual(result["causation"], "NOT_ESTABLISHED")

    def test_retained_cycle_stays_readable_without_rewriting_history(self):
        path = Path(__file__).resolve().parents[2] / "learning/PROSPECTIVE_CYCLE_STATUS.json"
        original = path.read_bytes()
        data = json.loads(original)
        result = validate(data)
        self.assertEqual(result["cycle_id"], data["cycle_id"])
        self.assertEqual(result["status"], data["status"])
        self.assertEqual(result["effectiveness"], "NOT_ESTABLISHED")
        self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
