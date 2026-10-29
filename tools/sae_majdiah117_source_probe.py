#!/usr/bin/env python3
"""Read-only Scrapling discovery of *existing* Almajdiah 117 project's original units.

The publisher firstparty ID 184 is already linked to canonical PRJ-001436.
No project/developer creation, no private access, stop on 403/429 and robots.
"""
import asyncio,hashlib,json,time,re
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlparse,urljoin
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
BASE="https://etmaam.almajdiah.com"
API=BASE+"/api/client/v1/projects/184"
UA="SAE-DB-public-unit-study/1.0"
OUT=Path("sae-almajdiah117-firstparty-units.json")
DATA={"schema":"SAE_EXISTING_MAJDIAH117_EXACT_FIRSTPARTY_API_ORIGINAL_SOURCE_V1",
      "canonical_project_id":"PRJ-001436","source_project_id":184,
      "source_main":"https://almajdiah.com/projects/184","api":API,
      "source_id":"SRC-000054","source_capture_utc":datetime.now(timezone.utc).isoformat(),
      "pages":[],"records":[],"errors":[],"writes":0}
def capture(url):
    r=Fetcher.get(url,retries=0,timeout=24,headers={"User-Agent":UA,"Accept":"application/json"})
    code=int(r.status)
    if code in (403,429):raise RuntimeError("STOP_ACCESS_"+str(code))
    if code!=200:raise RuntimeError("HTTP_"+str(code))
    return r.body,code
def valid_url(url):
    a=urlparse(url)
    return a.scheme=="https" and a.hostname=="etmaam.almajdiah.com" and a.path=="/api/client/v1/projects/184"
try:
    robots_url=BASE+"/robots.txt"
    b,_=capture(robots_url)
    rp=RobotFileParser();rp.parse(b.decode("utf8","replace").splitlines())
    DATA["robots_permits"]=rp.can_fetch(UA,API)
    if not DATA["robots_permits"]:raise RuntimeError("ROBOTS_DISALLOW")
    target=API
    visited=set()
    for no in range(25):
        if target in visited or not valid_url(target):raise RuntimeError("NEXT_URL_NOT_WHITELISTED")
        visited.add(target)
        time.sleep(2.4)
        b,_=capture(target)
        data=json.loads(b)
        meta=data.get("project") or {}
        if str(meta.get("id"))!="184":raise RuntimeError("PROJECT_IDENTITY_MISMATCH")
        listed=data.get("units")
        if not listed:
            DATA["pages"].append({"url":target,"units":None,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()})
            DATA["state"]="SOURCE_EXPLICITLY_UNLISTED_UNITS_NULL_OR_EMPTY"
            break
        if not isinstance(listed,dict) or not isinstance(listed.get("data"),list):raise RuntimeError("UNRECOGNIZED_SOURCE_SCHEMA")
        original=listed["data"]
        whitelist=("id","building_name","unit_number","floor","floor_text","room_count","bathroom_count",
            "area","total_area","special_area","price_before_tax","price_after_tax",
            "tax_value","website_price_text","status","status_text","sale_type","available_for_rent",
            "purchased_completed","project_id","building_id")
        extracted=[]
        for v in original:
            if not isinstance(v,dict) or not isinstance(v.get("id"),int):continue
            extracted.append({k:v.get(k) for k in whitelist})
        DATA["records"].extend(extracted)
        DATA["pages"].append({"url":target,"items":len(original),"qualified":len(extracted),
           "sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b),
           "reported_total":(listed.get("meta") or {}).get("total")})
        link=(listed.get("links") or {}).get("next")
        if not link:
            DATA["state"]="SOURCE_EXHAUSTED"
            break
        target=urljoin(target,str(link))
    else:DATA["state"]="MAX_25_PAGES_HOLD"
    codes=[(v.get("building_name"),v.get("unit_number")) for v in DATA["records"]]
    ids=[v.get("id") for v in DATA["records"]]
    DATA["exact_unique_source_id_count"]=len(set(ids))
    DATA["original_building_unit_pair_count"]=len(set(str(v) for v in codes))
    DATA["publisher_explicit_count"]=len(DATA["records"])
except Exception as e:
    DATA["state"]="STOP_NO_IMPORT"
    DATA["errors"].append(str(e)[:350])
OUT.write_text(json.dumps(DATA,ensure_ascii=False,indent=2),encoding="utf8")
print("SAE_MAJDIAH117_RESULT="+json.dumps({k:DATA.get(k) for k in
("state","source_capture_utc","publisher_explicit_count","exact_unique_source_id_count",
 "original_building_unit_pair_count","pages","errors")},ensure_ascii=False),flush=True)
