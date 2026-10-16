"""Fail-closed candidate consumer release gate, with real OpenSSH signatures."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from tools import independent_consumer_gate as gate


class ConsumerPermitShapeTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 17, 0, 0, tzinfo=timezone.utc)
        self.item = {
            "schema_version": 1, "purpose": gate.PURPOSE,
            "repository": gate.REPOSITORY, "consumer_id": gate.CONSUMER,
            "target_ref": "a" * 40, "carrier_ref": "b" * 40,
            "scope_sha256": "c" * 64,
            "admission_envelope_sha256": "d" * 64,
            "actions_policy_sha256": "e" * 64, "actions_run_id": 123,
            "actions_run_attempt": 1, "nonce": "f" * 64,
            "issued_at": "2026-10-16T23:55:00Z",
            "expires_at": "2026-10-17T00:20:00Z",
        }

    def raw(self):
        return (json.dumps(self.item, sort_keys=True, separators=(",", ":")) + "\n").encode()

    def test_valid_canonical_permit(self):
        self.assertEqual(gate._permit(self.raw(), self.now), self.item)

    def test_noncanonical_rejected(self):
        with self.assertRaisesRegex(gate.ConsumerGateError, "canonical"):
            gate._permit(json.dumps(self.item, indent=2).encode(), self.now)

    def test_non_utf8_rejected(self):
        with self.assertRaises(gate.ConsumerGateError):
            gate._permit(self.raw().decode().encode("utf-16"), self.now)

    def test_unknown_field_rejected(self):
        self.item["consumer_activation_authorized"] = True
        with self.assertRaisesRegex(gate.ConsumerGateError, "field set"):
            gate._permit(self.raw(), self.now)

    def test_bool_run_id_rejected(self):
        self.item["actions_run_id"] = True
        with self.assertRaisesRegex(gate.ConsumerGateError, "positive integer"):
            gate._permit(self.raw(), self.now)

    def test_stale_permit_rejected(self):
        with self.assertRaisesRegex(gate.ConsumerGateError, "not valid"):
            gate._permit(self.raw(), self.now + timedelta(hours=1))

    def test_future_permit_rejected(self):
        with self.assertRaisesRegex(gate.ConsumerGateError, "not valid"):
            gate._permit(self.raw(), self.now - timedelta(hours=1))

    def test_long_lifetime_rejected(self):
        self.item["expires_at"] = "2026-10-17T01:00:00Z"
        with self.assertRaisesRegex(gate.ConsumerGateError, "at most 30"):
            gate._permit(self.raw(), self.now)

    def test_other_consumer_rejected(self):
        self.item["consumer_id"] = "rogue-deployment"
        with self.assertRaisesRegex(gate.ConsumerGateError, "consumer identity"):
            gate._permit(self.raw(), self.now)

    def test_invalid_commit_rejected(self):
        self.item["target_ref"] = "main"
        with self.assertRaisesRegex(gate.ConsumerGateError, "target_ref"):
            gate._permit(self.raw(), self.now)

    def test_naive_clock_rejected(self):
        with self.assertRaisesRegex(gate.ConsumerGateError, "timezone aware"):
            gate._permit(self.raw(), self.now.replace(tzinfo=None))


@unittest.skipUnless(shutil.which("ssh-keygen"), "real OpenSSH required for consumer crypto contract")
class ConsumerGateIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for item in ("repo", "permit", "consumer-trust", "admission-packet", "admission-trust", "keys"):
            (self.root / item).mkdir()
        self.repo = self.root / "repo"
        self.packet = self.root / "permit"
        self.trust = self.root / "consumer-trust"
        self.admission = self.root / "admission-packet"
        self.admission_trust = self.root / "admission-trust"
        self.now = datetime(2026, 10, 17, 0, 0, tzinfo=timezone.utc)
        self.scope_sha = "c" * 64
        self.policy_sha = "e" * 64
        self.target = "a" * 40
        self.carrier = "b" * 40
        self.admission_raw = (
            json.dumps({"scope_sha256": self.scope_sha,
                        "source_assurance": {"run_id": 123, "run_attempt": 1}},
                       sort_keys=True, separators=(",", ":")) + "\n"
        ).encode()
        (self.admission / "admission.json").write_bytes(self.admission_raw)
        self.permit = {
            "schema_version": 1, "purpose": gate.PURPOSE, "repository": gate.REPOSITORY,
            "consumer_id": gate.CONSUMER, "target_ref": self.target, "carrier_ref": self.carrier,
            "scope_sha256": self.scope_sha,
            "admission_envelope_sha256": hashlib.sha256(self.admission_raw).hexdigest(),
            "actions_policy_sha256": self.policy_sha, "actions_run_id": 123,
            "actions_run_attempt": 1, "nonce": "f" * 64,
            "issued_at": "2026-10-16T23:55:00Z",
            "expires_at": "2026-10-17T00:20:00Z",
        }
        self.keys = {}
        for role, principal in (*gate.PRINCIPALS.items(), *gate.carrier.ROLES.items()):
            key = self.root / "keys" / role
            subprocess.run(
                ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "", "-f", str(key)],
                check=True, capture_output=True, timeout=20,
            )
            public = key.with_suffix(".pub").read_text().strip().split()
            folder = self.trust if role in gate.PRINCIPALS else self.admission_trust
            (folder / (role + ".allowed_signers")).write_text(
                principal + " " + public[0] + " " + public[1] + "\n", encoding="ascii"
            )
            self.keys[role] = key
        self._resign()

    def _resign(self):
        permit_path = self.packet / "permit.json"
        permit_path.write_bytes(
            (json.dumps(self.permit, sort_keys=True, separators=(",", ":")) + "\n").encode()
        )
        for role in gate.PRINCIPALS:
            subprocess.run(
                ["ssh-keygen", "-Y", "sign", "-f", str(self.keys[role]),
                 "-n", gate.NAMESPACE, str(permit_path)],
                check=True, capture_output=True, timeout=20,
            )
            produced = Path(str(permit_path) + ".sig")
            (self.packet / (role + ".sig")).write_bytes(produced.read_bytes())
            produced.unlink()

    def _verify(self, *, signed_carrier_override=None, source_override=None, **kw):
        signed_carrier = {
            "status": "verified_offline_signatures_only",
            "target_ref": self.target, "carrier_ref": self.carrier,
            "signed_envelope_sha256": self.permit["admission_envelope_sha256"],
            "verified_roles": list(gate.carrier.ROLES),
            "stable_enforcement_satisfied": False,
        }
        source = {
            "status": "authenticated_actions_source_metadata_only",
            "target_ref": self.target, "run_id": 123, "run_attempt": 1,
            "policy_sha256": self.policy_sha, "required_job": "assurance",
            "stable_enforcement_satisfied": False,
        }
        if signed_carrier_override:
            signed_carrier.update(signed_carrier_override)
        if source_override:
            source.update(source_override)
        params = dict(
            expected_consumer=gate.CONSUMER, expected_target=self.target,
            expected_carrier=self.carrier, expected_actions_policy_sha256=self.policy_sha,
            github_token="mock-read-only-token", at=self.now,
        )
        params.update(kw)
        with mock.patch.object(gate.carrier, "verify_candidate", return_value=signed_carrier) as check_carrier:
            with mock.patch.object(gate.actions, "verify_source", return_value=source) as check_actions:
                result = gate.verify_precheck(
                    self.repo, self.packet, self.trust, self.admission,
                    self.admission_trust, self.root / "actions-policy.json", **params
                )
        return result, check_carrier.call_count, check_actions.call_count

    def test_real_distinct_signatures_accepted_as_precheck_only(self):
        result, a, b = self._verify()
        self.assertEqual(result["status"], "consumer_admission_precheck_only")
        self.assertIs(result["consumer_activation_authorized"], False)
        self.assertIs(result["stable_enforcement_satisfied"], False)
        self.assertIs(result["independent_runtime_enforcement_attested"], False)
        self.assertIs(result["replay_protection_attested"], False)
        self.assertEqual((a, b), (1, 1))

    def test_missing_signature_denied(self):
        (self.packet / "consumer-security.sig").unlink()
        with self.assertRaises(gate.ConsumerGateError):
            self._verify()

    def test_mutated_permit_after_signing_denied(self):
        self.permit["nonce"] = "0" * 64
        (self.packet / "permit.json").write_bytes(
            (json.dumps(self.permit, sort_keys=True, separators=(",", ":")) + "\n").encode()
        )
        with self.assertRaisesRegex(gate.ConsumerGateError, "invalid consumer signature"):
            self._verify()

    def test_incorrect_signature_namespace_denied(self):
        p = self.packet / "permit.json"
        subprocess.run(["ssh-keygen", "-Y", "sign", "-f",
                        str(self.keys["consumer-security"]), "-n", "other-namespace", str(p)],
                       check=True, capture_output=True, timeout=20)
        (self.packet / "consumer-security.sig").write_bytes(Path(str(p) + ".sig").read_bytes())
        with self.assertRaisesRegex(gate.ConsumerGateError, "invalid consumer signature"):
            self._verify()

    def test_reused_role_key_denied_even_if_other_signatures_are_valid(self):
        key = (self.trust / "consumer-architecture.allowed_signers").read_text().split()
        (self.trust / "consumer-security.allowed_signers").write_text(
            gate.PRINCIPALS["consumer-security"] + " " + " ".join(key[1:]) + "\n"
        )
        with self.assertRaisesRegex(gate.ConsumerGateError, "four distinct"):
            self._verify()

    def test_scope_tamper_denied(self):
        self.permit["scope_sha256"] = "0" * 64
        self._resign()
        with self.assertRaisesRegex(gate.ConsumerGateError, "scope or run"):
            self._verify()

    def test_wrong_expected_target_denied(self):
        with self.assertRaisesRegex(gate.ConsumerGateError, "expected exact commits"):
            self._verify(expected_target="0" * 40)

    def test_wrong_external_policy_pin_denied(self):
        with self.assertRaisesRegex(gate.ConsumerGateError, "Actions policy"):
            self._verify(expected_actions_policy_sha256="1" * 64)

    def test_missing_read_only_token_denied(self):
        with self.assertRaisesRegex(gate.ConsumerGateError, "credential"):
            self._verify(github_token="")

    def test_fake_upstream_green_status_denied(self):
        with self.assertRaisesRegex(gate.ConsumerGateError, "contract mismatch"):
            self._verify(source_override={"status": "unverified_green_report"})

    def test_cannot_upcast_component_to_stable_enforcement(self):
        with self.assertRaisesRegex(gate.ConsumerGateError, "contract mismatch"):
            self._verify(signed_carrier_override={"stable_enforcement_satisfied": True})

    def test_untrusted_repo_packet_location_denied(self):
        (self.repo / "permit").mkdir()
        with self.assertRaisesRegex(gate.ConsumerGateError, "outside"):
            self._verify_unused_repo_packet()

    def _verify_unused_repo_packet(self):
        return gate.verify_precheck(
            self.repo, self.repo / "permit", self.trust,
            self.admission, self.admission_trust, self.root / "policy.json",
            expected_consumer=gate.CONSUMER, expected_target=self.target,
            expected_carrier=self.carrier, expected_actions_policy_sha256=self.policy_sha,
            github_token="mock-token", at=self.now,
        )


if __name__ == "__main__":
    unittest.main()
