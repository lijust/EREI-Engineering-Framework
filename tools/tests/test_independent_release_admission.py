"""Adversarial tests for source-only, non-authoritative external release admission."""
import json
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tools import independent_release_admission as admission


class AdmissionShapeTests(unittest.TestCase):
    def test_rejects_bool_instead_of_positive_run_id(self):
        now = datetime(2026, 10, 16, 18, tzinfo=timezone.utc)
        item = {
            "schema_version": 1, "purpose": admission.PURPOSE,
            "repository": admission.REPOSITORY, "target_id": "vnext-rc4",
            "target_ref": "a"*40, "target_tree": "b"*40,
            "carrier_ref": "c"*40, "carrier_tree": "d"*40,
            "scope_sha256": "e"*64,
            "source_assurance": {
                "workflow": "Framework Assurance Gate", "run_id": True,
                "run_attempt": 1, "event": "push", "conclusion": "success",
            },
            "issued_at": "2026-10-16T18:00:00Z",
            "expires_at": "2026-10-17T18:00:00Z",
        }
        raw = (json.dumps(item, separators=(",", ":"), sort_keys=True) + "\n").encode()
        with self.assertRaisesRegex(admission.AdmissionError, "run_id"):
            admission._envelope(raw, now)

    def test_rejects_noncanonical_envelope(self):
        now = datetime(2026, 10, 16, 18, tzinfo=timezone.utc)
        with self.assertRaises(admission.AdmissionError):
            admission._envelope(b'{"schema_version": 1}\n', now)

    def test_never_sets_stable_enforcement_from_offline_signatures(self):
        self.assertEqual(admission.PURPOSE, "erei-framework-v2-trusted-carrier-admission")
        self.assertEqual(len(admission.ROLES), 2)


