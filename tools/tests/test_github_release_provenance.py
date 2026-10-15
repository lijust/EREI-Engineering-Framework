import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import github_release_provenance as mod


class GitHubReleaseProvenanceTests(unittest.TestCase):
    HEAD = "a" * 40
    MERGE = "b" * 40
    TARGET = "c" * 40

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.path = "security/ASSURANCE_ENFORCEMENT.json"
        full = self.root / self.path
        full.parent.mkdir(parents=True)
        full.write_text('{"schema_version":2}\n', encoding="utf-8")
        self.content = full.read_bytes()
        self.policy = {
            "schema_version": 1,
            "repository": "lijust/EREI-Engineering-Framework",
            "release_branch_prefix": "release/",
            "codex_reviewer_login": "chatgpt-codex-connector",
            "architecture_approver_login": "lijust",
            "require_verified_merge_commit": True,
        }

    def tearDown(self):
        self.tmp.cleanup()

    def api(self, path, *, owner_comment=False, blob=None):
        if path == "pulls/55":
            return {
                "head": {"sha": self.HEAD},
                "base": {"ref": "release/vnext-rc3"},
                "merged": True,
                "merge_commit_sha": self.MERGE,
            }
        if path.startswith("contents/"):
            body = self.content if blob is None else blob
            return {
                "type": "file",
                "sha": mod._git_blob_sha(body),
                "content": base64.b64encode(body).decode("ascii"),
            }
        if path == "issues/55/comments?per_page=100":
            if owner_comment:
                return [{
                    "id": 91,
                    "user": {"login": "lijust"},
                    "body": mod.architecture_approval_comment(
                        "EAPP-20261016T010000Z-A1B2C3D4",
                        self.TARGET,
                        self.HEAD,
                    ),
                }]
            state = {
                "code_review": {
                    "commit_sha": None,
                    "has_any_findings": None,
                    "has_unresolved_findings": None,
                    "status": None,
                },
                "security_review": {
                    "commit_sha": self.HEAD,
                    "has_any_findings": False,
                    "has_unresolved_findings": False,
                    "status": "completed",
                },
            }
            return [{
                "id": 90,
                "user": {"login": "chatgpt-codex-connector"},
                "body": f"<!-- codex-review-state:v1 {json.dumps(state)} -->",
            }]
        if path == "pulls/55/reviews?per_page=100":
            return [{
                "id": 77,
                "user": {"login": "chatgpt-codex-connector"},
                "state": "COMMENTED",
                "body": f"Reviewed commit:** `{self.HEAD[:10]}`",
            }]
        if path == f"commits/{self.MERGE}":
            return {"commit": {"verification": {"verified": True}}}
        self.fail(f"unexpected API path: {path}")

    def test_clean_codex_review_authenticates_exact_reviewed_file(self):
        provenance = {
            "kind": "github_codex_clean_security_review",
            "pr_number": 55,
            "actor_login": "chatgpt-codex-connector",
        }
        with mock.patch.object(
            mod,
            "_api_json",
            side_effect=lambda repository, path, token: self.api(path),
        ), mock.patch.object(
            mod.subprocess,
            "run",
            return_value=mock.Mock(returncode=0, stdout="", stderr=""),
        ):
            result = mod.verify_reviewed_file(
                self.root,
                self.path,
                provenance,
                policy=self.policy,
                target_ref=self.TARGET,
                token="token",
                git_repo=self.root,
                closure_ref="HEAD",
            )
        self.assertEqual(result["status"], "authenticated")
        self.assertEqual(result["head_sha"], self.HEAD)
        self.assertEqual(result["merge_commit_sha"], self.MERGE)

    def test_reviewed_blob_must_equal_release_record(self):
        provenance = {
            "kind": "github_codex_clean_security_review",
            "pr_number": 55,
            "actor_login": "chatgpt-codex-connector",
        }
        with mock.patch.object(
            mod,
            "_api_json",
            side_effect=lambda repository, path, token: self.api(path, blob=b"different\n")
            if path.startswith("contents/") else self.api(path),
        ):
            with self.assertRaisesRegex(mod.GitHubProvenanceError, "differs"):
                mod.verify_reviewed_file(
                    self.root,
                    self.path,
                    provenance,
                    policy=self.policy,
                    target_ref=self.TARGET,
                    token="token",
                    git_repo=self.root,
                    closure_ref="HEAD",
                )

    def test_architecture_owner_comment_must_bind_approval_target_and_head(self):
        approval_id = "EAPP-20261016T010000Z-A1B2C3D4"
        provenance = {
            "kind": "github_owner_approval_comment",
            "pr_number": 55,
            "actor_login": "lijust",
        }
        with mock.patch.object(
            mod,
            "_api_json",
            side_effect=lambda repository, path, token: self.api(path, owner_comment=True),
        ), mock.patch.object(
            mod.subprocess,
            "run",
            return_value=mock.Mock(returncode=0, stdout="", stderr=""),
        ):
            result = mod.verify_reviewed_file(
                self.root,
                self.path,
                provenance,
                policy=self.policy,
                target_ref=self.TARGET,
                approval_id=approval_id,
                token="token",
                git_repo=self.root,
                closure_ref="HEAD",
            )
        self.assertEqual(result["comment_id"], 91)

    def test_unsigned_merge_is_rejected(self):
        provenance = {
            "kind": "github_codex_clean_security_review",
            "pr_number": 55,
            "actor_login": "chatgpt-codex-connector",
        }

        def api(repository, path, token):
            if path == f"commits/{self.MERGE}":
                return {"commit": {"verification": {"verified": False}}}
            return self.api(path)

        with mock.patch.object(mod, "_api_json", side_effect=api), mock.patch.object(
            mod.subprocess,
            "run",
            return_value=mock.Mock(returncode=0, stdout="", stderr=""),
        ):
            with self.assertRaisesRegex(mod.GitHubProvenanceError, "not GitHub-verified"):
                mod.verify_reviewed_file(
                    self.root,
                    self.path,
                    provenance,
                    policy=self.policy,
                    target_ref=self.TARGET,
                    token="token",
                )

    def test_reviewed_head_must_descend_from_frozen_target(self):
        provenance = {
            "kind": "github_codex_clean_security_review",
            "pr_number": 55,
            "actor_login": "chatgpt-codex-connector",
        }
        with mock.patch.object(
            mod,
            "_api_json",
            side_effect=lambda repository, path, token: self.api(path),
        ), mock.patch.object(
            mod.subprocess,
            "run",
            return_value=mock.Mock(returncode=1, stdout="", stderr=""),
        ):
            with self.assertRaisesRegex(mod.GitHubProvenanceError, "does not descend"):
                mod.verify_reviewed_file(
                    self.root,
                    self.path,
                    provenance,
                    policy=self.policy,
                    target_ref=self.TARGET,
                    token="token",
                    git_repo=self.root,
                    closure_ref="HEAD",
                )

    def test_reviewed_merge_must_be_in_carrier_history(self):
        provenance = {
            "kind": "github_codex_clean_security_review",
            "pr_number": 55,
            "actor_login": "chatgpt-codex-connector",
        }
        calls = [
            mock.Mock(returncode=0, stdout="", stderr=""),
            mock.Mock(returncode=1, stdout="", stderr=""),
        ]
        with mock.patch.object(
            mod,
            "_api_json",
            side_effect=lambda repository, path, token: self.api(path),
        ), mock.patch.object(mod.subprocess, "run", side_effect=calls):
            with self.assertRaisesRegex(mod.GitHubProvenanceError, "not an ancestor"):
                mod.verify_reviewed_file(
                    self.root,
                    self.path,
                    provenance,
                    policy=self.policy,
                    target_ref=self.TARGET,
                    token="token",
                    git_repo=self.root,
                    closure_ref="HEAD",
                )

    def test_missing_token_fails_closed(self):
        provenance = {
            "kind": "github_codex_clean_security_review",
            "pr_number": 55,
            "actor_login": "chatgpt-codex-connector",
        }
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(mod.GitHubProvenanceError, "requires GH_TOKEN"):
                mod.verify_reviewed_file(
                    self.root,
                    self.path,
                    provenance,
                    policy=self.policy,
                    target_ref=self.TARGET,
                )


if __name__ == "__main__":
    unittest.main()
