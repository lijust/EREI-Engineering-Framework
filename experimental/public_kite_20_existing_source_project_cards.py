#!/usr/bin/env python3
"""Robots-gated original third-party Kite project card links for public Saudi projects.

Public marketing pages only. No private identifiers and no user data, no canonical
writes. Capture publisher exact unit link, unit text and itemized count separately
from aggregate marketed project counts. HTTP 429 halts all requests.
"""
from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

UA = "Open-Saudi-Project-Card-Research/1.0 (+https://github.com/lijust/EREI-Engineering-Framework)"
BASE = "https://kite.sa"
SOURCES = [
    ("jeddah","73015","المروة D4"),
    ("riyadh","64574","تارك 116"),
    ("riyadh","77167","Roya Sedra"),
    ("riyadh","43369","ربوة الرمز"),
    ("riyadh","40753","ستون الملقا"),
    ("riyadh","1677","هيلز 2"),
    ("eastern-province","1379","أجدان إنفينيتي"),
    ("eastern-province","731","Roya AlNakheel"),
    ("riyadh","12","مكين 64"),
    ("riyadh","97428","رواء"),
    ("jeddah","98115","إرساء الريان"),
    ("jeddah","98176","رابية الفيصلية 2"),
    ("riyadh","97422","فيورا"),
    ("riyadh","111832","Alegria"),
    ("riyadh","97424","ريفييرا ريزدنس"),
    ("jeddah","98267","درب الرؤية 115"),
    ("riyadh","96149","Satel at Opal"),
    ("jeddah","98188","زهرة النعيم"),
    ("riyadh","77165","Ewan Sedra4"),
    ("riyadh","112311","Dyari Alarid"),
]
class Stopped429(Exception):
    pass
class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current = None
        self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a":
            self.current={"href":dict(attrs).get("href",""),"text":[]}
    def handle_data(self,data):
        if self.current is not None and data.strip():
            self.current["text"].append(data.strip())
    def handle_endtag(self,tag):
        if tag=="a" and self.current is not None:
            d=self.current
            self.links.append((d["href"]," ".join(d["text"])))
            self.current=None

def fetch(url):
    from scrapling.fetchers import Fetcher
    r=Fetcher.get(url,retries=0,timeout=28,follow_redirects="safe",headers={"User-Agent":UA})
    if int(r.status)==429:raise Stopped429(url)
    if int(r.status)!=200:raise RuntimeError("HTTP_"+str(r.status))
    if urlparse(str(r.url)).hostname!="kite.sa":raise RuntimeError("Off-site redirect")
    if not isinstance(r.body,bytes) or not 0<len(r.body)<4_000_000:raise RuntimeError("Invalid body")
    return r.body.decode("utf-8",errors="replace")

def atomic_save(p, data):
    p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(".tmp")
    q.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    q.replace(p)

def main():
    import os
    p=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"kite-20-public-sources-itemized.json"
    state={"schema":"PUBLIC_KITE_20_EXACT_PROJECT_SOURCE_CARDS_V1",
           "date":datetime.now(timezone.utc).isoformat(),
           "count_source_projects":len(SOURCES),
           "cards":[],"source_projects":[],"errors":[],"canonical_writes":0,"status":"STARTED"}
    try:
        rules=RobotFileParser()
        rules.parse(fetch(BASE+"/robots.txt").splitlines())
        seen=set()
        for city,no,label in SOURCES:
            url=BASE+"/en/projects/"+city+"/"+no
            if not rules.can_fetch(UA,url):
                state["errors"].append({"url":url,"error":"ROBOTS_DISALLOW"});continue
            time.sleep(max(2.5,float(rules.crawl_delay(UA) or rules.crawl_delay("*") or 0)))
            try:html=fetch(url)
            except Stopped429:raise
            except Exception as e:
                state["errors"].append({"url":url,"error":str(e)[:120]});continue
            links=Links();links.feed(html)
            cards=[]
            for href,txt in links.links:
                target=urlparse(urljoin(BASE,href))
                if target.scheme!="https" or target.hostname!="kite.sa":continue
                if not re.fullmatch(r"/en/listing/\d+/?",target.path):continue
                link=BASE+target.path
                if link in seen:continue
                seen.add(link)
                cards.append({"source_unit_listing_url":link,
                              "source_listing_id":target.path.strip("/").split("/")[-1],
                              "display_text":re.sub(r"\s+"," ",txt).strip()[:350],
                              "source_project_url":url,"source_project_name":label})
            state["source_projects"].append({"original_project_url":url,"original_project_name":label,
                 "individual_itemized_source_cards":len(cards)})
            state["cards"].extend(cards)
            atomic_save(p,state)
        state["status"]="COMPLETE_SOURCE_ONLY"
    except Stopped429 as e:
        state["status"]="STOP_429";state["errors"].append({"error":"HTTP429","url":str(e)})
    except Exception as e:
        state["status"]="STOP_ERROR";state["errors"].append({"error":str(e)})
    finally:
        atomic_save(p,state)
        print(json.dumps({"status":state["status"],"projects":len(state["source_projects"]),
                          "items":len(state["cards"]),"errors":len(state["errors"]),
                          "artifact":str(p)},ensure_ascii=False))
    if state["status"]!="COMPLETE_SOURCE_ONLY":raise SystemExit(1)
if __name__=="__main__":main()
