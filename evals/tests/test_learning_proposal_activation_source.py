"""Offline, synthetic tests for source-bound activation proposal preview."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from tools import capability_activation as activation
from tools import learning_proposal_activation_source as bound

SHA = "a" * 40
NOW = datetime(2026, 10, 27, 17, 0, tzinfo=timezone.utc)
CAPABILITY = "learning_pattern_analysis"


def proposal(decision, action):
    return {"contract": "erei-proposal-v1", "decision": decision,
            "actions": [action]}


def allow(mode="stable", *, capability=CAPABILITY, version="v1"):
    return proposal("allow_capability",
                    {"op": "execute_capability", "capability": capability,
                     "version": version, "mode": mode})


def block(reason):
    return proposal("block_capability",
                    {"op": "block_capability", "reason": reason})


class SourceBoundActivationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / ".erei").mkdir()
        self.manifest_path = self.root / activation.MANIFEST_PATH
        self.registry_path = self.root / "CAPABILITIES.json"
        self.adoption_path = self.root / activation.ADOPTION_PATH
        self.manifest = {
            "schema_version": 1,
            "framework": {"repository": "lijust/EREI-Engineering-Framework",
                          "baseline": "v1", "ref_type": "commit", "ref": SHA},
            "project": {}, "overlays": [], "runtime_adapters": [],
        }
        self.registry = {
            "schema_version": 1,
            "development_line": {
                "capabilities": {
                    CAPABILITY: {"status": "stable", "version": "v1"},
                }
            },
        }
        self.save_sources()

    def save_sources(self):
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        self.registry_path.write_text(json.dumps(self.registry), encoding="utf-8")

    @contextmanager
    def verified_local_fixture(self):
        with mock.patch.object(activation, "REGISTRY_PATH", self.registry_path), \
             mock.patch.object(activation, "assert_clean_framework_checkout"), \
             mock.patch.object(activation, "detect_loaded_framework_ref",
                               return_value=SHA):
            yield

    def run_preview(self, prop):
        with self.verified_local_fixture():
            return bound.evaluate_activation_from_project(
                prop, self.root, CAPABILITY, now=NOW)

    def assert_denied(self, result, reason):
        self.assertEqual(result["status"], "DENIED")
        self.assertEqual(result["reason_code"], reason)
        self.assertFalse(result["executed"])
        self.assertFalse(result["independently_verified"])
        self.assertNotIn("materialized_state", result)

    def test_stable_action_bound_to_project_and_registry_without_writes(self):
        original = {key: path.read_bytes() for key, path in
                    (("manifest", self.manifest_path), ("registry", self.registry_path))}
        prop = allow()
        original_prop = copy.deepcopy(prop)
        result = self.run_preview(prop)
        self.assertEqual(result["status"], "AUTHORIZED_IN_MEMORY_PREVIEW")
        self.assertEqual(result["materialized_state"]["capability_status"],
                         "STABLE")
        self.assertEqual(len(result["materialized_state"]["executions"]), 1)
        self.assertEqual(result["source_binding"]["resolver_status"],
                         "ACTIVE_STABLE")
        self.assertEqual(result["source_binding"]["framework_checkout_sha"], SHA)
        self.assertIsNone(result["source_binding"]["adoption_sha256"])
        self.assertFalse(result["executed"])
        self.assertFalse(result["independently_verified"])
        self.assertEqual(prop, original_prop)
        self.assertEqual(self.manifest_path.read_bytes(), original["manifest"])
        self.assertEqual(self.registry_path.read_bytes(), original["registry"])

    def test_candidate_requires_existing_bounded_adoption(self):
        self.registry["development_line"]["capabilities"][CAPABILITY]["status"] = "candidate"
        self.save_sources()
        self.assert_denied(self.run_preview(allow("candidate")),
                           "CAPABILITY_NOT_ACTIVE")
        blocked = self.run_preview(block("no_adoption"))
        self.assertEqual(blocked["status"], "AUTHORIZED_IN_MEMORY_PREVIEW")
        self.assertEqual(blocked["source_binding"]["resolver_status"],
                         "DORMANT_CANDIDATE")
        self.assertEqual(blocked["materialized_state"]["capability_status"],
                         "DORMANT")

        self.adoption_path.write_text(json.dumps({
            "schema_version": 1, "framework_ref": SHA,
            "adoptions": [{
                "adoption_id": "CAD-20261027T120000Z-ABCD1234",
                "capability": CAPABILITY, "version": "v1",
                "approved_at": "2026-10-27T12:00:00Z",
                "expires_at": "2026-11-01T12:00:00Z",
                "approved_by_role": "project_owner", "risk": "L2",
                "purpose": "Synthetic limited candidate adoption for offline tests",
                "evidence": ["fixture:evidence"],
            }]
        }), encoding="utf-8")
        accepted = self.run_preview(allow("candidate"))
        self.assertEqual(accepted["status"], "AUTHORIZED_IN_MEMORY_PREVIEW")
        self.assertEqual(accepted["source_binding"]["resolver_status"],
                         "ACTIVE_CANDIDATE")
        self.assertEqual(accepted["materialized_state"]["capability_status"],
                         "ACTIVE_CANDIDATE")

    def test_branch_project_pin_denies_capability_execution(self):
        self.manifest["framework"]["ref_type"] = "branch"
        self.manifest["framework"]["ref"] = "main"
        self.save_sources()
        self.assert_denied(self.run_preview(allow()),
                           "CAPABILITY_NOT_ACTIVE")
        result = self.run_preview(block("mutable_pin"))
        self.assertEqual(result["status"], "AUTHORIZED_IN_MEMORY_PREVIEW")
        self.assertEqual(result["source_binding"]["resolver_status"],
                         "BLOCK_NON_COMMIT_PROJECT_PIN")

    def test_fabricated_identity_or_context_does_not_grant_permission(self):
        self.assert_denied(self.run_preview(allow(capability="other")),
                           "CAPABILITY_ACTION_MISMATCH")
        self.assert_denied(self.run_preview(allow(version="v123")),
                           "CAPABILITY_ACTION_MISMATCH")
        injected = allow()
        injected["trusted_context"] = {"manifest": {"owner": "model"}}
        self.assert_denied(self.run_preview(injected),
                           "PROPOSAL_CONTRACT_INVALID")

    def test_corrupt_manifest_and_dirty_framework_fail_closed(self):
        self.manifest_path.write_text("{not json", encoding="utf-8")
        self.assert_denied(self.run_preview(allow()),
                           "ACTIVATION_SOURCE_UNVERIFIED")
        self.save_sources()
        with mock.patch.object(activation, "assert_clean_framework_checkout",
                               side_effect=activation.ActivationError("dirty checkout")):
            self.assert_denied(bound.evaluate_activation_from_project(
                allow(), self.root, CAPABILITY, now=NOW),
                "ACTIVATION_SOURCE_UNVERIFIED")

    def test_concurrent_registry_change_blocks_materialization(self):
        actual = bound._digest
        calls = 0

        def altered_digest(path):
            nonlocal calls
            calls += 1
            return "f" * 64 if calls == 5 else actual(path)

        with self.verified_local_fixture(), \
             mock.patch.object(bound, "_digest", side_effect=altered_digest):
            result = bound.evaluate_activation_from_project(
                allow(), self.root, CAPABILITY, now=NOW)
        self.assert_denied(result, "ACTIVATION_SOURCE_CHANGED_DURING_PREVIEW")
        self.assertEqual(calls, 6)

    def test_invalid_target_or_clock_fails_closed(self):
        self.assert_denied(bound.evaluate_activation_from_project(
            allow(), None, CAPABILITY, now=NOW), "ACTIVATION_TARGET_INVALID")
        self.assert_denied(bound.evaluate_activation_from_project(
            allow(), self.root, CAPABILITY, now=datetime(2026, 10, 27)),
            "ACTIVATION_CLOCK_UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
