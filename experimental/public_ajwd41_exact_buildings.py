#!/usr/bin/env python3
"""Public Ajwd 41 exact building-link and per-unit source discovery. No private ID."""
import json,re,os,time
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
from lxml import html as H
HOST="www.ajwd-sa.com"
URL="https://www.ajwd-sa.com/project/%D8%A3%D8%AC%D9%88%D8%AF-41"
UA="SAE-DB-public-ajwd41-unit-discovery/1.0"
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"ajwd41_firstparty_building_unit_links.json"
result={"source":URL,"status":"START","building_links":[],"units":[],"pages":[],"errors":[],"master_writes":0}
def save():OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def get(url):
 p=urlsplit(url)
 if p.scheme!="https" or p.hostname not in (HOST,"ajwd-sa.com"):raise ValueError("HOST_NOT_APPROVED")
 r=Fetcher.get(url,retries=0,timeout=30,follow_redirects="safe",headers={"User-Agent":UA})
 if r.status==429:raise RuntimeError("GLOBAL_STOP_429")
 if r.status!=200:raise RuntimeError("HTTP_"+str(r.status))
 if urlsplit(str(r.url)).hostname not in (HOST,"ajwd-sa.com"):raise ValueError("EXTERNAL_REDIRECT")
 return r
try:
 rb=get("https://"+HOST+"/robots.txt")
 rp=RobotFileParser();rp.parse(rb.body.decode("utf8","replace").splitlines())
 if not rp.can_fetch(UA,URL):raise RuntimeError("ROBOTS_BLOCK_PROJECT")
 time.sleep(max(2,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
 project=get(URL);doc=H.fromstring(project.body)
 all_buildings=[]
 for a in doc.xpath('//a[@href]'):
  href=urljoin(str(project.url),a.attrib["href"]);p=urlsplit(href)
  if p.hostname in (HOST,"ajwd-sa.com") and re.fullmatch(r"/building/\d+/?",p.path):
   surrounding=" ".join(" ".join(a.getparent().itertext()).split())[:250]
   if href not in all_buildings:all_buildings.append(href)
   result["building_links"].append({"original_url":href,"anchor":" ".join(a.itertext()).strip()[:100],"surrounding":surrounding})
 print("PROJECT_BUILDING_LINKS",json.dumps(result["building_links"],ensure_ascii=False),flush=True)
 result["project_h1"]=[" ".join(x.itertext()).strip() for x in doc.xpath("//h1")][:4]
 for url in all_buildings:
  if not rp.can_fetch(UA,url):result["pages"].append({"url":url,"status":"ROBOTS_DISALLOW"});continue
  time.sleep(2)
  x=get(url);d=H.fromstring(x.body)
  content=" ".join(" ".join(d.itertext()).split())
  res={"url":url,"status":200,"h1":[" ".join(e.itertext()).strip() for e in d.xpath("//h1")][:5],"card_section_text":content[0:5000]}
  for a in d.xpath("//a[@href]"):
   link=urljoin(str(x.url),a.attrib["href"])
   if re.fullmatch(r"/unit/\d+/?",urlsplit(link).path) and urlsplit(link).hostname in (HOST,"ajwd-sa.com"):
    item={"building_url":url,"unit_detail_url":link,"unit_link_label":" ".join(a.itertext()).strip()[:120],
          "source_context":" ".join(" ".join(a.getparent().getparent().itertext()).split())[:350]}
    result["units"].append(item)
  result["pages"].append(res);save()
 result["status"]="COMPLETE"
except Exception as e:
 result["status"]="STOPPED_429" if "429" in str(e) else "STOPPED_ERROR"
 result["errors"].append(str(e)[:250])
finally:
 save()
 print("FINAL_AJWD41_SOURCE",json.dumps({"state":result["status"],"buildings":len(result["building_links"]),"unit_details":len(result["units"]),"errors":result["errors"]},ensure_ascii=False),flush=True)
 for item in result["units"]:print("AJWD41_UNIT_LINK",json.dumps(item,ensure_ascii=False),flush=True)
