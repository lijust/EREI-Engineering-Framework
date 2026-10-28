#!/usr/bin/env python3
"""Source-only safe robots-respecting market probe: identify itemized cards without scraping identities."""
import json,os,re,time
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from lxml import html as LX
from scrapling.fetchers import Fetcher
UA="SAE-DB-public-source-card-discovery/1.0"
URLS=[
"https://rahaa.sa/assala9/",
"https://ajwd-sa.com/project/%D8%A3%D8%AC%D9%88%D8%AF-42",
"https://darco.com.sa/projects",
"https://alhazem.com.sa/project/%D8%AC%D9%88%D9%87%D8%B1%D8%A9-%D8%A7%D9%84%D8%AD%D8%B2%D9%85/",
"https://naf.com.sa/projects/naf-9",
"https://www.rasf.sa/listing/aarq-lyt-23",
]
OUT=Path(os.environ["RUNNER_TEMP"])/"sae-public-six-source-units-dom-probe.json"
state={"status":"STARTED","probes":[],"errors":[],"writes":0,"private_data":False}
def save():OUT.write_text(json.dumps(state,ensure_ascii=False),encoding="utf-8")
def get(url,host):
 p=urlparse(url)
 if p.scheme!="https" or p.hostname!=host:raise ValueError("DOMAIN_SCOPE_VIOLATION")
 r=Fetcher.get(url,retries=1,timeout=24,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("STOP_ALL_HTTP429")
 if urlparse(str(r.url)).hostname not in (host,host.removeprefix("www."),"www."+host):raise ValueError("OFFSITE_REDIRECT")
 return r
try:
 for url in URLS:
  host=urlparse(url).hostname
  try:
   rob=get("https://"+host+"/robots.txt",host)
   if int(rob.status)!=200:
    state["probes"].append({"url":url,"status":"ROBOTS_UNAVAILABLE_"+str(rob.status)});save();continue
   rp=RobotFileParser();rp.parse(rob.body.decode("utf-8","replace").splitlines())
   if not rp.can_fetch(UA,url):
    state["probes"].append({"url":url,"status":"ROBOTS_DISALLOWED"});save();continue
   time.sleep(max(3,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
   r=get(url,host)
   row={"url":url,"http":int(r.status),"redirect":str(r.url),"html_bytes":len(r.body),"titles":[],"tables":[],"promising_classes":[],"unit_label_nodes":0,
        "unit_card_candidate_links":[],"json_keys":[],"original_codes":[]}
   if int(r.status)==200:
    s=r.body.decode("utf-8","replace");rt=LX.fromstring(s)
    row["titles"]=[" ".join(x.itertext()).strip()[:120] for x in rt.xpath("//h1|//h2")][:10]
    row["tables"]=[{"rows":len(t.xpath(".//tr")),"headers":" ".join(t.xpath(".//th//text()"))[:180]} for t in rt.xpath("//table")[:12]]
    row["promising_classes"]=list(dict.fromkeys((x.get("class") or "")[:100] for x in rt.xpath("//*[contains(@class,'unit') or contains(@class,'apartment') or contains(@class,'floor')]")[:25]))
    row["unit_label_nodes"]=len(rt.xpath("//*[contains(text(),'رقم الوحدة') or contains(text(),'الوحدات السكنية')]"))
    row["unit_card_candidate_links"]=list(dict.fromkeys(x.get("href") for x in rt.xpath("//a[@href]") if re.search(r'unit|apartment|وحد',x.get("href") or "",re.I)))[:20]
    row["json_keys"]=list(dict.fromkeys(re.findall(r'["\\\'](unit_id|unitNumber|unit_number|unit_no|units|unitCode|price|status|availability)["\\\']',s)))[:20]
    row["original_codes"]=list(dict.fromkeys(re.findall(r'\b[A-Z]\d{1,3}[A-Z]-\d{1,3}\b|\b[A-Z]-\d{2,4}\b',s)))[:15]
   state["probes"].append(row)
   print("SITE_PROBE "+json.dumps(row,ensure_ascii=False,separators=(",",":")))
   save()
  except Exception as exc:
   if "HTTP429" in str(exc):raise
   state["errors"].append({"url":url,"error":str(exc)[:140]})
 state["status"]="FINISHED_PROBES"
except Exception as exc:
 state["status"]="STOPPED_429" if "HTTP429" in str(exc) else "STOPPED_ERROR"
 state["errors"].append({"error":str(exc)[:160]})
finally:
 save()
 print("SIX_SOURCE_SUMMARY "+json.dumps({"status":state["status"],"pages":len(state["probes"]),"errors":state["errors"]},ensure_ascii=False,separators=(",",":")))
