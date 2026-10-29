#!/usr/bin/env python3
"""Public original Raz Elevate numbered unit listing audit; source-only.
Only public project and units text, no contact forms, PII, canonical DB writes.
"""
import json,os,re,time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from scrapling.fetchers import Fetcher
ROOT="https://www.razre.sa"
TARGET="/com/4"
UA="SAE-public-raz-original-unit-research/1.0"
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"raz-elevate-original-com4-unit-cards.json"
s={"publisher":"Raz Real Estate","source_url":ROOT+TARGET,"status":"STARTED",
   "project_header":"","source_units_text":"","headers":[],"parts":[],"errors":[],"canonical_writes":0}
def fetch(path):
 url=ROOT+path
 if path not in ("/robots.txt",TARGET):raise ValueError("NOT_ALLOWED")
 r=Fetcher.get(url,retries=0,timeout=35,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("STOP_HTTP429")
 if int(r.status)==404 and path=="/robots.txt":return None
 if int(r.status)!=200:raise RuntimeError("HTTP_"+str(r.status))
 if urlsplit(str(r.url)).hostname not in ("www.razre.sa","razre.sa"):raise RuntimeError("OFF_DOMAIN")
 if len(r.body)>6_000_000:raise RuntimeError("BODY_EXCEEDS_LIMIT")
 return r.body.decode("utf8","replace")
try:
 rp=RobotFileParser();rb=fetch("/robots.txt")
 rp.parse(rb.splitlines() if rb is not None else [])
 if not rp.can_fetch(UA,ROOT+TARGET):raise RuntimeError("ROBOTS_DISALLOW")
 time.sleep(max(3,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
 html=fetch(TARGET)
 soup=BeautifulSoup(html,"lxml")
 for t in soup(["script","style","noscript","svg","form"]):t.decompose()
 text=soup.get_text(" ",strip=True)
 start=text.find("وحـــدات")
 if start<0:start=text.find("وحدات المشروع")
 if start<0:raise ValueError("NO_ORIGINAL_UNIT_CARD_TEXT")
 end=text.find("سجل اهتمامك",start)
 if end<start:end=len(text)
 s["project_header"]=text[:start][-2000:]
 s["source_units_text"]=text[start:end][:26000]
 s["headers"]=[x.get_text(" ",strip=True)[:100] for x in soup.find_all(["h1","h2","h3","h4"])][:150]
 marker=re.compile("رقم الوحدة")
 for t in soup.find_all(string=marker):
  par=t.parent
  top=par
  for _ in range(4):
   if top.parent and len(top.parent.get_text(" ",strip=True))<1100:top=top.parent
  label=top.get_text(" ",strip=True)
  if len(label)>1400:label=label[:1400]
  if label not in s["parts"]:s["parts"].append(label)
 s["status"]="COMPLETE_SOURCE_ONLY"
except Exception as exc:
 s["status"]="STOPPED_SOURCE_ERROR";s["errors"].append(type(exc).__name__+": "+str(exc)[:250])
finally:
 OUT.write_text(json.dumps(s,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print(json.dumps({"status":s["status"],"headers":len(s["headers"]),"parts":len(s["parts"]),"text_chars":len(s["source_units_text"]),"errors":s["errors"]},ensure_ascii=False),flush=True)
if s["status"]!="COMPLETE_SOURCE_ONLY":raise SystemExit(1)
