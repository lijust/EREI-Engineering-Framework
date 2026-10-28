#!/usr/bin/env python3
"""Public Kite project index discovery only; raw publisher links, no user project data.

The index supplies project links and marketed unit/offer counts, NOT individual
physical inventory; no production writes. Stops on 429, respects robots.txt.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit, urljoin, parse_qs
from urllib.robotparser import RobotFileParser

UA = "Public-Source-Index-Audit/1.0 (+https://github.com/lijust/EREI-Engineering-Framework)"
HOST = "kite.sa"
URL = "https://kite.sa"
CITIES = {"riyadh":36, "jeddah":22, "eastern-province":18}
INDEX = re.compile(r"^/en/projects/(riyadh|jeddah|eastern-province)/?$")
DETAIL = re.compile(r"^/en/projects/(riyadh|jeddah|eastern-province)/\d+/?$")


class Halt429(Exception):
    pass


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out = []
        self.anchor = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.anchor = {"href": dict(attrs).get("href", ""), "texts": []}

    def handle_data(self, text):
        if self.anchor is not None:
            self.anchor["texts"].append(text)

    def handle_endtag(self, tag):
        if tag == "a" and self.anchor is not None:
            rec = self.anchor
            self.out.append((rec["href"], " ".join(rec["texts"]).strip()))
            self.anchor = None


def get(url):
    from scrapling.fetchers import Fetcher
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname != HOST or parts.username or parts.password:
        raise ValueError("Off-host URL")
    if parts.path != "/robots.txt" and not INDEX.fullmatch(parts.path):
        raise ValueError("Only public index allowed")
    if parts.query:
        q = parse_qs(parts.query)
        if set(q) != {"page"} or len(q["page"]) != 1 or not q["page"][0].isdigit() or not 1 <= int(q["page"][0]) <= 50:
            raise ValueError("Unexpected index query")
    resp = Fetcher.get(url, retries=0, timeout=25, follow_redirects="safe",
                       headers={"User-Agent": UA})
    code = int(resp.status)
    if code == 429:
        raise Halt429(url)
    if code != 200:
        raise ValueError("HTTP_" + str(code) + " " + url)
    if urlsplit(str(resp.url)).hostname != HOST:
        raise ValueError("Off-source redirect")
    body = resp.body
    if not isinstance(body, bytes) or not body or len(body) > 3_500_000:
        raise ValueError("Invalid HTML size")
    return body.decode("utf-8", errors="replace")


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--max-pages-per-city", type=int, default=40)
    p.add_argument("--delay", type=float, default=2.25)
    a = p.parse_args()
    if a.delay < 2 or not 1 <= a.max_pages_per_city <= 50:
        raise ValueError("Minimum 2 seconds and at most 50 pages/city")
    state = {"schema":"PUBLIC_SA_KITE_PROJECT_INDEX_SOURCE_LINKS_V1",
             "run_at_utc":datetime.now(timezone.utc).isoformat(),
             "source_url":URL, "projects":[], "pages":[], "errors":[],
             "status":"STARTED", "source_only":True, "canonical_writes":0}
    seen=set()
    try:
        rules=RobotFileParser()
        rules.parse(get(URL + "/robots.txt").splitlines())
        for city, maximum in CITIES.items():
            for page in range(1,min(maximum,a.max_pages_per_city)+1):
                url=URL + "/en/projects/" + city + (("?page="+str(page)) if page>1 else "")
                if not rules.can_fetch(UA,url):
                    state["errors"].append({"url":url,"reason":"ROBOTS_DISALLOW"})
                    break
                time.sleep(max(a.delay,float(rules.crawl_delay(UA) or rules.crawl_delay("*") or 0)))
                try:
                    doc=get(url)
                except Halt429:
                    raise
                except Exception as e:
                    state["errors"].append({"url":url,"reason":str(e)[:200]})
                    break
                parser=Anchors()
                parser.feed(doc)
                count=0
                for href, label in parser.out:
                    parsed=urlsplit(urljoin(URL,href))
                    if parsed.hostname!=HOST or not DETAIL.fullmatch(parsed.path):
                        continue
                    link=URL+parsed.path
                    if link in seen:
                        continue
                    seen.add(link)
                    label=re.sub(r"\s+"," ",label).strip()[:260]
                    count+=1
                    state["projects"].append({"source_page":url,"city":city,
                                               "source_project_url":link,"anchor":label,
                                               "marketed_listing_count":int(re.search(r"(\d+)\s+units",label,re.I).group(1))
                                               if re.search(r"(\d+)\s+units",label,re.I) else None})
                state["pages"].append({"url":url,"new_project_links":count})
                if count==0:
                    break
                if len(state["pages"])%5==0:save(a.out,state)
        state["status"]="COMPLETE_SOURCE_INDEX_ONLY"
    except Halt429 as e:
        state["status"]="STOP_429";state["errors"].append({"reason":"HTTP429","url":str(e)})
    except Exception as e:
        state["status"]="STOP_ERROR";state["errors"].append({"reason":str(e)[:300]})
    finally:
        save(a.out,state)
        print(json.dumps({"status":state["status"],"source_project_links":len(state["projects"]),
                          "pages":len(state["pages"]),"errors":len(state["errors"])},ensure_ascii=False))
    if state["status"] not in ("COMPLETE_SOURCE_INDEX_ONLY",):
        raise SystemExit(1)


if __name__=="__main__":
    main()
