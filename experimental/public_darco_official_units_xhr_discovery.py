#!/usr/bin/env python3
"""Public Darco official /units page XHR response shape: firstparty individually coded inventory.
Browser only public pages, robots-gated, no private SAE mapping, no writes.
"""
import json,os,re,time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher,StealthySession
ROOT="https://darco.com.sa";UA="SAE-DB-firstparty-Darco-physical-unit-API-discovery/1.0"
URL=ROOT+"/units";OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"darco_firstparty_units_api_xhr_shapes.json"
state={"status":"STARTED","public_unit_page":URL,"source_only":True,"xhr":[],"errors":[],"master_writes":0}
def save():OUT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def shapes(obj,depth=0,path="$"):
 if depth>5:return []
 if isinstance(obj,list):
  v=[{"path":path,"length":len(obj),"sample_keys":list(obj[0])[:65] if obj and isinstance(obj[0],dict) else []}]
  if obj:v+=shapes(obj[0],depth+1,path+"[0]")
  return v
 if isinstance(obj,dict):
  out=[]
  for k,v in list(obj.items())[:60]:
   if isinstance(v,(dict,list)):out+=shapes(v,depth+1,path+"."+str(k))
  return out
 return []
try:
 rob=Fetcher.get(ROOT+"/robots.txt",retries=0,timeout=30,follow_redirects="safe",headers={"User-Agent":UA})
 if int(rob.status)==429:raise RuntimeError("GLOBAL_STOP_429")
 if int(rob.status)!=200:raise RuntimeError("ROBOTS_"+str(rob.status))
 rp=RobotFileParser();rp.parse(rob.body.decode("utf8","replace").splitlines())
 if not rp.can_fetch(UA,URL):raise RuntimeError("ROBOTS_DENY")
 time.sleep(max(3,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
 with StealthySession(record_requests=True,max_recorded_requests=500) as b:
  page=b.fetch(URL,network_idle=True)
  if int(page.status)==429:raise RuntimeError("GLOBAL_STOP_429")
  if int(page.status)!=200:raise RuntimeError("PAGE_HTTP_"+str(page.status))
  for x in b.network.search(limit=None,include_static=False):
   if int(x.status)==429:raise RuntimeError("GLOBAL_STOP_429")
   if int(x.status)!=200:continue
   u=urlsplit(str(x.url))
   if u.hostname!="darco.com.sa":continue
   meta=getattr(x,"meta",{}) or {}
   if meta.get("resource_type") not in ("xhr","fetch"):continue
   raw=getattr(x,"body",b"")
   if not isinstance(raw,bytes) or len(raw)>3_000_000 or not raw:continue
   try:obj=json.loads(raw)
   except:continue
   shape=shapes(obj)
   if not shape:continue
   allow_keys=("id","unitNumber","unitNo","number","unitCode","unitType","projectId","propertyId","project","property","floor","floorNumber","area","totalArea","price","salePrice","priceAfterTax","status","bedrooms","bathrooms","buildingNumber","building","projectNumber","unit_number","project_id","property_id")
   def subset(q):
    return {k:q.get(k) for k in allow_keys if k in q} if isinstance(q,dict) else {}
   samples=[]
   if isinstance(obj,list):samples=[subset(q) for q in obj[:3]]
   elif isinstance(obj,dict):
    for k,v in obj.items():
     if isinstance(v,list):samples.extend([subset(q) for q in v[:3]]);break
     if isinstance(v,dict):
      for kk,vv in v.items():
       if isinstance(vv,list):samples.extend([subset(q) for q in vv[:3]]);break
   item={"api_url":str(x.url),"http":int(x.status),"content_bytes":len(raw),"shapes":shape[:30],"safe_public_sample_units":samples[:3]}
   state["xhr"].append(item)
   print("DARCO_OFFICIAL_XHR "+json.dumps(item,ensure_ascii=False,separators=(",",":")),flush=True)
  state["status"]="PUBLIC_ORIGINAL_UNIT_ENDPOINT_DISCOVERED" if state["xhr"] else "NO_JSON_XHR"
except Exception as e:
 state["status"]="STOPPED_429" if "GLOBAL_STOP_429" in str(e) else "SOURCE_ERROR"
 state["errors"].append(type(e).__name__+": "+str(e)[:200])
finally:
 save()
 print("DARCO_OFFICIAL_UNITS_API_SUMMARY "+json.dumps({"status":state["status"],"api_results":len(state["xhr"]),"errors":state["errors"]},ensure_ascii=False),flush=True)
if state["status"] not in ("PUBLIC_ORIGINAL_UNIT_ENDPOINT_DISCOVERED","NO_JSON_XHR"):raise SystemExit(2)
