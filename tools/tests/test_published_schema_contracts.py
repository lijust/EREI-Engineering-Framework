import json
import unittest
from pathlib import Path


class PublishedSchemaContractTests(unittest.TestCase):
    def test_retrospective_v2_signal_definitions_are_self_contained(self):
        schema = json.loads(Path("schemas/retrospective-task-learning-event.schema.json").read_text(encoding="utf-8"))
        definitions = schema["$defs"]
        self.assertNotIn("signalBase", definitions)
        for name in ("countSignal", "booleanSignal"):
            signal = definitions[name]
            self.assertEqual(signal["type"], "object")
            self.assertFalse(signal["additionalProperties"])
            self.assertEqual(set(signal["required"]), {"name", "value", "quality", "source_refs"})
            self.assertEqual(set(signal["properties"]), {"name", "value", "quality", "source_refs"})
            self.assertNotIn("allOf", signal)
        self.assertEqual(definitions["countSignal"]["properties"]["value"]["type"], "integer")
        self.assertEqual(definitions["booleanSignal"]["properties"]["value"]["type"], "boolean")

    def test_exact_target_run_schema_is_reconstructible_v2(self):
        schema = json.loads(Path("evals/exact-target-run.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], 2)
        execution = schema["properties"]["executions"]["items"]
        self.assertFalse(execution["additionalProperties"])
        self.assertEqual(
            set(execution["required"]),
            {"suite_id", "case_id", "status", "response_digest", "response", "adapter_error"},
        )
        self.assertEqual(execution["properties"]["status"]["enum"], ["pass", "fail"])
        self.assertEqual(execution["properties"]["adapter_error"]["type"], "boolean")
        response_types = execution["properties"]["response"]["type"]
        self.assertEqual(set(response_types), {"object", "null"})
        conditions = execution.get("allOf")
        self.assertIsInstance(conditions, list)
        self.assertEqual(len(conditions), 1)
        condition = conditions[0]
        self.assertEqual(condition["if"]["properties"]["adapter_error"]["const"], True)
        self.assertEqual(condition["then"]["properties"]["status"]["const"], "fail")
        self.assertEqual(condition["then"]["properties"]["response"]["type"], "null")
        self.assertEqual(condition["else"]["properties"]["response"]["type"], "object")

    def test_exact_target_package_identity_schema_is_strict_v2(self):
        schema = json.loads(Path("evals/exact-target-package-identity.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], 2)
        self.assertFalse(schema["additionalProperties"])
        required = {
            "schema_version", "repository", "target_id", "framework_ref", "target_tree",
            "release_carrier_ref", "adapter_id", "adapter_revision", "runtime_id",
            "runtime_version", "requested_cli_version", "requested_cli_integrity", "model",
            "github_run_id", "github_run_attempt", "run_id", "run_manifest_path",
            "execution_evidence_path", "runtime_identity_path", "run_manifest_sha256",
            "execution_evidence_sha256",
        }
        self.assertEqual(set(schema["required"]), required)
        self.assertEqual(set(schema["properties"]), required)
        self.assertEqual(schema["properties"]["repository"]["pattern"], "^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
        self.assertEqual(
            schema["properties"]["requested_cli_integrity"]["pattern"],
            "^sha512-[A-Za-z0-9+/]{86}==$",
        )
        manifest_path = schema["properties"]["run_manifest_path"]
        identity_path = schema["properties"]["runtime_identity_path"]
        self.assertIn("exact-target-runs", manifest_path["pattern"])
        self.assertEqual(manifest_path["not"]["pattern"], "\\.identity\\.json$")
        self.assertIn("identity", identity_path["pattern"])
        self.assertEqual(schema["properties"]["github_run_id"]["minimum"], 1)
        self.assertEqual(schema["properties"]["github_run_attempt"]["minimum"], 1)
        self.assertEqual(schema["properties"]["run_manifest_sha256"]["pattern"], "^[a-f0-9]{64}$")
        self.assertEqual(schema["properties"]["execution_evidence_sha256"]["pattern"], "^[a-f0-9]{64}$")


if __name__ == "__main__":
    unittest.main()
