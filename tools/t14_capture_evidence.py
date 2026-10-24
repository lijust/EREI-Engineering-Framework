"""Capture T14 synthetic drill evidence before deciding its result.

This helper is not a release authority. It runs only the fixed opt-in drill,
persists unfiltered stdout/stderr/exit status, and rejects ambiguous receipts.
Artifacts must be stored outside the checked-out source tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_COMMIT = "69079018606750312344cb3c648952b9ab72d35b"
V1_SHA256 = "336037ea356c91d780f61684889b7c92c5d2bde21a8fff2591fec95e559be8f2"


def validate_report(data: bytes, target_ref: str) -> None:
    try:
        report = json.loads(data.decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("missing or invalid JSON report") from exc
    if not isinstance(report, dict):
        raise ValueError("drill JSON root must be an object")
    if report.get("evidence_kind") != "LOCAL_SYNTHETIC_ROLLBACK_DRILL":
        raise ValueError("unexpected evidence kind")
    if report.get("v1_commit") != V1_COMMIT or report.get("v1_tool_sha256") != V1_SHA256:
        raise ValueError("untrusted V1 source identity")
    if report.get("isolated_checkout_ref") != target_ref or report.get("checkout_identity_verified") is not True:
        raise ValueError("untrusted exact Git checkout identity")
    if report.get("live_adoption") is not False or report.get("internal_release_qualified") is not False:
        raise ValueError("synthetic drill claims live adoption or release")
    source_hashes = report.get("v2_source_sha256")
    expected_sources = ("tools/task_learning.py", "tools/validation_contract.py",
                        "tools/tests/drill_task_learning_rollback.py")
    if not isinstance(source_hashes, dict) or set(source_hashes) != set(expected_sources):
        raise ValueError("source hash manifest incomplete")
    if any(not isinstance(source_hashes[key], str) or
           not re.fullmatch(r"[a-f0-9]{64}", source_hashes[key]) for key in expected_sources):
        raise ValueError("invalid source hash digest")
    for name, value in (("tests_run", 4), ("failures", 0), ("errors", 0)):
        if type(report.get(name)) is not int or report[name] != value:
            raise ValueError("unexpected drill test result: " + name)
    if report.get("passed") is not True:
        raise ValueError("drill did not pass")


def capture(command: list[str], evidence_dir: Path, target_ref: str, timeout: int = 600) -> bool:
    """Always retain a machine-readable receipt, including negative executions."""
    folder = evidence_dir.resolve()
    if folder == ROOT.resolve() or ROOT.resolve() in folder.parents:
        raise ValueError("evidence must be outside the source checkout")
    if not re.fullmatch(r"[a-f0-9]{40}", target_ref):
        raise ValueError("target-ref must be exact lowercase 40-hex")
    folder.mkdir(parents=True, exist_ok=True)

    try:
        done = subprocess.run(command, cwd=ROOT, capture_output=True,
                              timeout=timeout, check=False)
        stdout, stderr, code = done.stdout, done.stderr, done.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or b""
        stderr = (exc.stderr or b"") + b"\nT14 capture timeout\n"
        code = 124
    except OSError as exc:
        stdout, stderr, code = b"", str(exc).encode("utf-8", "replace"), 127

    # Persist raw, unmodified subprocess evidence and exit status *before*
    # JSON interpretation or any exception/denial.
    (folder / "drill-report.stdout.json").write_bytes(stdout)
    (folder / "drill-stderr.txt").write_bytes(stderr)
    (folder / "drill-exit-code.txt").write_text(str(code) + "\n", encoding="utf-8")
    accepted, reason = False, "nonzero drill exit status: " + str(code)
    if code == 0:
        try:
            validate_report(stdout, target_ref)
            accepted, reason = True, "synthetic four-case source-bound PASS only"
        except ValueError as exc:
            reason = str(exc)
    receipt = {
        "schema_version": 1,
        "evidence_kind": "T14_SYNTHETIC_CI_CAPTURE",
        "target_ref": target_ref,
        "subprocess_exit_code": code,
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "accepted": accepted,
        "reason": reason,
        "live_adoption": False,
        "internal_release_qualified": False,
        "independent_security_approval": False,
    }
    (folder / "capture-verdict.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return accepted


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v1-tool", type=Path, required=True)
    parser.add_argument("--target-ref", required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    command = [sys.executable, "-B", "tools/tests/drill_task_learning_rollback.py",
               "--v1-tool", str(args.v1_tool), "--target-ref", args.target_ref]
    try:
        accepted = capture(command, args.evidence_dir, args.target_ref)
    except (ValueError, OSError) as exc:
        print("T14 capture preflight failed: " + str(exc), file=sys.stderr)
        return 2
    print(("PASS" if accepted else "BLOCKED") +
          " T14 synthetic evidence capture: " + str(args.evidence_dir))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
