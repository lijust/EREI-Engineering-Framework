#!/usr/bin/env python3
"""Safe public first-party Wakan inventory DOM probe; no private canonical data."""
import os,json,re,time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
from lxml import html as LH
HOST="wakan.sa"; UA="SAE-DB-source-original-unit-inventory/1.0"
URLS={"042":"https://wakan.sa/EstateProjects/Detail/30074","027":"https://wakan.sa/EstateProjects/Detail/10047","013":"https://wakan.sa/EstateProjects/Detail/42","017":"https://wakan.sa/EstateProjects/Detail/56"}
OUT=Path(os.environ["RUNNER_TEMP"])/"wakan_four_original_inventory_probe.json"
data={"status":"STARTED","projects":[],"errors":[],"writes":0}
def save():OUT.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
def get(url):
 u=urlsplit(url)
 if u.scheme!="https" or u.hostname!=HOST or (u.path!="/robots.txt" and u.path not in [urlsplit(x).path for x in URLS.values()]):raise ValueError("OUT_OF_SCOPE")
 r=Fetcher.get(url,retries=1,timeout=30,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("429_STOP")
 if urlsplit(str(r.url)).hostname not in ("wakan.sa","www.wakan.sa"):raise ValueError("OFFSITE_REDIRECT")
 return r
try:
 rob=get("https://"+HOST+"/robots.txt")
 if int(rob.status) not in (200,404,410):raise RuntimeError("ROBOTS_UNAVAILABLE_"+str(rob.status))
 rp=RobotFileParser()
 if int(rob.status)==200:rp.parse(rob.body.decode("utf-8","replace").splitlines())
 else:rp.allow_all=True
 for key,url in URLS.items():
  if not rp.can_fetch(UA,url):raise RuntimeError("ROBOTS_DISALLOW_"+key)
  time.sleep(max(3.,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
  res=get(url)
  v={"key":key,"url":url,"http":int(res.status),"bytes":len(res.body),"h1":[],"candidate_headers":[],"class_counts":{},"cards":[]}
  if int(res.status)==200:
   root=LH.fromstring(res.body.decode("utf-8","replace"))
   v["h1"]=[" ".join(x.itertext()).strip()[:80] for x in root.xpath("//h1|//h2")][:15]
   for x in root.xpath("//*[contains(text(),'مباع') or contains(text(),'للبيع') or contains(text(),'للايجار')]")[:6]:
    par=x.getparent();v["candidate_headers"].append({"tag":x.tag,"class":x.get("class"),"sample":" ".join(x.itertext()).strip()[:120],"parent_html":LH.tostring(par,encoding="unicode")[:1300] if par is not None else ""})
   for needle in ("unit","item","apartment","building"):
    v["class_counts"][needle]=[(c,n) for c,n in sorted({c:len(root.xpath("//*[@class]")) for c in []}.items())]
   v["cards"]=[{"class":el.get("class"),"html":LH.tostring(el,encoding="unicode")[:2100]} for el in root.xpath("//*[contains(@class,'unit') or contains(@class,'Unit')]")[:7]]
  data["projects"].append(v);save()
 data["status"]="COMPLETE_PROBE"
except Exception as e:
 data["status"]="STOPPED_429" if "429_STOP" in str(e) else "STOPPED_ERROR"
 data["errors"].append({"error":type(e).__name__+": "+str(e)[:170]})
finally:
 save();print("WAKAN_PROBE "+json.dumps(data,ensure_ascii=False,separators=(",",":")))
