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


if __name__ == "__main__":
    unittest.main()
