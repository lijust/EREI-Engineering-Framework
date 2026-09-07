import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "validate_runtime_adapter.py"
spec = importlib.util.spec_from_file_location("validate_runtime_adapter", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def base_manifest():
    return {
        "schema_version": 1,
        "adapter_id": "mock-runtime",
        "display_name": "Mock Runtime",
        "version": "1.0",
        "status": "candidate",
        "runtime_kind": "mock",
        "transport": "cli",
        "capabilities": ["execute_task", "trace_export"],
    }


class RuntimeAdapterValidatorTests(unittest.TestCase):
    def test_valid_candidate(self):
        self.assertTrue(mod.validate_manifest(base_manifest())["valid"])

    def test_unknown_capability_rejected(self):
        data = base_manifest()
        data["capabilities"].append("telepathy")
        with self.assertRaises(mod.ValidationError):
            mod.validate_manifest(data)

    def test_duplicate_capability_rejected(self):
        data = base_manifest()
        data["capabilities"].append("execute_task")
        with self.assertRaises(mod.ValidationError):
            mod.validate_manifest(data)

    def test_unknown_field_rejected(self):
        data = base_manifest()
        data["unpublished_contract"] = True
        with self.assertRaisesRegex(mod.ValidationError, "unknown fields"):
            mod.validate_manifest(data)

    def test_display_name_type_is_enforced(self):
        data = base_manifest()
        data["display_name"] = {"not": "a string"}
        with self.assertRaises(mod.ValidationError):
            mod.validate_manifest(data)

    def test_runtime_kind_type_is_enforced(self):
        data = base_manifest()
        data["runtime_kind"] = ["mock"]
        with self.assertRaises(mod.ValidationError):
            mod.validate_manifest(data)

    def test_metadata_must_be_object(self):
        data = base_manifest()
        data["metadata"] = "not-an-object"
        with self.assertRaises(mod.ValidationError):
            mod.validate_manifest(data)

    def test_stable_requires_sources(self):
        data = base_manifest()
        data["status"] = "stable"
        with self.assertRaises(mod.ValidationError):
            mod.validate_manifest(data)

    def test_stable_with_sources(self):
        data = base_manifest()
        data["status"] = "stable"
        data["sources"] = "SOURCES.md"
        self.assertTrue(mod.validate_manifest(data)["valid"])


if __name__ == "__main__":
    unittest.main()
