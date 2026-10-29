#!/usr/bin/env python3
"""Read-only Darco exact public unit sources for previously published named projects.
No private database identifiers, credentials, clients, or production writes.
"""
import json,os,time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
ROOT="https://darco.com.sa"
PATHS=("/api/projects","/api/properties","/api/units")
UA="Saudi-Public-Developer-Unit-Research/1.0"
PROJECT_NUMBERS={"603","613","660","204"}
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"darco-existing-source-603-613-660-204-refresh.json"
state={"schema":"DARCO_PUBLIC_EXACT_EXISTING_PROJECT_UNITS_REFRESH",
"publisher_origin":ROOT,"status":"STARTED","project_numbers":sorted(PROJECT_NUMBERS),
"publisher_projects":[],"publisher_buildings":[],"original_unit_cards":[],
"all_api_unit_count":0,"errors":[],"production_writes":0}
def save():
 OUT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def fetch(path):
 if path not in PATHS+("/robots.txt",):raise ValueError("NOT_PUBLIC_SOURCE_ENDPOINT")
 url=ROOT+path
 response=Fetcher.get(url,retries=0,timeout=50,follow_redirects="safe",
    headers={"User-Agent":UA,"Accept":"application/json"})
 code=int(response.status)
 if code==429:raise RuntimeError("HTTP_429_STOP")
 if code!=200:raise ValueError("HTTP_"+str(code)+" "+path)
 if urlsplit(str(response.url)).hostname!="darco.com.sa":raise ValueError("OFF_SOURCE_REDIRECT")
 if not isinstance(response.body,bytes) or len(response.body)>12_000_000:raise ValueError("INVALID_SOURCE_BODY")
 return response.body
try:
 robots=RobotFileParser()
 robots.parse(fetch("/robots.txt").decode("utf8","replace").splitlines())
 raw={}
 for path in PATHS:
  if not robots.can_fetch(UA,ROOT+path):raise ValueError("ROBOTS_DENY_"+path)
  time.sleep(max(3,float(robots.crawl_delay(UA) or robots.crawl_delay("*") or 0)))
  raw[path]=json.loads(fetch(path))
  if not isinstance(raw[path],list):raise ValueError("EXPECTED_SOURCE_API_ARRAY")
  print("PUBLIC_DARCO_API "+json.dumps({"path":path,"count":len(raw[path])}),flush=True)
 projects=raw["/api/projects"]
 building=raw["/api/properties"]
 units=raw["/api/units"]
 selected={str(p.get("id")):p for p in projects
    if str(p.get("projectNumber") or "") in PROJECT_NUMBERS}
 state["publisher_projects"]=[{k:p.get(k) for k in
    ("id","projectNumber","nameAr","projectCode","totalUnits","totalProperties","status")}
    for p in selected.values()]
 bmap={str(b.get("id")):b for b in building}
 state["publisher_buildings"]=[{k:b.get(k) for k in
    ("id","projectId","propertyNumber","buildingCode","titleAr","totalUnits","status")}
    for b in building if str(b.get("projectId")) in selected]
 fields=("id","projectId","propertyId","floorId","unitCode","unitNumber","titleAr","unitType",
 "price","cashPrice","area","totalArea","bedrooms","bathrooms",
 "unitStatus","status","isPublished","publishStatus","floorNumber","propertyNumber")
 seen=set()
 for u in units:
  sid=str(u.get("id"))
  if sid in seen:raise ValueError("REPEATED_SOURCE_UNIT_UUID")
  seen.add(sid)
  p=str(u.get("projectId"))
  if p not in selected:continue
  b=bmap.get(str(u.get("propertyId")))
  row={k:u.get(k) for k in fields}
  row["source_project_number"]=selected[p].get("projectNumber")
  row["source_building_number"]=b.get("propertyNumber") if b else None
  row["building_matches_project"]=bool(b and str(b.get("projectId"))==p)
  state["original_unit_cards"].append(row)
 state["all_api_unit_count"]=len(units)
 state["source_unit_counts_by_project"]={number:sum(x["source_project_number"]==number
       for x in state["original_unit_cards"]) for number in sorted(PROJECT_NUMBERS)}
 state["source_unmatched_building_refs"]=sum(not x["building_matches_project"]
       for x in state["original_unit_cards"])
 state["status"]="COMPLETE_PUBLIC_SOURCE_ONLY"
except Exception as exc:
 state["status"]="STOP_HTTP429" if "HTTP_429_STOP" in str(exc) else "STOP_SOURCE_ERROR"
 state["errors"].append(type(exc).__name__+": "+str(exc)[:300])
finally:
 save()
 print("DARCO_REFRESH "+json.dumps({"status":state["status"],
 "total_api_unit_rows":state["all_api_unit_count"],
 "source_project_counts":state.get("source_unit_counts_by_project",{}),
 "errors":state["errors"]},ensure_ascii=False),flush=True)
if state["status"]!="COMPLETE_PUBLIC_SOURCE_ONLY":raise SystemExit(1)
