#!/usr/bin/env python3
"""Read publicly advertised Darco unit endpoint schema and static HTML JS script refs. No private DB.
Limited to four plausible original public endpoints; no path enumeration or access bypass.
"""
import json,os,re,time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
from lxml import html as LX
HOST="darco.com.sa";ROOT="https://"+HOST;UA="SAE-public-Darco-unit-endpoint-schema/1.0"
PATHS=["/units","/api/units","/api/units?page=1","/api/public/units"]
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"darco_unit_endpoint_candidate_shapes.json"
s={"status":"STARTED","responses":[],"errors":[],"master_writes":0}
def save():OUT.write_text(json.dumps(s,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def get(url):
 p=urlsplit(url)
 if p.hostname!=HOST or p.scheme!="https":raise ValueError("NOT_OFFICIAL_DARCO_HOST")
 if p.path not in ["/robots.txt","/units","/api/units","/api/public/units"]:raise ValueError("NOT_ALLOWED_PATH")
 x=Fetcher.get(url,retries=0,timeout=35,follow_redirects="safe",headers={"User-Agent":UA,"Accept":"application/json, text/html"})
 if int(x.status)==429:raise RuntimeError("HTTP429_STOP_ALL")
 if urlsplit(str(x.url)).hostname!=HOST:raise ValueError("REDIRECT_OFF_ORIGINAL_SOURCE")
 return x
try:
 rb=get(ROOT+"/robots.txt")
 if int(rb.status)!=200:raise RuntimeError("ROBOTS_HTTP_"+str(rb.status))
 rp=RobotFileParser();rp.parse(rb.body.decode("utf8","replace").splitlines())
 for path in PATHS:
  url=ROOT+path
  if not rp.can_fetch(UA,url):
   s["responses"].append({"source_path":path,"status":"ROBOTS_DENY"});continue
  time.sleep(max(3,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
  r=get(url);resp={"source":url,"http":int(r.status),"bytes":len(r.body)}
  if int(r.status)==200:
   if r.body.strip().startswith((b"[",b"{")):
    try:
     x=json.loads(r.body)
     if isinstance(x,dict):
      resp["top_fields"]={k:type(v).__name__ for k,v in list(x.items())[:30]}
      resp["list_fields"]={k:len(v) for k,v in x.items() if isinstance(v,list)}
     if isinstance(x,list):
      resp["array_len"]=len(x)
      resp["first_item_fields"]=list(x[0])[:60] if x and isinstance(x[0],dict) else []
    except Exception as e:resp["json_error"]=str(e)[:100]
   else:
    doc=LX.fromstring(r.body)
    resp["scripts"]=[x.get("src") for x in doc.xpath("//script[@src]")][:60]
    resp["nextdata_present"]=bool(doc.xpath('//script[@id="__NEXT_DATA__"]'))
    resp["page_visible_text"]=" ".join(" ".join(doc.itertext()).split())[-1300:]
  s["responses"].append(resp);save()
  print("DARCO_PUBLIC_UNIT_ENDPOINT_DIAG "+json.dumps(resp,ensure_ascii=False,separators=(",",":")),flush=True)
 s["status"]="COMPLETE"
except Exception as e:
 s["status"]="STOPPED_429" if "HTTP429_STOP_ALL" in str(e) else "STOPPED_ERROR"
 s["errors"].append(type(e).__name__+": "+str(e)[:180])
finally:
 save()
 print("DARCO_ENDPOINT_SUMMARY "+json.dumps({"status":s["status"],"n":len(s["responses"]),"errors":s["errors"]},ensure_ascii=False),flush=True)
