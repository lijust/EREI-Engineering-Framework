#!/usr/bin/env python3
"""Source-only discovery of publicly indexed Almajdiah project API list, never unit personal info."""
import json,os,time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
UA="SAE-DB-public-unit-research/1.0"
HOST="etmaam.almajdiah.com"
ENDPOINTS=["https://etmaam.almajdiah.com/api/client/v1/projects","https://etmaam.almajdiah.com/api/client/v1/projects?per_page=100"]
OUT=Path(os.environ["RUNNER_TEMP"])/"public-almajdiah-project-catalog-discovery.json"
state={"status":"STARTED","endpoints":[],"errors":[],"canonical_writes":0,"private_data":False}
def save():OUT.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf-8")
def fetch(url):
 u=urlsplit(url)
 if u.scheme!="https" or u.hostname!=HOST or u.path not in ("/robots.txt","/api/client/v1/projects"):raise ValueError("OUT_OF_SCOPE_URL")
 r=Fetcher.get(url,retries=1,timeout=25,follow_redirects="safe",headers={"User-Agent":UA,"Accept":"application/json"})
 if int(r.status)==429:raise RuntimeError("HTTP_429_GLOBAL_HALT")
 if urlsplit(str(r.url)).hostname!=HOST:raise RuntimeError("OFFSITE_REDIRECT")
 return r
try:
 robots=fetch("https://"+HOST+"/robots.txt")
 if int(robots.status)!=200:raise RuntimeError("ROBOTS_UNAVAILABLE_"+str(robots.status))
 rp=RobotFileParser();rp.parse(robots.body.decode("utf-8","replace").splitlines())
 for url in ENDPOINTS:
  if not rp.can_fetch(UA,url):
   state["endpoints"].append({"url":url,"status":"ROBOTS_DISALLOW"});continue
  time.sleep(max(3.,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
  r=fetch(url)
  record={"url":url,"http":int(r.status),"size":len(r.body),"structure":None,"items":[]}
  if int(r.status)==200:
   try:
    data=json.loads(r.body)
    record["structure"]={k:str(type(v).__name__) for k,v in data.items()} if isinstance(data,dict) else str(type(data).__name__)
    collection=data.get("data") or data.get("projects") or data.get("items") if isinstance(data,dict) else data
    if isinstance(collection,dict):collection=collection.get("data") or collection.get("items") or []
    if isinstance(collection,list):
     for p in collection[:150]:
      if not isinstance(p,dict):continue
      record["items"].append({k:p.get(k) for k in ("id","name","name_ar","name_en","title","project_number","project_name","code","slug","city","units_count") if k in p})
    else:record["raw_keys"]=list(data.keys())[:30] if isinstance(data,dict) else None
   except Exception as exc:record["parse_error"]=str(exc)[:100]
  state["endpoints"].append(record);save()
 state["status"]="COMPLETE_SOURCE_INDEX_CHECKS"
except Exception as exc:
 state["status"]="STOPPED_429" if "HTTP_429_GLOBAL" in str(exc) else "STOPPED_ERROR"
 state["errors"].append({"error":type(exc).__name__+": "+str(exc)[:200]})
finally:
 save()
 print("ALMAJDIAH_PROJECT_INDEX "+json.dumps(state,ensure_ascii=False,separators=(",",":")))
