"""Candidate-only authenticated GitHub Actions provenance with external pinned policy."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import independent_actions_source as src


class IndependentActionsSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.policies = self.base / "trusted-off-github"
        self.policies.mkdir()
        self.file = self.policies / "assurance-policy.json"
        self.target = "a" * 40
        self.run_id = 34567
        self.attempt = 2
        self.workflow_bytes = b"name: Framework Assurance Gate\non:\n  push:\n"
        self.policy = {
            "schema_version": 1,
            "repository": src.REPOSITORY,
            "workflow_path": src.WORKFLOW_PATH,
            "workflow_sha256": hashlib.sha256(self.workflow_bytes).hexdigest(),
            "workflow_id": 12345678,
            "required_job": "assurance",
            "head_branch": "main",
        }
        self._save_policy()
        self.run = {
            "id": self.run_id,
            "run_attempt": self.attempt,
            "workflow_id": self.policy["workflow_id"],
            "name": src.RUN_NAME,
            "path": src.WORKFLOW_PATH,
            "event": "push",
            "head_branch": "main",
            "head_sha": self.target,
            "status": "completed",
            "conclusion": "success",
            "repository": {"full_name": src.REPOSITORY},
            "head_repository": {"full_name": src.REPOSITORY},
        }
        self.jobs = {"total_count": 1, "jobs": [{
            "name": "assurance",
            "run_id": self.run_id,
            "run_attempt": self.attempt,
            "head_sha": self.target,
            "status": "completed",
            "conclusion": "success",
        }]}

    def tearDown(self):
        self.tmp.cleanup()

    def _save_policy(self):
        raw = (json.dumps(self.policy, sort_keys=True, separators=(",", ":")) + "\n").encode()
        self.file.write_bytes(raw)
        self.pin = hashlib.sha256(raw).hexdigest()

    def _verify(self, *, pin=None, source=None, run=None, jobs=None, policy_path=None, token="read-only-token"):
        # No real GitHub API or Git operations occur in this isolated test.
        def response(url, credential):
            self.assertEqual(credential, token)
            self.assertTrue(url.startswith(src.API_ROOT + "/"))
            if url.endswith(f"/actions/runs/{self.run_id}"):
                return self.run if run is None else run
            if url.endswith(f"/actions/runs/{self.run_id}/attempts/{self.attempt}/jobs?per_page=100"):
                return self.jobs if jobs is None else jobs
            self.fail(f"unexpected API endpoint: {url}")
        with mock.patch.object(src, "_git_blob", return_value=self.workflow_bytes if source is None else source) as git, \
             mock.patch.object(src, "_request_json", side_effect=response) as api:
            result = src.verify_source(
                self.repo, self.file if policy_path is None else policy_path,
                self.pin if pin is None else pin,
                target_ref=self.target, run_id=self.run_id, run_attempt=self.attempt,
                token=token,
            )
        self.assertEqual(git.call_args.args[1:], (self.target, src.WORKFLOW_PATH))
        self.assertEqual(api.call_count, 2)
        return result

    def test_authenticated_metadata_only_cannot_enable_stable(self):
        out = self._verify()
        self.assertEqual(out["status"], "authenticated_actions_source_metadata_only")
        self.assertFalse(out["stable_enforcement_satisfied"])
        self.assertFalse(out["trusted_externally_enforced_consumption"])
        self.assertFalse(out["self_hosted_runner_execution_attested"])

    def test_external_policy_pin_changed_fails(self):
        self.policy["workflow_id"] = 99999
        self._save_policy()
        with self.assertRaisesRegex(src.ActionsSourceError, "externally pinned hash"):
            self._verify(pin="0" * 64)

    def test_policy_must_be_outside_repository(self):
        inner = self.repo / "policy.json"
        inner.write_bytes(self.file.read_bytes())
        with self.assertRaisesRegex(src.ActionsSourceError, "outside mutable Git checkout"):
            self._verify(policy_path=inner)

    def test_external_policy_symlink_is_rejected(self):
        alias = self.policies / "linked-policy.json"
        try:
            alias.symlink_to(self.file)
        except (OSError, NotImplementedError):
            self.skipTest("symbolic link creation unavailable for test user")
        with self.assertRaisesRegex(src.ActionsSourceError, "symlink or indirect path"):
            self._verify(policy_path=alias)

    def test_external_policy_parent_traversal_is_rejected(self):
        weird = self.policies / "subdir" / ".." / self.file.name
        with self.assertRaisesRegex(src.ActionsSourceError, "parent traversal"):
            self._verify(policy_path=weird)

    def test_source_workflow_changed_fails_even_with_successful_run(self):
        with self.assertRaisesRegex(src.ActionsSourceError, "workflow source not externally pinned"):
            self._verify(source=b"altered workflow\n")

    def test_github_run_on_different_commit_rejected(self):
        changed = {**self.run, "head_sha": "b" * 40}
        with self.assertRaisesRegex(src.ActionsSourceError, "run metadata"):
            self._verify(run=changed)

    def test_github_documented_main_qualified_workflow_path_is_valid(self):
        authenticated = {**self.run, "path": src.WORKFLOW_PATH + "@main"}
        result = self._verify(run=authenticated)
        self.assertEqual(result["status"], "authenticated_actions_source_metadata_only")

    def test_wrong_qualified_workflow_ref_is_rejected(self):
        for untrusted_path in (
            src.WORKFLOW_PATH + "@feature",
            src.WORKFLOW_PATH + "@refs/pull/1/merge",
            src.WORKFLOW_PATH + "@main/unsafe",
        ):
            with self.subTest(path=untrusted_path):
                with self.assertRaisesRegex(src.ActionsSourceError, "run metadata"):
                    self._verify(run={**self.run, "path": untrusted_path})

    def test_github_nested_repository_objects_must_be_objects(self):
        # Valid JSON can still be adversarially typed: strings/lists/truthy
        # scalars must fail with ActionsSourceError, not AttributeError.
        for key in ("repository", "head_repository"):
            for malformed in ("rogue", ["repo"], True, None, 12, {}):
                with self.subTest(key=key, malformed=malformed):
                    run = {**self.run, key: malformed}
                    with self.assertRaises(src.ActionsSourceError):
                        self._verify(run=run)

    def test_github_workflow_path_wrong_json_types_denied(self):
        for malformed in ([".github/workflows/assurance-gate.yml"], {"path": src.WORKFLOW_PATH}, True, 23, None):
            with self.subTest(path=malformed):
                with self.assertRaises(src.ActionsSourceError):
                    self._verify(run={**self.run, "path": malformed})

    def test_github_run_wrong_workflow_id_rejected(self):
        with self.assertRaisesRegex(src.ActionsSourceError, "run metadata"):
            self._verify(run={**self.run, "workflow_id": 999})

    def test_github_run_wrong_attempt_rejected(self):
        with self.assertRaisesRegex(src.ActionsSourceError, "run metadata"):
            self._verify(run={**self.run, "run_attempt": 1})

    def test_github_run_for_pull_request_rejected(self):
        with self.assertRaisesRegex(src.ActionsSourceError, "run metadata"):
            self._verify(run={**self.run, "event": "pull_request"})

    def test_github_run_for_different_branch_rejected(self):
        with self.assertRaisesRegex(src.ActionsSourceError, "run metadata"):
            self._verify(run={**self.run, "head_branch": "malicious"})

    def test_missing_or_failed_job_rejected(self):
        for jobs in (
            {"total_count": 0, "jobs": []},
            {"total_count": 1, "jobs": [{**self.jobs["jobs"][0], "conclusion": "failure"}]},
            {"total_count": 2, "jobs": self.jobs["jobs"]},
        ):
            with self.subTest(jobs=jobs):
                with self.assertRaises(src.ActionsSourceError):
                    self._verify(jobs=jobs)

    def test_github_documented_attempt_job_without_run_attempt_field_passes(self):
        official_jobs = {"total_count": 1, "jobs": [{
            key: value for key, value in self.jobs["jobs"][0].items()
            if key != "run_attempt"
        }]}
        result = self._verify(jobs=official_jobs)
        self.assertEqual(result["status"], "authenticated_actions_source_metadata_only")

    def test_wrong_attempt_job_rejected(self):
        jobs = {"total_count": 1, "jobs": [
            {**self.jobs["jobs"][0], "run_attempt": 1},
        ]}
        with self.assertRaisesRegex(src.ActionsSourceError, "exact-attempt"):
            self._verify(jobs=jobs)

    def test_malformed_policy_rejected_even_when_matching_pin(self):
        self.policy["required_job"] = "not-assurance"
        self._save_policy()
        with self.assertRaisesRegex(src.ActionsSourceError, "trusted workflow/job/branch"):
            self._verify()

    def test_missing_read_only_token_rejected_in_http_boundary(self):
        with self.assertRaisesRegex(src.ActionsSourceError, "token is required"):
            src._request_json(f"{src.API_ROOT}/actions/runs/1", "")

    def test_github_api_host_is_pinned(self):
        with self.assertRaisesRegex(src.ActionsSourceError, "outside official repository"):
            src._request_json("https://attacker.invalid/secret", "token")

    def test_git_source_reader_disables_partial_clone_fetch_and_external_transports(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            def git(*args):
                r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)
                return r.stdout.strip()
            git("init", "-q")
            git("config", "user.name", "Source Test")
            git("config", "user.email", "source-test@erei.invalid")
            file = root / src.WORKFLOW_PATH
            file.parent.mkdir(parents=True)
            file.write_bytes(self.workflow_bytes)
            git("add", "-A")
            git("commit", "-q", "-m", "exact source")
            target = git("rev-parse", "HEAD")
            original_run = subprocess.run
            with mock.patch.object(src.subprocess, "run", wraps=original_run) as trace:
                data = src._git_blob(root, target, src.WORKFLOW_PATH)
            self.assertEqual(data, self.workflow_bytes)
            seen = [
                item for item in trace.call_args_list
                if item.args and item.args[0][0] == "git"
            ]
            self.assertGreaterEqual(len(seen), 3)
            for call in seen:
                args = call.args[0]
                self.assertIn("core.commitGraph=false", args)
                self.assertIn("protocol.allow=never", args)
                self.assertIn("protocol.ext.allow=never", args)
                self.assertEqual(call.kwargs["env"]["GIT_NO_LAZY_FETCH"], "1")
                self.assertEqual(call.kwargs["env"]["GIT_ALLOW_PROTOCOL"], "")

    def test_boolean_run_id_is_not_a_valid_number(self):
        with self.assertRaisesRegex(src.ActionsSourceError, "positive integers"):
            src.verify_source(
                self.repo, self.file, self.pin, target_ref=self.target,
                run_id=True, run_attempt=1, token="read-only-token",
            )


if __name__ == "__main__":
    unittest.main()
