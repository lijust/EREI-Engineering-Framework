#!/usr/bin/env python3
"""Sakani public developer/project API structure probe for real individual units.

Read only and robots gated, source first, no master records written. Reject
non-200 responses, stop at HTTP 429. Probe only public, independently observed
source endpoints and two known first-party project pages.
"""
from __future__ import annotations
import json, re, time, os
from pathlib import Path
from datetime import datetime, timezone
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
from html.parser import HTMLParser

BASE="https://sakani.sa"
UA="Public-Saudi-Unit-Api-Source-Discovery/1.0 (+https://github.com/lijust/EREI-Engineering-Framework)"
PATHS=[
"/mainIntermediaryApi/v4/projects/1312?include=amenities,projects_amenities,developer,project_unit_types",
"/mainIntermediaryApi/v4/projects/1049?include=amenities,projects_amenities,developer,project_unit_types",
"/mainIntermediaryApi/v4/units/961368",
"/app/offplan-projects/1312",
"/app/offplan-projects/1049",
]
class H429(Exception):pass
class Tags(HTMLParser):
    def __init__(self):
        super().__init__();self.scripts=[]
    def handle_starttag(self,tag,attrs):
        x=dict(attrs)
        if tag=="script" and x.get("src"):self.scripts.append(x["src"])

def get(url):
    from scrapling.fetchers import Fetcher
    x=urlparse(url)
    if x.scheme!="https" or x.hostname!="sakani.sa" or x.port or x.username or x.password:
        raise ValueError("Off-source URL")
    response=Fetcher.get(url,timeout=25,retries=0,follow_redirects="safe",headers={"User-Agent":UA})
    status=int(response.status)
    if status==429:raise H429(url)
    if status!=200:raise ValueError("HTTP_"+str(status))
    if urlparse(str(response.url)).hostname!="sakani.sa":raise ValueError("Off-host redirect")
    body=response.body
    if not isinstance(body,bytes) or not 0<len(body)<7_500_000:raise ValueError("Body missing or too long")
    return body.decode("utf-8",errors="replace")

def walk_keys(x, depth=0, acc=None):
    if acc is None:acc=[]
    if depth>2 or len(acc)>100:return acc
    if isinstance(x,dict):
        for k,v in x.items():
            if len(acc)>100:break
            if any(s in str(k).lower() for s in ("unit","price","model","project","stock","available","booking")):
                acc.append({"key":str(k)[:65],"type":type(v).__name__,
                           "items":len(v) if isinstance(v,(list,dict)) else None})
            if depth<2 and isinstance(v,(dict,list)):
                walk_keys(v,depth+1,acc)
    elif isinstance(x,list):
        for v in x[:2]:walk_keys(v,depth+1,acc)
    return acc

def main():
    p=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"sakani-original-api-shape-probe.json"
    state={"schema":"SAKANI_PUBLIC_ORIGINAL_API_UNIT_DISCOVERY_V1","date":datetime.now(timezone.utc).isoformat(),
           "source":BASE,"probes":[],"original_javascript_assets":[],"canonical_writes":0,"status":"STARTED"}
    try:
        robots=get(BASE+"/robots.txt")
        r=RobotFileParser();r.parse(robots.splitlines())
        for path in PATHS:
            url=BASE+path
            if not r.can_fetch(UA,url):
                state["probes"].append({"url":url,"status":"ROBOTS_DISALLOW"});continue
            time.sleep(max(2.5,float(r.crawl_delay(UA) or r.crawl_delay("*") or 0)))
            try:body=get(url)
            except H429:raise
            except Exception as e:
                state["probes"].append({"url":url,"status":str(e)[:100]});continue
            result={"url":url,"status":"HTTP200","body_size":len(body)}
            try:
                j=json.loads(body)
                result.update(data_kind=type(j).__name__,public_collection_keys=walk_keys(j))
            except (ValueError,TypeError):
                p=Tags();p.feed(body)
                result.update(public_script_urls=[s for s in p.scripts if s.startswith("/")][:35],
                              possible_unit_route_expressions=sorted(set(re.findall(
                               r'[/]mainIntermediaryApi[/][^"\x27 ]{0,120}',body)))[:15])
            state["probes"].append(result)
        state["status"]="COMPLETE_SOURCE_ONLY"
    except H429 as e:
        state["status"]="STOP_429";state["error"]=str(e)
    except Exception as e:
        state["status"]="STOP_ERROR";state["error"]=str(e)[:180]
    finally:
        p.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print(json.dumps({"status":state["status"],"probes":len(state["probes"]),"output":str(p)},ensure_ascii=False))
    if state["status"]!="COMPLETE_SOURCE_ONLY":raise SystemExit(1)
if __name__=="__main__":main()
