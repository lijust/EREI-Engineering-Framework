#!/usr/bin/env python3
"""Source-only, fail-closed consumer-side admission PRECHECK (not deployment authority).

This precheck combines independent, externally pinned carrier and Actions evidence
with an independently double-signed, consumer-bound permit. A successful return
NEVER activates a consumer or proves effective enforcement. The actual consumer
must refuse ALL activation paths unless a separately controlled operator installs
and authenticates an exclusive gate, replay store, and independently pinned code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from . import independent_release_admission as carrier
    from . import independent_actions_source as actions
except ImportError:
    import independent_release_admission as carrier
    import independent_actions_source as actions

REPOSITORY = "lijust/EREI-Engineering-Framework"
PURPOSE = "erei-framework-v2-consumer-admission-precheck"
NAMESPACE = "erei-consumer-admission@erei.invalid"
CONSUMER = "erei-app-google"
PRINCIPALS = {
    "consumer-architecture": "consumer-architecture@erei.invalid",
    "consumer-security": "consumer-security@erei.invalid",
}
FIELDS = {
    "schema_version", "purpose", "repository", "consumer_id", "target_ref",
    "carrier_ref", "scope_sha256", "admission_envelope_sha256",
    "actions_policy_sha256", "actions_run_id", "actions_run_attempt",
    "nonce", "issued_at", "expires_at",
}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
MAX_PERMIT_BYTES = 16 * 1024


class ConsumerGateError(RuntimeError):
    pass


def _hex(value: Any, pattern: re.Pattern[str], name: str) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise ConsumerGateError(name + " must have exact lowercase digest syntax")
    return value


def _permit(raw: bytes, now: datetime) -> dict[str, Any]:
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_PERMIT_BYTES:
        raise ConsumerGateError("permit bytes missing or oversized")
    try:
        item = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ConsumerGateError("permit is not UTF-8 JSON") from exc
    if not isinstance(item, dict) or set(item) != FIELDS:
        raise ConsumerGateError("permit field set differs from governed contract")
    canonical = (json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if raw != canonical:
        raise ConsumerGateError("permit must be canonical UTF-8 JSON bytes")
    if type(item["schema_version"]) is not int or item["schema_version"] != 1:
        raise ConsumerGateError("unsupported permit version")
    if item["purpose"] != PURPOSE or item["repository"] != REPOSITORY:
        raise ConsumerGateError("incorrect consumer permit purpose or repository")
    if item["consumer_id"] != CONSUMER:
        raise ConsumerGateError("consumer identity mismatch")
    for key in ("target_ref", "carrier_ref"):
        _hex(item[key], SHA40, key)
    for key in ("scope_sha256", "admission_envelope_sha256", "actions_policy_sha256", "nonce"):
        _hex(item[key], SHA256, key)
    if item["target_ref"] == item["carrier_ref"]:
        raise ConsumerGateError("target and carrier must differ")
    for key in ("actions_run_id", "actions_run_attempt"):
        if type(item[key]) is not int or item[key] <= 0:
            raise ConsumerGateError(key + " must be positive integer")
    try:
        issued = carrier._timestamp(item["issued_at"], "issued_at")
        expires = carrier._timestamp(item["expires_at"], "expires_at")
    except carrier.AdmissionError as exc:
        raise ConsumerGateError(str(exc)) from exc
    if expires <= issued or expires - issued > timedelta(minutes=30):
        raise ConsumerGateError("permit lifetime must be at most 30 minutes")
    if now.tzinfo is None:
        raise ConsumerGateError("verification clock must be timezone aware")
    when = now.astimezone(timezone.utc)
    if when < issued - timedelta(minutes=5) or when >= expires:
        raise ConsumerGateError("permit is not valid at verification time")
    return item


def verify_precheck(
    repo_root: Path,
    permit_dir: Path,
    consumer_trust_dir: Path,
    admission_packet_dir: Path,
    admission_trust_dir: Path,
    actions_policy_file: Path,
    *,
    expected_consumer: str,
    expected_target: str,
    expected_carrier: str,
    expected_actions_policy_sha256: str,
    github_token: str,
    at: datetime | None = None,
) -> dict[str, Any]:
    """Never authorizes consumption: positive result means precheck only."""
    if expected_consumer != CONSUMER:
        raise ConsumerGateError("consumer identity not independently recognized")
    target = _hex(expected_target, SHA40, "expected_target")
    evidence_carrier = _hex(expected_carrier, SHA40, "expected_carrier")
    policy_sha = _hex(expected_actions_policy_sha256, SHA256, "expected_actions_policy_sha256")
    if not isinstance(github_token, str) or not github_token.strip():
        raise ConsumerGateError("independent GitHub read credential required")
    root = Path(repo_root).resolve(strict=True)
    try:
        packet = carrier._external_folder(root, Path(permit_dir), "permit_dir")
        trust = carrier._external_folder(root, Path(consumer_trust_dir), "consumer_trust_dir")
        admitted_packet = carrier._external_folder(root, Path(admission_packet_dir), "admission_packet_dir")
        admitted_trust = carrier._external_folder(root, Path(admission_trust_dir), "admission_trust_dir")
    except carrier.AdmissionError as exc:
        raise ConsumerGateError(str(exc)) from exc
    folders = (packet, trust, admitted_packet, admitted_trust)
    if any(a == b or a in b.parents or b in a.parents for i, a in enumerate(folders) for b in folders[i + 1:]):
        raise ConsumerGateError("packet and trust folders must be disjoint independent paths")
    # Snapshot ALL submitted packets, signing policy and four trust anchors
    # into an owner-only directory before validating or passing paths to
    # ssh-keygen and the upstream verifiers. Reopening caller-controlled
    # mutable trust paths after checking key distinctness is a TOCTOU bypass.
    try:
        actions._policy(root, Path(actions_policy_file), policy_sha)
    except (actions.ActionsSourceError, OSError) as exc:
        raise ConsumerGateError("independent Actions policy path/pin invalid") from exc
    with tempfile.TemporaryDirectory(prefix="erei-consumer-verified-") as temp:
        snapshot = Path(temp).resolve(strict=True)
        if snapshot == root or root in snapshot.parents:
            raise ConsumerGateError("private trust snapshot directory is inside release checkout")
        # POSIX owner-only mode is testable here. Windows ACL independence
        # requires separately audited trusted-host configuration; do not
        # pretend that Windows st_mode is a portable ACL attestation.
        if os.name != "nt" and snapshot.stat().st_mode & 0o077:
            raise ConsumerGateError("private trust snapshot directory is not owner-only")
        names = ("permit", "consumer-trust", "admission-packet", "admission-trust")
        locations = tuple(snapshot / name for name in names)
        for folder in locations:
            folder.mkdir(mode=0o700)
        snapshot_packet, snapshot_trust, snapshot_admission, snapshot_admission_trust = locations
        for source, destination, filenames in (
            (packet, snapshot_packet, ("permit.json", *(role + ".sig" for role in PRINCIPALS))),
            (trust, snapshot_trust, tuple(role + ".allowed_signers" for role in PRINCIPALS)),
            (admitted_packet, snapshot_admission, ("admission.json", *(role + ".sig" for role in carrier.ROLES))),
            (admitted_trust, snapshot_admission_trust, tuple(role + ".allowed_signers" for role in carrier.ROLES)),
        ):
            for name in filenames:
                try:
                    raw = carrier._single_file(source / name)
                except carrier.AdmissionError as exc:
                    raise ConsumerGateError("unavailable independent evidence snapshot: " + str(exc)) from exc
                (destination / name).write_bytes(raw)
        try:
            raw_policy = carrier._single_file(Path(actions_policy_file), actions.MAX_POLICY_BYTES)
        except carrier.AdmissionError as exc:
            raise ConsumerGateError("unable to snapshot independent Actions policy") from exc
        snapshot_policy = snapshot / "actions-policy.json"
        snapshot_policy.write_bytes(raw_policy)
        if hashlib.sha256(raw_policy).hexdigest() != policy_sha:
            raise ConsumerGateError("snapshotted Actions policy differs from pinned digest")
        # Everything below verifies ONLY private immutable-in-this-process
        # snapshots; the submitter may rotate or mutate original paths now.
        packet, trust, admitted_packet, admitted_trust = locations
        permit_bytes = (packet / "permit.json").read_bytes()
        admission_bytes = (admitted_packet / "admission.json").read_bytes()
        item = _permit(permit_bytes, at or datetime.now(timezone.utc))
        if item["target_ref"] != target or item["carrier_ref"] != evidence_carrier:
            raise ConsumerGateError("permit is not bound to externally expected exact commits")
        if item["actions_policy_sha256"] != policy_sha:
            raise ConsumerGateError("permit does not bind independently pinned Actions policy")
        if hashlib.sha256(admission_bytes).hexdigest() != item["admission_envelope_sha256"]:
            raise ConsumerGateError("permit does not bind independent signed admission envelope")
        try:
            admitted_record = json.loads(admission_bytes.decode("utf-8"))
        except (UnicodeError, ValueError) as exc:
            raise ConsumerGateError("admission envelope malformed") from exc
        assurance = admitted_record.get("source_assurance") if isinstance(admitted_record, dict) else None
        if not isinstance(assurance, dict) or (
            admitted_record.get("scope_sha256") != item["scope_sha256"]
            or assurance.get("run_id") != item["actions_run_id"]
            or assurance.get("run_attempt") != item["actions_run_attempt"]
        ):
            raise ConsumerGateError("consumer permit scope or run differs from signed release admission")
        # Two independent consumer permit signers, each distinct from BOTH release
        # admission signers. Same cryptographic key cannot impersonate two roles.
        pinned_keys: list[str] = []
        for role, principal in (
            *PRINCIPALS.items(),
            *carrier.ROLES.items(),
        ):
            directory = trust if role in PRINCIPALS else admitted_trust
            try:
                key = carrier._authorized_key(
                    carrier._single_file(directory / (role + ".allowed_signers")), principal
                )
            except carrier.AdmissionError as exc:
                raise ConsumerGateError(str(exc)) from exc
            if key in pinned_keys:
                raise ConsumerGateError("independent roles must use four distinct signer keys")
            pinned_keys.append(key)
        executable = shutil.which("ssh-keygen")
        if not executable:
            raise ConsumerGateError("OpenSSH signature verification unavailable")
        for role, principal in PRINCIPALS.items():
            try:
                signed = carrier._single_file(packet / (role + ".sig"))
                # In tests the signature may be supplied as bytes, but OpenSSH's
                # signed input is ALWAYS the exact canonical permit bytes.
                if not signed.startswith(b"-----BEGIN SSH SIGNATURE-----"):
                    raise ConsumerGateError("invalid detached signature format")
                result = subprocess.run(
                    [executable, "-Y", "verify", "-f", str(trust / (role + ".allowed_signers")),
                     "-I", principal, "-n", NAMESPACE, "-s", str(packet / (role + ".sig"))],
                    input=permit_bytes, capture_output=True, check=False, timeout=20,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise ConsumerGateError("detached consumer signature unavailable or timed out") from exc
            except carrier.AdmissionError as exc:
                raise ConsumerGateError(str(exc)) from exc
            if result.returncode != 0:
                raise ConsumerGateError("invalid consumer signature for " + role)
        # Re-execute both verifiers in this trusted process; NEVER trust caller-
        # supplied JSON booleans or an unattested precomputed CI artifact.
        try:
            signed_carrier = carrier.verify_candidate(
                root, admitted_packet, admitted_trust,
                expected_target=target, expected_carrier=evidence_carrier,
                at=at,
            )
            source = actions.verify_source(
                root, snapshot_policy, policy_sha, target_ref=target,
                run_id=item["actions_run_id"], run_attempt=item["actions_run_attempt"],
                token=github_token,
            )
        except (carrier.AdmissionError, actions.ActionsSourceError, OSError, subprocess.TimeoutExpired) as exc:
            raise ConsumerGateError("independent upstream checks denied: " + str(exc)) from exc
        if (
            signed_carrier.get("status") != "verified_offline_signatures_only"
            or signed_carrier.get("target_ref") != target
            or signed_carrier.get("carrier_ref") != evidence_carrier
            or signed_carrier.get("signed_envelope_sha256") != item["admission_envelope_sha256"]
            or set(signed_carrier.get("verified_roles", ())) != set(carrier.ROLES)
            or signed_carrier.get("stable_enforcement_satisfied") is not False
            or source.get("status") != "authenticated_actions_source_metadata_only"
            or source.get("target_ref") != target
            or source.get("run_id") != item["actions_run_id"]
            or source.get("run_attempt") != item["actions_run_attempt"]
            or source.get("policy_sha256") != policy_sha
            or source.get("required_job") != "assurance"
            or source.get("stable_enforcement_satisfied") is not False
        ):
            raise ConsumerGateError("independent upstream check contract mismatch")
        return {
            "status": "consumer_admission_precheck_only",
            "consumer_id": CONSUMER,
            "target_ref": target,
            "carrier_ref": evidence_carrier,
            "permit_sha256": hashlib.sha256(permit_bytes).hexdigest(),
            "admission_envelope_sha256": item["admission_envelope_sha256"],
            "source_policy_sha256": policy_sha,
            "actions_run_id": item["actions_run_id"],
            "actions_run_attempt": item["actions_run_attempt"],
            "consumer_activation_authorized": False,
            "stable_enforcement_satisfied": False,
            "independent_runtime_enforcement_attested": False,
            "replay_protection_attested": False,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail-closed source-only EREI consumer admission precheck")
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--permit-dir", type=Path, required=True)
    parser.add_argument("--consumer-trust-dir", type=Path, required=True)
    parser.add_argument("--admission-packet-dir", type=Path, required=True)
    parser.add_argument("--admission-trust-dir", type=Path, required=True)
    parser.add_argument("--actions-policy-file", type=Path, required=True)
    parser.add_argument("--expected-consumer", required=True)
    parser.add_argument("--expected-target", required=True)
    parser.add_argument("--expected-carrier", required=True)
    parser.add_argument("--expected-actions-policy-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        value = verify_precheck(
            args.repo_root, args.permit_dir, args.consumer_trust_dir,
            args.admission_packet_dir, args.admission_trust_dir,
            args.actions_policy_file,
            expected_consumer=args.expected_consumer,
            expected_target=args.expected_target,
            expected_carrier=args.expected_carrier,
            expected_actions_policy_sha256=args.expected_actions_policy_sha256,
            github_token=os.environ.get("EREI_INDEPENDENT_GITHUB_READ_TOKEN", ""),
        )
        print(json.dumps(value, sort_keys=True))
    except (ConsumerGateError, OSError, subprocess.TimeoutExpired) as exc:
        print("DENIED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
