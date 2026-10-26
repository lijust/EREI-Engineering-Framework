"""Offline-only diagnostics for a preexisting actual Gemini receipt; no network."""
from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from evals import diagnose_gemini_core_receipt as diag


def raw_response(*, model="gemini-3.5-flash-lite", finish="STOP",
                 text_value=None):
    if text_value is None:
        text_value = json.dumps({
            "output": {"contract": "erei-action-simulation-v1",
                       "decision": "capture_task",
                       "actions": [], "state": {"task_events": []}},
            "metadata": {"risk": "L0"},
        })
    return json.dumps({
        "modelVersion": model,
        "responseId": "synthetic-id",
        "usageMetadata": {"totalTokenCount": 4361},
        "candidates": [{"finishReason": finish,
                        "content": {"parts": [{"text": text_value}]}}],
    }).encode("utf-8")


def write_receipt(folder: Path, raw: bytes, *, expected_hash=None,
                  model="gemini-3.5-flash-lite"):
    (folder / "provider-raw.json").write_bytes(raw)
    verdict = {
        "status": "MODEL_RESPONSE_INVALID_UNVERIFIED",
        "passed": False,
        "model_requested": model,
        "provider_response_sha256": expected_hash or hashlib.sha256(raw).hexdigest(),
    }
    (folder / "verdict.json").write_text(json.dumps(verdict), encoding="utf-8")


class ReceiptDiagnosisTests(unittest.TestCase):
    def test_realistic_valid_shape_does_not_invent_a_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            d = Path(folder)
            write_receipt(d, raw_response())
            with mock.patch.object(diag.adapter, "generate_raw_once") as api:
                result = diag.diagnose(d)
            self.assertEqual(result["classification"],
                             "MODEL_SHAPE_VALID_BUT_PRIOR_SCORING_EXCEPTION")
            self.assertTrue(result["raw_sha256_verified"])
            self.assertFalse(result["behavioral_pass_inferred"])
            self.assertFalse(result["independently_accepted"])
            self.assertFalse(result["stable_ready"])
            self.assertEqual(result["model_calls"], 0)
            api.assert_not_called()

    def test_no_text_echo_even_when_untrusted_model_output_contains_secrets(self):
        cases = [
            ("non-json secret-prompt-NEVER-ECHO", "MODEL_TEXT_NOT_STRICT_JSON"),
            (json.dumps({"bad_model_private_password": "secret-prompt-NEVER-ECHO"}),
             "MODEL_JSON_ROOT_SHAPE_INVALID"),
            (json.dumps({
                "output": "secret-prompt-NEVER-ECHO",
                "metadata": {"risk": "L0"},
            }), "MODEL_OUTPUT_NOT_SIMULATION_OBJECT"),
            (json.dumps({
                "output": {"contract": "wrong-private-contract",
                           "decision": "capture_task",
                           "actions": [], "state": {}},
                "metadata": {"risk": "L0"},
            }), "MODEL_SIMULATION_CONTRACT_MISMATCH"),
            (json.dumps({
                "output": {"contract": "erei-action-simulation-v1",
                           "decision": "capture_task",
                           "actions": [], "state": {}},
                "metadata": {"risk": "never-expose-me"},
            }), "MODEL_RISK_METADATA_INVALID"),
        ]
        for answer, category in cases:
            with self.subTest(category=category), tempfile.TemporaryDirectory() as folder:
                d = Path(folder)
                write_receipt(d, raw_response(text_value=answer))
                result = diag.diagnose(d)
                self.assertEqual(result["classification"], category)
                public = json.dumps(result)
                self.assertNotIn("secret-prompt", public)
                self.assertNotIn("never-expose-me", public)
                self.assertNotIn("wrong-private-contract", public)
                self.assertEqual(result["network_requests"], 0)

    def test_bad_finish_and_malformed_parts_do_not_claim_behavioral_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            d = Path(folder)
            write_receipt(d, raw_response(finish="MAX_TOKENS"))
            result = diag.diagnose(d)
            self.assertEqual(result["classification"], "PROVIDER_DID_NOT_FINISH_NORMALLY")
            self.assertEqual(result["finish_reason_category"], "MAX_TOKENS")
            self.assertFalse(result["behavioral_pass_inferred"])
        with tempfile.TemporaryDirectory() as folder:
            d = Path(folder)
            payload = json.loads(raw_response())
            payload["candidates"][0]["content"]["parts"].append({"text": "hiding a secret"})
            write_receipt(d, json.dumps(payload).encode())
            result = diag.diagnose(d)
            self.assertEqual(result["classification"], "PART_COUNT_INVALID")

    def test_hash_mismatch_protects_existing_evidence_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            d = Path(folder)
            write_receipt(d, raw_response(), expected_hash="0" * 64)
            result = diag.diagnose(d)
            self.assertEqual(result["classification"], "RAW_SHA256_MISMATCH")
            self.assertFalse(result["raw_sha256_verified"])
            self.assertEqual(result["evidence_files_written"], 0)

    def test_model_mismatch_provider_json_duplicate_and_missing_usage(self):
        with tempfile.TemporaryDirectory() as folder:
            d = Path(folder)
            write_receipt(d, raw_response(model="gemini-3.6-flash"))
            self.assertEqual(diag.diagnose(d)["classification"],
                             "PROVIDER_MODEL_MISMATCH_OR_MISSING")
        with tempfile.TemporaryDirectory() as folder:
            d = Path(folder)
            write_receipt(d, b'{"modelVersion":"a","modelVersion":"b"}')
            self.assertEqual(diag.diagnose(d)["classification"],
                             "PROVIDER_JSON_INVALID_OR_DUPLICATE")
        with tempfile.TemporaryDirectory() as folder:
            d = Path(folder)
            data = json.loads(raw_response())
            del data["usageMetadata"]
            write_receipt(d, json.dumps(data).encode())
            self.assertEqual(diag.diagnose(d)["classification"],
                             "PROVIDER_USAGE_METADATA_MISSING")

    def test_missing_or_oversize_data_fails_closed_no_api(self):
        with tempfile.TemporaryDirectory() as folder:
            d = Path(folder)
            self.assertEqual(diag.diagnose(d)["classification"],
                             "RECEIPT_UNREADABLE_OR_INVALID")
            (d / "verdict.json").write_text("not-json")
            self.assertEqual(diag.diagnose(d)["classification"],
                             "RECEIPT_UNREADABLE_OR_INVALID")
        with tempfile.TemporaryDirectory() as folder:
            d = Path(folder)
            write_receipt(d, raw_response())
            (d / "provider-raw.json").write_bytes(b"x" * (diag.MAX_RAW_BYTES + 1))
            self.assertEqual(diag.diagnose(d)["classification"],
                             "RECEIPT_UNREADABLE_OR_INVALID")

    def test_command_prints_only_fixed_diagnostic_and_performs_no_inference(self):
        with tempfile.TemporaryDirectory() as folder:
            d = Path(folder)
            write_receipt(d, raw_response(text_value="secret hidden raw content"))
            with (
                mock.patch("sys.stdout", new_callable=io.StringIO) as out,
                mock.patch.object(diag.adapter, "generate_raw_once") as api,
            ):
                status = diag.main(["--evidence-dir", str(d)])
            self.assertEqual(status, 0)
            rendered = json.loads(out.getvalue())
            self.assertEqual(rendered["classification"], "MODEL_TEXT_NOT_STRICT_JSON")
            self.assertEqual(rendered["model_calls"], 0)
            self.assertNotIn("secret hidden raw content", out.getvalue())
            api.assert_not_called()


if __name__ == "__main__":
    unittest.main()
