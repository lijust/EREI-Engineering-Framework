"""Synthetic local project integration tests; no remote provider or real project."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from tools import capability_activation as activation
from tools import learning_project_runtime_bridge as bridge
from evals.tests.test_learning_trace_reference_producer import KnowledgeReadProducerTests

SHA = "a" * 40
NOW = datetime(2026, 10, 28, 8, 0, tzinfo=timezone.utc)
CAPABILITY = "learning_pattern_analysis"


class ActivatedProjectKnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = KnowledgeReadProducerTests("test_no_read_means_no_marker_even_when_event_exists")
        self.fixture.setUp()
        self.addCleanup(self.fixture.f.tmp.cleanup)
        self.root = self.fixture.f.root
        self.manifest_path = self.root / activation.MANIFEST_PATH
        self.registry_path = self.root / "CAPABILITIES.json"
        self.adoption_path = self.root / activation.ADOPTION_PATH
        self.manifest = {
            "schema_version": 1,
            "framework": {
                "repository": "lijust/EREI-Engineering-Framework",
                "baseline": "v1", "ref_type": "commit", "ref": SHA,
            },
            "project": {}, "overlays": [], "runtime_adapters": [],
        }
        self.registry = {
            "schema_version": 1,
            "development_line": {
                "capabilities": {
                    CAPABILITY: {"status": "stable", "version": "v1"},
                },
            },
        }
        self.save()

        self.registry_patch = mock.patch.object(activation, "REGISTRY_PATH", self.registry_path)
        self.clean_patch = mock.patch.object(activation, "assert_clean_framework_checkout")
        self.loaded_patch = mock.patch.object(
            activation, "detect_loaded_framework_ref", return_value=SHA
        )
        for patch in (self.registry_patch, self.clean_patch, self.loaded_patch):
            patch.start()
            self.addCleanup(patch.stop)

    def save(self):
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        self.registry_path.write_text(json.dumps(self.registry), encoding="utf-8")

    def session(self, event):
        return bridge.ProjectKnowledgeReadSession(
            self.root, event["occurrence_id"], "synthetic-intervention",
            SHA, capability=CAPABILITY, now=NOW,
        )

    def adopt(self, *, expires_at="2026-11-01T08:00:00Z"):
        self.registry["development_line"]["capabilities"][CAPABILITY]["status"] = "candidate"
        self.save()
        self.adoption_path.write_text(json.dumps({
            "schema_version": 1, "framework_ref": SHA,
            "adoptions": [{
                "adoption_id": "CAD-20261028T070000Z-ABCD1234",
                "capability": CAPABILITY, "version": "v1",
                "approved_at": "2026-10-28T07:00:00Z",
                "expires_at": expires_at,
                "approved_by_role": "project_owner", "risk": "L2",
                "purpose": "Synthetic bounded adoption for the isolated bridge fixture",
                "evidence": ["synthetic:approval"],
            }],
        }), encoding="utf-8")

    def test_stable_project_read_join_requires_actual_captured_event(self):
        event = self.fixture.f.add(0, outcome_class="failed", terminal_state="FAILED")
        session = self.session(event)
        data = session.read("sample.txt", self.fixture.sha)
        self.assertEqual(data, self.fixture.payload)
        intervention = self.fixture.f.data([event])
        result = session.finalize_after_capture(
            intervention, self.fixture.f.selector(), SHA
        )
        self.assertEqual(result["status"], "PROJECT_LOCAL_ACTIVE_KNOWLEDGE_READ_RECONCILED")
        self.assertEqual(result["source_activation"]["status"], "ACTIVE_STABLE")
        self.assertEqual(result["source_activation"]["framework_sha"], SHA)
        self.assertEqual(result["bundle"]["traces"][0]["steps"][0]["op"], "learning_reuse")
        self.assertFalse(result["consumer_use_verified"])
        self.assertFalse(result["trace_runtime_independently_attested"])
        self.assertFalse(result["learning_exposure_independently_verified"])
        self.assertEqual(result["effectiveness"], "NOT_ESTABLISHED")
        self.assertEqual(result["causation"], "NOT_ESTABLISHED")

    def test_missing_terminal_event_denies_no_false_exposure(self):
        event = self.fixture.f.add(0)
        session = self.session(event)
        session.read("sample.txt", self.fixture.sha)
        # Project-local event deliberately disappears from the authoritative ledger.
        from tools import task_learning
        directory = task_learning._paths(self.root)["event_dir"]
        (directory / (event["occurrence_id"] + ".json")).unlink()
        with self.assertRaisesRegex(bridge.ProjectReadDenied, "TERMINAL_TASK_NOT_RECORDED"):
            session.finalize_after_capture(self.fixture.f.data([]), self.fixture.f.selector(), SHA)

    def test_candidate_without_adoption_and_expired_adoption_deny(self):
        event = self.fixture.f.add(0)
        self.registry["development_line"]["capabilities"][CAPABILITY]["status"] = "candidate"
        self.save()
        with self.assertRaisesRegex(bridge.ProjectReadDenied, "CAPABILITY_NOT_ACTIVE"):
            self.session(event)
        self.adopt(expires_at="2026-10-28T07:30:00Z")
        with self.assertRaisesRegex(bridge.ProjectReadDenied, "CAPABILITY_NOT_ACTIVE"):
            self.session(event)

    def test_candidate_with_bounded_adoption_can_record_local_read(self):
        event = self.fixture.f.add(0)
        self.adopt()
        session = self.session(event)
        session.read("sample.txt", self.fixture.sha)
        r = session.finalize_after_capture(
            self.fixture.f.data([event]), self.fixture.f.selector(), SHA,
        )
        self.assertEqual(r["source_activation"]["status"], "ACTIVE_CANDIDATE")
        self.assertFalse(r["learning_exposure_independently_verified"])

    def test_branch_pin_wrong_loaded_sha_and_dirty_checkout_denied(self):
        event = self.fixture.f.add(0)
        self.manifest["framework"]["ref_type"] = "branch"
        self.manifest["framework"]["ref"] = "main"
        self.save()
        with self.assertRaisesRegex(bridge.ProjectReadDenied, "CAPABILITY_NOT_ACTIVE"):
            self.session(event)
        self.manifest["framework"]["ref_type"] = "commit"
        self.manifest["framework"]["ref"] = "f" * 40
        self.save()
        with self.assertRaisesRegex(bridge.ProjectReadDenied, "CAPABILITY_NOT_ACTIVE"):
            self.session(event)
        self.manifest["framework"]["ref"] = SHA
        self.save()
        with mock.patch.object(
            activation, "assert_clean_framework_checkout",
            side_effect=activation.ActivationError("dirty"),
        ):
            with self.assertRaisesRegex(
                bridge.ProjectReadDenied, "ACTIVATION_SOURCE_UNVERIFIED"
            ):
                self.session(event)

    def test_mutated_registry_after_read_denies_reuse_receipt(self):
        event = self.fixture.f.add(0)
        session = self.session(event)
        session.read("sample.txt", self.fixture.sha)
        self.registry["development_line"]["capabilities"][CAPABILITY]["status"] = "candidate"
        self.save()
        with self.assertRaises(bridge.ProjectReadDenied):
            session.finalize_after_capture(
                self.fixture.f.data([event]), self.fixture.f.selector(), SHA,
            )

    def test_task_framework_mismatch_denied_after_read(self):
        event = self.fixture.f.add(0, framework_ref="f" * 40)
        session = self.session(event)
        session.read("sample.txt", self.fixture.sha)
        with self.assertRaisesRegex(
            bridge.ProjectReadDenied, "TASK_FRAMEWORK_REVISION_MISMATCH"
        ):
            session.finalize_after_capture(
                self.fixture.f.data([event]), self.fixture.f.selector(), SHA,
            )

    def test_denominator_omission_of_failed_task_still_denied(self):
        first = self.fixture.f.add(0)
        self.fixture.f.add(1, outcome_class="failed", terminal_state="FAILED")
        session = self.session(first)
        session.read("sample.txt", self.fixture.sha)
        with self.assertRaisesRegex(
            bridge.ProjectReadDenied, "PROJECT_TRACE_RECONCILIATION_DENIED"
        ):
            session.finalize_after_capture(
                self.fixture.f.data([first]), self.fixture.f.selector(), SHA,
            )

    def test_no_read_no_session_and_invalid_clock_denied(self):
        event = self.fixture.f.add(0)
        session = self.session(event)
        with self.assertRaisesRegex(bridge.ProjectReadDenied, "NO_PROJECT_READ"):
            session.finalize_after_capture(
                self.fixture.f.data([event]), self.fixture.f.selector(), SHA,
            )
        with self.assertRaisesRegex(bridge.ProjectReadDenied, "SESSION_POLICY_INPUT_INVALID"):
            bridge.ProjectKnowledgeReadSession(
                self.root, event["occurrence_id"], "synthetic-intervention",
                SHA, capability=CAPABILITY, now=datetime(2026, 10, 28),
            )
        with self.assertRaisesRegex(bridge.ProjectReadDenied, "SESSION_POLICY_INPUT_INVALID"):
            bridge.ProjectKnowledgeReadSession(
                self.root, event["occurrence_id"], "synthetic-intervention",
                SHA, capability="unregistered_capability", now=NOW,
            )


if __name__ == "__main__":
    unittest.main()
