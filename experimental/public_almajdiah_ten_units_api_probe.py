#!/usr/bin/env python3
"""Probe firstparty Almajdiah project per-unit API schema for 232 Khayala and new public IDs."""
from pathlib import Path
from urllib.robotparser import RobotFileParser
from urllib.parse import urlsplit
from scrapling.fetchers import Fetcher
import os,json,time
UA="SAE-DB-public-firstparty-unit-api-probe/1.0"
HOST="etmaam.almajdiah.com"
IDS=["232","229","234","239","248","203","210","218","221","241"]
OUT=Path(os.environ["RUNNER_TEMP"])/"almajdiah_ten_source_unit_api_probe.json"
state={"status":"STARTED","projects":[],"errors":[],"private_mapping":False,"unit_db_writes":0}
def save():OUT.write_text(json.dumps(state,ensure_ascii=False),encoding="utf-8")
def get(url):
 p=urlsplit(url)
 if p.scheme!="https" or p.hostname!=HOST or (p.path!="/robots.txt" and p.path not in ["/api/client/v1/projects/"+i for i in IDS]):raise ValueError("OUTSIDE_PUBLIC_API_SCOPE")
 r=Fetcher.get(url,retries=1,timeout=30,follow_redirects="safe",headers={"User-Agent":UA,"Accept":"application/json"})
 if int(r.status)==429:raise RuntimeError("429_GLOBAL_STOP")
 if urlsplit(str(r.url)).hostname!=HOST:raise ValueError("OFF_PUBLISHER_REDIRECT")
 return r
try:
 rob=get("https://"+HOST+"/robots.txt")
 if int(rob.status)!=200:raise RuntimeError("NO_ROBOTS_"+str(rob.status))
 rp=RobotFileParser();rp.parse(rob.body.decode("utf-8","replace").splitlines())
 for project in IDS:
  url="https://"+HOST+"/api/client/v1/projects/"+project
  if not rp.can_fetch(UA,url):
   state["projects"].append({"id":project,"status":"ROBOTS_DISALLOW"});continue
  time.sleep(max(3.,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
  r=get(url)
  rec={"id":project,"http":int(r.status),"bytes":len(r.body),"url":url}
  if int(r.status)==200:
   doc=json.loads(r.body)
   p=doc.get("project") or {}
   units=doc.get("units")
   rec["identity"]={k:p.get(k) for k in ["id","name","name_ar","name_en","code","units_count","unit_count","unit_count_text"] if k in p}
   rec["unit_list_type"]="null" if units is None else type(units).__name__
   if isinstance(units,dict):
    rec["unit_keys"]=list(units.keys())
    rec["unit_metadata"]={k:units.get(k) for k in ("current_page","last_page","per_page","total","next_page_url") if k in units}
    arr=units.get("data") or []
    rec["unit_count_first_page"]=len(arr)
    rec["sample_safe_units"]=[{k:x.get(k) for k in ["id","building_name","unit_number","floor","room_count","bathroom_count","total_area","area","price_before_tax","status"] if k in x} for x in arr[:3] if isinstance(x,dict)]
   else:rec["unit_keys"]=[]
  state["projects"].append(rec);save()
  print("SOURCE_API_PROJECT "+json.dumps(rec,ensure_ascii=False,separators=(",",":")))
 state["status"]="COMPLETE_SOURCE_PROJECT_PROBE"
except Exception as ex:
 state["status"]="STOPPED_429" if "429_GLOBAL" in str(ex) else "STOPPED_ERROR"
 state["errors"].append({"error":type(ex).__name__+": "+str(ex)[:200]})
finally:
 save()
 print("SOURCE_API_SUMMARY "+json.dumps({"status":state["status"],"projects_checked":len(state["projects"]),"list_non_null":sum(x.get("unit_list_type")=="dict" for x in state["projects"]),"errors":state["errors"]},ensure_ascii=False,separators=(",",":")))
