#!/usr/bin/env python3
"""Read-only, robots-gated Scrapling source discovery for Kite Saudi project listings.

Target identity list consists only of public marketing project names, without private project identifiers.
No writes to any third-party or private production database. A third-party listing ID is NOT a physical-unit ID.
Stores publisher-facing itemized cards only, without contact/customer data.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

BASE = "https://kite.sa"
UA = "Open-Source-Publisher-Inventory-Research/1.0 (+https://github.com/lijust/EREI-Engineering-Framework)"
TARGETS = {
    "الماجدية 117": "PUBLIC_KITE_117",
    "الماجدية 156": "PUBLIC_KITE_156",
}
INDEX_PAGES = ["/en/projects/riyadh", "/en/projects/riyadh?page=2",
               "/en/projects/riyadh?page=3", "/en/projects/riyadh?page=4"]
PROJECT_URL_RE = re.compile(r"^/en/projects/riyadh/\d+/?$")
LISTING_URL_RE = re.compile(r"^/en/listing/\d+/?$")
MAX_BYTES = 3_000_000


class StopOn429(Exception):
    pass


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            self.current = {"href": href, "pieces": []}

    def handle_data(self, data):
        if self.current is not None and data.strip():
            self.current["pieces"].append(data.strip())

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            x = self.current
            self.links.append((x["href"], " ".join(x["pieces"])))
            self.current = None


def canonical_url(path):
    url = urljoin(BASE, path)
    p = urlparse(url)
    if p.scheme != "https" or p.hostname != "kite.sa" or p.port:
        raise ValueError("Off-domain URL rejected")
    if p.username or p.password or p.fragment:
        raise ValueError("Unexpected credentials/fragment")
    if not (p.path == "/robots.txt" or
            p.path == "/en/projects/riyadh" or
            PROJECT_URL_RE.fullmatch(p.path) or LISTING_URL_RE.fullmatch(p.path)):
        raise ValueError("Unapproved URL path")
    if p.query and not (p.path == "/en/projects/riyadh" and
                        re.fullmatch(r"page=[1-4]", p.query)):
        raise ValueError("Unapproved query")
    return url


def download(url):
    from scrapling.fetchers import Fetcher
    safe = canonical_url(url)
    resp = Fetcher.get(safe, timeout=25, retries=0, follow_redirects="safe",
                       headers={"User-Agent": UA})
    status = int(resp.status)
    if status == 429:
        raise StopOn429(safe)
    if status != 200:
        raise ValueError(f"HTTP_{status}: {safe}")
    resolved = urlparse(str(getattr(resp, "url", safe)))
    if resolved.hostname != "kite.sa":
        raise ValueError("Cross-domain redirect")
    body = resp.body
    if not isinstance(body, bytes) or not body or len(body) > MAX_BYTES:
        raise ValueError("Invalid public HTML response size")
    return body.decode("utf-8", errors="replace")


def atomic_save(dest, obj):
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp = dest.with_suffix(".partial.json")
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    temp.replace(dest)


def links(html):
    p = LinkParser()
    p.feed(html)
    return p.links


def clean_name(t):
    return re.sub(r"\s+", " ", t.strip()).replace("ـ", "")


def project_for_anchor(anchor):
    # Exact project label required; avoid false substring 1179 or unrelated publisher.
    s = clean_name(anchor)
    hits = [(name, pid) for name, pid in TARGETS.items()
            if re.search(r"(?<!\d)" + re.escape(name) + r"(?!\d)", s)]
    return hits[0] if len(hits) == 1 else None


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--delay", type=float, default=2.5)
    cli.add_argument("--max-listings", type=int, default=100)
    args = cli.parse_args()
    if args.delay < 2 or not (1 <= args.max_listings <= 150):
        raise SystemExit("Minimum 2-second delay, 1-150 listing cap")

    result = {"schema": "SAE_KITE_FIRSTPARTY_NAMED_PROJECT_CROSS_SOURCE_PILOT_V1",
              "date_utc": datetime.now(timezone.utc).isoformat(),
              "source": BASE, "classification": "THIRD_PARTY_PORTAL",
              "public_target_names": TARGETS,
              "indexed_pages": [], "matched_project_pages": [],
              "listing_cards": [], "error": None,
              "source_only_no_sheet_writes": 0, "no_research_sheet_writes": 0,
              "new_projects": 0, "new_developers": 0}

    try:
        robots_content = download(BASE + "/robots.txt")
        rules = RobotFileParser()
        rules.parse(robots_content.splitlines())
        candidates = {}
        for path in INDEX_PAGES:
            url = canonical_url(path)
            if not rules.can_fetch(UA, url):
                result["indexed_pages"].append({"url": url, "status": "ROBOTS_DISALLOW"})
                continue
            time.sleep(max(args.delay, float(rules.crawl_delay(UA) or
                                             rules.crawl_delay("*") or 0)))
            html = download(url)
            hit = []
            for href, label in links(html):
                resolved = urlparse(urljoin(BASE, href))
                if resolved.hostname != "kite.sa" or not PROJECT_URL_RE.fullmatch(resolved.path):
                    continue
                match = project_for_anchor(label)
                if match is None:
                    continue
                name, canonical_id = match
                target_url = canonical_url(resolved.path)
                candidates[(canonical_id, target_url)] = name
                hit.append({"name": name, "project_id": canonical_id, "url": target_url})
            result["indexed_pages"].append({"url": url, "status": "FETCHED",
                                             "matching_project_links": hit})
            atomic_save(args.output, result)

        # An independently observed source project URL, previously indexed.
        # Not a fabricated URL or a generated unit code.
        if not any(pid == "PUBLIC_KITE_156" for pid, u in candidates):
            candidates[("PUBLIC_KITE_156", "https://kite.sa/en/projects/riyadh/10")] = "الماجدية 156"
        found = set()
        for (pid, url), label in candidates.items():
            if not rules.can_fetch(UA, url):
                result["matched_project_pages"].append({"project_id": pid, "url": url,
                                                        "status": "ROBOTS_DISALLOW"})
                continue
            time.sleep(args.delay)
            html = download(url)
            candidates_links = []
            for href, txt in links(html):
                p = urlparse(urljoin(BASE, href))
                if p.hostname == "kite.sa" and LISTING_URL_RE.fullmatch(p.path):
                    url2 = canonical_url(p.path)
                    if url2 not in found:
                        candidates_links.append({"url": url2,
                                                 "preview": clean_name(txt)[:240]})
                        found.add(url2)
            all_browse_links = [
                {"url": urljoin(BASE, href).split("#", 1)[0], "anchor": clean_name(txt)[:140]}
                for href, txt in links(html)
                if urlparse(urljoin(BASE, href)).hostname == "kite.sa"
                and ("list" in href.lower() or "unit" in href.lower() or "page=" in href.lower())
            ][:90]
            result["matched_project_pages"].append(
                {"public_source_project_label": pid, "project_name": label,
                 "url": url, "status": "FETCHED", "linked_listing_urls": len(candidates_links),
                 "browse_listing_links": all_browse_links})
            atomic_save(args.output, result)
            for item in candidates_links:
                if len(result["listing_cards"]) >= args.max_listings:
                    break
                item["public_source_project_label"] = pid
                item["source_project_url"] = url
                # Save only short card label and listing identity; never dump full pages
                # containing potentially personal phone/customer data.
                result["listing_cards"].append(item)
                if len(result["listing_cards"]) % 10 == 0:
                    atomic_save(args.output, result)
        result["status"] = "COMPLETE_READ_ONLY"
    except StopOn429 as exc:
        result.update(status="STOP_HTTP_429", error=str(exc))
    except Exception as exc:
        result.update(status="STOP_SOURCE_ERROR", error=f"{type(exc).__name__}:{exc}")
    finally:
        atomic_save(args.output, result)
        print(json.dumps({"status": result.get("status"), "error": result["error"],
                          "project_pages": len(result["matched_project_pages"]),
                          "source_listing_urls": len(result["listing_cards"]),
                          "output": str(args.output)}, ensure_ascii=False))
    if result["status"] != "COMPLETE_READ_ONLY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
