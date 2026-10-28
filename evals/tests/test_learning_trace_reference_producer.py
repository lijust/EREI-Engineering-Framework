"""Synthetic, no-provider tests for the actual knowledge-read reference hook."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools import learning_trace_reference_producer as producer
from tools import task_learning
from evals.tests.test_learning_intervention_sources import InterventionLedgerBindingTests


class KnowledgeReadProducerTests(unittest.TestCase):
    def setUp(self):
        f = InterventionLedgerBindingTests(
            "test_exact_cohort_and_quality_accounting_are_local_only"
        )
        f.setUp()
        self.f = f
        self.addCleanup(f.tmp.cleanup)
        self.knowledge = f.root / ".erei" / "knowledge"
        self.knowledge.mkdir(parents=True)
        self.payload = b"Synthetic approved knowledge read; not executed by an AI."
        (self.knowledge / "sample.txt").write_bytes(self.payload)
        self.sha = hashlib.sha256(self.payload).hexdigest()

    def observer(self, event):
        return producer.KnowledgeReadObserver(
            self.f.root, event["occurrence_id"], "synthetic-intervention", "a" * 40
        )

    def test_reference_cli_fixture_records_actual_read_but_not_real_use(self):
        result = producer.produce_reference_fixture("a" * 40)
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(len(result["traces"]), 1)
        self.assertEqual(result["traces"][0]["occurrence_id"],
                         producer.REFERENCE_OCCURRENCE)
        self.assertEqual(result["traces"][0]["steps"][0]["op"], "learning_reuse")
        self.assertTrue(result["traces"][0]["capture_complete"])
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "learning-traces.json"
            exitcode = producer.main([
                "--reference-fixture", "--framework-sha", "b" * 40,
                "--output", str(output),
            ])
            self.assertEqual(exitcode, 0)
            produced = json.loads(output.read_text())
            self.assertEqual(produced["traces"][0]["framework_ref"], "b" * 40)
        with self.assertRaises(producer.ObservationDenied):
            producer.produce_reference_fixture("main")

    def test_standalone_module_cli_import_and_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "learning-traces.json"
            result = subprocess.run(
                [
                    sys.executable, "-m",
                    "tools.learning_trace_reference_producer",
                    "--reference-fixture", "--framework-sha", "c" * 40,
                    "--output", str(output),
                ],
                check=False, capture_output=True, text=True, timeout=20,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.is_file())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["traces"][0]["framework_ref"], "c" * 40)

    def test_recorded_actual_read_joins_to_only_that_task(self):
        a = self.f.add(0)
        b = self.f.add(1, outcome_class="failed", terminal_state="FAILED")
        before = task_learning.authoritative_snapshot(self.f.root)["generation"]
        observer = self.observer(a)
        self.assertEqual(observer.read("sample.txt", self.sha), self.payload)
        declaration = self.f.data([a, b])
        pristine = copy.deepcopy(declaration)
        output = observer.finish(declaration, self.f.selector(), "f" * 40)
        bundle = output["bundle"]
        self.assertEqual(output["status"], "LOCAL_KNOWLEDGE_READ_OBSERVED")
        self.assertFalse(output["knowledge_used_in_real_project_verified"])
        self.assertEqual(output["effectiveness"], "NOT_ESTABLISHED")
        self.assertEqual(output["causation"], "NOT_ESTABLISHED")
        self.assertEqual(bundle["traces"][0]["steps"][0]["op"], "learning_reuse")
        self.assertTrue(bundle["traces"][0]["capture_complete"])
        self.assertEqual(bundle["traces"][1]["steps"], [])
        self.assertFalse(bundle["traces"][1]["capture_complete"])
        self.assertTrue(output["intervention_accounting_input"]["cohort"]["tasks"][0]["exposed"])
        self.assertIsNone(output["intervention_accounting_input"]["cohort"]["tasks"][1]["exposed"])
        self.assertEqual(declaration, pristine)
        self.assertEqual(before, task_learning.authoritative_snapshot(self.f.root)["generation"])

    def test_no_read_means_no_marker_even_when_event_exists(self):
        e = self.f.add(0)
        observer = self.observer(e)
        with self.assertRaisesRegex(producer.ObservationDenied, "NO_KNOWLEDGE_READ"):
            observer.finish(self.f.data([e]), self.f.selector(), "f" * 40)

    def test_read_requires_digest_identity_and_single_read(self):
        e = self.f.add(0)
        observer = self.observer(e)
        with self.assertRaisesRegex(producer.ObservationDenied, "KNOWLEDGE_DIGEST_MISMATCH"):
            observer.read("sample.txt", "0" * 64)
        self.assertEqual(observer.read("sample.txt", self.sha), self.payload)
        with self.assertRaisesRegex(producer.ObservationDenied, "ALREADY_OBSERVED"):
            observer.read("sample.txt", self.sha)

    def test_path_traversal_symlink_external_and_large_file_denied(self):
        e = self.f.add(0)
        for path in ("../framework.json", "/etc/hosts", "not-found", ""):
            with self.subTest(path=path):
                with self.assertRaises(producer.ObservationDenied):
                    self.observer(e).read(path, self.sha)
        (self.knowledge / "oversize.txt").write_bytes(
            b"x" * (producer.MAX_KNOWLEDGE_BYTES + 1)
        )
        with self.assertRaisesRegex(producer.ObservationDenied, "KNOWLEDGE_FILE_TOO_LARGE"):
            self.observer(e).read(
                "oversize.txt", hashlib.sha256(b"x" * (producer.MAX_KNOWLEDGE_BYTES + 1)).hexdigest()
            )
        with tempfile.TemporaryDirectory() as external:
            other = Path(external) / "secret.txt"
            other.write_bytes(self.payload)
            try:
                (self.knowledge / "link.txt").symlink_to(other)
            except (OSError, NotImplementedError):
                return
            with self.assertRaisesRegex(producer.ObservationDenied, "KNOWLEDGE_LOCATION_INVALID"):
                self.observer(e).read("link.txt", self.sha)

    def test_wrong_intervention_or_incomplete_cohort_denied(self):
        a = self.f.add(0)
        b = self.f.add(1, outcome_class="failed", terminal_state="FAILED")
        observer = self.observer(a)
        observer.read("sample.txt", self.sha)
        partial = self.f.data([a])
        with self.assertRaisesRegex(producer.ObservationDenied, "SOURCE_COHORT_NOT_ESTABLISHED"):
            observer.finish(partial, self.f.selector(), "f" * 40)
        complete = self.f.data([a, b])
        complete["intervention_id"] = "wrong"
        with self.assertRaisesRegex(producer.ObservationDenied, "INTERVENTION_IDENTITY_MISMATCH"):
            observer.finish(complete, self.f.selector(), "f" * 40)

    def test_existing_exposure_declarations_cannot_be_overwritten(self):
        e = self.f.add(0)
        observer = self.observer(e)
        observer.read("sample.txt", self.sha)
        declared = self.f.data([e], exposure=False)
        with self.assertRaisesRegex(producer.ObservationDenied, "COHORT_EXPOSURE_ALREADY_DECLARED"):
            observer.finish(declared, self.f.selector(), "f" * 40)


if __name__ == "__main__":
    unittest.main()
