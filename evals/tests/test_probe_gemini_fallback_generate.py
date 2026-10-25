"""No-network regression for one-shot public-only Gemini fallback diagnostic."""
import io
import json
import unittest
import urllib.error
from unittest import mock
from evals import probe_gemini_fallback_generate as target


class Answer:
    status = 200
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def read(self, bound):
        return self.payload


class FallbackProbeTests(unittest.TestCase):
    def test_approved_alternate_model_constant_public_text_single_post(self):
        for model in target.ALLOWED_DIAGNOSTIC_MODELS:
            obj = {"modelVersion": model, "usageMetadata": {
                "promptTokenCount": 10, "candidatesTokenCount": 4, "totalTokenCount": 14
            }, "candidates": [{"finishReason": "STOP", "content": {
                "parts": [{"text": "READY"}]
            }}]}
            opener = mock.Mock()
            opener.open.return_value = Answer(json.dumps(obj).encode())
            report = target.probe(model=model, key="synthetic-test-key", opener=opener)
            opener.open.assert_called_once()
            request = opener.open.call_args.args[0]
            self.assertEqual(request.get_method(), "POST")
            self.assertIn("/models/" + model + ":generateContent", request.full_url)
            self.assertNotIn("synthetic-test-key", request.full_url)
            self.assertEqual(
                json.loads(request.data)["contents"][0]["parts"][0]["text"],
                "Reply with exactly READY."
            )
            self.assertTrue(report["returned_ready"])
            self.assertEqual(report["usage_metadata"]["totalTokenCount"], 14)
            self.assertEqual(report["counted_core_cases"], 0)
            self.assertFalse(report["stable_ready"])

    def test_503_429_403_never_echo_provider_or_secret(self):
        for code in (503, 429, 403):
            opener = mock.Mock()
            opener.open.side_effect = urllib.error.HTTPError(
                "https://generativelanguage.googleapis.com", code,
                "private-data-SECRET", {}, io.BytesIO(b"PRIVATE-SECRET")
            )
            report = target.probe(model="gemini-3.6-flash",
                                  key="private-test-secret", opener=opener)
            self.assertEqual(report["status"], "MODEL_DIAGNOSTIC_HTTP_ERROR")
            self.assertEqual(report["http_status"], code)
            self.assertNotIn("PRIVATE-SECRET", json.dumps(report))
            self.assertNotIn("private-test-secret", json.dumps(report))
            self.assertEqual(report["counted_core_cases"], 0)
            opener.open.assert_called_once()

    def test_unapproved_models_and_invalid_key_no_http(self):
        for model in ("gemini-3.8-flash", "gemini-flash-latest", "anything"):
            client = mock.Mock()
            report = target.probe(model=model, key="valid-test", opener=client)
            self.assertEqual(report["status"], "UNAPPROVED_DIAGNOSTIC_MODEL")
            client.open.assert_not_called()
        for key in ("", " secret", "secret\n", "secret\r", None, "with☃"):
            with self.subTest(key=repr(key)):
                client = mock.Mock()
                report = target.probe(model="gemini-3.6-flash", key=key, opener=client)
                self.assertEqual(report["status"], "KEY_FORMAT_INVALID")
                client.open.assert_not_called()

    def test_no_live_or_no_confirm_guards_all_network_calls(self):
        for args in (
            ["--model", "gemini-3.6-flash"],
            ["--model", "gemini-3.5-flash-lite", "--live"],
            ["--model", "gemini-3.6-flash", "--confirm-free-tier"],
        ):
            with (
                self.subTest(args=args),
                mock.patch.object(target, "probe") as api,
                mock.patch("sys.stdout", new_callable=io.StringIO) as out,
                mock.patch.object(target.getpass, "getpass") as ask,
            ):
                self.assertEqual(target.main(args), 2)
                self.assertIn("NOT_AUTHORIZED_NO_API_CALL", out.getvalue())
                api.assert_not_called()
                ask.assert_not_called()

    def test_malformed_body_fails_without_false_core_receipt(self):
        for raw in (b"not-json", b"[]", b'{"candidates":[]}',
                    b'{"candidates":[null]}', b'{"candidates":[{"content":{"parts":null}}]}'):
            with self.subTest(raw=raw):
                client = mock.Mock()
                client.open.return_value = Answer(raw)
                result = target.probe(model="gemini-3.5-flash-lite",
                                      key="local-test-key", opener=client)
                self.assertNotEqual(result.get("status"), "MODEL_DIAGNOSTIC_RESPONSE_RECEIVED")
                self.assertEqual(result["counted_core_cases"], 0)


if __name__ == "__main__":
    unittest.main()
