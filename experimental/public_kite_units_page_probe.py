#!/usr/bin/env python3
"""Source-only Kite robots + listing/detail HTML shape probe. No database or personal information."""
import json,os,time,re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from html.parser import HTMLParser
from scrapling.fetchers import Fetcher
UA="SAE-DB-public-research/1.0"
HOST="kite.sa"
URLS=["https://kite.sa/en/projects/riyadh","https://kite.sa/en/projects/riyadh/97401"]
OUT=Path(os.environ["RUNNER_TEMP"])/"kite-public-firstparty-page-probe.json"
state={"status":"STARTED","site":"kite.sa","pages":[],"errors":[],"canonical_writes":0,"project_writes":0,"unit_writes":0}
def save(): OUT.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf-8")
def fetch(url):
 p=urlsplit(url)
 if p.scheme!="https" or p.hostname not in (HOST,"www."+HOST) or not p.path.startswith(("/robots.txt","/en/projects/")):raise ValueError("OUT_OF_SCOPE")
 r=Fetcher.get(url,retries=1,timeout=30,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("HTTP_429_GLOBAL_STOP")
 return r
try:
 robots=fetch("https://kite.sa/robots.txt")
 if int(robots.status)!=200:raise RuntimeError("ROBOTS_UNAVAILABLE_HTTP_"+str(robots.status))
 rp=RobotFileParser()
 rp.parse(robots.body.decode("utf-8","replace").splitlines())
 for url in URLS:
  if not rp.can_fetch(UA,url):
   state["errors"].append({"path":urlsplit(url).path,"error":"ROBOTS_DISALLOW"})
   continue
  time.sleep(max(3.0,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
  r=fetch(url)
  if int(r.status)!=200:
   state["errors"].append({"path":urlsplit(url).path,"error":"HTTP_"+str(r.status)})
   continue
  final=urlsplit(str(r.url))
  if final.hostname not in (HOST,"www."+HOST):raise RuntimeError("OFFSITE_REDIRECT")
  html=r.body.decode("utf-8","replace")
  hrefs=list(dict.fromkeys(re.findall(r'href=["\\\']([^"\\\']+)["\\\']',html)))
  project_links=[h for h in hrefs if re.search(r'/(?:en/)?projects/(?:riyadh|jeddah|eastern-province|makkah|madinah)/\\d+/?',h)]
  page_links=[h for h in hrefs if "page=" in h and "projects" in h]
  json_keys=list(dict.fromkeys(re.findall(r'"(?:unit_number|unitNo|unitCode|units|price|area|projectId|project_name)"',html)))[:30]
  state["pages"].append({"path":final.path,"size":len(r.body),"title":re.findall(r'<title>(.*?)</title>',html,re.S)[:1],
     "sample_project_urls":project_links[:45],"pagination_links":page_links[:15],
     "json_field_name_hints":json_keys,"script_next_data_present":'__NEXT_DATA__' in html,
     "unit_text_count":len(re.findall(r'unit',html,re.I)),
     "matched_sample_text":re.sub(r'<[^>]+>'," ",html[:7000])[:700]})
  save()
 state["status"]="COMPLETE_ROBOTS_CHECKED"
except Exception as e:
 state["status"]="HALTED_429" if "429" in str(e) else "STOPPED_WITH_ERROR"
 state["errors"].append({"error":type(e).__name__+": "+str(e)[:130]})
finally:
 save()
 print("PUBLIC_KITE_PROBE "+json.dumps(state,ensure_ascii=False,separators=(",",":")))
