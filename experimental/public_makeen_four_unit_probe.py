#!/usr/bin/env python3
"""Robots-gated firstparty Asas Makeen published unit cards DOM probe; public data only."""
import json,os,time,re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
from lxml import html as LX
HOST="asasmakeen.com"
URLS={"63":"https://asasmakeen.com/ar/u/pu/3/42/%D8%B4%D9%82%D9%82-%D8%AD%D9%8A-%D8%A7%D9%84%D8%B9%D8%A7%D8%B1%D8%B6-%D8%A7%D9%84%D8%B1%D9%8A%D8%A7%D8%B6-%D9%85%D9%83%D9%8A%D9%86-63",
"64":"https://asasmakeen.com/ar/u/pu/3/43/%D8%B4%D9%82%D9%82-%D9%84%D9%84%D8%A8%D9%8A%D8%B9-%D8%AD%D9%8A-%D8%A7%D9%84%D8%B9%D8%A7%D8%B1%D8%B6",
"66":"https://asasmakeen.com/ar/u/pu/3/45/%D8%B4%D9%82%D9%82-%D8%AD%D9%8A-%D8%A7%D9%84%D8%B1%D9%85%D8%A7%D9%84-%D9%84%D9%84%D8%A8%D9%8A%D8%B9",
"90":"https://asasmakeen.com/ar/u/pu/3/64/%D9%85%D9%83%D9%8A%D9%86-90"}
UA="SAE-DB-public-original-unit-cards/1.0"
OUT=Path(os.environ["RUNNER_TEMP"])/"makeen_four_firstparty_unit_page_probe.json"
state={"status":"STARTED","sources":[],"errors":[],"personal_data_collected":False,"private_project_mapping_used":False,"master_writes":0}
def save():OUT.write_text(json.dumps(state,ensure_ascii=False),encoding="utf-8")
def fetch(url):
 p=urlsplit(url)
 if p.scheme!="https" or p.hostname!=HOST or (p.path!="/robots.txt" and not p.path.startswith("/ar/u/pu/3/")):
  raise ValueError("UNAPPROVED_SOURCE_URL")
 r=Fetcher.get(url,retries=1,timeout=35,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("HTTP_429_GLOBAL_STOP")
 if urlsplit(str(r.url)).hostname not in ("asasmakeen.com","www.asasmakeen.com"):raise ValueError("REDIRECT_NOT_SAME_PUBLISHER")
 return r
try:
 robot=fetch("https://"+HOST+"/robots.txt")
 if int(robot.status)!=200:raise RuntimeError("ROBOTS_NOT_ACCESSIBLE_"+str(robot.status))
 rp=RobotFileParser();rp.parse(robot.body.decode("utf-8","replace").splitlines())
 for project,url in URLS.items():
  if not rp.can_fetch(UA,url):
   state["errors"].append({"project":project,"error":"ROBOTS_DISALLOW"});continue
  time.sleep(max(3.,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
  res=fetch(url)
  e={"project":project,"status":int(res.status),"final_url":str(res.url),"html_bytes":len(res.body),"tables":[],"tr_samples":[],"heading":[],"card_samples":[],"unit_code_snippets":[]}
  if int(res.status)==200:
   html=res.body.decode("utf-8","replace");root=LX.fromstring(html)
   e["heading"]=[" ".join(x.itertext()).strip()[:100] for x in root.xpath("//h1|//h2")][:12]
   ts=root.xpath("//table")
   e["tables"]=[{"classes":t.get("class"),"rows":len(t.xpath(".//tr")),"sample":" ".join(" ".join(t.itertext()).split())[:400]} for t in ts[:25]]
   e["tr_samples"]=[{"class":x.get("class"),"html":LX.tostring(x,encoding="unicode")[:1450]} for x in root.xpath("//tr")[:6]]
   e["card_samples"]=[{"tag":x.tag,"class":x.get("class"),"html":LX.tostring(x,encoding="unicode")[:1100]} for x in root.xpath("//*[contains(@class,'unit-row') or contains(@class,'unit-item')]")[:3]]
   e["unit_code_snippets"]=[html[max(0,m.start()-150):m.start()+330] for m in list(re.finditer(re.escape(("A1A-"+project)),html))[:2]]
  state["sources"].append(e);save()
 state["status"]="COMPLETE_SOURCES_CHECKED"
except Exception as ex:
 state["status"]="HALTED_429" if "429_GLOBAL" in str(ex) else "STOPPED_ERROR"
 state["errors"].append({"error":type(ex).__name__+": "+str(ex)[:180]})
finally:
 save()
 print("MAKEEN_FIRSTPARTY_PROBE "+json.dumps(state,ensure_ascii=False,separators=(",",":")))
