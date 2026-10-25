"""Free-tier metadata-only diagnosis never uses generateContent or leaks secrets."""
import io
import json
import unittest
import urllib.error
from unittest import mock

from evals import probe_gemini_access as probe


class MetadataProbeTests(unittest.TestCase):
    def test_valid_key_lists_target_model_without_any_generate_call(self):
        class Response:
            status = 200
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, n):
                return json.dumps({
                    "name": "models/gemini-3.8-flash",
                    "supportedGenerationMethods": ["generateContent", "countTokens"],
                }).encode()
        class Opener:
            def __init__(self):
                self.calls = []
            def open(self, request, timeout):
                self.calls.append((request, timeout))
                return Response()
        fake = Opener()
        x = probe.metadata_check("synthetic-key-ONLY", opener=fake)
        self.assertEqual(x["http_status"], 200)
        self.assertEqual(x["result"], "MODEL_METADATA_AVAILABLE")
        self.assertTrue(x["model_identity_matches"])
        self.assertTrue(x["generate_content_listed"])
        self.assertTrue(x["does_not_prove_free_tier_or_generation_quota"])
        self.assertEqual(len(fake.calls), 1)
        req, _ = fake.calls[0]
        self.assertEqual(req.get_method(), "GET")
        self.assertNotIn(":generateContent", req.full_url)
        self.assertNotIn("synthetic-key-ONLY", req.full_url)

    def test_403_400_429_404_only_safe_status_without_error_body(self):
        for code in (400, 401, 403, 404, 429):
            with self.subTest(code=code):
                fail = urllib.error.HTTPError(
                    probe.API_URL, code,
                    "synthetic secret SHOULD-NOT-LOG", {},
                    io.BytesIO(b'{"error":{"message":"secret SHOULD-NOT-LOG"}}')
                )
                opener = mock.Mock()
                opener.open.side_effect = fail
                x = probe.metadata_check("synthetic-key-ONLY", opener=opener)
                self.assertEqual(x["result"], "MODEL_METADATA_HTTP_ERROR")
                self.assertEqual(x["http_status"], code)
                self.assertNotIn("secret", json.dumps(x).lower())

    def test_bad_key_never_opens_network(self):
        for value in ("secret\n", "secret\r", " secret", "x\u2603", "", None):
            with self.subTest(value=repr(value)):
                fake = mock.Mock()
                result = probe.metadata_check(value, opener=fake)
                self.assertEqual(result["result"], "KEY_FORMAT_INVALID")
                fake.open.assert_not_called()

    def test_wrong_or_missing_metadata_never_reports_model_ready(self):
        for data in ({"name": "models/other", "supportedGenerationMethods": ["generateContent"]},
                     {"name": "models/gemini-3.8-flash", "supportedGenerationMethods": []}):
            result = probe.metadata_check("synthetic-key", opener=_Fake(data))
            self.assertEqual(result["result"], "MODEL_METADATA_AVAILABLE")
            self.assertFalse(result["model_identity_matches"] and result["generate_content_listed"])


class _Fake:
    def __init__(self, value):
        self.value = value
    def open(self, request, timeout):
        value = self.value
        class Response:
            status = 200
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def read(self, n):
                return json.dumps(value).encode()
        return Response()


if __name__ == "__main__":
    unittest.main()
