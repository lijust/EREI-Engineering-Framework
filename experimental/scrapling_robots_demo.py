#!/usr/bin/env python3
"""Generic public robots availability/access diagnostic via Scrapling, no crawling."""
from __future__ import annotations
import json
from pathlib import Path
import os
import time
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher

HOSTS = ["etmaam.almajdiah.com"]
UA = "Open-source-Scrapling-Public-Demo/0.1"
out = []
for host in HOSTS:
    url = f"https://{host}/robots.txt"
    item = {"host": host, "robots_url": url}
    try:
        response = Fetcher.get(url, retries=1, timeout=17, follow_redirects="safe",
                               headers={"User-Agent": UA})
        item["status_code"] = int(response.status)
        if response.status == 200 and 0 < len(response.body) <= 200_000:
            parser = RobotFileParser()
            parser.parse(response.body.decode("utf-8", "replace").splitlines())
            item["root_allowed"] = parser.can_fetch(UA, f"https://{host}/")
            item["project_path_allowed"] = parser.can_fetch(UA, f"https://{host}/projects/197")
            item["crawl_delay_s"] = parser.crawl_delay(UA) or parser.crawl_delay("*")
        else:
            item["state"] = "ROBOTS_UNAVAILABLE_FAIL_CLOSED"
    except Exception as exc:
        item["state"] = "ERROR_FAIL_CLOSED"
        item["exception_type"] = type(exc).__name__
    out.append(item)
    print(json.dumps(item))
    time.sleep(2.5)
Path(os.environ["RUNNER_TEMP"],"public-publisher-robots-scrapling.json").write_text(
    json.dumps({"checks":out, "request_method":"Scrapling Fetcher.get",
                "source_project_cards_collected":0,"no_private_data":True},indent=2),
    encoding="utf-8",
)
