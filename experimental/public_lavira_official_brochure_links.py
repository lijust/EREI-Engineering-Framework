#!/usr/bin/env python3
"""Firstparty Lavira publisher brochure link discovery, read-only."""
import json,os,re,time,sys
from pathlib import Path
from urllib.parse import urlsplit,urljoin
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
from lxml import html
BASE="https://koohejidevelopment.sa"
PAGES=["lavira","lavira-al-thara","lavira-al-bareh","lavira-al-thuraya","lavira-al-ruaa","lavira-al-jawhara","lavira-al-naseem"]
UA="SAE-DB-official-villa-docs/1.0"
out=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"lavira_firstparty_document_hrefs.json"
s={"status":"START","pages":[],"errors":[],"master_writes":0}
def save():out.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding="utf8")
def get(url):
 r=Fetcher.get(url,retries=0,timeout=42,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("HTTP_429_STOP")
 if urlsplit(str(r.url)).hostname!="koohejidevelopment.sa":raise RuntimeError("OFF_SOURCE_REDIRECT")
 return r
try:
 rb=get(BASE+"/robots.txt")
 if int(rb.status)!=200:raise RuntimeError("ROBOTS_HTTP_"+str(rb.status))
 rp=RobotFileParser();rp.parse(rb.body.decode("utf8","replace").splitlines())
 for name in PAGES:
  url=BASE+"/community/"+name+"/"
  if not rp.can_fetch(UA,url):s["pages"].append({"key":name,"status":"ROBOTS_DISALLOW"});save();continue
  time.sleep(max(3.0,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
  r=get(url);entry={"key":name,"url":url,"http":int(r.status),"pdf_hrefs":[],"external_brochure_links":[],"status":"FETCHED"}
  if int(r.status)==200:
   d=html.fromstring(r.body)
   for a in d.xpath("//a[@href]"):
    h=a.get("href") or ""
    label=" ".join(" ".join(a.itertext()).split())
    full=urljoin(url,h)
    if urlsplit(full).hostname!="koohejidevelopment.sa":continue
    if re.search(r"\.pdf($|\?)",full,re.I) or "brochure" in label.lower():
     entry["pdf_hrefs"].append({"link":full,"text":label[:110]})
   entry["pdf_hrefs"]=list({d["link"]:d for d in entry["pdf_hrefs"]}.values())
  s["pages"].append(entry);save()
  print("LAVIRA_PUBLISHER_PAGE "+json.dumps(entry,ensure_ascii=False,separators=(",",":")))
 s["status"]="COMPLETE_SOURCE_DISCOVERY"
except Exception as e:
 s["status"]="STOPPED_429" if "429" in str(e) else "STOPPED_ERROR"
 s["errors"].append(str(e)[:200])
finally:
 save();print("LAVIRA_PUBLISHER_FINAL "+json.dumps({"status":s["status"],"pages":len(s["pages"]),"pdf_count":sum(len(x.get("pdf_hrefs",[])) for x in s["pages"]),"errors":s["errors"],"writes":0},ensure_ascii=False))
if s["status"]!="COMPLETE_SOURCE_DISCOVERY":sys.exit(2)
