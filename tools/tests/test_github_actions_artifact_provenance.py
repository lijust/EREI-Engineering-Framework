"""No-network regression tests for authenticated Actions evidence artifact admission."""
from __future__ import annotations

import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from tools import github_actions_artifact_provenance as verify

REPO = verify.REPOSITORY
CARRIER = "a" * 40


class AuthenticatedActionsArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.archive = Path(self.temp.name) / "artifact.zip"
        self.payload = {
            "exact-target-run.json": b'{"run":1}',
            "execution-evidence.json": b'{"evidence":1}',
            "runtime-identity.json": b'{"identity":1}',
        }
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w") as z:
            for path, value in self.payload.items():
                z.writestr(path, value)
        self.archive.write_bytes(buf.getvalue())
        self.digest = hashlib.sha256(buf.getvalue()).hexdigest()
        self.identity = {
            "repository": REPO, "github_run_id": 123,
            "github_run_attempt": 1,
            "release_carrier_ref": CARRIER,
            "target_id": "vnext-rc4",
        }
        self.run = {
            "id": 123, "run_attempt": 1, "event": "workflow_dispatch",
            "status": "completed", "conclusion": "success",
            "name": verify.WORKFLOW_NAME, "path": verify.WORKFLOW_PATH,
            "head_sha": CARRIER, "repository": {"full_name": REPO, "id": 555},
        }
        self.artifact = {
            "artifacts": [{
                "id": 321, "name": "vnext-exact-target-vnext-rc4-123-1",
                "expired": False, "digest": "sha256:" + self.digest,
                "workflow_run": {"id": 123, "head_sha": CARRIER},
            }]
        }

    def tearDown(self):
        self.temp.cleanup()

    def authenticate(self):
        with mock.patch.object(verify, "_api_json", side_effect=[self.run, self.artifact]) as called:
            value = verify.verify_official_run_artifact(
                self.identity, self.payload, archive=self.archive, token="read-only-test-token"
            )
        self.assertEqual(called.call_count, 2)
        return value

    def test_official_successful_run_binds_exact_archive_and_files(self):
        result = self.authenticate()
        self.assertEqual(result["artifact_id"], 321)
        self.assertTrue(result["authenticated"])

    def test_missing_auth_or_original_archive_fails_closed(self):
        for archive, token in ((self.archive, None), (None, "fake")):
            with self.subTest(archive=archive, token=token):
                with self.assertRaises(verify.ActionsProvenanceError):
                    verify.verify_official_run_artifact(
                        self.identity, self.payload, archive=archive, token=token
                    )

    def test_unauthorized_or_wrong_run_fails(self):
        for key, value in (
            ("head_sha", "b" * 40),
            ("path", ".github/workflows/untrusted.yml"),
            ("status", "queued"),
            ("event", "push"),
            ("conclusion", "failure"),
            ("run_attempt", 2),
        ):
            with self.subTest(key=key):
                bad = dict(self.run, **{key: value})
                with mock.patch.object(verify, "_api_json", side_effect=[bad, self.artifact]):
                    with self.assertRaisesRegex(verify.ActionsProvenanceError, "authenticate exact controlled"):
                        verify.verify_official_run_artifact(
                            self.identity, self.payload, archive=self.archive, token="fake"
                        )

    def test_archive_metadata_digest_or_extracted_payload_tamper_fails(self):
        with mock.patch.object(verify, "_api_json", side_effect=[
            self.run, {"artifacts": [{**self.artifact["artifacts"][0], "digest": "sha256:" + "0" * 64}]}
        ]):
            with self.assertRaisesRegex(verify.ActionsProvenanceError, "SHA-256 digest mismatch"):
                verify.verify_official_run_artifact(
                    self.identity, self.payload, archive=self.archive, token="fake"
                )
        with mock.patch.object(verify, "_api_json", side_effect=[self.run, self.artifact]):
            with self.assertRaisesRegex(verify.ActionsProvenanceError, "differs from authenticated artifact"):
                verify.verify_official_run_artifact(
                    self.identity, {**self.payload, "exact-target-run.json": b"edited"},
                    archive=self.archive, token="fake"
                )

    def test_missing_duplicate_or_extra_artifacts_fail_closed(self):
        for artifacts in (
            [],
            self.artifact["artifacts"] * 2,
            [{**self.artifact["artifacts"][0], "expired": True}],
            [{**self.artifact["artifacts"][0], "workflow_run": {"id": 55, "head_sha": CARRIER}}],
        ):
            with self.subTest(artifacts=len(artifacts)):
                with mock.patch.object(verify, "_api_json", side_effect=[self.run, {"artifacts": artifacts}]):
                    with self.assertRaisesRegex(verify.ActionsProvenanceError, "unique unexpired"):
                        verify.verify_official_run_artifact(
                            self.identity, self.payload, archive=self.archive, token="fake"
                        )

    def test_zip_file_set_excludes_extra_or_nested_entries(self):
        with zipfile.ZipFile(self.archive, mode="a") as z:
            z.writestr("extra.txt", "outside authorized package")
        with mock.patch.object(verify, "_api_json", side_effect=[self.run, self.artifact]):
            with self.assertRaisesRegex(verify.ActionsProvenanceError, "exactly three flat"):
                verify.verify_official_run_artifact(
                    self.identity, self.payload, archive=self.archive, token="fake"
                )


if __name__ == "__main__":
    unittest.main()
