#!/usr/bin/env python3
"""Multi-project Almajdiah first-party native paginated UNIT endpoint discovery.

Four EXISTING canonical projects, exact original publisher project IDs. Scrapling
source-only, no unauthorized calls, no synthetic units, stop on 403/429.
"""
import json,time,hashlib
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlparse,urljoin
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
BASE="https://etmaam.almajdiah.com"
ROOT=BASE+"/api/client/v1/projects/"
PUB=[("PRJ-001438",156,206),("PRJ-001439",161,192),("PRJ-001437",119,136),("PRJ-001434",153,133)]
UA="SAE-DB-public-original-unit-survey/1.0"
OUT=Path("sae-majdiah-four-exact-original-unit-inventories.json")
RESULT={"schema":"SAE_MAJDIAH_FOUR_EXISTING_SOURCE_UNIT_INVENTORIES_20261029",
        "utc":datetime.now(timezone.utc).isoformat(),"writes":0,"source_id":"SRC-000054","projects":[]}
def fetch(url):
 r=Fetcher.get(url,retries=0,timeout=24,headers={"User-Agent":UA,"Accept":"application/json"})
 status=int(r.status)
 if status in (403,429):raise RuntimeError("STOP_ALL_SOURCE_HTTP_"+str(status))
 if status!=200:raise RuntimeError("HTTP_"+str(status))
 return r.body
def checked(url,pid):
 u=urlparse(url)
 return u.scheme=="https" and u.hostname=="etmaam.almajdiah.com" and u.path==("/api/client/v1/projects/"+str(pid))
def main():
 try:
  b=fetch(BASE+"/robots.txt")
  rp=RobotFileParser();rp.parse(b.decode("utf-8","replace").splitlines())
 except Exception as e:
  RESULT["stop_reason"]="ROBOTS_NOT_VERIFIABLE_"+type(e).__name__
  OUT.write_text(json.dumps(RESULT,ensure_ascii=False,indent=2))
  return
 for canonical,pid,marketed in PUB:
  url=ROOT+str(pid)
  row={"canonical_project_id":canonical,"publisher_id":pid,"marketed_units_not_assumed":marketed,
       "publisher_exact_project_url":"https://almajdiah.com/projects/"+str(pid),
       "api":url,"source_capture_utc":datetime.now(timezone.utc).isoformat(),"pages":[],"records":[],"errors":[]}
  if not rp.can_fetch(UA,url):
   row["state"]="ROBOTS_DISALLOW";RESULT["projects"].append(row);continue
  visited=set()
  try:
   for page in range(40):
    if url in visited or not checked(url,pid):raise RuntimeError("UNEXPECTED_OR_DUPLICATE_PUBLISHER_NEXT_URL")
    visited.add(url)
    time.sleep(2.0)
    raw=fetch(url);obj=json.loads(raw)
    actual=obj.get("project")
    if not isinstance(actual,dict) or str(actual.get("id"))!=str(pid):
     raise RuntimeError("SOURCE_PROJECT_ID_MISMATCH")
    units=obj.get("units")
    receipt={"path":url,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
    if not units:
     receipt["source_units"]="NULL_OR_EMPTY";row["pages"].append(receipt)
     row["state"]="PUBLISHER_UNLISTED_UNITS";break
    if not isinstance(units,dict) or not isinstance(units.get("data"),list):
     raise RuntimeError("SOURCE_SCHEMA_UNRECOGNIZED")
    batch=units["data"]
    receipt["items"]=len(batch);receipt["reported_total"]=(units.get("meta") or {}).get("total")
    subset=[]
    for item in batch:
     if not isinstance(item,dict) or not isinstance(item.get("id"),int):continue
     if item.get("project_id") not in (None,pid,str(pid)):
      raise RuntimeError("UNIT_ORIGIN_PROJECT_CONFLICT")
     keys=("id","building_id","building_name","unit_number","floor","floor_text","room_count",
           "bathroom_count","area","total_area","special_area","price_before_tax",
           "price_after_tax","tax_value","website_price_text","status","status_text",
           "sale_type","available_for_rent","purchased_completed","project_id")
     subset.append({k:item.get(k) for k in keys})
    row["records"].extend(subset)
    receipt["qualified"]=len(subset);row["pages"].append(receipt)
    nexturl=(units.get("links") or {}).get("next")
    if not nexturl:row["state"]="PUBLISHER_PAGINATION_EXHAUSTED";break
    url=urljoin(url,str(nexturl))
   else:row["state"]="MAX_40_PAGES_HOLD"
  except Exception as e:
   row["state"]="STOP_NO_IMPORT";row["errors"].append(str(e)[:250])
  row["count"]=len(row["records"])
  row["unique_source_ids"]=len({x["id"] for x in row["records"]})
  RESULT["projects"].append(row)
  OUT.write_text(json.dumps(RESULT,ensure_ascii=False,indent=2))
  print("SAE_MAJDIAH_EXACT",json.dumps({k:row.get(k) for k in
    ("canonical_project_id","publisher_id","state","count","unique_source_ids","errors")},ensure_ascii=False),flush=True)
  if any("STOP_ALL_SOURCE_HTTP_" in e for e in row["errors"]):
   RESULT["stop_reason"]="PUBLISHER_ACCESS_CONTROL";break
 RESULT["summary"]={"projects_processed":len(RESULT["projects"]),
   "native_physical_source_records":sum(x.get("count",0) for x in RESULT["projects"]),"production_writes":0}
 OUT.write_text(json.dumps(RESULT,ensure_ascii=False,indent=2))
 print("SAE_MAJDIAH_FOUR_SUMMARY",json.dumps(RESULT["summary"],ensure_ascii=False),flush=True)
if __name__=="__main__":main()
