import subprocess
import tempfile
import unittest
from pathlib import Path

from tools import exact_target_evidence


class ExactTargetEvidenceHistoryTests(unittest.TestCase):
    PATHS = (
        Path("evals/exact-target-runs/copilot-123-1.json"),
        Path("evals/EXECUTION_EVIDENCE.copilot-123-1.json"),
        Path("evals/exact-target-runs/copilot-123-1.identity.json"),
    )

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "EREI Test")
        self.base_branch = self.git("branch", "--show-current")
        self.write("README.md", "carrier\n")
        self.carrier = self.commit("release carrier")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        process = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        if process.returncode != 0:
            self.fail(f"git {' '.join(args)} failed: {process.stderr}")
        return process.stdout.strip()

    def write(self, path, content="{}\n"):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def identity(self, carrier=None):
        return {
            "run_manifest_path": self.PATHS[0].as_posix(),
            "execution_evidence_path": self.PATHS[1].as_posix(),
            "runtime_identity_path": self.PATHS[2].as_posix(),
            "release_carrier_ref": carrier or self.carrier,
        }

    def add_three(self):
        for index, path in enumerate(self.PATHS):
            self.write(path, f"{{\"file\": {index}}}\n")
        return self.commit("import exact-target evidence")

    def test_materialized_carrier_checks_original_three_file_history(self):
        self.add_three()
        revision = self.git("rev-parse", "HEAD")
        with tempfile.TemporaryDirectory() as tmp:
            copied = Path(tmp)
            for p in self.PATHS:
                destination = copied / p
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((self.repo / p).read_bytes())
            result = exact_target_evidence._validate_history_binding(
                self.repo, self.identity(), closure_ref=revision, materialized_root=copied
            )
            self.assertEqual(result["release_carrier_ref"], self.carrier)

    def test_materialized_carrier_rejects_split_evidence_commits(self):
        self.write(self.PATHS[0])
        self.write(self.PATHS[1])
        self.commit("partial evidence")
        self.write(self.PATHS[2])
        revision = self.commit("late identity")
        with tempfile.TemporaryDirectory() as tmp:
            copied = Path(tmp)
            for p in self.PATHS:
                dest = copied / p
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes((self.repo / p).read_bytes())
            with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "one commit"):
                exact_target_evidence._validate_history_binding(
                    self.repo, self.identity(), closure_ref=revision, materialized_root=copied
                )

    def test_materialized_carrier_rejects_bytes_different_from_git(self):
        self.add_three()
        revision = self.git("rev-parse", "HEAD")
        with tempfile.TemporaryDirectory() as tmp:
            copied = Path(tmp)
            for p in self.PATHS:
                dest = copied / p
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes((self.repo / p).read_bytes())
            (copied / self.PATHS[0]).write_text("tampered materialization", encoding="utf-8")
            with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "differ from exact carrier Git blob"):
                exact_target_evidence._validate_history_binding(
                    self.repo, self.identity(), closure_ref=revision, materialized_root=copied
                )

    def test_three_file_evidence_commit_directly_above_carrier_passes(self):
        evidence_commit = self.add_three()
        result = exact_target_evidence._validate_history_binding(self.repo, self.identity())
        self.assertEqual(result["evidence_commit"], evidence_commit)
        self.assertEqual(result["release_carrier_ref"], self.carrier)
        self.assertEqual(set(result["retained_paths"]), {path.as_posix() for path in self.PATHS})

    def test_split_evidence_commits_fail(self):
        self.write(self.PATHS[0])
        self.write(self.PATHS[1])
        self.commit("partial evidence")
        self.write(self.PATHS[2])
        self.commit("late identity")
        with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "one commit"):
            exact_target_evidence._validate_history_binding(self.repo, self.identity())

    def test_wrong_recorded_carrier_fails(self):
        self.add_three()
        with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "release_carrier_ref"):
            exact_target_evidence._validate_history_binding(self.repo, self.identity("f" * 40))

    def test_fourth_file_in_evidence_commit_fails(self):
        for path in self.PATHS:
            self.write(path)
        self.write("notes.txt", "not evidence\n")
        self.commit("evidence plus unrelated file")
        with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "exactly"):
            exact_target_evidence._validate_history_binding(self.repo, self.identity())

    def test_later_rewrite_of_any_retained_file_fails(self):
        self.add_three()
        self.write(self.PATHS[2], "{\"rewritten\": true}\n")
        self.commit("rewrite identity")
        with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "changed after"):
            exact_target_evidence._validate_history_binding(self.repo, self.identity())

    def test_side_branch_evidence_merged_later_is_not_release_first_parent_history(self):
        self.git("checkout", "-q", "-b", "evidence-side")
        self.add_three()
        self.git("checkout", "-q", self.base_branch)
        self.write("main-note.txt", "release branch moved\n")
        self.commit("move release branch")
        self.git("merge", "--no-ff", "-q", "-m", "merge evidence side branch", "evidence-side")
        with self.assertRaisesRegex(exact_target_evidence.ExactTargetEvidenceError, "first-parent"):
            exact_target_evidence._validate_history_binding(self.repo, self.identity())


if __name__ == "__main__":
    unittest.main()
