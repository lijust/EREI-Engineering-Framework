import unittest

from tools.stable_readiness import derive_readiness


class StableReadinessTests(unittest.TestCase):
    def test_current_shape_can_close_cycle_without_claiming_stable(self):
        result = derive_readiness(
            cycle_pass=True,
            eval_pass=False,
            enforcement_pass=False,
            approvals_pass=False,
        )
        self.assertFalse(result["ready_for_final_approvals"])
        self.assertFalse(result["stable_ready"])
        self.assertNotIn("prospective_cycle_incomplete", result["blockers"])
        self.assertIn("exact_target_runtime_evidence_incomplete", result["blockers"])
        self.assertIn("release_enforcement_not_satisfied", result["blockers"])

    def test_preapproval_requires_cycle_eval_and_enforcement(self):
        result = derive_readiness(
            cycle_pass=True,
            eval_pass=True,
            enforcement_pass=True,
            approvals_pass=False,
        )
        self.assertTrue(result["ready_for_final_approvals"])
        self.assertFalse(result["stable_ready"])
        self.assertEqual(result["blockers"], ["final_architecture_security_approvals_not_bound"])

    def test_all_four_gates_are_required_for_stable(self):
        result = derive_readiness(
            cycle_pass=True,
            eval_pass=True,
            enforcement_pass=True,
            approvals_pass=True,
        )
        self.assertTrue(result["ready_for_final_approvals"])
        self.assertTrue(result["stable_ready"])
        self.assertEqual(result["blockers"], [])

    def test_missing_cycle_blocks_preapproval(self):
        result = derive_readiness(
            cycle_pass=False,
            eval_pass=True,
            enforcement_pass=True,
            approvals_pass=False,
        )
        self.assertFalse(result["ready_for_final_approvals"])
        self.assertIn("prospective_cycle_incomplete", result["blockers"])


if __name__ == "__main__":
    unittest.main()
