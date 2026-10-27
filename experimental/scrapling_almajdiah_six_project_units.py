#!/usr/bin/env python3
"""Six public original Almajdiah developer-project inventory API snapshots.

Only firstparty unit listing cards; no private DB access. Robots both firstparty
public hostnames explicitly permit visits. HTTP429 aborts ALL requests.
No authentication, scraping of protected data, or proxy rotation.
"""
from __future__ import annotations
import json, os, time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from pathlib import Path
from scrapling.fetchers import Fetcher

HOST="etmaam.almajdiah.com"
PUBLISHER_PROJECTS={"153":"120","2":"150","119":"118","156":"124","161":"130","195":"156"}
ROOT=f"https://{HOST}/api/client/v1/projects/"
UA="Open-source-Scrapling-Public-Demo/0.1"
OUT=Path(os.environ["RUNNER_TEMP"])/"public-almajdiah-six-projects-cards.json"
state={"schema":"PUBLIC_ALMAJDIAH_SIX_ORIGINAL_PROJECTS_ITEMIZED_UNITS_V1","items":[],
       "project_page_receipts":[],"status":"STARTED",
       "private_database_accessed":False,"master_writes":0}
def save():
    OUT.write_text(json.dumps(state,ensure_ascii=False),encoding="utf-8")
def get(url, valid_path):
    p=urlsplit(url)
    if p.scheme!="https" or p.hostname!=HOST or p.path!=valid_path or p.username or p.password:
        raise ValueError("Source path/host out of expected firstparty range")
    r=Fetcher.get(url,retries=1,timeout=25,follow_redirects="safe",
                  headers={"User-Agent":UA,"Accept":"application/json"})
    if int(r.status)==429:raise RuntimeError("HTTP_429_GLOBAL_STOP")
    if int(r.status)!=200:raise ValueError("HTTP_"+str(r.status))
    p=urlsplit(str(r.url))
    if p.hostname!=HOST or p.path!=valid_path:raise ValueError("Off-origin redirect")
    return r.body
try:
    robots=get(f"https://{HOST}/robots.txt","/robots.txt")
    rp=RobotFileParser()
    rp.parse(robots.decode("utf8","replace").splitlines())
    delay=max(2.5,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0))
    for pid,code in PUBLISHER_PROJECTS.items():
        base=ROOT+pid
        if not rp.can_fetch(UA,base):raise ValueError("ROBOTS_DISALLOW_"+pid)
        page=0
        url=base
        seen=set()
        while url is not None and page<25:
            time.sleep(delay)
            data=json.loads(get(url,urlsplit(base).path))
            project=data.get("project")
            if not isinstance(project,dict) or str(project.get("id"))!=pid or str(project.get("code"))!=code:
                raise ValueError("Publisher_project_mismatch_"+pid)
            group=data.get("units")
            if group is None:
                print("PROJECT_NO_UNIT_LIST "+json.dumps({"project_id":pid,"publisher_code":code,"units":None}))
                url=None
                break
            if not isinstance(group,dict) or not isinstance(group.get("data"),list):
                raise ValueError("No firstparty itemized units for project "+pid)
            rows=group["data"]
            page+=1
            for item in rows:
                if not isinstance(item,dict) or not isinstance(item.get("id"),int):raise ValueError("Missing physical unit ID")
                if item["id"] in seen:raise ValueError("Duplicate original physical unit id")
                seen.add(item["id"])
                record={k:item.get(k) for k in (
                    "id","unit_number","building_name","floor","floor_text","room_count",
                    "bathroom_count","area","total_area","special_area","price_before_tax",
                    "price_after_tax","tax_value","website_price_text",
                    "status","status_text","sale_type","available_for_rent",
                )}
                record["publisher_project_id"]=pid
                record["publisher_project_code"]=code
                record["original_project_url"]="https://almajdiah.com/projects/"+pid
                state["items"].append(record)
            meta=group.get("meta") or {}
            state["project_page_receipts"].append({"project_id":pid,"project_code":code,
                "page":page,"total":meta.get("total"),"last_page":meta.get("last_page"),
                "items":len(rows)})
            save()
            for i in range(0,len(rows),10):
                print("PROJECT_UNIT_ITEMS "+json.dumps(state["items"][-len(rows):][i:i+10],ensure_ascii=False,separators=(",",":")))
            print("PROJECT_PAGE_REPORT "+json.dumps(state["project_page_receipts"][-1],separators=(",",":")))
            nxt=(group.get("links") or {}).get("next")
            if nxt is not None:
                q=urlsplit(str(nxt))
                if q.scheme!="https" or q.hostname!=HOST or q.path!=urlsplit(base).path or not q.query or nxt==url:
                    raise ValueError("Unsafe, repeated or missing pagination URL")
            url=nxt
        if url is not None:raise ValueError("MAX_PAGES_INCOMPLETE")
        print("PROJECT_COMPLETE_REPORT "+json.dumps({"project_id":pid,"source_units":len(seen)},separators=(",",":")))
    state["status"]="COMPLETE_FIRSTPARTY_6_PROJECTS"
except Exception as e:
    state["status"]="STOPPED_HTTP_429" if "HTTP_429_GLOBAL_STOP" in str(e) else "SOURCE_FAILED_CLOSED"
    state["error_type"]=type(e).__name__
    state["error_message"]=str(e)[:160]
finally:
    save()
    print("PROJECT_FINAL_REPORT "+json.dumps({"status":state["status"],"total_cards":len(state["items"]),
          "page_receipts":len(state["project_page_receipts"]),"error":state.get("error_message"),
          "zero_master_writes":True},ensure_ascii=False,separators=(",",":")))
