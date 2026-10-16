from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import github_review_provenance as mod


class ReviewProvenanceTests(unittest.TestCase):
    def descriptor(self, purpose="security_approval"):
        return {
            "provider": "github_codex_review",
            "reviewer_login": "chatgpt-codex-connector[bot]",
            "review_type": "code_review",
            "purpose": purpose,
        }

    def test_descriptor_is_strict(self):
        self.assertEqual(
            mod.validate_descriptor(self.descriptor(), expected_purpose="security_approval")["provider"],
            "github_codex_review",
        )
        bad = self.descriptor()
        bad["reviewer_login"] = "owner"
        with self.assertRaisesRegex(mod.ReviewProvenanceError, "Codex bot"):
            mod.validate_descriptor(bad)

    def test_clean_summary_must_match_exact_commit(self):
        comment = {
            "id": 42,
            "user": {"login": "chatgpt-codex-connector[bot]"},
            "body": '<!-- codex-review-state:v1 {"code_review":{"commit_sha":"'
            + "a" * 40
            + '","has_any_findings":false,"has_unresolved_findings":false,"status":"completed"}} -->',
        }
        self.assertEqual(
            mod._clean_codex_summary([comment], "a" * 40, "chatgpt-codex-connector[bot]"),
            42,
        )
        self.assertIsNone(
            mod._clean_codex_summary([comment], "b" * 40, "chatgpt-codex-connector[bot]")
        )

    def test_verify_requires_authenticated_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict("os.environ", {}, clear=True):
                with self.assertRaisesRegex(mod.ReviewProvenanceError, "GITHUB_TOKEN"):
                    mod.verify_artifact_review(
                        Path(tmp),
                        repository="lijust/EREI-Engineering-Framework",
                        target_ref="a" * 40,
                        closure_ref="b" * 40,
                        artifact_path="releases/approvals/security.json",
                        descriptor=self.descriptor(),
                        expected_purpose="security_approval",
                    )

    def test_verify_accepts_matching_merged_release_pr_and_clean_codex_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "EREI Test"], check=True)
            (repo / "README.md").write_text("target\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "target"], check=True)
            target = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()

            path = repo / "releases" / "approvals" / "security.json"
            path.parent.mkdir(parents=True)
            path.write_text('{"approved":true}\n', encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "reviewed"], check=True)
            reviewed = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
            reviewed_blob = subprocess.check_output(
                ["git", "-C", str(repo), "rev-parse", f"{reviewed}:releases/approvals/security.json"],
                text=True,
            ).strip()

            pulls = [{
                "number": 77,
                "merged_at": "2026-10-16T00:00:00Z",
                "head": {"sha": reviewed},
                "base": {"ref": "release/vnext-rc3"},
            }]
            comments = [{
                "id": 88,
                "user": {"login": "chatgpt-codex-connector[bot]"},
                "body": '<!-- codex-review-state:v1 '
                + json.dumps({"code_review": {
                    "commit_sha": reviewed,
                    "has_any_findings": False,
                    "has_unresolved_findings": False,
                    "status": "completed",
                }}, separators=(",", ":"))
                + " -->",
            }]
            files = [{
                "filename": "releases/approvals/security.json",
                "status": "added",
                "sha": reviewed_blob,
            }]

            def fake(url, token):
                if "/commits/" in url:
                    return pulls
                if "/files" in url:
                    return files
                return comments

            with mock.patch.object(mod, "_github_json", side_effect=fake):
                result = mod.verify_artifact_review(
                    repo,
                    repository="lijust/EREI-Engineering-Framework",
                    target_ref=target,
                    closure_ref=reviewed,
                    artifact_path="releases/approvals/security.json",
                    descriptor=self.descriptor(),
                    expected_purpose="security_approval",
                    token="token",
                )
            self.assertEqual(result["status"], "verified")
            self.assertEqual(result["pull_request_number"], 77)
            self.assertEqual(result["reviewed_commit"], reviewed)
            self.assertEqual(result["reviewed_artifact_blob"], reviewed_blob)


    def test_unrelated_clean_pr_cannot_launder_preexisting_artifact(self):
        files = [{
            "filename": "README.md",
            "status": "modified",
            "sha": "a" * 40,
        }]
        self.assertFalse(
            mod._pr_reviews_artifact(
                files,
                artifact_path="releases/approvals/security.json",
                expected_blob="b" * 40,
            )
        )

    def test_reviewed_artifact_requires_exact_resulting_blob(self):
        files = [{
            "filename": "releases/approvals/security.json",
            "status": "modified",
            "sha": "a" * 40,
        }]
        self.assertFalse(
            mod._pr_reviews_artifact(
                files,
                artifact_path="releases/approvals/security.json",
                expected_blob="b" * 40,
            )
        )
        self.assertTrue(
            mod._pr_reviews_artifact(
                files,
                artifact_path="releases/approvals/security.json",
                expected_blob="a" * 40,
            )
        )


if __name__ == "__main__":
    unittest.main()
