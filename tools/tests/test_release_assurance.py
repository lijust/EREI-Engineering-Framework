import unittest

from tools import release_assurance


class ReleaseAssuranceTests(unittest.TestCase):
    def base(self, **overrides):
        value = {
            "schema_version": 1,
            "assurance_contract_version": 2,
            "release_id": "vnext",
            "baseline": "vnext",
            "status": "candidate",
            "framework_ref": "a" * 40,
            "released_at": "2026-09-07T02:30:00Z",
            "capabilities": {"hardening": "candidate"},
            "notes": "Candidate assurance release.",
            "stable_blockers": ["prospective cycle pending"],
        }
        value.update(overrides)
        return value

    def test_candidate_requires_explicit_stable_blockers(self):
        value = self.base()
        del value["stable_blockers"]
        with self.assertRaisesRegex(release_assurance.ReleaseError, "stable_blockers"):
            release_assurance.validate_manifest(value)

    def test_candidate_with_blockers_is_valid(self):
        result = release_assurance.validate_manifest(self.base())
        self.assertEqual(result["status"], "candidate")
        self.assertFalse(result["next_stable_gate_applied"])

    def test_v2_stable_requires_exact_target_runtime_level(self):
        value = self.base(
            status="stable",
            approval_ref="b" * 40,
            security_review_ref="c" * 40,
            minimum_eval_assurance_level="reference_contract",
            behavioral_eval_evidence="evals/evidence.json",
            prospective_learning_cycle={
                "capture_ref": "capture",
                "review_ref": "review",
                "feedback_ref": "feedback",
                "improvement_ref": "improvement",
                "adoption_ref": "adoption",
                "measured_outcome_ref": "outcome",
            },
        )
        with self.assertRaisesRegex(release_assurance.ReleaseError, "exact_target_runtime"):
            release_assurance.validate_manifest(value)


if __name__ == "__main__":
    unittest.main()
