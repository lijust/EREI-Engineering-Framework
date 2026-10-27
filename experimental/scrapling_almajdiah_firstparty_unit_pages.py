#!/usr/bin/env python3
"""Read published itemized Almajdiah 147 units through its observed public API.

No SAE-DB data or private mappings. Robots checked on etmaam subdomain first.
One HTTP request at a time, >=2.5s delay, stop immediately on HTTP 429.
Publisher asking prices and statuses are HISTORICAL SNAPSHOT, NOT live stock.
"""
from __future__ import annotations
import json, os, re, time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher

PID="183"
PROJECT_URL="https://almajdiah.com/projects/183"
BASE=f"https://etmaam.almajdiah.com/api/client/v1/projects/{PID}"
UA="Open-source-Scrapling-Public-Demo/0.1"
OUTPUT=Path(os.environ["RUNNER_TEMP"])/"public-almajdiah147-firstparty-unit-pages.json"
state={"state":"INIT","publisher_project_id":PID,"publisher_project_url":PROJECT_URL,
       "pages":[],"units":[],"raw_api_bodies_saved":False,"private_data_accessed":False,
       "master_writes":0,"project_ids_or_private_mapping_included":False}
def save():
    OUTPUT.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf-8")

def get(url):
    p=urlsplit(url)
    if p.scheme!="https" or p.hostname!="etmaam.almajdiah.com" or p.path not in ("/robots.txt",f"/api/client/v1/projects/{PID}") or p.username or p.password:
        raise ValueError("URL out of exact publisher project API scope")
    r=Fetcher.get(url,retries=1,follow_redirects="safe",timeout=25,
                  headers={"User-Agent":UA,"Accept":"application/json"})
    if r.status==429: raise RuntimeError("HTTP_429_GLOBAL_STOP")
    if r.status!=200: raise ValueError("Source HTTP "+str(r.status))
    rp=urlsplit(str(r.url))
    if rp.hostname!="etmaam.almajdiah.com": raise ValueError("Off-site redirect")
    return r.body

try:
    robot_txt=get("https://etmaam.almajdiah.com/robots.txt")
    rule=RobotFileParser()
    rule.parse(robot_txt.decode("utf8","replace").splitlines())
    if not rule.can_fetch(UA,BASE):
        state["state"]="ROBOTS_DISALLOW"
    else:
        delay=max(2.5,float(rule.crawl_delay(UA) or rule.crawl_delay("*") or 0))
        url=BASE
        codes=set()
        page=0
        while url is not None and page<15:
            time.sleep(delay)
            obj=json.loads(get(url))
            project=obj.get("project")
            if not isinstance(project,dict) or str(project.get("id"))!=PID:
                raise ValueError("Wrong firstparty project identity")
            units=obj.get("units")
            if not isinstance(units,dict) or not isinstance(units.get("data"),list):
                raise ValueError("No individually identified publisher units")
            page+=1
            meta=units.get("meta") or {}
            link=units.get("links") or {}
            state["pages"].append({"page":page,"current_page":meta.get("current_page"),
                 "last_page":meta.get("last_page"),"per_page":meta.get("per_page"),
                 "published_total":meta.get("total"),"physical_cards":len(units["data"])})
            new=[]
            for item in units["data"]:
                if not isinstance(item,dict) or not str(item.get("id") or ""):
                    raise ValueError("Individual publisher unit id missing")
                key=str(item["id"])
                if key in codes:raise ValueError("Duplicated publisher ID across pages")
                codes.add(key)
                projection={k:item.get(k) for k in (
                    "id","building_name","unit_number","full_name","floor","floor_text",
                    "room_count","bathroom_count","area","special_area","total_area",
                    "price_before_tax","price_after_tax","tax_value","website_price_text",
                    "status","status_text","sale_type","available_for_rent",
                    "purchased_completed"
                )}
                projection["publisher_project_id"]=PID
                projection["publisher_project_code"]=str(project.get("code") or "")
                projection["original_project_url"]=PROJECT_URL
                new.append(projection)
            state["units"].extend(new)
            state["state"]="PARTIAL_SAVED"
            save()
            # Emitting source public unit cards as independently auditable JSON chunks.
            for j in range(0,len(new),10):
                print("SOURCE_CARDS_JSON "+json.dumps(new[j:j+10],ensure_ascii=False,separators=(",",":")))
            print("PAGE_REPORT_JSON "+json.dumps(state["pages"][-1],separators=(",",":")))
            n=link.get("next")
            if n is not None:
                p=urlsplit(str(n))
                if p.hostname!="etmaam.almajdiah.com" or p.path!=urlsplit(BASE).path or not p.query:
                    raise ValueError("Untrusted publisher pagination URL")
                if n==url:raise ValueError("Non-progressing pagination")
            url=n
        state["state"]="COMPLETE_FIRSTPARTY_SOURCE_SNAPSHOT" if url is None else "PARTIAL_MAX_15_PAGES"
except Exception as exc:
    state["state"]="HTTP_429_STOPPED" if "HTTP_429_GLOBAL_STOP" in str(exc) else "SOURCE_ERROR_FAIL_CLOSED"
    state["error_type"]=type(exc).__name__
    state["error_text"]=str(exc)[:160]
finally:
    save()
    print("SOURCE_FINAL_JSON "+json.dumps({
        "state":state["state"],"pages":len(state["pages"]), "cards":len(state["units"]),
        "last_page_report":state["pages"][-1] if state["pages"] else None,
        "error":state.get("error_text"),"master_writes":0,
    },ensure_ascii=False,separators=(",",":")))
