"""Offline safety tests for owner-local one-call V3 runner; no Gemini requests."""
from __future__ import annotations

import inspect
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from evals.experiments import gemini_core13_learning_contract_v3 as v3
from evals.experiments import run_gemini_learning_v3_smoke as v3_runner
from evals.experiments import run_gemini_schema_smoke as v2_runner


class V3RunnerSafetyTests(unittest.TestCase):
    def test_transport_and_scorer_bytecode_source_is_same_except_experiment(self):
        """No subtle scorer, admission, CLI, provider or safety gate differences."""
        old_source = inspect.getsource(v2_runner)
        new_source = inspect.getsource(v3_runner)
        old_doc = "One owner-authorized local Gemini schema-experiment call, never CI."
        new_doc = "One owner-authorized local Gemini Learning V3 experiment call, never CI."
        old_description = "but Gemini request adds candidate responseJsonSchema."
        new_description = "but Gemini request appends general coaching over compact responseJsonSchema."
        expected = (
            old_source
            .replace(old_doc, new_doc)
            .replace(old_description, new_description)
            .replace(
                "from evals.experiments import gemini_core13_schema_compact_v2 as candidate",
                "from evals.experiments import gemini_core13_learning_contract_v3 as candidate",
            )
        )
        self.assertEqual(new_source, expected)
        self.assertIs(v3_runner.candidate, v3)

    def test_v3_has_exact_v2_schema_interface_needed_by_live_preflight(self):
        self.assertIs(v3.response_json_schema, v3.v2.response_json_schema)
        self.assertEqual(v3.response_json_schema(), v3.v2.response_json_schema())

    def test_authorized_preflight_and_evidence_path_no_provider_call(self):
        import os
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "target"
            target.mkdir()
            output = Path(temp) / "V3_EVIDENCE_MOCK_ONLY"
            prepared = {
                "root": target.resolve(),
                "prompt": "PUBLIC_SYNTHETIC_NO_PROVIDER",
                "case": {"id": "TLR-003-VERIFICATION-ESCAPE"},
                "suite": {"suite_id": "public-suite"},
                "request": {"kind": "synthetic", "prompt": "public"},
                "adapter_source": {"adapter_source_revision": "mock-source-sha"},
            }
            fake_verdict = {
                "status": "EXPERIMENTAL_MODEL_RESPONSE_SCORED_PASS_UNVERIFIED",
                "passed": True, "provider_model_version": "gemini-3.5-flash-lite",
                "usage_metadata": {"totalTokenCount": 1},
            }
            with (
                mock.patch.object(v3_runner.smoke, "prepare",
                                  return_value=prepared),
                mock.patch.object(v3_runner, "record_candidate",
                                  return_value=fake_verdict) as mocked_scoring,
                mock.patch.object(v3_runner.urllib.request, "build_opener") as network,
                mock.patch.dict(os.environ, {"GEMINI_API_KEY": "MOCK_ONLY"}, clear=False),
            ):
                result = v3_runner.main([
                    "--target-root", str(target),
                    "--case-id", "TLR-003-VERIFICATION-ESCAPE",
                    "--model", "gemini-3.5-flash-lite",
                    "--output-dir", str(output),
                    "--live", "--confirm-free-tier",
                    "--confirm-experimental-schema",
                ])
            self.assertEqual(result, 0)
            self.assertEqual(mocked_scoring.call_count, 1)
            network.assert_not_called()
            self.assertTrue((output / "candidate-provenance.json").exists())
            provenance = json.loads(
                (output / "candidate-provenance.json").read_text(encoding="utf-8"))
            self.assertEqual(provenance["experiment"], v3.EXPERIMENT)
            self.assertFalse(provenance["independently_accepted"])
            self.assertFalse(provenance["stable_ready"])
            self.assertEqual(provenance["network_requests_authorized_max"], 1)

    def test_no_network_when_owner_has_not_authorized_live_run(self):
        with tempfile.TemporaryDirectory() as temp:
            with (
                mock.patch.object(v3_runner.smoke, "prepare") as prepare,
                mock.patch.object(v3_runner.urllib.request, "build_opener") as network,
            ):
                code = v3_runner.main([
                    "--target-root", str(Path(temp) / "target"),
                    "--case-id", "TLR-003-VERIFICATION-ESCAPE",
                    "--model", "gemini-3.5-flash-lite",
                    "--output-dir", str(Path(temp) / "evidence"),
                ])
            self.assertEqual(code, 2)
            prepare.assert_not_called()
            network.assert_not_called()

    def test_exactly_one_fake_http_post_uses_v3_request_with_no_retry(self):
        fake_provider = b'{"fake":"PUBLIC_SYNTHETIC_FIXTURE"}'
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = fake_provider
        opener = mock.MagicMock()
        opener.open.return_value = response
        with mock.patch.object(v3_runner.urllib.request, "build_opener",
                               return_value=opener) as network:
            raw, body = v3_runner.generate_candidate_raw_once(
                "PUBLIC_SYNTHETIC_PROMPT", key="TEST_ONLY_NOT_SECRET",
                model="gemini-3.5-flash-lite", timeout=15.0)
        self.assertEqual(raw, fake_provider)
        payload = json.loads(body)
        self.assertEqual(
            payload["contents"][0]["parts"][0]["text"],
            "PUBLIC_SYNTHETIC_PROMPT" + v3.coaching_text(),
        )
        network.assert_called_once()
        opener.open.assert_called_once()
        req = opener.open.call_args.args[0]
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.data, body)
        self.assertIn("gemini-3.5-flash-lite", req.full_url)

    def test_reject_invalid_key_before_any_http_call(self):
        with mock.patch.object(v3_runner.urllib.request, "build_opener") as network:
            for bad in ("", "abc\r\nX:bad", " key ", "nonascii-🔒"):
                with self.subTest(key_status=len(bad)):
                    with self.assertRaises(v3_runner.gemini.GeminiAdapterError):
                        v3_runner.generate_candidate_raw_once(
                            "public", key=bad, model="gemini-3.5-flash-lite",
                            timeout=15,
                        )
            network.assert_not_called()


if __name__ == "__main__":
    unittest.main()
