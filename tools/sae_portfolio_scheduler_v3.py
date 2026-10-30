"""SAE-DB source-first inventory frontier planner (read-only, offline).

A source's advertised project size is NEVER evidence of independently identified
physical units. Only original publisher/building/unit composite keys can create
an inventory delta candidate. This module never fetches a website or writes DB.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Any
from urllib.parse import urlsplit
import re

_PID = re.compile(r"^PRJ-\d{6}$")


@dataclass(frozen=True)
class FrontierItem:
    project_id: str
    url: str
    origin: str
    mode: str  # ITEMIZED_DELTA or DISCOVERY_ONLY or SOURCE_REFRESH
    confirmed_source_keys: int
    unmatched_source_keys: int
    score: int


def _host(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Only explicit publisher HTTPS URLs are accepted")
    if parsed.port not in (None, 443):
        raise ValueError("Non-standard port")
    return parsed.hostname.lower().removeprefix("www.")


def _unit_key(item: dict[str, Any]) -> tuple[str, str] | None:
    """Unique physical identity requires original unit code AND building scope.

    A publisher can explicitly declare a project-wide unique unit code by
    setting unit_code_unique_across_buildings=True; otherwise building is
    mandatory. No synthetic keys from prices, areas, types or sequences.
    """
    code = str(item.get("source_unit_code") or "").strip()
    if not code:
        return None
    building = str(item.get("source_building_code") or "").strip()
    if not building and not item.get("unit_code_unique_across_buildings", False):
        return None
    return (building if building else "PROJECT_WIDE_PUBLISHER_CODE", code)


def plan_sources(candidates: list[dict], seen: dict[str, dict], *,
                 max_publishers: int | None = None,
                 max_items: int | None = None) -> dict:
    """Prioritize exact source-to-Master ID gaps, then bounded discovery.

    Candidate schema: project_id, url, origin, project_match_confirmed,
    robots_verified, terms_allow_automation, source_units=[{source_unit_code,
    source_building_code or unit_code_unique_across_buildings}],
    master_unit_keys=[{...}], source_fingerprint, marketing_total(optional).
    On any permission uncertainty, no automated probing is scheduled.
    """
    # None means schedule ALL qualified registered publisher/source-project
    # items, not an implicit 14-publisher / 80-project artificial frontier.
    # Real acquisition safety lives in robots, terms, per-origin throttling,
    # 403/429 fail-closed and durable source checkpoints.
    if (max_publishers is not None and not 0 <= max_publishers <= 10000) or (
        max_items is not None and not 0 <= max_items <= 100000
    ):
        raise ValueError("Invalid execution limits")
    item_budget = max_items if max_items is not None else len(candidates)
    origin_budget = max_publishers if max_publishers is not None else len(candidates)
    by_origin: dict[str, list[FrontierItem]] = defaultdict(list)
    skipped: list[dict] = []
    unique_project_urls: set[tuple[str, str]] = set()
    for row in candidates:
        project_id = str(row.get("project_id", ""))
        url = str(row.get("url", ""))
        if not _PID.fullmatch(project_id):
            raise ValueError("Noncanonical project ID")
        host = _host(url)
        origin = str(row.get("origin") or host).lower().removeprefix("www.")
        if origin != host:
            raise ValueError("Origin mismatch")
        key = (project_id, url)
        if key in unique_project_urls:
            raise ValueError("Duplicate project+URL")
        unique_project_urls.add(key)
        if not row.get("project_match_confirmed"):
            skipped.append({"project_id": project_id, "reason": "PROJECT_IDENTITY_UNCONFIRMED"})
            continue
        if not row.get("robots_verified") or not row.get("terms_allow_automation"):
            skipped.append({"project_id": project_id, "reason": "ACCESS_PERMISSION_UNVERIFIED"})
            continue
        previous = seen.get(project_id + "|" + url, {})
        if previous.get("http_blocked") or previous.get("stop_429"):
            skipped.append({"project_id": project_id, "reason": "SOURCE_BLOCKED"})
            continue
        raw_items = row.get("source_units") or []
        source_keys = [_unit_key(x) for x in raw_items]
        if any(x is None for x in source_keys) or len(set(source_keys)) != len(source_keys):
            skipped.append({"project_id": project_id, "reason": "SOURCE_IDENTITY_COLLISION_OR_MISSING"})
            continue
        master_keys = [_unit_key(x) for x in row.get("master_unit_keys", [])]
        if any(x is None for x in master_keys):
            skipped.append({"project_id": project_id, "reason": "MASTER_IDENTITY_UNSAFE"})
            continue
        new_keys = set(source_keys) - set(master_keys)
        fingerprint = row.get("source_fingerprint")
        unchanged = bool(fingerprint and fingerprint == previous.get("source_fingerprint"))
        if source_keys and new_keys:
            mode = "ITEMIZED_DELTA"
            score = 1000 + min(len(new_keys), 100000)
        elif unchanged:
            skipped.append({"project_id": project_id, "reason": "SOURCE_UNCHANGED_NO_UNIT_DELTA"})
            continue
        elif source_keys:
            mode = "SOURCE_REFRESH"
            score = 100 + min(len(source_keys), 500)
        elif previous.get("landing_only") and not row.get("source_changed"):
            skipped.append({"project_id": project_id, "reason": "UNCHANGED_MARKETING_LANDING"})
            continue
        else:
            mode = "DISCOVERY_ONLY"
            score = 10
        by_origin[origin].append(FrontierItem(project_id, url, origin, mode,
                                            len(source_keys), len(new_keys), score))
    for group in by_origin.values():
        group.sort(key=lambda x: (-x.score, x.project_id, x.url))
    queue: list[FrontierItem] = []
    selected_origins: set[str] = set()
    while by_origin and len(queue) < item_budget:
        active = sorted(by_origin, key=lambda o: (-by_origin[o][0].score, o))
        advanced = False
        for origin in active:
            if len(queue) == item_budget:
                break
            if origin not in selected_origins and len(selected_origins) >= origin_budget:
                continue
            queue.append(by_origin[origin].pop(0))
            selected_origins.add(origin)
            advanced = True
            if not by_origin[origin]:
                del by_origin[origin]
        if not advanced:
            break
    return {"queue": [asdict(x) for x in queue],
            "skipped": skipped,
            "summary": {"queued": len(queue), "origins": len(selected_origins),
                        "itemized_unmatched_candidates": sum(
                            x.unmatched_source_keys for x in queue if x.mode == "ITEMIZED_DELTA"),
                        "canonical_writes": 0,
                        "important": "Unmatched source codes are candidates, not yet proven net-new physical units."}}
