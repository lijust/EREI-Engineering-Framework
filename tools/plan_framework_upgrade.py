#!/usr/bin/env python3
"""Plan EREI Framework upgrades from verified immutable Git objects.

Verified Stable upgrades require two independent identities:
1. the exact Framework target commit under evaluation;
2. an immutable Stable release carrier that proves that exact target was promoted.

BASELINE.json is historical/project metadata, not sufficient Stable provenance for V2.
Legacy caller-supplied metadata remains an unverified planning aid and is never
approval-eligible.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    from . import stable_release_carrier
except ImportError:
    import stable_release_carrier

PROTECTED_EXACT = {
    "BASELINE.json",
    "CAPABILITIES.json",
    "RELEASES.json",
    "schemas/AGENT_CONTRACT.md",
    "schemas/SKILL_CONTRACT.md",
    "schemas/WORKFLOW_CONTRACT.md",
    "schemas/EVIDENCE_CONTRACT.md",
    "schemas/RISK_CONTRACT.md",
    "schemas/RUNTIME_ADAPTER_CONTRACT.md",
    "schemas/project-framework.schema.json",
}
PROTECTED_PREFIXES = (
    "constitution/",
    "schemas/",
    "architecture/",
    "adr/",
    "security/",
    "releases/",
)
REVIEW_PREFIXES = (
    "agents/",
    "skills/",
    "workflows/",
    "overlays/",
    "adapters/",
    "evals/",
    "tools/",
    "templates/project-bootstrap/",
    ".github/workflows/",
    "feedback/",
    "learning/",
    "evidence/",
    "research/",
    "docs/",
)
KNOWN_LOW_RISK_EXACT = {"README.md", ".gitignore", "LICENSE", "LICENSE.md"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class PlanError(Exception):
    pass


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PlanError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PlanError(f"invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PlanError(f"JSON root must be an object: {path}")
    return value


def validate_manifest(manifest: dict) -> None:
    if manifest.get("schema_version") != 1:
        raise PlanError("unsupported project manifest schema_version")
    framework = manifest.get("framework")
    if not isinstance(framework, dict):
        raise PlanError("project manifest missing framework object")
    for key in ("repository", "baseline", "ref_type", "ref"):
        if not isinstance(framework.get(key), str) or not framework[key].strip():
            raise PlanError(f"project manifest missing framework.{key}")
    if framework["ref_type"] not in {"commit", "tag", "branch"}:
        raise PlanError("invalid framework.ref_type")


def validate_baseline(baseline: dict, label: str) -> None:
    for key in ("framework", "baseline", "status"):
        if not isinstance(baseline.get(key), str) or not baseline[key].strip():
            raise PlanError(f"{label} baseline missing {key}")


def is_immutable_ref(ref_type: str, ref: str) -> bool:
    if ref_type == "commit":
        return bool(SHA_RE.fullmatch(ref))
    if ref_type == "tag":
        return bool(isinstance(ref, str) and ref.strip())
    return False


def read_changed_paths(path: Path) -> list[str]:
    if not path.exists():
        raise PlanError(f"missing changed-paths file: {path}")
    values = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        item = raw.strip().replace("\\", "/")
        if item and not item.startswith("#"):
            values.append(item)
    return sorted(set(values))


def classify(paths: list[str]):
    protected: list[str] = []
    review: list[str] = []
    unknown: list[str] = []
    for path in paths:
        p = path.replace("\\", "/").lstrip("./")
        if p in PROTECTED_EXACT or p.startswith(PROTECTED_PREFIXES):
            protected.append(p)
        elif p.startswith(REVIEW_PREFIXES) or p in KNOWN_LOW_RISK_EXACT:
            review.append(p)
        else:
            unknown.append(p)
    if protected or unknown:
        return "ARCHITECTURE_APPROVAL_REQUIRED", "L3", sorted(protected + unknown), sorted(review), sorted(unknown)
    if review:
        return "PROJECT_REVIEW_REQUIRED", "L2", [], sorted(review), []
    return "NO_GOVERNANCE_CHANGE", "L2", [], [], []


def _git(repo: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise PlanError(f"git {' '.join(args)} failed: {process.stderr.strip()}")
    return process.stdout.strip()


def _resolve_commit(repo: Path, ref: str, label: str) -> str:
    resolved = _git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
    if not SHA_RE.fullmatch(resolved):
        raise PlanError(f"{label} did not resolve to an exact commit")
    return resolved


def _git_json(repo: Path, revision: str, path: str) -> dict:
    text = _git(repo, "show", f"{revision}:{path}")
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PlanError(f"invalid {path} at {revision}: {exc}") from exc
    if not isinstance(value, dict):
        raise PlanError(f"{path} at {revision} must be an object")
    return value


def _verified_inputs(args: argparse.Namespace, manifest: dict) -> tuple[dict, dict, list[str], str, str]:
    repo = Path(args.framework_repo).resolve()
    if not (repo / ".git").exists():
        raise PlanError(f"framework_repo is not a Git checkout: {repo}")
    current_fw = manifest["framework"]
    if current_fw["repository"] != args.target_repository:
        raise PlanError("verified planner does not permit repository identity substitution")
    current_ref = args.current_ref or current_fw["ref"]
    if current_ref != current_fw["ref"]:
        raise PlanError("current_ref must match the project manifest Framework pin")
    current_commit = _resolve_commit(repo, current_ref, "current Framework ref")
    target_commit = _resolve_commit(repo, args.target_ref, "target Framework ref")
    current = _git_json(repo, current_commit, "BASELINE.json")
    target = _git_json(repo, target_commit, "BASELINE.json")
    paths = sorted(set(filter(None, _git(repo, "diff", "--name-only", current_commit, target_commit, "--").splitlines())))
    return current, target, paths, current_commit, target_commit


def _legacy_inputs(args: argparse.Namespace) -> tuple[dict, dict, list[str], str, str]:
    current = load_json(Path(args.current_baseline))
    target = load_json(Path(args.target_baseline))
    paths = read_changed_paths(Path(args.changed_paths))
    current_ref = args.current_ref or ""
    return current, target, paths, current_ref, args.target_ref


def _verified_release(args: argparse.Namespace, target_ref: str) -> dict | None:
    carrier = getattr(args, "release_carrier_ref", None)
    if not carrier:
        return None
    try:
        return stable_release_carrier.verify_stable_release_carrier(
            Path(args.framework_repo), target_ref, carrier
        )
    except stable_release_carrier.StableCarrierError as exc:
        raise PlanError(f"Stable release carrier verification failed: {exc}") from exc


def build_plan(args: argparse.Namespace) -> dict:
    manifest = load_json(Path(args.project_manifest))
    validate_manifest(manifest)
    verified = bool(getattr(args, "framework_repo", None))
    release_info: dict | None = None
    if verified:
        current, target, paths, current_resolved_ref, target_resolved_ref = _verified_inputs(args, manifest)
        verification = "verified_git_objects"
    else:
        current, target, paths, current_resolved_ref, target_resolved_ref = _legacy_inputs(args)
        verification = "unverified_caller_supplied_inputs"

    validate_baseline(current, "current")
    validate_baseline(target, "target")
    current_fw = manifest["framework"]

    if current["baseline"] != current_fw["baseline"]:
        raise PlanError(
            f"current baseline metadata {current['baseline']!r} does not match project manifest {current_fw['baseline']!r}"
        )
    if current.get("framework") != target.get("framework"):
        raise PlanError("current and target baseline framework identities differ")
    if not is_immutable_ref(args.target_ref_type, args.target_ref) and not args.allow_mutable_target:
        raise PlanError("target ref is not immutable; use exact commit/tag or explicitly allow mutable target")

    warnings: list[str] = []
    if verified:
        release_info = _verified_release(args, target_resolved_ref)
        if release_info is None:
            if not args.allow_nonstable_target:
                raise PlanError(
                    "verified Stable upgrade requires --release-carrier-ref; BASELINE.status alone is not Stable provenance"
                )
            effective_target_baseline = target["baseline"]
            effective_target_status = "candidate_unverified"
            warnings.append(
                "No Stable release carrier was supplied. Target is treated as Candidate/unreleased even if BASELINE.json says stable."
            )
        else:
            effective_target_baseline = release_info["baseline"]
            effective_target_status = "stable"
            verification = "verified_git_objects_and_stable_release_carrier"
            if target["baseline"] != effective_target_baseline or target["status"] != "stable":
                warnings.append(
                    "Target BASELINE.json is not the release authority; verified Stable release-manifest identity is used for adoption."
                )
    else:
        effective_target_baseline = target["baseline"]
        effective_target_status = target["status"]
        if effective_target_status != "stable" and not args.allow_nonstable_target:
            raise PlanError(f"target baseline status is {effective_target_status!r}, not 'stable'")

    compatibility, risk, protected, review, unknown = classify(paths)
    if current_fw["repository"] != args.target_repository:
        compatibility = "ARCHITECTURE_APPROVAL_REQUIRED"
        risk = "L3"
        warnings.append("Framework repository identity changes.")
    if not is_immutable_ref(current_fw["ref_type"], current_fw["ref"]):
        warnings.append("Current project pin is mutable; preserve exact current commit evidence before upgrade.")
    if unknown:
        warnings.append("Unknown Framework paths were conservatively escalated to L3: " + ", ".join(unknown))
    if not verified:
        warnings.append(
            "Plan inputs were supplied by the caller and were not derived from Git objects. "
            "This output is a planning aid only and MUST NOT be used as an approval/compatibility gate."
        )

    approval_eligible = bool(verified and release_info is not None)
    gates = [
        "immutable-target",
        "verified-inputs",
        "stable-release-carrier" if release_info is not None else "stable-release-carrier-BLOCKED",
        "compatibility",
        "project-verification",
        "convergence",
        "release",
    ]
    if compatibility == "ARCHITECTURE_APPROVAL_REQUIRED":
        gates.insert(4, "explicit-architecture-approval")
    if any(
        p.startswith(("security/", "overlays/", "agents/security-engineer/", "skills/security-", "skills/threat-", "workflows/security-"))
        for p in paths
    ):
        gates.insert(-3, "security-review")
    if not verified:
        gates[1] = "verified-inputs-BLOCKED"

    return {
        "schema_version": 2,
        "operation": "framework-upgrade-plan",
        "input_verification": verification,
        "approval_eligible": approval_eligible,
        "current": {
            "repository": current_fw["repository"],
            "baseline": current_fw["baseline"],
            "ref_type": current_fw["ref_type"],
            "ref": current_fw["ref"],
            "resolved_commit": current_resolved_ref if verified else None,
            "framework_baseline_metadata": current["baseline"],
        },
        "target": {
            "repository": args.target_repository,
            "baseline": effective_target_baseline,
            "status": effective_target_status,
            "ref_type": args.target_ref_type,
            "ref": args.target_ref,
            "resolved_commit": target_resolved_ref if verified else None,
            "framework_baseline_metadata": target["baseline"],
        },
        "stable_release": {
            "verified": release_info is not None,
            "carrier_ref": release_info["carrier_ref"] if release_info else None,
            "manifest_path": release_info["manifest_path"] if release_info else None,
            "release_id": release_info["release_id"] if release_info else None,
            "assurance_contract_version": release_info["assurance_contract_version"] if release_info else None,
            "grandfathered_v1": release_info["grandfathered_v1"] if release_info else False,
        },
        "classification": {
            "compatibility": compatibility,
            "risk": risk,
            "protected_governance_paths": protected,
            "project_review_paths": review,
            "unknown_escalated_paths": unknown,
        },
        "changed_paths": paths,
        "required_gates": gates,
        "warnings": warnings,
        "rollback": {
            "repository": current_fw["repository"],
            "baseline": current_fw["baseline"],
            "ref_type": current_fw["ref_type"],
            "ref": current_fw["ref"],
        },
        "mutation_performed": False,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-manifest", required=True)
    parser.add_argument("--framework-repo", help="Framework Git checkout; enables verified planning mode")
    parser.add_argument("--current-ref", help="must equal project manifest ref in verified mode")
    parser.add_argument("--current-baseline", help="legacy unverified mode only")
    parser.add_argument("--target-baseline", help="legacy unverified mode only")
    parser.add_argument("--changed-paths", help="legacy unverified mode only")
    parser.add_argument("--target-repository", default="lijust/EREI-Engineering-Framework")
    parser.add_argument("--target-ref-type", choices=("commit", "tag", "branch"), default="commit")
    parser.add_argument("--target-ref", required=True)
    parser.add_argument("--release-carrier-ref", help="exact immutable commit carrying the verified Stable release evidence")
    parser.add_argument("--allow-nonstable-target", action="store_true")
    parser.add_argument("--allow-mutable-target", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    if not args.framework_repo and not all((args.current_baseline, args.target_baseline, args.changed_paths)):
        parser.error("legacy mode requires --current-baseline, --target-baseline and --changed-paths")
    return args


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        plan = build_plan(args)
    except PlanError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(plan, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
