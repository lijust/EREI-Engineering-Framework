#!/usr/bin/env python3
"""Public, robots-gated Scrapling JS XHR schema discovery for Saudi real-estate publisher pages.
No private SAE DB ids/records; captures only publicly emitted firstparty JSON field names and array counts.
"""
import json, os, time, re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher, StealthySession
UA="SAE-public-sakani-unit-api-discovery/1.0"
URLS=[
 "https://sakani.sa/app/offplan-projects/35",
 "https://sakani.sa/app/offplan-projects/650?lang=ar",
 "https://sakani.sa/app/offplan-projects/1540",
 "https://sakani.sa/app/offplan-projects/1515?lang=ar",
 "https://sakani.sa/app/offplan-projects/115",
 "https://sakani.sa/app/offplan-projects/120?lang=ar",
 "https://sakani.sa/app/offplan-projects/40?lang=ar",
 "https://sakani.sa/app/offplan-projects/666"
]
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"sakani8_source_only_original_xhr_api_shapes_20261028.json"
state={"status":"STARTED","requests":len(URLS),"pages":[],"errors":[],"source_only":True,"canonical_writes":0}
def save():OUT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def arrays(obj,p="$",depth=0):
 if depth>5:return []
 found=[]
 if isinstance(obj,list):
  found.append({"json_path":p,"length":len(obj),"keys":list(obj[0])[:30] if obj and isinstance(obj[0],dict) else []})
  if obj:found+=arrays(obj[0],p+"[0]",depth+1)
 if isinstance(obj,dict):
  for k,v in list(obj.items())[:80]:
   if isinstance(v,(dict,list)):found+=arrays(v,p+"."+str(k),depth+1)
 return found[:35]
def robot_get(host):
 u="https://"+host+"/robots.txt"
 r=Fetcher.get(u,retries=0,timeout=25,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("HTTP_429_GLOBAL_STOP")
 if int(r.status)!=200 or urlsplit(str(r.url)).hostname!=host:return None
 rp=RobotFileParser();rp.parse(r.body.decode("utf8","replace").splitlines())
 return rp
try:
 for i,url in enumerate(URLS):
  host=urlsplit(url).hostname
  entry={"publisher_page":url,"source_host":host,"index":i+1,"xhr_shapes":[]}
  try:
   robots=robot_get(host)
   if robots is None:
    entry["status"]="SKIP_ROBOTS_UNAVAILABLE"
    state["pages"].append(entry);save();continue
   if not robots.can_fetch(UA,url):
    entry["status"]="SKIP_ROBOTS_DISALLOW"
    state["pages"].append(entry);save();continue
   time.sleep(max(3,float(robots.crawl_delay(UA) or robots.crawl_delay("*") or 0)))
   with StealthySession(record_requests=True,max_recorded_requests=300) as browser:
    page=browser.fetch(url,network_idle=True)
    if int(page.status)==429:raise RuntimeError("HTTP_429_GLOBAL_STOP")
    if int(page.status)!=200:entry["status"]="PROJECT_HTTP_"+str(page.status)
    elif urlsplit(str(page.url)).hostname!=host:entry["status"]="OFF_SOURCE_REDIRECT"
    else:
     candidates=[]
     for rec in browser.network.search(limit=None,include_static=False):
      if int(rec.status)==429:raise RuntimeError("HTTP_429_GLOBAL_STOP")
      if int(rec.status)!=200:continue
      parsed=urlsplit(str(rec.url))
      if parsed.hostname!=host and not parsed.hostname.endswith("."+host):continue
      metadata=getattr(rec,"meta",{}) or {}
      if metadata.get("resource_type") not in ("xhr","fetch"):continue
      raw=getattr(rec,"body",b"")
      if not isinstance(raw,bytes) or not raw or len(raw)>2_000_000:continue
      try:obj=json.loads(raw)
      except Exception:continue
      rows=[x for x in arrays(obj) if x["length"]>0]
      if rows:
       candidates.append({"source_path":parsed.path,"source_host":parsed.hostname,"arrays":rows[:15],
                          "top_keys":list(obj)[:35] if isinstance(obj,dict) else [],
                          "sample_values_persisted":False})
     unique={}
     for c in candidates:unique.setdefault(c["source_host"]+c["source_path"],c)
     entry["xhr_shapes"]=list(unique.values())[:30]
     entry["status"]="SOURCE_ONLY_COMPLETE"
  except Exception as ex:
   if "HTTP_429_GLOBAL_STOP" in str(ex):raise
   entry["status"]="SKIPPED_SOURCE_ERROR"
   entry["source_error"]=type(ex).__name__+": "+str(ex)[:180]
  state["pages"].append(entry);save()
  print("SOURCE_XHR_PROGRESS "+json.dumps({"i":i+1,"host":host,"state":entry["status"],
                                        "api_candidates":len(entry["xhr_shapes"])},ensure_ascii=False),flush=True)
 state["status"]="COMPLETE_PUBLIC_XHR_DISCOVERY"
except Exception as e:
 state["status"]="STOPPED_429" if "HTTP_429_GLOBAL_STOP" in str(e) else "STOPPED_SOURCE_ERROR"
 state["errors"].append(str(e)[:220])
finally:
 save()
 print("SOURCE_XHR_SUMMARY "+json.dumps({"status":state["status"],"pages":len(state["pages"]),
        "api_endpoints":sum(len(p["xhr_shapes"]) for p in state["pages"]),"errors":state["errors"]},ensure_ascii=False),flush=True)
 for p in state["pages"]:
  if p["xhr_shapes"]:print("FIRSTPARTY_XHR_ARRAY_SHAPES "+json.dumps(p,ensure_ascii=False,separators=(",",":")),flush=True)
if state["status"]!="COMPLETE_PUBLIC_XHR_DISCOVERY":raise SystemExit(2)
