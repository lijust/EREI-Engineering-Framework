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
            "review_type": "code_review" if purpose == "architecture_approval" else "security_review",
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
            "body": '<!-- codex-review-state:v1 {"security_review":{"commit_sha":"'
            + "a" * 40
            + '","has_any_findings":false,"has_unresolved_findings":false,"status":"completed"}} -->',
        }
        self.assertEqual(
            mod._clean_codex_summary([comment], "a" * 40, "chatgpt-codex-connector[bot]", "security_review"),
            42,
        )
        self.assertIsNone(
            mod._clean_codex_summary([comment], "b" * 40, "chatgpt-codex-connector[bot]", "security_review")
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

    def _reviewed_merge_fixture(self, repo: Path):
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        for args in (
            ["config", "user.email", "test@example.invalid"],
            ["config", "user.name", "EREI Test"],
        ):
            subprocess.run(["git", "-C", str(repo), *args], check=True)
        (repo / "README.md").write_text("target\\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "target"], check=True)
        target = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
        ).strip()
        base_branch = subprocess.check_output(
            ["git", "-C", str(repo), "branch", "--show-current"], text=True
        ).strip()
        subprocess.run(["git", "-C", str(repo), "checkout", "-q", "-b", "reviewed-change"], check=True)
        path = repo / "releases" / "approvals" / "security.json"
        path.parent.mkdir(parents=True)
        path.write_text('{"approved":true}\\n', encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "reviewed"], check=True)
        reviewed = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
        ).strip()
        reviewed_blob = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", f"{reviewed}:releases/approvals/security.json"],
            text=True,
        ).strip()
        subprocess.run(["git", "-C", str(repo), "checkout", "-q", base_branch], check=True)
        subprocess.run(
            ["git", "-C", str(repo), "merge", "--no-ff", "-q", "-m", "reviewed merge", "reviewed-change"],
            check=True,
        )
        carrier = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
        ).strip()
        return target, reviewed, carrier, reviewed_blob

    def test_verify_accepts_matching_merged_release_pr_and_clean_codex_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            target, reviewed, carrier, reviewed_blob = self._reviewed_merge_fixture(repo)
            pulls = [{
                "number": 77,
                "merged_at": "2026-10-16T00:00:00Z",
                "merge_commit_sha": carrier,
                "head": {"sha": reviewed},
                "base": {"ref": "release/vnext-rc3"},
            }]
            comments = [{
                "id": 88,
                "updated_at": "2026-10-16T01:00:00Z",
                "user": {"login": "chatgpt-codex-connector[bot]"},
                "body": '<!-- codex-review-state:v1 '
                + json.dumps({"security_review": {
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
                    closure_ref=carrier,
                    artifact_path="releases/approvals/security.json",
                    descriptor=self.descriptor(),
                    expected_purpose="security_approval",
                    token="token",
                )
            self.assertEqual(result["status"], "verified")
            self.assertEqual(result["pull_request_number"], 77)
            self.assertEqual(result["reviewed_commit"], reviewed)
            self.assertEqual(result["merge_commit_sha"], carrier)
            self.assertEqual(result["reviewed_artifact_blob"], reviewed_blob)

    def test_unrelated_merged_pr_does_not_authenticate_carrier(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            target, reviewed, carrier, reviewed_blob = self._reviewed_merge_fixture(repo)
            alternate = "c" * 40
            pulls = [{
                "number": 77,
                "merged_at": "2026-10-16T00:00:00Z",
                "merge_commit_sha": alternate,
                "head": {"sha": reviewed},
                "base": {"ref": "release/vnext-rc3"},
            }]
            with mock.patch.object(mod, "_github_paginated_array", return_value=pulls):
                with self.assertRaisesRegex(mod.ReviewProvenanceError, "no merged release PR"):
                    mod.verify_artifact_review(
                        repo,
                        repository="lijust/EREI-Engineering-Framework",
                        target_ref=target,
                        closure_ref=carrier,
                        artifact_path="releases/approvals/security.json",
                        descriptor=self.descriptor(),
                        expected_purpose="security_approval",
                        token="token",
                    )

    def test_security_claim_rejects_clean_code_review_without_security_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            target, reviewed, carrier, reviewed_blob = self._reviewed_merge_fixture(repo)
            pulls = [{
                "number": 77,
                "merged_at": "2026-10-16T00:00:00Z",
                "merge_commit_sha": carrier,
                "head": {"sha": reviewed},
                "base": {"ref": "release/vnext-rc3"},
            }]
            comments = [{
                "id": 88,
                "user": {"login": "chatgpt-codex-connector[bot]"},
                "body": '<!-- codex-review-state:v1 ' + json.dumps({"code_review": {
                    "commit_sha": reviewed, "has_any_findings": False,
                    "has_unresolved_findings": False, "status": "completed",
                }}) + " -->",
            }]
            files = [{"filename":"releases/approvals/security.json", "status":"added", "sha":reviewed_blob}]
            def fake(url, token):
                if "/commits/" in url:
                    return pulls
                if "/files" in url:
                    return files
                return comments
            with mock.patch.object(mod, "_github_json", side_effect=fake):
                with self.assertRaisesRegex(mod.ReviewProvenanceError, "no merged release PR"):
                    mod.verify_artifact_review(
                        repo, repository="lijust/EREI-Engineering-Framework",
                        target_ref=target, closure_ref=carrier,
                        artifact_path="releases/approvals/security.json",
                        descriptor=self.descriptor(), expected_purpose="security_approval", token="token",
                    )

    def test_newer_findings_supersede_older_clean_review(self):
        def item(comment_id, timestamp, clean):
            return {
                "id": comment_id,
                "updated_at": timestamp,
                "user": {"login": "chatgpt-codex-connector[bot]"},
                "body": '<!-- codex-review-state:v1 ' + json.dumps({"security_review": {
                    "commit_sha": "a" * 40, "status":"completed",
                    "has_any_findings": not clean,
                    "has_unresolved_findings": not clean,
                }}) + " -->",
            }
        comments = [
            item(99, "2026-10-16T02:00:00Z", False),
            item(42, "2026-10-16T01:00:00Z", True),
        ]
        self.assertIsNone(mod._clean_codex_summary(
            comments, "a" * 40, "chatgpt-codex-connector[bot]", "security_review",
        ))

    def test_newer_in_progress_review_supersedes_older_clean(self):
        old = {
            "id": 10, "updated_at":"2026-10-16T01:00:00Z",
            "user":{"login":"chatgpt-codex-connector[bot]"},
            "body": '<!-- codex-review-state:v1 ' + json.dumps({"code_review": {
                "commit_sha":"a"*40, "status":"completed",
                "has_any_findings":False, "has_unresolved_findings":False,
            }}) + " -->",
        }
        newer = {
            "id": 20, "updated_at":"2026-10-16T02:00:00Z",
            "user":{"login":"chatgpt-codex-connector[bot]"},
            "body": '<!-- codex-review-state:v1 ' + json.dumps({"code_review": {
                "commit_sha":"a"*40, "status":"in_progress",
                "has_any_findings":None, "has_unresolved_findings":None,
            }}) + " -->",
        }
        self.assertIsNone(mod._clean_codex_summary(
            [old,newer], "a"*40, "chatgpt-codex-connector[bot]", "code_review",
        ))

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


    def test_candidate_selection_includes_later_reviewed_head_with_same_artifact_blob(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "EREI Test"], check=True)
            (repo / "README.md").write_text("target\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "target"], check=True)
            target = subprocess.check_output(
                ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
            ).strip()

            artifact = repo / "security" / "ASSURANCE_ENFORCEMENT.json"
            artifact.parent.mkdir(parents=True)
            artifact.write_text('{"schema_version":2}\n', encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "artifact"], check=True)

            (repo / "README.md").write_text("target\nfollow-up\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "follow-up"], check=True)
            reviewed_head = subprocess.check_output(
                ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
            ).strip()

            candidates = mod._candidate_review_commits(
                repo,
                target,
                reviewed_head,
                "security/ASSURANCE_ENFORCEMENT.json",
            )
            self.assertIn(reviewed_head, candidates)

    def test_paginated_lookup_reads_later_pages(self):
        page1 = [{"id": index} for index in range(100)]
        page2 = [{"id": 100}]
        with mock.patch.object(
            mod,
            "_github_json",
            side_effect=[page1, page2],
        ) as request:
            result = mod._github_paginated_array("https://api.github.test/items", "token")
        self.assertEqual(len(result), 101)
        self.assertIn("page=1", request.call_args_list[0].args[0])
        self.assertIn("page=2", request.call_args_list[1].args[0])

if __name__ == "__main__":
    unittest.main()