@unittest.skipUnless(shutil.which("ssh-keygen") and shutil.which("git"), "OpenSSH git integration test requires ssh-keygen and git")
class AdmissionIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.packet = self.root / "packet"
        self.packet.mkdir()
        self.trust = self.root / "trust"
        self.trust.mkdir()
        self.keys = self.root / "keys"
        self.keys.mkdir()
        self._git("init", "-q")
        self._git("config", "user.name", "EREI Offline Admission Test")
        self._git("config", "user.email", "test@erei.invalid")
        self._write("releases/VNEXT_RELEASE_SCOPE.json", '{"scope_id":"test-release-scope"}\n')
        self._write("README.md", "source tested independently\n")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "source candidate")
        self.target = self._git("rev-parse", "HEAD").strip()
        self.target_tree = self._git("rev-parse", f"{self.target}^{{tree}}").strip()
        self.assurance = {
            "workflow": "Framework Assurance Gate",
            "run_id": 123456, "run_attempt": 1,
            "event": "push", "conclusion": "success",
        }
        frozen = {
            "schema_version": 1, "target_id": "vnext-rc4",
            "status": "frozen_candidate", "framework_ref": self.target,
            "target_tree": self.target_tree, "selected_at": "2026-10-16T17:00:00Z",
            "source_branch": "main", "assurance": {
                k: self.assurance[k] for k in ("workflow", "run_id", "event", "conclusion")
            },
            "stable_baseline": {
                "baseline": "task-learning-review-v1",
                "framework_ref": "69079018606750312344cb3c648952b9ab72d35b",
            },
            "promotion_authorized": False,
        }
        self._write("releases/VNEXT_TARGET.json", json.dumps(frozen, sort_keys=True) + "\n")
        self._git("add", "releases/VNEXT_TARGET.json")
        self._git("commit", "-q", "-m", "freeze RC4")
        self.carrier = self._git("rev-parse", "HEAD").strip()
        self.carrier_tree = self._git("rev-parse", f"{self.carrier}^{{tree}}").strip()
        import hashlib
        scope_hash = hashlib.sha256((self.repo / "releases/VNEXT_RELEASE_SCOPE.json").read_bytes()).hexdigest()
        self.now = datetime(2026, 10, 16, 18, tzinfo=timezone.utc)
        self.data = {
            "schema_version": 1, "purpose": admission.PURPOSE,
            "repository": admission.REPOSITORY,
            "target_id": "vnext-rc4", "target_ref": self.target,
            "target_tree": self.target_tree, "carrier_ref": self.carrier,
            "carrier_tree": self.carrier_tree, "scope_sha256": scope_hash,
            "source_assurance": self.assurance,
            "issued_at": "2026-10-16T17:00:00Z",
            "expires_at": "2026-10-17T17:00:00Z",
        }
        for role, principal in admission.ROLES.items():
            priv = self.keys / role
            subprocess.run(
                ["ssh-keygen", "-q", "-t", "ed25519", "-f", str(priv), "-N", "", "-C", ""],
                check=True, capture_output=True,
            )
            parts = (self.keys / f"{role}.pub").read_text(encoding="ascii").split()
            (self.trust / f"{role}.allowed_signers").write_text(
                f"{principal} {parts[0]} {parts[1]}\n", encoding="ascii"
            )
        self._save_packet()

    def tearDown(self):
        self.tmp.cleanup()

    def _git(self, *args):
        res = subprocess.run(["git", "-C", str(self.repo), *args], capture_output=True, text=True)
        if res.returncode:
            self.fail(f"git failure: {args}: {res.stderr}")
        return res.stdout.strip()

    def _write(self, rel, text):
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def _save_packet(self):
        envelope = self.packet / "admission.json"
        envelope.write_bytes((json.dumps(
            self.data, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ) + "\n").encode("utf-8"))
        for role in admission.ROLES:
            generated = envelope.with_name("admission.json.sig")
            if generated.exists():
                generated.unlink()
            subprocess.run(
                ["ssh-keygen", "-Y", "sign", "-f", str(self.keys / role),
                 "-n", admission.NAMESPACE, str(envelope)],
                check=True, capture_output=True,
            )
            generated.replace(self.packet / f"{role}.sig")

    def _verify(self, **overrides):
        kw = {
            "expected_target": self.target,
            "expected_carrier": self.carrier, "at": self.now,
        }
        kw.update(overrides)
        return admission.verify_candidate(self.repo, self.packet, self.trust, **kw)

    def test_valid_two_independent_signatures_are_candidate_only(self):
        out = self._verify()
        self.assertEqual(out["status"], "verified_offline_signatures_only")
        self.assertEqual(out["verified_roles"], list(admission.ROLES))
        self.assertFalse(out["stable_enforcement_satisfied"])
        self.assertFalse(out["live_actions_run_authenticated"])
        self.assertFalse(out["trusted_verifier_host_attested"])

    def test_mutated_canonical_packet_fails_signature(self):
        self.data["source_assurance"]["run_attempt"] = 2
        (self.packet / "admission.json").write_bytes((
            json.dumps(self.data, separators=(",", ":"), sort_keys=True) + "\n"
        ).encode())
        with self.assertRaisesRegex(admission.AdmissionError, "signature invalid"):
            self._verify()

    def test_missing_second_signature_fails(self):
        (self.packet / "independent-security.sig").unlink()
        with self.assertRaises(admission.AdmissionError):
            self._verify()

    def test_shared_signing_key_is_rejected_even_with_valid_first_signature(self):
        (self.trust / "independent-security.allowed_signers").write_text(
            (self.trust / "release-owner.allowed_signers").read_text().replace(
                "release-owner@erei.invalid", "independent-security@erei.invalid"
            )
        )
        with self.assertRaisesRegex(admission.AdmissionError, "cannot share one key"):
            self._verify()

    def test_swapped_role_signatures_fail(self):
        a = (self.packet / "release-owner.sig").read_bytes()
        b = (self.packet / "independent-security.sig").read_bytes()
        (self.packet / "release-owner.sig").write_bytes(b)
        (self.packet / "independent-security.sig").write_bytes(a)
        with self.assertRaisesRegex(admission.AdmissionError, "signature invalid"):
            self._verify()

    def test_replayed_packet_to_different_carrier_fails(self):
        with self.assertRaisesRegex(admission.AdmissionError, "expected exact target/carrier"):
            self._verify(expected_carrier="f" * 40)

    def test_expired_packet_fails(self):
        with self.assertRaisesRegex(admission.AdmissionError, "not currently valid"):
            self._verify(at=self.now + timedelta(days=2))

    def test_packet_inside_mutable_repository_is_rejected(self):
        import shutil as _shutil
        in_repo = self.repo / "packet"
        _shutil.copytree(self.packet, in_repo)
        with self.assertRaisesRegex(admission.AdmissionError, "outside the Git worktree"):
            admission.verify_candidate(
                self.repo, in_repo, self.trust,
                expected_target=self.target, expected_carrier=self.carrier, at=self.now
            )

    def test_trust_anchor_inside_mutable_repository_is_rejected(self):
        import shutil as _shutil
        in_repo = self.repo / "trust"
        _shutil.copytree(self.trust, in_repo)
        with self.assertRaisesRegex(admission.AdmissionError, "outside the Git worktree"):
            admission.verify_candidate(
                self.repo, self.packet, in_repo,
                expected_target=self.target, expected_carrier=self.carrier, at=self.now
            )

    def test_wrong_git_target_scope_digest_is_rejected(self):
        self.data["scope_sha256"] = "0" * 64
        self._save_packet()
        with self.assertRaisesRegex(admission.AdmissionError, "scope hash differs"):
            self._verify()

    def test_all_git_provenance_reads_disable_untrusted_commit_graph(self):
        from unittest import mock
        original_run = subprocess.run
        with mock.patch.object(admission.subprocess, "run", wraps=original_run) as calls:
            out = self._verify()
        self.assertEqual(out["status"], "verified_offline_signatures_only")
        git_reads = [
            call.args[0] for call in calls.call_args_list
            if call.args and call.args[0][0] == "git"
        ]
        self.assertGreaterEqual(len(git_reads), 8)
        for args in git_reads:
            self.assertEqual(args[3:5], ["-c", "core.commitGraph=false"])
            self.assertIn("protocol.allow=never", args)
            self.assertIn("protocol.ext.allow=never", args)
        for call in calls.call_args_list:
            if call.args and call.args[0][0] == "git":
                self.assertEqual(call.kwargs["env"]["GIT_NO_LAZY_FETCH"], "1")
                self.assertEqual(call.kwargs["env"]["GIT_ALLOW_PROTOCOL"], "")
                self.assertEqual(call.kwargs["env"]["GIT_PROTOCOL_FROM_USER"], "0")


    def test_corrupted_commit_graph_does_not_change_raw_commit_verification(self):
        self._git("commit-graph", "write", "--reachable")
        graph = self.repo / ".git" / "objects" / "info" / "commit-graph"
        if not graph.exists():
            self.skipTest("Git build did not produce a commit-graph")
        payload = bytearray(graph.read_bytes())
        # Git writes commit-graph files read-only on Linux. Deliberately mutate
        # this test fixture after making it writable; production remains untouched.
        graph.chmod(0o600)
        payload[len(payload) // 2] ^= 0x01
        graph.write_bytes(bytes(payload))
        self.assertEqual(self._verify()["status"], "verified_offline_signatures_only")

    def test_git_replace_object_cannot_rewrite_signed_carrier_history(self):
        self._git("replace", "--graft", self.carrier)
        with self.assertRaisesRegex(admission.AdmissionError, "replace refs"):
            self._verify()

    def test_legacy_git_graft_cannot_rewrite_signed_carrier_history(self):
        graft = self.repo / ".git" / "info" / "grafts"
        graft.parent.mkdir(parents=True, exist_ok=True)
        graft.write_text(f"{self.carrier} {self.target}\\n", encoding="utf-8")
        with self.assertRaisesRegex(admission.AdmissionError, "graft records"):
            self._verify()

    def test_untrusted_git_environment_variables_are_ignored(self):
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {
            "GIT_NO_REPLACE_OBJECTS": "0",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.useReplaceRefs",
            "GIT_CONFIG_VALUE_0": "true",
        }):
            result = self._verify()
        self.assertFalse(result["stable_enforcement_satisfied"])

    def test_corrupt_loose_blob_under_signed_oid_is_rejected(self):
        import zlib
        blob_sha = self._git("rev-parse", f"{self.target}:README.md")
        loose = self.repo / ".git" / "objects" / blob_sha[:2] / blob_sha[2:]
        if not loose.is_file():
            self.skipTest("fixture has no loose README blob")
        forged = b"forged README bytes under a trusted Git blob id\\n"
        loose.chmod(0o600)
        loose.write_bytes(zlib.compress(b"blob " + str(len(forged)).encode() + bytes([0]) + forged))
        with self.assertRaises(admission.AdmissionError):
            self._verify()

    def test_symlink_mode_manifest_is_rejected_even_when_contents_are_json(self):
        old_blob = self._git("rev-parse", f"{self.carrier}:releases/VNEXT_TARGET.json")
        self._git("reset", "--hard", self.target)
        self._git("update-index", "--add", "--cacheinfo",
                  f"120000,{old_blob},releases/VNEXT_TARGET.json")
        self._git("commit", "-q", "-m", "unsafe signed carrier manifest as symlink")
        self.carrier = self._git("rev-parse", "HEAD")
        self.carrier_tree = self._git("rev-parse", f"{self.carrier}^{{tree}}")
        self.data["carrier_ref"] = self.carrier
        self.data["carrier_tree"] = self.carrier_tree
        self._save_packet()
        with self.assertRaisesRegex(admission.AdmissionError, "ordinary non-executable blob"):
            self._verify()

    def test_canonical_frozen_manifest_shape_rejects_mutated_fields(self):
        original = json.loads(self._git("show", f"{self.carrier}:releases/VNEXT_TARGET.json"))
        bad = [
            ("unsupported version", lambda x: x.update(schema_version=999)),
            ("missing selected_at", lambda x: x.pop("selected_at")),
            ("malformed selected_at", lambda x: x.update(selected_at="not a timestamp")),
            ("missing stable_baseline", lambda x: x.pop("stable_baseline")),
            ("invalid stable ref", lambda x: x["stable_baseline"].update(framework_ref="not-a-sha")),
            ("unknown extra field", lambda x: x.update(unexpected_source="trusted")),
            ("extra baseline field", lambda x: x["stable_baseline"].update(unknown=True)),
            ("invalid run number", lambda x: x["assurance"].update(run_id=True)),
        ]
        for title, mutate in bad:
            with self.subTest(case=title):
                self._git("reset", "--hard", self.target)
                altered = json.loads(json.dumps(original))
                mutate(altered)
                self._write("releases/VNEXT_TARGET.json", json.dumps(altered, sort_keys=True) + "\n")
                self._git("add", "releases/VNEXT_TARGET.json")
                self._git("commit", "-q", "-m", "candidate altered complete target schema")
                self.carrier = self._git("rev-parse", "HEAD")
                self.carrier_tree = self._git("rev-parse", f"{self.carrier}^{{tree}}")
                self.data["carrier_ref"] = self.carrier
                self.data["carrier_tree"] = self.carrier_tree
                self._save_packet()
                with self.assertRaisesRegex(admission.AdmissionError, "authoritative schema"):
                    self._verify()

    def test_carrier_with_extra_file_is_rejected(self):
        self._write("unexpected.txt", "extra mutation\n")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "untrusted extra")
        extra = self._git("rev-parse", "HEAD")
        extra_tree = self._git("rev-parse", f"{extra}^{{tree}}")
        self.data["carrier_ref"] = extra
        self.data["carrier_tree"] = extra_tree
        self._save_packet()
        with self.assertRaisesRegex(admission.AdmissionError, "one direct single-parent"):
            self._verify(expected_carrier=extra)


if __name__ == "__main__":
    unittest.main()
