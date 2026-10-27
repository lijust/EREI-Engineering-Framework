#!/usr/bin/env python3
"""Public Kite projects catalog sampling, robots-gated; no private project IDs or writes."""
from __future__ import annotations
import json,os,re,time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from lxml import html as lx
from scrapling.fetchers import Fetcher

UA="SAE-DB-public-catalog-research/1.0"
AREAS={"riyadh":35,"eastern-province":15,"jeddah":15}
OUT=Path(os.environ["RUNNER_TEMP"])/"public-kite-project-index.json"
state={"status":"STARTED","schema":"KITE_PUBLIC_PROJECT_INDEX_ROBOTS_GATED_V1",
       "pages":[],"projects":[],"errors":[],"unit_master_writes":0,
       "private_data_accessed":False}
def save():OUT.write_text(json.dumps(state,ensure_ascii=False),encoding="utf-8")
def get(url):
 u=urlsplit(url)
 if u.scheme!="https" or u.hostname!="kite.sa" or not (u.path=="/robots.txt" or u.path.startswith("/en/projects/")):
  raise ValueError("URL_OUT_OF_PUBLISHER_SCOPE")
 r=Fetcher.get(url,retries=1,timeout=25,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("HTTP_429_STOP")
 if str(r.url).split("?")[0]!=url.split("?")[0]:raise ValueError("OFF_SOURCE_REDIRECT")
 return r
try:
 robots=get("https://kite.sa/robots.txt")
 if int(robots.status)!=200:raise RuntimeError("ROBOTS_HTTP_"+str(robots.status))
 rp=RobotFileParser();rp.parse(robots.body.decode("utf-8","replace").splitlines())
 all_keys=set()
 for area,last_page in AREAS.items():
  for page in range(1,last_page+1):
   url="https://kite.sa/en/projects/"+area+("?page="+str(page) if page>1 else "")
   if not rp.can_fetch(UA,url):
    state["errors"].append({"url_path":urlsplit(url).path,"page":page,"error":"ROBOTS_DISALLOW"})
    continue
   time.sleep(max(3.0,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
   r=get(url)
   if int(r.status)!=200:
    state["errors"].append({"page":page,"area":area,"http":int(r.status)})
    save()
    continue
   root=lx.fromstring(r.body)
   matches=[]
   for a in root.xpath('//a[@href]'):
    link=a.get("href") or ""
    if not re.fullmatch(r"/en/projects/"+re.escape(area)+r"/[0-9]{1,9}/?",link):continue
    title=" ".join(" ".join(a.itertext()).split())
    project_id=link.rstrip("/").split("/")[-1]
    if not title or not project_id:continue
    if (area,project_id) in all_keys:continue
    all_keys.add((area,project_id))
    matches.append({"area":area,"publisher_project_id":project_id,"url":"https://kite.sa"+link,"listing_text":title[:450]})
   state["projects"].extend(matches)
   state["pages"].append({"area":area,"page":page,"projects":len(matches),"source_status":200})
   save()
   print("INDEX_PAGE "+json.dumps({"area":area,"page":page,"projects":len(matches)},separators=(",",":")))
 state["status"]="COMPLETED_PUBLIC_INDEX"
except Exception as exc:
 state["status"]="HALTED_HTTP429" if "HTTP_429_STOP" in str(exc) else "STOPPED_WITH_ERROR"
 state["errors"].append({"error":type(exc).__name__+": "+str(exc)[:160]})
finally:
 save()
 print("INDEX_SUMMARY "+json.dumps({"status":state["status"],"pages":len(state["pages"]),"total_public_projects":len(state["projects"]),"errors":state["errors"][:10]},ensure_ascii=False,separators=(",",":")))
 # The public source itself is already public; this line supports private local matching
 # without putting private canonical project names/IDs on GitHub.
 for i in range(0,len(state["projects"]),35):
  print("PROJECT_PAIRS_JSON "+json.dumps(state["projects"][i:i+35],ensure_ascii=False,separators=(",",":")))
