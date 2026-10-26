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
