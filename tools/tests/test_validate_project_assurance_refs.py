import tempfile
import unittest
from pathlib import Path

from tools import validate_project_assurance_refs as guard


class AssuranceReferenceIntegrityTests(unittest.TestCase):
    def target(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / ".github" / "workflows").mkdir(parents=True)
        (root / "tests").mkdir()
        (root / "tools").mkdir()
        return temp, root

    def test_valid_literal_run_references_pass(self):
        temp, root = self.target()
        with temp:
            (root / "tests" / "alpha.test.js").write_text("", encoding="utf-8")
            (root / "tools" / "beta.py").write_text("", encoding="utf-8")
            (root / "tools" / "gamma.ps1").write_text("", encoding="utf-8")
            (root / ".github" / "workflows" / "ci.yml").write_text(
                "jobs:\n  x:\n    steps:\n      - run: node tests/alpha.test.js\n"
                "      - run: |\n          python -u tools/beta.py --check\n          pwsh -File tools/gamma.ps1\n",
                encoding="utf-8",
            )
            result = guard.scan_target(root)
            self.assertEqual(result["missing_count"], 0)
            self.assertEqual({item["path"] for item in result["references"]}, {
                "tests/alpha.test.js", "tools/beta.py", "tools/gamma.ps1"
            })

    def test_missing_literal_script_is_fail_closed(self):
        temp, root = self.target()
        with temp:
            (root / ".github" / "workflows" / "ci.yml").write_text(
                "jobs:\n  x:\n    steps:\n      - run: node tests/phantom.test.js\n",
                encoding="utf-8",
            )
            result = guard.scan_target(root)
            self.assertEqual(result["missing_count"], 1)
            self.assertEqual(result["missing"][0]["path"], "tests/phantom.test.js")

    def test_comments_echo_text_and_dynamic_paths_are_not_claimed_as_static_refs(self):
        temp, root = self.target()
        with temp:
            (root / ".github" / "workflows" / "ci.yml").write_text(
                "jobs:\n  x:\n    steps:\n      - run: |\n"
                "          # node tests/comment-only.test.js\n"
                "          echo \"node tests/display-only.test.js\"\n"
                "          node \"$ROOT/tests/dynamic.test.js\"\n",
                encoding="utf-8",
            )
            result = guard.scan_target(root)
            self.assertEqual(result["reference_count"], 0)
            self.assertEqual(result["missing_count"], 0)

    def test_direct_script_execution_is_checked(self):
        temp, root = self.target()
        with temp:
            (root / "tools" / "check.sh").write_text("", encoding="utf-8")
            (root / ".github" / "workflows" / "ci.yml").write_text(
                "jobs:\n  x:\n    steps:\n      - run: ./tools/check.sh && ./tests/missing.sh\n",
                encoding="utf-8",
            )
            result = guard.scan_target(root)
            self.assertEqual(result["missing_count"], 1)
            self.assertEqual(result["missing"][0]["path"], "tests/missing.sh")

    def test_literal_local_action_reference_is_checked(self):
        temp, root = self.target()
        with temp:
            (root / ".github" / "actions" / "known").mkdir(parents=True)
            (root / ".github" / "workflows" / "ci.yml").write_text(
                "jobs:\n  x:\n    steps:\n      - uses: ./.github/actions/known\n"
                "      - uses: ./.github/actions/phantom\n",
                encoding="utf-8",
            )
            result = guard.scan_target(root)
            self.assertEqual(result["missing_count"], 1)
            self.assertEqual(result["missing"][0]["kind"], "local_action")
            self.assertEqual(result["missing"][0]["path"], ".github/actions/phantom")

    def test_missing_workflow_directory_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(guard.ReferenceError, "missing workflow directory"):
                guard.scan_target(Path(tmp))


if __name__ == "__main__":
    unittest.main()
