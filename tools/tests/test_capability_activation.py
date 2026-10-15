from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from tools import capability_activation as mod


PIN = "a" * 40
NOW = datetime(2026, 10, 15, 20, 30, tzinfo=timezone.utc)


class CapabilityActivationTests(unittest.TestCase):
    def make_roots(self, *, capability_status="candidate", version="v1-test", ref_type="commit"):
        framework_temp = tempfile.TemporaryDirectory()
        project_temp = tempfile.TemporaryDirectory()
        framework = Path(framework_temp.name)
        project = Path(project_temp.name)
        (project / ".erei").mkdir()
        (project / ".erei" / "framework.json").write_text(
            json.dumps({
                "schema_version": 1,
                "framework": {
                    "repository": "lijust/EREI-Engineering-Framework",
                    "baseline": "test",
                    "ref_type": ref_type,
                    "ref": PIN if ref_type == "commit" else "candidate-tag",
                },
                "project": {},
                "overlays": [],
                "runtime_adapters": [],
            }),
            encoding="utf-8",
        )
        (framework / "CAPABILITIES.json").write_text(
            json.dumps({
                "schema_version": 1,
                "stable_release": {
                    "baseline": "stable",
                    "framework_ref": "b" * 40,
                    "manifest": "releases/stable.json"
                },
                "development_line": {
                    "status": "candidate",
                    "capabilities": {
                        "sample": {"status": capability_status, "version": version}
                    }
                }
            }),
            encoding="utf-8",
        )
        return framework_temp, project_temp, framework, project

    def adoption(self, project: Path, *, version="v1-test", ref=PIN, expires="2026-10-20T20:30:00Z"):
        (project / ".erei" / "candidate-capabilities.json").write_text(
            json.dumps({
                "schema_version": 1,
                "framework_ref": ref,
                "adoptions": [{
                    "capability": "sample",
                    "version": version,
                    "adopted_at": "2026-10-15T20:00:00Z",
                    "expires_at": expires,
                    "approved_by_role": "Chief Engineer",
                    "evidence": ["adr/ADR-CANDIDATE-TRIAL.md"]
                }]
            }),
            encoding="utf-8",
        )

    def resolve(self, framework, project):
        with mock.patch.object(mod, "_head", return_value=PIN), mock.patch.object(
            mod, "_resolve_project_ref", return_value=("commit", PIN)
        ):
            return mod.resolve(framework, project, "sample", NOW)

    def test_stable_capability_is_active_without_candidate_adoption(self):
        ft, pt, framework, project = self.make_roots(capability_status="stable")
        try:
            result = self.resolve(framework, project)
            self.assertEqual(result["status"], "ACTIVE_STABLE")
            self.assertTrue(result["active"])
        finally:
            ft.cleanup(); pt.cleanup()

    def test_candidate_is_dormant_by_default(self):
        ft, pt, framework, project = self.make_roots()
        try:
            result = self.resolve(framework, project)
            self.assertEqual(result["status"], "INACTIVE_CANDIDATE")
            self.assertFalse(result["active"])
        finally:
            ft.cleanup(); pt.cleanup()

    def test_exact_bounded_candidate_adoption_activates(self):
        ft, pt, framework, project = self.make_roots()
        try:
            self.adoption(project)
            result = self.resolve(framework, project)
            self.assertEqual(result["status"], "ACTIVE_CANDIDATE_TRIAL")
            self.assertTrue(result["active"])
        finally:
            ft.cleanup(); pt.cleanup()

    def test_expired_candidate_adoption_is_inactive(self):
        ft, pt, framework, project = self.make_roots()
        try:
            self.adoption(project, expires="2026-10-15T20:30:00Z")
            result = self.resolve(framework, project)
            self.assertEqual(result["status"], "INACTIVE_CANDIDATE_EXPIRED")
            self.assertFalse(result["active"])
        finally:
            ft.cleanup(); pt.cleanup()

    def test_version_mismatch_fails_closed(self):
        ft, pt, framework, project = self.make_roots()
        try:
            self.adoption(project, version="wrong")
            with self.assertRaisesRegex(mod.ActivationError, "does not match registry version"):
                self.resolve(framework, project)
        finally:
            ft.cleanup(); pt.cleanup()

    def test_framework_ref_mismatch_fails_closed(self):
        ft, pt, framework, project = self.make_roots()
        try:
            self.adoption(project, ref="c" * 40)
            with self.assertRaisesRegex(mod.ActivationError, "framework_ref does not match"):
                self.resolve(framework, project)
        finally:
            ft.cleanup(); pt.cleanup()

    def test_candidate_trial_requires_exact_commit_pin(self):
        ft, pt, framework, project = self.make_roots(ref_type="tag")
        try:
            self.adoption(project)
            with mock.patch.object(mod, "_head", return_value=PIN), mock.patch.object(
                mod, "_resolve_project_ref", return_value=("tag", PIN)
            ):
                with self.assertRaisesRegex(mod.ActivationError, "exact commit"):
                    mod.resolve(framework, project, "sample", NOW)
        finally:
            ft.cleanup(); pt.cleanup()

    def test_repository_identity_mismatch_fails_closed(self):
        ft, pt, framework, project = self.make_roots()
        try:
            manifest_path = project / ".erei" / "framework.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["framework"]["repository"] = "example/other-framework"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with mock.patch.object(mod, "_head", return_value=PIN):
                with self.assertRaisesRegex(mod.ActivationError, "does not match"):
                    mod.resolve(framework, project, "sample", NOW)
        finally:
            ft.cleanup(); pt.cleanup()

    def test_trial_longer_than_30_days_fails(self):
        ft, pt, framework, project = self.make_roots()
        try:
            self.adoption(project, expires="2026-11-20T20:00:00Z")
            with self.assertRaisesRegex(mod.ActivationError, "may not exceed 30 days"):
                self.resolve(framework, project)
        finally:
            ft.cleanup(); pt.cleanup()


if __name__ == "__main__":
    unittest.main()
