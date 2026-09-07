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


if __name__ == "__main__":
    unittest.main()
