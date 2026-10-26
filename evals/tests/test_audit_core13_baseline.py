"""Mock-only regression suite for read-only frozen Core13 receipt audit."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from evals.experiments import audit_core13_baseline as audit


class FrozenRunner:
    def score(self, expectation, result, case_input):
        return result["output"]["decision"] == "omit_task", "synthetic evidence"


class Core13AuditTests(unittest.TestCase):
    def test_expected_thirteen_are_fixed_and_unique(self):
        self.assertEqual(len(audit.CASES), 13)
        self.assertEqual(len(set(id for id, folder in audit.CASES)), 13)
        self.assertEqual(audit.CASES[0][1], "smoke-005")
        self.assertEqual(audit.CASES[-1][1], "smoke-017")
        self.assertEqual(audit.EXPECTED_MODEL, "gemini-3.5-flash-lite")

    def test_fails_closed_on_missing_evidence_without_network(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(audit.gemini, "generate_raw_once") as net:
                result = audit.audit(Path(d), Path(d), Path(d))
        self.assertEqual(result["status"], "AUDIT_BLOCKED_UNVERIFIED")
        self.assertEqual(result["observed_cases"], 0)
        self.assertEqual(result["passed"], 0)
        self.assertEqual(result["independently_accepted_cases"], 0)
        self.assertFalse(result["stable_ready"])
        net.assert_not_called()

    def test_thirteen_replays_only_offline_and_no_partial_counts(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            mocked_case = {
                "id": "synthetic-only",
                "input": {"prompt": "synthetic public"},
                "expectations": [{"type": "behavioral_simulation"}],
            }
            with (
                mock.patch.object(audit.gemini, "verify_frozen_target"),
                mock.patch.object(audit.smoke, "frozen_runner", return_value=FrozenRunner()),
                mock.patch.object(audit.smoke, "load_one", side_effect=lambda *_: (
                    {"suite_id": "test", "artifact": "synthetic"},
                    {**mocked_case, "id": _[1]}, {"protocol_version": "2.0"})),
                mock.patch.object(audit.gemini, "prepare_one", return_value="PUBLIC"),
                mock.patch.object(audit, "inspect_case", side_effect=lambda _folder, *,
                                  case_id, **kw: {
                                      "case_id": case_id,
                                      "scored_pass": not case_id.endswith("MUTABLE-PIN-BLOCKED"),
                                      "score_origin": "ORIGINAL_DIRECT_SCORING",
                                      "failure_categories": [],
                                      "sha256_bound": True,
                                  }) as checked,
                mock.patch.object(audit.gemini, "generate_raw_once") as net,
            ):
                result = audit.audit(root, root, root)
            self.assertEqual(result["status"],
                             "OWNER_LOCAL_RESCORING_COMPLETE_UNVERIFIED")
            self.assertEqual(result["observed_cases"], 13)
            self.assertEqual(result["passed"], 12)
            self.assertEqual(result["failed"], 1)
            self.assertEqual(checked.call_count, 13)
            self.assertEqual(result["model_calls"], 0)
            self.assertEqual(result["network_requests"], 0)
            self.assertEqual(result["evidence_files_written"], 0)
            net.assert_not_called()

    def test_real_inspect_case_validates_hashes_and_original_replay_labeled(self):
        from evals import run_gemini_core_smoke as smoke
        from evals.adapters import gemini_core13_exact_target as gemini
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            response = {
                "output": {
                    "contract": "erei-action-simulation-v1",
                    "decision": "omit_task",
                    "actions": [],
                    "state": {"task_events": []},
                },
                "metadata": {"risk": "L0"},
            }
            raw = json.dumps({
                "modelVersion": audit.EXPECTED_MODEL,
                "usageMetadata": {"totalTokenCount": 9},
                "candidates": [{
                    "finishReason": "STOP",
                    "content": {"parts": [
                        {"text": json.dumps(response), "thoughtSignature": "test-opaque"}
                    ]},
                }],
            }).encode("utf-8")
            req = {
                "protocol_version": "2.0",
                "suite_id": "blind-suite-0123456789abcdef",
                "case_id": "blind-case-fedcba9876543210",
                "artifact": "synthetic",
                "input": {"prompt": "synthetic"},
                "context": {},
            }
            verdict = {
                "status": "MODEL_RESPONSE_SCORED_PASS_UNVERIFIED",
                "passed": True,
                "case_id": "TLR-002-EXPLANATION-NO-EVENT",
                "suite_id": "synthetic-suite",
                "source_head": gemini.EXPECTED_TARGET_HEAD,
                "source_tree": gemini.EXPECTED_TARGET_TREE,
                "model_requested": audit.EXPECTED_MODEL,
                "provider_model_version": audit.EXPECTED_MODEL,
                "prompt_sha256": "synthetic-prompt-digest",
                "provider_response_sha256": smoke.sha(raw),
                "blind_request_sha256": smoke.sha(smoke.canonical_bytes(req)),
                "usage_metadata": {"totalTokenCount": 9},
                "independently_accepted": False,
                "stable_ready": False,
                "evidence_kind": "observed_unverified",
            }
            (folder / "provider-raw.json").write_bytes(raw)
            (folder / "blind-request.json").write_text(json.dumps(req), encoding="utf-8")
            (folder / "verdict.json").write_text(json.dumps(verdict), encoding="utf-8")
            suite = {"suite_id": "synthetic-suite", "artifact": "synthetic"}
            case = {"input": req["input"], "expectations": [{"type": "mock"}]}
            out = audit.inspect_case(
                folder, case_id="TLR-002-EXPLANATION-NO-EVENT",
                expected_suite=suite, expected_case=case,
                runner=FrozenRunner(), expected_prompt_sha="synthetic-prompt-digest",
            )
            self.assertTrue(out["scored_pass"])
            self.assertEqual(out["score_origin"], "ORIGINAL_DIRECT_SCORING")
            self.assertEqual(out["original_receipt_status"],
                             "MODEL_RESPONSE_SCORED_PASS_UNVERIFIED")

            # Original invalid smoke-005 is ONLY a compatibility replay and
            # may not silently be labeled an originally scored direct PASS.
            verdict["case_id"] = "TLR-001-SUCCESS-STILL-LEARNING-DATA"
            verdict["status"] = "MODEL_RESPONSE_INVALID_UNVERIFIED"
            verdict["passed"] = False
            (folder / "verdict.json").write_text(json.dumps(verdict), encoding="utf-8")
            out = audit.inspect_case(
                folder, case_id="TLR-001-SUCCESS-STILL-LEARNING-DATA",
                expected_suite=suite, expected_case=case,
                runner=FrozenRunner(), expected_prompt_sha="synthetic-prompt-digest",
            )
            self.assertTrue(out["scored_pass"])
            self.assertEqual(out["score_origin"], "PARSER_COMPATIBILITY_REPLAY")

            # Wrong model / tampered original request / altered raw SHA block.
            verdict["provider_model_version"] = "gemini-3.6-flash"
            (folder / "verdict.json").write_text(json.dumps(verdict), encoding="utf-8")
            with self.assertRaises(ValueError):
                audit.inspect_case(
                    folder, case_id="TLR-001-SUCCESS-STILL-LEARNING-DATA",
                    expected_suite=suite, expected_case=case,
                    runner=FrozenRunner(), expected_prompt_sha="synthetic-prompt-digest",
                )
            verdict["provider_model_version"] = audit.EXPECTED_MODEL
            (folder / "verdict.json").write_text(json.dumps(verdict), encoding="utf-8")
            req["input"]["prompt"] = "tampered"
            (folder / "blind-request.json").write_text(json.dumps(req), encoding="utf-8")
            with self.assertRaises(ValueError):
                audit.inspect_case(
                    folder, case_id="TLR-001-SUCCESS-STILL-LEARNING-DATA",
                    expected_suite=suite, expected_case=case,
                    runner=FrozenRunner(), expected_prompt_sha="synthetic-prompt-digest",
                )

    def test_late_failure_clears_all_partial_scores(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            ids = [id for id, folder in audit.CASES]
            def load(root, case_id, runner):
                return (
                    {"suite_id": "mock", "artifact": "mock"},
                    {"id": case_id, "input": {"prompt": "synthetic"}},
                    {"protocol_version": "2.0"},
                )
            called = []
            def inspect(folder, *, case_id, **kwargs):
                called.append(case_id)
                if case_id == ids[-1]:
                    raise ValueError("synthetic failure at final receipt")
                return {"case_id": case_id, "scored_pass": True,
                        "score_origin": "ORIGINAL_DIRECT_SCORING",
                        "failure_categories": []}
            with (
                mock.patch.object(audit.gemini, "verify_frozen_target"),
                mock.patch.object(audit.smoke, "frozen_runner", return_value=FrozenRunner()),
                mock.patch.object(audit.smoke, "load_one", side_effect=load),
                mock.patch.object(audit.gemini, "prepare_one", return_value="PUBLIC"),
                mock.patch.object(audit, "inspect_case", side_effect=inspect),
            ):
                out = audit.audit(root, root, root)
            self.assertEqual(len(called), 13)
            self.assertEqual(out["status"], "AUDIT_BLOCKED_UNVERIFIED")
            self.assertEqual(out["cases"], [])
            self.assertEqual(out["observed_cases"], 0)
            self.assertEqual(out["passed"], 0)
            self.assertEqual(out["original_direct_pass"], 0)
            self.assertEqual(out["parser_compatibility_replay_pass"], 0)

    def test_safe_category_maps_not_provider_text(self):
        self.assertEqual(audit.SAFE_FAIL_CODES[
            "simulation action must contain op"], "ACTION_OP_INVALID")
        self.assertEqual(audit.SAFE_FAIL_CODES[
            "capability blocking reason contradicts the required behavior"],
            "WRONG_BLOCK_CAUSE")
        self.assertNotIn("prompt", json.dumps(audit.SAFE_FAIL_CODES).lower())


if __name__ == "__main__":
    unittest.main()
