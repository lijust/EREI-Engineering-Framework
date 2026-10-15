from __future__ import annotations

import unittest
from datetime import datetime, timezone

from tools import capability_activation as activation


PIN = "a" * 40
OTHER_PIN = "b" * 40
NOW = datetime(2026, 10, 15, 20, 30, tzinfo=timezone.utc)


def manifest(*, ref=PIN, ref_type="commit"):
    return {
        "schema_version": 1,
        "framework": {
            "repository": "lijust/EREI-Engineering-Framework",
            "baseline": "candidate-trial",
            "ref_type": ref_type,
            "ref": ref,
        },
        "project": {},
        "overlays": [],
        "runtime_adapters": [],
    }


def registry():
    return {
        "schema_version": 1,
        "development_line": {
            "status": "candidate",
            "capabilities": {
                "stable_capability": {"status": "stable", "version": "v1"},
                "candidate_capability": {"status": "candidate", "version": "v2"},
            },
        },
    }


def adoption(**overrides):
    item = {
        "adoption_id": "CAD-20261015T200000Z-A1B2C3D4",
        "capability": "candidate_capability",
        "version": "v2",
        "approved_at": "2026-10-15T20:00:00Z",
        "expires_at": "2026-10-22T20:00:00Z",
        "approved_by_role": "chief-engineer",
        "risk": "L2",
        "purpose": "Bounded real-project candidate capability trial.",
        "evidence": ["approval:learning-operations-trial"],
    }
    item.update(overrides)
    return {"schema_version": 1, "framework_ref": PIN, "adoptions": [item]}


class CapabilityActivationTests(unittest.TestCase):
    def resolve(self, capability="candidate_capability", *, doc=None, project=None, loaded=PIN):
        return activation.resolve_activation(
            project or manifest(),
            registry(),
            capability,
            adoption_document=doc,
            loaded_framework_ref=loaded,
            now=NOW,
        )

    def test_stable_is_active_without_candidate_adoption(self):
        self.assertEqual(self.resolve("stable_capability")["status"], "ACTIVE_STABLE")

    def test_candidate_is_dormant_without_adoption(self):
        self.assertEqual(self.resolve()["status"], "DORMANT_CANDIDATE")

    def test_exact_bounded_adoption_activates_candidate(self):
        result = self.resolve(doc=adoption())
        self.assertEqual(result["status"], "ACTIVE_CANDIDATE")
        self.assertEqual(result["adoption_id"], "CAD-20261015T200000Z-A1B2C3D4")

    def test_pin_upgrade_alone_does_not_activate_candidate(self):
        doc = {"schema_version": 1, "framework_ref": PIN, "adoptions": []}
        self.assertEqual(self.resolve(doc=doc)["status"], "DORMANT_CANDIDATE")

    def test_candidate_requires_commit_pin(self):
        project = manifest(ref="candidate-branch", ref_type="branch")
        safe_default = {"schema_version": 1, "framework_ref": "candidate-branch", "adoptions": []}
        self.assertEqual(self.resolve(doc=safe_default, project=project)["status"], "BLOCK_NON_COMMIT_PROJECT_PIN")

    def test_empty_adoption_document_may_mirror_noncommit_experimental_ref(self):
        value = {"schema_version": 1, "framework_ref": "candidate-branch", "adoptions": []}
        self.assertEqual(activation._validate_adoptions(value), [])

    def test_nonempty_adoption_document_requires_commit_sha(self):
        value = adoption()
        value["framework_ref"] = "candidate-branch"
        with self.assertRaisesRegex(activation.ActivationError, "40-character commit SHA"):
            activation._validate_adoptions(value)

    def test_loaded_framework_must_match_project_pin(self):
        self.assertEqual(self.resolve(doc=adoption(), loaded=OTHER_PIN)["status"], "BLOCK_FRAMEWORK_REF_MISMATCH")

    def test_adoption_ref_must_match_project_pin(self):
        doc = adoption()
        doc["framework_ref"] = OTHER_PIN
        self.assertEqual(self.resolve(doc=doc)["status"], "BLOCK_FRAMEWORK_REF_MISMATCH")

    def test_version_mismatch_fails_closed(self):
        self.assertEqual(self.resolve(doc=adoption(version="v1"))["status"], "BLOCK_CANDIDATE_VERSION_MISMATCH")

    def test_expired_adoption_fails_closed(self):
        doc = adoption(expires_at="2026-10-15T20:30:00Z")
        self.assertEqual(self.resolve(doc=doc)["status"], "BLOCK_EXPIRED_CANDIDATE_ADOPTION")

    def test_future_approval_fails_closed(self):
        doc = adoption(approved_at="2026-10-16T20:00:00Z", expires_at="2026-10-20T20:00:00Z")
        self.assertEqual(self.resolve(doc=doc)["status"], "BLOCK_INVALID_CANDIDATE_ADOPTION")

    def test_trial_over_30_days_is_invalid(self):
        self.assertEqual(
            self.resolve(doc=adoption(expires_at="2026-11-20T20:00:00Z"))["status"],
            "BLOCK_INVALID_CANDIDATE_ADOPTION",
        )

    def test_duplicate_adoption_is_invalid(self):
        doc = adoption()
        duplicate = dict(doc["adoptions"][0])
        duplicate["adoption_id"] = "CAD-20261015T200001Z-A1B2C3D5"
        doc["adoptions"].append(duplicate)
        self.assertEqual(self.resolve(doc=doc)["status"], "BLOCK_INVALID_CANDIDATE_ADOPTION")

    def test_unknown_capability_is_blocked(self):
        self.assertEqual(self.resolve("missing")["status"], "BLOCK_UNKNOWN_CAPABILITY")


if __name__ == "__main__":
    unittest.main()
