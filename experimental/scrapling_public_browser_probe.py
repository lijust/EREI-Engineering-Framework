#!/usr/bin/env python3
"""Public, one-page robots-gated dynamic Scraping demo with Scrapling v0.5.

The target is a publicly available Saudi website. This code does not read any
private repository, client mapping, credentials, or other proprietary material.
Never stores request URLs with query params or actual JSON response field values.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher, StealthySession

URL = "https://sakani.sa/app/offplan-projects/35"
UA = "Open-source-Scrapling-Public-Demo/0.1"
RESULT = Path(os.environ["RUNNER_TEMP"]) / "public-scrapling-dynamic-shape.json"
state = {"source_domain": "sakani.sa", "target_path": "/app/offplan-projects/35",
         "state": "STARTED", "capture_count": 0, "json_shaped_endpoints": [],
         "raw_request_queries_saved": False, "raw_response_bodies_saved": False}
try:
    robots_url = "https://sakani.sa/robots.txt"
    response = Fetcher.get(robots_url, retries=1, timeout=25, follow_redirects="safe",
                           headers={"User-Agent": UA})
    if response.status == 429:
        state["state"] = "ROBOTS_HTTP_429_STOP"
    elif response.status != 200:
        state["state"] = "ROBOTS_UNAVAILABLE_FAIL_CLOSED"
        state["robots_status"] = response.status
    elif (urlsplit(str(response.url)).hostname or "").removeprefix("www.") != "sakani.sa":
        state["state"] = "ROBOTS_REDIRECT_UNEXPECTED"
    else:
        rules = RobotFileParser()
        rules.parse(response.body.decode("utf-8", errors="replace").splitlines())
        if not rules.can_fetch(UA, URL):
            state["state"] = "ROBOTS_DISALLOW_PAGE"
        else:
            from time import sleep
            sleep(max(3, rules.crawl_delay(UA) or rules.crawl_delay("*") or 0))
            with StealthySession(record_requests=True, max_recorded_requests=200) as session:
                page = session.fetch(URL, network_idle=True)
                if page.status == 429:
                    state["state"] = "PAGE_HTTP_429_STOP"
                else:
                    records = session.network.search(limit=None, include_static=False)
                    state["page_status"] = int(page.status)
                    state["capture_count"] = len(records)
                    statuses = Counter()
                    for item in records:
                        status = int(item.status)
                        statuses[str(status)] += 1
                        if status == 429:
                            state["state"] = "XHR_HTTP_429_STOP"
                            break
                        if status != 200: continue
                        parsed = urlsplit(str(item.url))
                        host = (parsed.hostname or "").removeprefix("www.")
                        if parsed.scheme != "https" or (host != "sakani.sa" and not host.endswith(".sakani.sa")):
                            continue
                        if item.meta.get("resource_type") not in ("xhr", "fetch"):
                            continue
                        try:
                            content = json.loads(item.body)
                        except (ValueError, TypeError, UnicodeError):
                            continue
                        if isinstance(content, list):
                            count = len(content)
                            keys = sorted(content[0].keys())[:35] if count and isinstance(content[0], dict) else []
                        elif isinstance(content, dict):
                            arrays = [v for v in content.values() if isinstance(v, list)]
                            count = len(arrays[0]) if arrays else 0
                            keys = sorted(str(k) for k in content.keys())[:35]
                        else:
                            continue
                        state["json_shaped_endpoints"].append({
                            "host": host, "path_only": parsed.path,
                            "top_keys": keys, "first_array_count": count,
                        })
                        if len(state["json_shaped_endpoints"]) >= 30: break
                    state["statuses"] = dict(statuses)
                    if state["state"] == "STARTED":
                        state["state"] = "DYNAMIC_METADATA_CAPTURE_DONE"
except Exception as exc:
    state["state"] = "EXCEPTION"
    state["exception_type"] = type(exc).__name__
    state["exception_message"] = str(exc)[:160]

state["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
RESULT.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(state, ensure_ascii=False))
