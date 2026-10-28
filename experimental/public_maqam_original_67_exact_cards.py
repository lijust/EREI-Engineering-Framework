#!/usr/bin/env python3
"""Public Maqam developer original individually coded unit cards, source-only.

Read-only robots-gated Scrapling public HTML, no credentials/PII/canonical writes.
Extract exact original publisher unit card fields without synthetic units or price.
HTTP 429 stops the entire crawl, source observations checkpointed to an artifact.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import json
import os
import re
import time

HOST="maqamco.sa"
BASE="https://maqamco.sa"
UA="Source-Only-Saudi-Property-Index/1.0 (+https://github.com/lijust/EREI-Engineering-Framework)"
TARGETS=[("18","/projects/1",60),("17","/projects/2",4),("19","/projects/3",3)]
RE_UNIT=re.compile(r"رقم\s*الوحدة\s*:\s*([A-Z][0-9]{1,3}|(?:Ground|First|Second)\s+floor\s+\d{2})",re.I)
STATUS=re.compile(r"(متاحة|محجوزة|مباعة|غير متاحة)")
AREA=re.compile(r"المساحة\s*(\d+(?:[.,]\d+)?)\s*م²")
BEDS=re.compile(r"غرف\s*النوم\s*(\d+)")
BATHS=re.compile(r"الحمامات\s*(\d+)")
PRICE=re.compile(r"(\d[\d,]{3,})\s*ر\.س")

class Stop429(Exception):pass

def fetch(path):
    from scrapling.fetchers import Fetcher
    url=BASE+path
    p=urlsplit(url)
    if p.scheme!="https" or p.hostname!=HOST or p.path not in ["/robots.txt"]+[v[1] for v in TARGETS]:
        raise ValueError("Unapproved publisher endpoint")
    resp=Fetcher.get(url,timeout=30,retries=0,follow_redirects="safe",
                     headers={"User-Agent":UA})
    code=int(resp.status)
    if code==429:raise Stop429(url)
    if code!=200:raise ValueError(f"HTTP_{code} from {p.path}")
    if urlsplit(str(resp.url)).hostname!=HOST:raise ValueError("Off-publisher redirect")
    if not isinstance(resp.body,bytes) or not 0<len(resp.body)<6_000_000:raise ValueError("Invalid HTML body")
    return resp.body.decode("utf8",errors="replace")

def parse(original_html, project_no, source_url):
    from bs4 import BeautifulSoup
    tree=BeautifulSoup(original_html,"lxml")
    for elem in tree(["script","style","noscript","svg"]):elem.decompose()
    txt=tree.get_text(" ",strip=True)
    # Search only after the publisher's explicit project inventory section.
    start=txt.find("وحدات المشروع")
    if start<0:raise ValueError("No original unit section")
    end=txt.find("مشاريع مشابهة",start+20)
    if end<0:end=txt.find("موقع المشروع",start+20)
    if end<0:end=len(txt)
    txt=txt[start:end]
    cards=[]
    markers=list(RE_UNIT.finditer(txt))
    for i,m in enumerate(markers):
        section=txt[m.end():markers[i+1].start() if i+1<len(markers) else len(txt)]
        # Usually statuses are inserted immediately before the NEXT unit header.
        # Identify status from last 35 characters preceding current code, if possible.
        prefix=txt[max(0,m.start()-42):m.start()]
        previous_status=STATUS.findall(prefix)
        trailing=STATUS.findall(section)
        status=previous_status[-1] if previous_status else (trailing[-1] if trailing else "")
        area=AREA.search(section)
        beds=BEDS.search(section)
        baths=BATHS.search(section)
        # Only first numeric sale ask in this unit card; NEVER use project starting price.
        price=PRICE.search(section)
        floor=re.search(r"(الدور\s*(?:الأرضي|الأول|الثاني|الثالث|\d+)|الملحق\s*العلوي)",section)
        code=m.group(1).strip()
        item={
          "source_project_no":project_no,
          "source_page_url":source_url,
          "source_unit_code":code,
          "source_floor":floor.group(1) if floor else "",
          "source_area_sqm":float(area.group(1).replace(",",".")) if area else None,
          "source_bedrooms":int(beds.group(1)) if beds else None,
          "source_bathrooms":int(baths.group(1)) if baths else None,
          "source_sale_asking_sar":int(price.group(1).replace(",","")) if price else None,
          "source_status_ar":status,
          "source_excerpt":section[:180],
        }
        cards.append(item)
    return cards,{"cards":len(cards),"unique_codes":len({x["source_unit_code"] for x in cards}),
                   "visible_section_chars":len(txt),"first_card_context":txt[:280]}

def main():
    from urllib.robotparser import RobotFileParser
    out=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"maqam-source-original-numbered-units.json"
    state={"schema":"PUBLIC_MAQAM_ORIGINAL_INDIVIDUAL_UNIT_CARDS_V1",
       "publisher":BASE,"captured_at_utc":datetime.now(timezone.utc).isoformat(),
       "pages":[],"cards":[],"errors":[],"canonical_writes":0,"status":"STARTED"}
    try:
        robots=RobotFileParser()
        try:
            robots.parse(fetch("/robots.txt").splitlines())
        except ValueError as exc:
            if str(exc)!="HTTP_404 from /robots.txt":
                raise
            # RFC 9309: HTTP 404 for robots.txt = unavailable rules, may crawl.
            # This does NOT override HTTP403 or 429 and never follows login paths.
            robots.parse([])
            state["robots_note"]="404_ROBOTS_UNAVAILABLE_RFC9309_ALLOW_PUBLIC_PAGES"
        for name,path,expected in TARGETS:
            url=BASE+path
            if not robots.can_fetch(UA,url):
                state["errors"].append({"url":url,"error":"ROBOTS_DISALLOW"});continue
            time.sleep(max(2.5,float(robots.crawl_delay(UA) or robots.crawl_delay("*") or 0)))
            try:html=fetch(path)
            except Stop429:raise
            except Exception as e:
                state["errors"].append({"url":url,"error":str(e)[:140]});continue
            cards,meta=parse(html,name,url)
            state["cards"].extend(cards)
            state["pages"].append({"project_no":name,"url":url,"expected_source_cards":expected,**meta})
            out.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        state["status"]="COMPLETE_SOURCE_ONLY"
    except Stop429 as e:
        state["status"]="STOP_HTTP429";state["errors"].append({"error":str(e)})
    except Exception as e:
        state["status"]="STOP_ERROR";state["errors"].append({"error":repr(e)})
    finally:
        out.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print(json.dumps({"status":state["status"],"pages":state["pages"],
            "cards":len(state["cards"]),"errors":state["errors"],"artifact":str(out)},ensure_ascii=False))
    if state["status"]!="COMPLETE_SOURCE_ONLY":raise SystemExit(1)

if __name__=="__main__":main()
