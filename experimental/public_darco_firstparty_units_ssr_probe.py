#!/usr/bin/env python3
"""Darco public /units SSR paginated page diagnostic, robots-gated, no private SAE mappings."""
import os,json,time,re
from pathlib import Path
from urllib.parse import urlsplit,urljoin
from urllib.robotparser import RobotFileParser
from lxml import html as LX
from scrapling.fetchers import Fetcher
HOST="darco.com.sa";ROOT="https://"+HOST;UA="SAE-DB-public-Darco-firstparty-units-SSR-research/1.0"
URLS=[ROOT+"/units",ROOT+"/units?page=2",ROOT+"/units?page=3"]
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"darco_units_three_pages_ssr_shape.json"
s={"status":"START","pages":[],"errors":[],"master_writes":0}
def save():OUT.write_text(json.dumps(s,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def get(url):
 p=urlsplit(url)
 if p.scheme!="https" or p.hostname!=HOST or p.path not in ("/robots.txt","/units"):raise ValueError("BAD_SOURCE")
 if p.query not in ("","page=2","page=3"):raise ValueError("BAD_QUERY")
 r=Fetcher.get(url,retries=0,timeout=50,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("HTTP_429_GLOBAL_STOP")
 if int(r.status)!=200:raise RuntimeError("HTTP_"+str(r.status))
 if urlsplit(str(r.url)).hostname!=HOST:raise ValueError("OUTSIDE_SOURCE_REDIRECT")
 return r
try:
 rb=get(ROOT+"/robots.txt")
 rp=RobotFileParser();rp.parse(rb.body.decode("utf8","replace").splitlines())
 for url in URLS:
  if not rp.can_fetch(UA,url):raise RuntimeError("ROBOTS_DISALLOW")
  time.sleep(max(3,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
  r=get(url);html=r.body.decode("utf8","replace");doc=LX.fromstring(html)
  links=[]
  for a in doc.xpath('//a[@href]'):
   u=urljoin(str(r.url),a.get("href"));p=urlsplit(u)
   if p.hostname!=HOST:continue
   if not re.search(r"/(?:units|unit|properties|property)/",p.path):continue
   parent=a.getparent()
   links.append({"href":u,"anchor_text":" ".join(" ".join(a.itertext()).split())[:440],
                 "parent_text":" ".join(" ".join(parent.itertext()).split())[:700] if parent is not None else None,
                 "parent_class":parent.get("class")[:200] if parent is not None and parent.get("class") else None})
  rec={"url":url,"final_url":str(r.url),"body_bytes":len(r.body),
       "h1":[" ".join(" ".join(x.itertext()).split()) for x in doc.xpath("//h1")][:3],
       "title":doc.xpath("string(//title)")[:220],"page_text_head":" ".join(" ".join(doc.itertext()).split())[:1200],
       "unit_detail_links":links[:25],"unit_detail_links_count":len(links),
       "next_script_data_len":sum(len(x.text or "") for x in doc.xpath("//script"))}
  s["pages"].append(rec);save()
  print("DARCO_SSR_PAGE "+json.dumps(rec,ensure_ascii=False,separators=(",",":"))[:22500],flush=True)
 s["status"]="COMPLETE_SOURCE_PROBE"
except Exception as e:
 s["status"]="STOPPED_429" if "HTTP_429_GLOBAL_STOP" in str(e) else "STOPPED_ERROR"
 s["errors"].append(type(e).__name__+": "+str(e)[:200])
finally:
 save()
 print("DARCO_SSR_SUMMARY "+json.dumps({"status":s["status"],"pages":len(s["pages"]),"errors":s["errors"]},ensure_ascii=False),flush=True)
if s["status"]!="COMPLETE_SOURCE_PROBE":raise SystemExit(2)
