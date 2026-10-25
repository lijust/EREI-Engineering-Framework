#!/usr/bin/env python3
"""Read-only main Ruleset observation; NEVER a Stable/release authority verifier.

Observing GitHub's current public rule metadata is helpful but cannot pin the
mutable workflow source, protect release/**/tags, authenticate independent
approvals, or grant real consumer adoption. This module has no positive
Stable authority output, even when every main-branch predicate passes.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

REPOSITORY = "lijust/EREI-Engineering-Framework"
API = "https://api.github.com/repos/" + REPOSITORY
EXPECTED_RULESET_ID = 25712179
REQUIRED_APP_ID = 15368
EXPECTED_CHECK = "assurance"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
MAX_BYTES = 128 * 1024


class ObservationError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ObservationError("GitHub REST redirect not allowed")


def public_json(path: str) -> Any:
    """Public, anonymous, fixed-repository GET only. Never reads API tokens."""
    if path not in ("/", "/branches/main", "/rulesets",
                    f"/rulesets/{EXPECTED_RULESET_ID}"):
        raise ObservationError("unexpected GitHub REST path")
    req = urllib.request.Request(
        API + path,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "EREI-T11-Public-Ruleset-Observer",
        },
        method="GET",
    )
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=12) as res:
            payload = res.read(MAX_BYTES + 1)
    except ObservationError:
        raise
    except (OSError, urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise ObservationError("public GitHub REST metadata unavailable") from exc
    if len(payload) > MAX_BYTES:
        raise ObservationError("GitHub REST response exceeds safe bound")
    try:
        return strict_json(payload)
    except (ValueError, UnicodeError) as exc:
        raise ObservationError("invalid GitHub REST JSON") from exc


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise ObservationError("duplicate JSON key rejected: " + name)
        result[name] = value
    return result


def _nonfinite_json(value: str) -> Any:
    raise ValueError("non-finite JSON constant: " + value)


def strict_json(payload: bytes | str) -> Any:
    """Reject ambiguous duplicate object keys at every nesting depth."""
    return json.loads(
        payload,
        object_pairs_hook=_unique_json_object,
        parse_constant=_nonfinite_json,
    )


def _object(value: Any, name: str) -> dict:
    if not isinstance(value, dict):
        raise ObservationError(name + " must be an object")
    return value


def _items(value: Any, name: str) -> list:
    if not isinstance(value, list):
        raise ObservationError(name + " must be an array")
    return value


def _bound_sha(branch: dict) -> str:
    if branch.get("name") != "main" or branch.get("protected") is not True:
        raise ObservationError("main branch must be live protected")
    sha = _object(branch.get("commit"), "main.commit").get("sha")
    if not isinstance(sha, str) or not SHA40.fullmatch(sha):
        raise ObservationError("main SHA missing or malformed")
    return sha


def assess_public_main_ruleset(
    repository: Any, branch: Any, rulesets: Any, details: Any, *, mode: str
) -> dict[str, Any]:
    """Validate default-branch identity and main-only controls, no release pass."""
    if mode not in {"LIVE_PUBLIC_API", "OFFLINE_FIXTURE_UNTRUSTED"}:
        raise ObservationError("invalid observation mode")
    repo = _object(repository, "repository metadata")
    if repo.get("full_name") != REPOSITORY or repo.get("default_branch") != "main":
        raise ObservationError("repository identity or default-branch drift")
    main_sha = _bound_sha(_object(branch, "main branch"))
    listed = _items(rulesets, "ruleset listing")
    matching = [
        item for item in listed
        if isinstance(item, dict) and type(item.get("id")) is int
        and item["id"] == EXPECTED_RULESET_ID
    ]
    if len(matching) != 1:
        raise ObservationError("missing or duplicate known main Ruleset")
    item, rule = matching[0], _object(details, "ruleset details")
    if any(
        r.get("id") != EXPECTED_RULESET_ID
        or r.get("name") != "EREI-Main-Protection"
        or r.get("enforcement") != "active"
        or r.get("target") != "branch"
        or r.get("source_type") != "Repository"
        or r.get("source") != REPOSITORY
        for r in (item, rule)
    ):
        raise ObservationError("main ruleset identity or enforcement drift")

    conditions = _object(rule.get("conditions"), "ruleset.conditions")
    refs = _object(conditions.get("ref_name"), "ruleset.ref_name")
    if refs.get("include") != ["~DEFAULT_BRANCH"] or refs.get("exclude") != []:
        raise ObservationError("ruleset ref scope is no longer exact main-only")
    bypass = _items(rule.get("bypass_actors"), "ruleset.bypass_actors")
    if bypass:
        raise ObservationError("main ruleset bypass actors present")
    if rule.get("current_user_can_bypass") != "never":
        raise ObservationError("current authenticated principal may bypass ruleset")
    active_rules = _items(rule.get("rules"), "ruleset.rules")
    by_type: dict[str, dict] = {}
    for entry in active_rules:
        entry = _object(entry, "ruleset rule")
        name = entry.get("type")
        if not isinstance(name, str) or name in by_type:
            raise ObservationError("unknown or duplicate ruleset rule type")
        by_type[name] = entry

    required = {"deletion", "non_fast_forward", "pull_request",
                "required_status_checks"}
    if not required.issubset(by_type):
        raise ObservationError("main safety rules missing")
    for name in ("deletion", "non_fast_forward"):
        if set(by_type[name]) != {"type"}:
            raise ObservationError(name + " has unexpected override parameters")

    reviews = _object(by_type["pull_request"].get("parameters"), "PR rules")
    minimum = reviews.get("required_approving_review_count")
    if type(minimum) is not int or minimum < 0:
        raise ObservationError("invalid required reviewer count")
    if reviews.get("required_reviewers") != []:
        raise ObservationError("specialized required reviewers need separate verification")
    if reviews.get("require_code_owner_review") is not False:
        raise ObservationError("unexpected code owner requirement")
    if reviews.get("require_extra_approval_for_unattributed_changes") is not True:
        raise ObservationError("missing unattributed-change approval guard")

    checks = _object(by_type["required_status_checks"].get("parameters"),
                     "status check rules")
    if (checks.get("strict_required_status_checks_policy") is not True
            or checks.get("do_not_enforce_on_create") is not False):
        raise ObservationError("main status-check policy not strict")
    required_checks = _items(checks.get("required_status_checks"), "required checks")
    expected_binding = {"context": EXPECTED_CHECK, "integration_id": REQUIRED_APP_ID}
    if len(required_checks) != 1 or required_checks[0] != expected_binding:
        raise ObservationError("assurance check app binding drift")

    # Deliberately NO path to release authority, even if min reviews > 0.
    return {
        "schema_version": 1,
        "observation_type": "PUBLIC_MAIN_RULESET_SNAPSHOT_ONLY",
        "observation_mode": mode,
        "repository": REPOSITORY,
        "main_sha_observed": main_sha,
        "ruleset_id": EXPECTED_RULESET_ID,
        "status": "MAIN_CI_OBSERVED_RELEASE_BLOCKED",
        "main_rule_require_pr": True,
        "main_rule_strict_assurance_app_bound": True,
        "required_approvals_on_main": minimum,
        "main_force_push_and_delete_denied": True,
        "workflow_source_authenticated": False,
        "release_branches_and_tags_covered": False,
        "reviewer_independence_verified": False,
        "consumer_release_authorized": False,
        "stable_enforcement_verified": False,
        "stable_ready": False,
        "limitations": [
            "public GitHub API snapshot is unsigned and time-varying",
            "GitHub Actions check context/app ID does not authenticate workflow bytes",
            "default-branch Ruleset does not cover release branches or tags",
            "positive T11 requires independent workflow/consumer authority and reviewers",
        ],
    }


def observe(fetch: Callable[[str], Any] = public_json) -> dict[str, Any]:
    return assess_public_main_ruleset(
        fetch("/"),
        fetch("/branches/main"),
        fetch("/rulesets"),
        fetch(f"/rulesets/{EXPECTED_RULESET_ID}"),
        mode="LIVE_PUBLIC_API",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--live", action="store_true", help="public GET only")
    selection.add_argument("--fixture", type=Path, help="offline untrusted fixture")
    args = parser.parse_args(argv)
    try:
        if args.live:
            observation = observe()
        else:
            if args.fixture.stat().st_size > MAX_BYTES:
                raise ObservationError("offline fixture exceeds safe bound")
            obj = strict_json(args.fixture.read_bytes())
            obj = _object(obj, "fixture")
            if set(obj) != {"repository", "branch", "rulesets", "details"}:
                raise ObservationError("fixture must contain exactly 4 API responses")
            observation = assess_public_main_ruleset(
                obj["repository"], obj["branch"], obj["rulesets"], obj["details"],
                mode="OFFLINE_FIXTURE_UNTRUSTED"
            )
    except (ObservationError, OSError, ValueError, UnicodeError) as exc:
        print("BLOCKED_T11_OBSERVATION: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(observation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
