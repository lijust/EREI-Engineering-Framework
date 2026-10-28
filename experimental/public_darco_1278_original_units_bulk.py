#!/usr/bin/env python3
"""REAL bulk Darco original public API: 1278 genuine unique unit cards, project and building crosswalk.
Read only, robots-gated, NO SAE private mapping, NO developer/project/unit production writes.
Exact original public fields only; private CRM/broker IDs and PII omitted.
"""
import json,os,time,re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
HOST="darco.com.sa";ROOT="https://"+HOST;UA="SAE-DB-public-Darco-official-unit-cards-bulk/1.0"
PATHS=["/api/projects","/api/properties","/api/units"]
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"darco_official_1278_source_only_individual_unit_cards.json"
state={"schema":"FIRSTPARTY_DARCO_ALL_PUBLIC_INDIVIDUAL_UNIT_API_SNAPSHOT_V1","status":"START",
       "publisher_origin":ROOT,"source_urls":[ROOT+p for p in PATHS],
       "projects":[],"buildings":[],"unit_cards":[],"errors":[],"private_canonical_ids":False,"master_writes":0}
def save():OUT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def get(path):
 if path not in PATHS+["/robots.txt"]:raise ValueError("OFF_SCOPE")
 url=ROOT+path
 r=Fetcher.get(url,retries=0,timeout=50,follow_redirects="safe",headers={"User-Agent":UA,"Accept":"application/json"})
 if int(r.status)==429:raise RuntimeError("HTTP429_GLOBAL_STOP")
 if int(r.status)!=200:raise RuntimeError("HTTP_"+str(r.status)+"_"+path)
 if urlsplit(str(r.url)).hostname!=HOST:raise ValueError("UNEXPECTED_HOST_REDIRECT")
 if not r.body or len(r.body)>9_000_000:raise RuntimeError("BAD_RESPONSE_SIZE")
 return r
try:
 robots=get("/robots.txt")
 rp=RobotFileParser();rp.parse(robots.body.decode("utf8","replace").splitlines())
 raws={}
 for path in PATHS:
  if not rp.can_fetch(UA,ROOT+path):raise RuntimeError("ROBOTS_DENY_"+path)
  time.sleep(max(3,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
  r=get(path);obj=json.loads(r.body)
  if not isinstance(obj,list) or not obj:raise ValueError("API_EXPECTED_NONEMPTY_LIST_"+path)
  raws[path]=obj
  print("ORIGINAL_DARCO_API_RETRIEVED "+json.dumps({"path":path,"records":len(obj),"bytes":len(r.body)},separators=(",",":")),flush=True)
 projects=raws["/api/projects"];buildings=raws["/api/properties"];units=raws["/api/units"]
 project_ids={str(q.get("id")) for q in projects};building_by_id={str(q.get("id")):q for q in buildings}
 if len(project_ids)!=len(projects) or len(building_by_id)!=len(buildings):raise ValueError("DUPLICATE_PUBLISHER_PROJECT_OR_BUILDING_ID")
 fields_p=("id","projectNumber","projectCode","nameAr","city","cityAr","neighborhoodAr","totalProperties","totalUnits","status")
 fields_b=("id","projectId","propertyNumber","titleAr","totalFloors","totalUnits","status","buildingCode")
 fields_u=("id","projectId","propertyId","floorId","unitNumber","unitCode","titleAr","unitType","price","cashPrice","area","totalArea","bedrooms","bathrooms","parking","balconies","unitStatus","status","isPublished","publishStatus","propertyNumber","floorNumber","projectNumber","projectNameAr","propertyTitleAr","projectCity","facing","roofArea","livingRooms","slug")
 state["projects"]=[{k:q.get(k) for k in fields_p} for q in projects]
 state["buildings"]=[{k:q.get(k) for k in fields_b} for q in buildings]
 originals=set();missing_fk=0
 for item in units:
  if not isinstance(item,dict):raise TypeError("UNIT_NOT_OBJECT")
  sid=str(item.get("id") or "")
  if not re.fullmatch(r"[0-9a-f-]{36}",sid):raise ValueError("NO_UNIQUE_ORIGINAL_UNIT_UUID")
  if sid in originals:raise ValueError("DUPLICATE_UNIT_UUID_"+sid)
  originals.add(sid)
  p=str(item.get("projectId") or "")
  b=str(item.get("propertyId") or "")
  if p not in project_ids or b not in building_by_id or str(building_by_id[b].get("projectId"))!=p:missing_fk+=1
  sample={k:item.get(k) for k in fields_u}
  if b in building_by_id:
   sample["publisher_original_building_number"]=building_by_id[b].get("propertyNumber")
  state["unit_cards"].append(sample)
  if len(state["unit_cards"])%100==0:save()
 state["source_fk_failures"]=missing_fk
 state["unique_unit_uuid_count"]=len(originals)
 if missing_fk:raise ValueError("INCOMPLETE_DEVELOPER_PROJECT_BUILDING_SOURCE_FKS_"+str(missing_fk))
 state["status"]="COMPLETE_ALL_FIRSTPARTY_INDIVIDUAL_UNITS"
except Exception as e:
 state["status"]="STOPPED_HTTP_429" if "HTTP429_GLOBAL_STOP" in str(e) else "STOPPED_ERROR"
 state["errors"].append(type(e).__name__+": "+str(e)[:210])
finally:
 save()
 by={}
 for x in state["unit_cards"]:
  num=str(x.get("projectNumber") or "")
  if not num:
   p=next((p for p in state["projects"] if p["id"]==x["projectId"]),{})
   num=p.get("projectNumber") or "NO_PROJECT_NUMBER"
  by[num]=by.get(num,0)+1
 print("DARCO_1278_BULK_FIRSTPARTY_SOURCE_SUMMARY "+json.dumps({"status":state["status"],"projects":len(state["projects"]),"buildings":len(state["buildings"]),"individual_uuid_cards":len(state["unit_cards"]),"by_project_number":by,"fk_errors":state.get("source_fk_failures"),"errors":state["errors"],"master_writes":0},ensure_ascii=False,separators=(",",":")),flush=True)
 for name in ("projects","buildings","unit_cards"):
  for i in range(0,len(state[name]),30):
   print("DARCO_1278_REAL_SOURCE_"+name.upper()+"_JSON "+json.dumps(state[name][i:i+30],ensure_ascii=False,separators=(",",":")),flush=True)
if state["status"]!="COMPLETE_ALL_FIRSTPARTY_INDIVIDUAL_UNITS":raise SystemExit(2)
