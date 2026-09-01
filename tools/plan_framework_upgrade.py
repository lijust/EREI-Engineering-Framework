#!/usr/bin/env python3
"""Plan an EREI Engineering Framework pin upgrade without mutating the project."""

from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

PROTECTED_EXACT = {
    "schemas/AGENT_CONTRACT.md",
    "schemas/SKILL_CONTRACT.md",
    "schemas/WORKFLOW_CONTRACT.md",
    "schemas/EVIDENCE_CONTRACT.md",
    "schemas/RISK_CONTRACT.md",
    "schemas/project-framework.schema.json",
}
PROTECTED_PREFIXES = ("constitution/",)
REVIEW_PREFIXES = (
    "agents/",
    "skills/",
    "workflows/",
    "overlays/",
    "adapters/",
    "evals/",
    "tools/",
    "templates/project-bootstrap/",
)


class PlanError(Exception):
    pass


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PlanError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PlanError(f"invalid JSON: {path}: {exc}") from exc


def validate_manifest(m: dict) -> None:
    if m.get("schema_version") != 1:
        raise PlanError("unsupported project manifest schema_version")
    fw = m.get("framework")
    if not isinstance(fw, dict):
        raise PlanError("project manifest missing framework object")
    for key in ("repository", "baseline", "ref_type", "ref"):
        if not fw.get(key):
            raise PlanError(f"project manifest missing framework.{key}")
    if fw["ref_type"] not in {"commit", "tag", "branch"}:
        raise PlanError("invalid framework.ref_type")


def validate_baseline(b: dict, label: str) -> None:
    for key in ("framework", "baseline", "status"):
        if not b.get(key):
            raise PlanError(f"{label} baseline missing {key}")


def is_immutable_ref(ref_type: str, ref: str) -> bool:
    if ref_type == "commit":
        return bool(re.fullmatch(r"[0-9a-fA-F]{7,64}", ref))
    if ref_type == "tag":
        return bool(ref.strip())
    return False


def read_changed_paths(path: Path) -> list[str]:
    if not path.exists():
        raise PlanError(f"missing changed-paths file: {path}")
    paths = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        p = raw.strip()
        if p and not p.startswith("#"):
            paths.append(p)
    return sorted(set(paths))


def classify(paths: list[str]):
    protected = []
    review = []
    for p in paths:
        if p in PROTECTED_EXACT or p.startswith(PROTECTED_PREFIXES):
            protected.append(p)
        elif p.startswith(REVIEW_PREFIXES):
            review.append(p)
    if protected:
        return "ARCHITECTURE_APPROVAL_REQUIRED", "L3", protected, review
    if review:
        return "PROJECT_REVIEW_REQUIRED", "L2", protected, review
    return "NO_GOVERNANCE_CHANGE", "L2", protected, review


def build_plan(args: argparse.Namespace) -> dict:
    manifest = load_json(Path(args.project_manifest))
    current = load_json(Path(args.current_baseline))
    target = load_json(Path(args.target_baseline))
    validate_manifest(manifest)
    validate_baseline(current, "current")
    validate_baseline(target, "target")

    if target["status"] != "stable" and not args.allow_nonstable_target:
        raise PlanError(f"target baseline status is {target['status']!r}, not 'stable'")

    if not is_immutable_ref(args.target_ref_type, args.target_ref) and not args.allow_mutable_target:
        raise PlanError("target ref is not immutable; use commit/tag or explicitly allow mutable target")

    paths = read_changed_paths(Path(args.changed_paths))
    compatibility, risk, protected, review = classify(paths)

    current_fw = manifest["framework"]
    warnings = []
    if current_fw["repository"] != args.target_repository:
        compatibility = "ARCHITECTURE_APPROVAL_REQUIRED"
        risk = "L3"
        warnings.append("Framework repository identity changes.")
    if not is_immutable_ref(current_fw["ref_type"], current_fw["ref"]):
        warnings.append("Current project pin is mutable; preserve exact current ref evidence before upgrade.")

    gates = ["immutable-target", "compatibility", "project-verification", "convergence", "release"]
    if compatibility == "ARCHITECTURE_APPROVAL_REQUIRED":
        gates.insert(2, "explicit-architecture-approval")
    if any(p.startswith(("overlays/", "agents/security-engineer/", "skills/security-", "skills/threat-", "workflows/security-")) for p in paths):
        gates.insert(-3, "security-review")

    return {
        "schema_version": 1,
        "operation": "framework-upgrade-plan",
        "current": {
            "repository": current_fw["repository"],
            "baseline": current_fw["baseline"],
            "ref_type": current_fw["ref_type"],
            "ref": current_fw["ref"],
            "framework_baseline_metadata": current["baseline"],
        },
        "target": {
            "repository": args.target_repository,
            "baseline": target["baseline"],
            "status": target["status"],
            "ref_type": args.target_ref_type,
            "ref": args.target_ref,
        },
        "classification": {
            "compatibility": compatibility,
            "risk": risk,
            "protected_governance_paths": protected,
            "project_review_paths": review,
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
    p = argparse.ArgumentParser()
    p.add_argument("--project-manifest", required=True)
    p.add_argument("--current-baseline", required=True)
    p.add_argument("--target-baseline", required=True)
    p.add_argument("--changed-paths", required=True)
    p.add_argument("--target-repository", default="lijust/EREI-Engineering-Framework")
    p.add_argument("--target-ref-type", choices=("commit", "tag", "branch"), default="commit")
    p.add_argument("--target-ref", required=True)
    p.add_argument("--allow-nonstable-target", action="store_true")
    p.add_argument("--allow-mutable-target", action="store_true")
    p.add_argument("--output")
    return p.parse_args(argv)


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
