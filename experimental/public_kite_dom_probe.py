#!/usr/bin/env python3
"""Diagnostics of public Kite unit cards on one known project; no private canonical data."""
import json,os,re,time
from pathlib import Path
from urllib.robotparser import RobotFileParser
from urllib.parse import urlsplit
from lxml import html as LX
from scrapling.fetchers import Fetcher
UA="SAE-DB-public-card-parser/1.0"
URL="https://kite.sa/en/projects/riyadh/97401"
OUT=Path(os.environ["RUNNER_TEMP"])/"kite-public-dom-diagnostics.json"
data={"source":URL,"status":"INIT","recorded_at":None,"snippets":[],"links":[],"headers":[],"unit_detail_url_samples":[],"tables":[],"errors":[]}
def save(): OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
try:
 robots=Fetcher.get("https://kite.sa/robots.txt",retries=1,timeout=20,headers={"User-Agent":UA})
 if int(robots.status)!=200:raise ValueError("Robots "+str(robots.status))
 rp=RobotFileParser();rp.parse(robots.body.decode("utf-8","replace").splitlines())
 if not rp.can_fetch(UA,URL):raise ValueError("ROBOTS_DISALLOW")
 time.sleep(max(3,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
 resp=Fetcher.get(URL,retries=1,timeout=25,follow_redirects="safe",headers={"User-Agent":UA})
 if int(resp.status)==429:raise RuntimeError("HTTP_429_HALT")
 if int(resp.status)!=200:raise ValueError("HTTP "+str(resp.status))
 if urlsplit(str(resp.url)).hostname!="kite.sa":raise ValueError("OFFSITE_REDIRECT")
 doc=resp.body.decode("utf-8","replace")
 tree=LX.fromstring(doc)
 for needle in ("02-01-0144","280","1,011,405","1011405","297.9","Units","units","Unit"):
  found=[m.start() for m in list(re.finditer(re.escape(needle),doc,re.I))[:3]]
  data["snippets"].append({"needle":needle,"occurrences":doc.lower().count(needle.lower()),"samples":[doc[max(0,j-200):j+320] for j in found]})
 for a in tree.xpath("//a[@href]"):
  href=a.get("href")
  if not href:continue
  label=" ".join(" ".join(a.itertext()).split())
  if "unit" in href.lower() or "property" in href.lower() or re.search(r"/riyadh/97401",href):
   data["unit_detail_url_samples"].append({"url":href[:170],"text":label[:150]})
 data["unit_detail_url_samples"]=data["unit_detail_url_samples"][:45]
 for x in tree.xpath("//h1|//h2|//h3|//table"):
  if x.tag=="table":
   rows=x.xpath(".//tr")
   data["tables"].append({"rows":len(rows),"head":" ".join(" ".join(x.itertext()).split())[:500]})
  else:data["headers"].append({"tag":x.tag,"text":" ".join(" ".join(x.itertext()).split())[:150]})
 data["status"]="HTML_200_ROBOTS_ALLOWED"
except Exception as exc:
 data["status"]="ERROR" ; data["errors"].append(type(exc).__name__+": "+str(exc)[:180])
finally:
 save()
 print("KITE_DOM_PROBE "+json.dumps(data,ensure_ascii=False,separators=(",",":")))
