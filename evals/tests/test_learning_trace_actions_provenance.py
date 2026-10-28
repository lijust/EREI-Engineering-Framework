"""No-network tests for GitHub Actions trace artifact *origin*, not model learning."""
from __future__ import annotations

import copy
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from tools import learning_trace_actions_provenance as verifier
from tools import task_learning
from evals.tests.test_learning_intervention_sources import InterventionLedgerBindingTests


def zip_bytes(raw: bytes, *, filename=verifier.MEMBER, extra=False) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as out:
        out.writestr(filename, raw)
        if extra:
            out.writestr("unexpected.txt", b"not allowed")
    return buf.getvalue()


class ActionsLearningTraceOriginTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.archive = Path(self.temp.name) / "artifact.zip"
        self.bundle = {"schema_version": 1, "intervention_id": "synthetic",
                       "epoch_id": "EPOCH-001",
                       "ledger_generation_sha256": "0" * 64, "traces": []}
        self.identity = {
            "repository": verifier.REPOSITORY, "run_id": 321,
            "run_attempt": 2, "framework_sha": "a" * 40,
        }
        self.write_bundle(self.bundle)
        self.run = {
            "id": 321, "run_attempt": 2, "event": "workflow_dispatch",
            "status": "completed", "conclusion": "success",
            "name": verifier.WORKFLOW_NAME, "path": verifier.WORKFLOW_PATH,
            "head_sha": "a" * 40, "repository": {"full_name": verifier.REPOSITORY},
        }
        self.artifacts = self.make_artifacts()

    def write_bundle(self, bundle):
        self.archive.write_bytes(zip_bytes(
            json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ))

    def make_artifacts(self):
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        return {"artifacts": [{
            "id": 678, "name": "core13-learning-traces-321-2",
            "expired": False, "digest": "sha256:" + digest,
            "workflow_run": {"id": 321, "head_sha": "a" * 40},
        }]}

    def authenticated(self, *, bundle=None, run=None, artifacts=None):
        with mock.patch.object(verifier.actions, "_api_json",
                               side_effect=[self.run if run is None else run,
                                            self.artifacts if artifacts is None else artifacts]) as api:
            result = verifier.verify_actions_trace_origin(
                self.archive, self.bundle if bundle is None else bundle,
                self.identity, token="synthetic-readonly-token",
            )
            self.assertEqual(api.call_count, 2)
            return result

    def test_origin_digest_and_run_metadata_verified_without_semantics(self):
        before = self.archive.read_bytes()
        result = self.authenticated()
        self.assertEqual(result["status"], "GITHUB_ACTIONS_ARTIFACT_ORIGIN_VERIFIED")
        self.assertTrue(result["artifact_origin_metadata_verified"])
        self.assertFalse(result["trusted_producer_code_verified"])
        self.assertFalse(result["trace_semantics_verified"])
        self.assertFalse(result["learning_exposure_independently_verified"])
        self.assertEqual(result["effectiveness"], "NOT_ESTABLISHED")
        self.assertEqual(result["causation"], "NOT_ESTABLISHED")
        self.assertEqual(before, self.archive.read_bytes())

    def test_missing_token_or_malformed_run_identity_no_network(self):
        for record, token in (
            (self.identity, None),
            ({**self.identity, "run_id": True}, "synthetic"),
            ({**self.identity, "run_attempt": 0}, "synthetic"),
            ({**self.identity, "framework_sha": "main"}, "synthetic"),
            ({**self.identity, "repository": "attacker/repo"}, "synthetic"),
        ):
            with self.subTest(record=record, token=token):
                with mock.patch.object(verifier.actions, "_api_json") as api:
                    with self.assertRaises(verifier.TraceOriginError):
                        verifier.verify_actions_trace_origin(
                            self.archive, self.bundle, record, token=token
                        )
                    api.assert_not_called()

    def test_bad_run_workflow_status_ref_and_event_all_rejected(self):
        changes = [
            ("head_sha", "f" * 40),
            ("path", ".github/workflows/untrusted.yml"),
            ("name", "Unreviewed Workflow"),
            ("event", "pull_request"),
            ("run_attempt", 1),
            ("conclusion", "failure"),
            ("id", 100),
            ("id", True),
            ("repository", {"full_name": "wrong/repository"}),
        ]
        for field, value in changes:
            with self.subTest(field=field, value=value):
                with mock.patch.object(verifier.actions, "_api_json",
                                       return_value={**self.run, field: value}) as api:
                    with self.assertRaisesRegex(
                        verifier.TraceOriginError, "ACTIONS_RUN_NOT_APPROVED_SOURCE"
                    ):
                        verifier.verify_actions_trace_origin(
                            self.archive, self.bundle, self.identity,
                            token="synthetic",
                        )
                    self.assertEqual(api.call_count, 1)

    def test_artifact_requires_unique_exact_digest_nonexpired_and_run_binding(self):
        original = self.artifacts["artifacts"][0]
        cases = [
            {"artifacts": []},
            {"artifacts": [original, original]},
            {"artifacts": [{**original, "expired": True}]},
            {"artifacts": [{**original, "digest": "sha256:" + "f" * 64}]},
            {"artifacts": [{**original, "workflow_run": {"id": 999,
                                                         "head_sha": "a" * 40}}]},
            {"artifacts": [{**original, "id": True}]},
        ]
        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(verifier.TraceOriginError):
                    self.authenticated(artifacts=case)

    def test_tampered_bundle_or_archive_fails_before_positive_origin(self):
        changed = dict(self.bundle, epoch_id="EPOCH-002")
        with self.assertRaisesRegex(verifier.TraceOriginError,
                                    "TRACE_BUNDLE_DIFFERS_FROM_ARCHIVE"):
            self.authenticated(bundle=changed)
        self.write_bundle(changed)
        with self.assertRaisesRegex(verifier.TraceOriginError,
                                    "ACTIONS_ARTIFACT_DIGEST_INVALID"):
            self.authenticated(bundle=changed)

    def test_zip_bomb_fileset_and_duplicate_json_rejected_without_network(self):
        raw = b'{"schema_version":1,"schema_version":1}'
        for data in (
            zip_bytes(raw),
            zip_bytes(b"{}", filename="../learning-traces.json"),
            zip_bytes(b"{}", extra=True),
            zip_bytes(b"null"),
            zip_bytes(b"NaN"),
        ):
            with self.subTest(n=len(data)):
                self.archive.write_bytes(data)
                with mock.patch.object(verifier.actions, "_api_json") as api:
                    with self.assertRaises(verifier.TraceOriginError):
                        verifier.verify_actions_trace_origin(
                            self.archive, self.bundle, self.identity,
                            token="synthetic",
                        )
                    api.assert_not_called()
        self.archive.write_bytes(zip_bytes(b"a" * (verifier.MAX_MEMBER_BYTES + 1)))
        with self.assertRaisesRegex(verifier.TraceOriginError,
                                    "TRACE_ARCHIVE_UNSAFE_MEMBER"):
            verifier.verify_actions_trace_origin(
                self.archive, self.bundle, self.identity, token="synthetic"
            )

    def test_reject_bzip2_and_lzma_before_unbounded_decompression(self):
        for method in (zipfile.ZIP_BZIP2, zipfile.ZIP_LZMA):
            with self.subTest(method=method):
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", compression=method) as out:
                    out.writestr(verifier.MEMBER, b"{}" + b"x" * 500000)
                self.archive.write_bytes(buf.getvalue())
                with mock.patch.object(verifier.actions, "_api_json") as api:
                    with self.assertRaisesRegex(
                        verifier.TraceOriginError, "TRACE_ARCHIVE_UNSAFE_MEMBER"
                    ):
                        verifier.verify_actions_trace_origin(
                            self.archive, self.bundle, self.identity,
                            token="synthetic",
                        )
                    api.assert_not_called()

    def test_corrupt_deflate_and_recursive_json_fail_closed(self):
        # The first compressed byte starts after the ZIP local-file header.
        raw = bytearray(zip_bytes(b"{}"))
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            entry = z.infolist()[0]
            start = entry.header_offset + 30 + len(entry.filename.encode("utf-8"))
            start += len(entry.extra)
        raw[start] = 0x07
        self.archive.write_bytes(raw)
        with mock.patch.object(verifier.actions, "_api_json") as api:
            result = verifier.reconcile_actions_trace_evidence(
                "/unused", self.bundle, {}, self.archive,
                self.identity, token="synthetic",
            )
            self.assertEqual(result["status"], "DENIED")
            self.assertEqual(result["reason_code"], "TRACE_ORIGIN_UNVERIFIED")
            api.assert_not_called()
        deeply_nested = b"[" * 1100 + b"0" + b"]" * 1100
        self.archive.write_bytes(zip_bytes(deeply_nested))
        with mock.patch.object(verifier.actions, "_api_json") as api:
            result = verifier.reconcile_actions_trace_evidence(
                "/unused", self.bundle, {}, self.archive,
                self.identity, token="synthetic",
            )
            self.assertEqual(result["status"], "DENIED")
            self.assertEqual(result["reason_code"], "TRACE_ORIGIN_UNVERIFIED")
            api.assert_not_called()

    def test_no_implicit_real_producer_metadata_and_no_network_from_ci(self):
        # This test does not install/dispatch the named producer workflow.
        self.assertTrue(verifier.WORKFLOW_PATH.endswith("core13-learning-trace-export.yml"))
        with mock.patch.object(verifier.actions, "_api_json",
                               side_effect=verifier.actions.ActionsProvenanceError("missing")):
            with self.assertRaisesRegex(verifier.TraceOriginError,
                                        "ACTIONS_METADATA_UNAVAILABLE"):
                verifier.verify_actions_trace_origin(
                    self.archive, self.bundle, self.identity,
                    token="synthetic",
                )

    def test_authenticated_artifact_can_join_complete_local_ledger_but_not_prove_effect(self):
        fixture = InterventionLedgerBindingTests(
            "test_exact_cohort_and_quality_accounting_are_local_only"
        )
        fixture.setUp()
        self.addCleanup(fixture.tmp.cleanup)
        ev = fixture.add(0)
        d = fixture.data([ev], exposure=True, recurrence=None)
        selection = fixture.selector()
        generation = task_learning.authoritative_snapshot(fixture.root)["generation"]
        bundle = {
            "schema_version": 1, "intervention_id": d["intervention_id"],
            "epoch_id": d["cohort"]["epoch_id"],
            "ledger_generation_sha256": generation,
            "traces": [{
                "occurrence_id": ev["occurrence_id"],
                "task_fingerprint": ev["fingerprint"],
                "framework_ref": ev["framework_ref"],
                "trace_ref": "f" * 40,
                "capture_complete": True,
                "steps": [{
                    "op": "learning_reuse", "intervention_id": d["intervention_id"],
                    "implementation_ref": d["implementation"]["ref"],
                }],
            }],
        }
        self.write_bundle(bundle)
        self.artifacts = self.make_artifacts()
        before = copy.deepcopy(d)
        with mock.patch.object(verifier.actions, "_api_json",
                               side_effect=[self.run, self.artifacts]):
            result = verifier.reconcile_actions_trace_evidence(
                fixture.root, d, selection, self.archive, self.identity,
                token="synthetic",
            )
        self.assertEqual(result["status"], "ACTIONS_ORIGIN_VERIFIED_TRACE_CLAIMS_RECONCILED")
        self.assertTrue(result["origin"]["artifact_origin_metadata_verified"])
        self.assertFalse(result["origin"]["trace_semantics_verified"])
        self.assertFalse(result["learning_exposure_independently_verified"])
        self.assertFalse(result["stable_ready"])
        self.assertEqual(result["effectiveness"], "NOT_ESTABLISHED")
        self.assertEqual(d, before)

    def test_authenticated_artifact_cannot_bypass_invalid_local_cohort(self):
        fixture = InterventionLedgerBindingTests(
            "test_exact_cohort_and_quality_accounting_are_local_only"
        )
        fixture.setUp()
        self.addCleanup(fixture.tmp.cleanup)
        event1 = fixture.add(0, outcome_class="failed", terminal_state="FAILED")
        event2 = fixture.add(1)
        d = fixture.data([event2])
        selection = fixture.selector()
        self.bundle["intervention_id"] = d["intervention_id"]
        self.write_bundle(self.bundle)
        self.artifacts = self.make_artifacts()
        with mock.patch.object(verifier.actions, "_api_json",
                               side_effect=[self.run, self.artifacts]):
            result = verifier.reconcile_actions_trace_evidence(
                fixture.root, d, selection, self.archive, self.identity,
                token="synthetic",
            )
        self.assertEqual(result["status"], "DENIED")
        self.assertEqual(result["reason_code"], "SOURCE_COHORT_NOT_ESTABLISHED")
        self.assertFalse(result["learning_exposure_independently_verified"])


if __name__ == "__main__":
    unittest.main()
