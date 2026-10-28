#!/usr/bin/env python3
"""First-party Al Soliman property-unit markup discovery; robots-gated, source-only."""
import json,os,re,time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
from lxml import html as LX
HOST="www.alsoliman.com.sa"
UA="SAE-DB-public-firstparty-probe/1.0"
OUT=Path(os.environ["RUNNER_TEMP"])/"alsoliman132-public-firstparty-probe.json"
data={"site":HOST,"status":"STARTED","pages":[],"errors":[],"private_data":False,"writes":0}
def save():OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
def fetch(url):
 p=urlsplit(url)
 if p.scheme!="https" or p.hostname!=HOST:raise ValueError("OFF_SCOPE_HOST")
 r=Fetcher.get(url,retries=1,timeout=35,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("GLOBAL_429_HALT")
 return r
try:
 rob=fetch("https://"+HOST+"/robots.txt")
 if int(rob.status)!=200:raise RuntimeError("ROBOTS_NOT_ACCESSIBLE_HTTP_"+str(rob.status))
 rp=RobotFileParser();rp.parse(rob.body.decode("utf-8","replace").splitlines())
 urls=["https://www.alsoliman.com.sa/ar/selling/project/AressCompound132",
       "https://www.alsoliman.com.sa/public/ar/selling/project/AressCompound132"]
 for url in urls:
  if not rp.can_fetch(UA,url):
   data["errors"].append({"url":url,"reason":"ROBOTS_DISALLOWED"});continue
  time.sleep(max(3.0,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
  res=fetch(url)
  doc=res.body.decode("utf-8","replace")
  if urlsplit(str(res.url)).hostname!=HOST:raise RuntimeError("REDIRECTED_OFF_SOURCE")
  page={"url":url,"http":int(res.status),"final_url":str(res.url),
        "html_bytes":len(res.body),"heading":[],
        "candidate_elements":[],"table_count":0,"table_samples":[],"meta_items":[],"dom_sample":[]}
  if int(res.status)==200:
   root=LX.fromstring(doc)
   page["heading"]=[" ".join(x.itertext()).strip()[:120] for x in root.xpath("//h1|//h2|//h3")][:18]
   tables=root.xpath("//table")
   page["table_count"]=len(tables)
   page["table_samples"]=[{"classes":t.get("class"),"rows":len(t.xpath(".//tr")),"text":" ".join(t.itertext()).strip()[:350]} for t in tables[:4]]
   for txt in root.xpath("//*[normalize-space(text())='101' or normalize-space(text())='102' or normalize-space(text())='113']")[:12]:
    parent=txt.getparent()
    page["candidate_elements"].append({"tag":txt.tag,"attrs":{k:v[:150] for k,v in txt.attrib.items()},"text":" ".join(txt.itertext()).strip()[:280],
     "parent":parent.tag if parent is not None else None,"parent_class":parent.get("class") if parent is not None else None,
     "parent_html":LX.tostring(parent,encoding="unicode")[:1100] if parent is not None else ""})
   for attr in ["data-unit-id","data-apartment-id","data-name"]:
    page["meta_items"].append({attr:len(root.xpath("//*[@"+attr+"]"))})
   page["dom_sample"]=[{"needle":needle,"snippets":[doc[max(0,m.start()-330):m.start()+760] for m in list(re.finditer(re.escape(needle),doc))[:4]]} for needle in ("مباعة","الوحدة","AressCompound132","101","unit_number","unit_id")]
  data["pages"].append(page);save()
 data["status"]="COMPLETED_PUBLIC_SOURCE_PROBE"
except Exception as ex:
 data["status"]="HALTED_GLOBAL_429" if "429" in str(ex) else "STOPPED_ERROR"
 data["errors"].append({"error":type(ex).__name__+": "+str(ex)[:180]})
finally:
 save()
 print("SOLIMAN_FIRSTPARTY_PROBE "+json.dumps(data,ensure_ascii=False,separators=(",",":")))
