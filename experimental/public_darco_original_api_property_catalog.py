#!/usr/bin/env python3
"""Source-only Darco public property/project API fact extraction, no private SAE project or unit IDs."""
import json,os,re,time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
ROOT="https://darco.com.sa";HOST="darco.com.sa";UA="SAE-DB-public-Darco-original-API-audit/1.0"
ENDPOINTS=["/api/projects","/api/properties"]
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"darco_exact_original_public_api_properties_20261028.json"
s={"status":"START","source_host":HOST,"publisher_projects":[],"publisher_properties":[],"errors":[],"private_mapping":False,"canonical_writes":0}
def save():OUT.write_text(json.dumps(s,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def get(url):
 p=urlsplit(url)
 if p.scheme!="https" or p.hostname!=HOST or p.path not in ["/robots.txt",*ENDPOINTS]:raise ValueError("SOURCE_SCOPE")
 r=Fetcher.get(url,retries=0,timeout=30,follow_redirects="safe",headers={"User-Agent":UA,"Accept":"application/json"})
 if int(r.status)==429:raise RuntimeError("HTTP_429_GLOBAL_STOP")
 if int(r.status)!=200:raise RuntimeError("HTTP_"+str(r.status))
 if urlsplit(str(r.url)).hostname!=HOST:raise ValueError("SOURCE_REDIRECT")
 return r
try:
 rb=get(ROOT+"/robots.txt")
 rp=RobotFileParser();rp.parse(rb.body.decode("utf8","replace").splitlines())
 for path in ENDPOINTS:
  url=ROOT+path
  if not rp.can_fetch(UA,url):raise RuntimeError("ROBOTS_DISALLOW_"+path)
  time.sleep(max(3,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
  r=get(url);data=json.loads(r.body)
  if not isinstance(data,list):raise ValueError("SOURCE_SHAPE_NOT_LIST_"+path)
  if path=="/api/projects":
   allow=("id","projectNumber","slug","projectCode","name","nameAr","city","cityAr","neighborhood","neighborhoodAr","totalProperties","totalUnits","priceRange","status","projectType","developerId")
   s["publisher_projects"]=[{k:q.get(k) for k in allow} for q in data if isinstance(q,dict)]
  else:
   allow=("id","title","titleAr","type","locationAr","projectId","totalFloors","totalUnits","city","cityAr","neighborhood","neighborhoodAr","propertyNumber","status","projectType","publishStatus","isPublished","publishedAt")
   s["publisher_properties"]=[{k:q.get(k) for k in allow} for q in data if isinstance(q,dict)]
  save()
  print("DARCO_PUBLIC_API_RESPONSE "+json.dumps({"path":path,"records":len(data),
        "fields":list(data[0]) if data else []},ensure_ascii=False),flush=True)
 s["status"]="COMPLETE_REAL_ORIGINAL_SOURCE_API"
except Exception as e:
 s["status"]="STOPPED_429" if "HTTP_429_GLOBAL_STOP" in str(e) else "STOPPED_ERROR"
 s["errors"].append(type(e).__name__+": "+str(e)[:200])
finally:
 save()
 print("DARCO_ORIGINAL_API_SUMMARY "+json.dumps({"status":s["status"],"projects":len(s["publisher_projects"]),"properties":len(s["publisher_properties"]),"errors":s["errors"],"master_writes":0},ensure_ascii=False),flush=True)
 for k in ["publisher_projects","publisher_properties"]:
  for a in range(0,len(s[k]),12):print("DARCO_ORIGINAL_"+k.upper()+"_JSON "+json.dumps(s[k][a:a+12],ensure_ascii=False,separators=(",",":")),flush=True)
if s["status"]!="COMPLETE_REAL_ORIGINAL_SOURCE_API":raise SystemExit(2)
