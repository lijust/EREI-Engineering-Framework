#!/usr/bin/env python3
"""Read-only first-party Al Thara source PDF block 159 exact numbered villa labels."""
import json,os,re,time,sys,hashlib
from pathlib import Path
from urllib.robotparser import RobotFileParser
from urllib.parse import urlsplit
from scrapling.fetchers import Fetcher
import fitz
URL="https://koohejidevelopment.sa/wp-content/uploads/2025/06/Kooheji-Development_Lavira-Thara-.pdf"
BASE="https://koohejidevelopment.sa"
UA="SAE-DB-publisher-original-Lavira-Thara/1.0"
out=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"sae_thara_exact_source_unit_codes.json"
state={"schema":"LAVIRA_THARA_EXACT_BLOCK_159_VILLA_IDENTITIES_V2","status":"STARTED","source":URL,"pages":[],"codes":[],"errors":[],"master_writes":0}
def save():out.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf8")
def get(url):
 r=Fetcher.get(url,retries=0,timeout=95,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("HTTP_429_STOP")
 if int(r.status)!=200:raise RuntimeError("HTTP_"+str(r.status))
 if urlsplit(str(r.url)).hostname!="koohejidevelopment.sa":raise RuntimeError("OFF_HOST")
 return r.body
try:
 rob=get(BASE+"/robots.txt")
 rp=RobotFileParser();rp.parse(rob.decode("utf8","replace").splitlines())
 if not rp.can_fetch(UA,URL):raise RuntimeError("ROBOTS_DISALLOW")
 time.sleep(max(3.0,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
 b=get(URL)
 if not b.startswith(b"%PDF") or len(b)>60_000_000:raise RuntimeError("PDF_INVALID")
 state["sha256"]=hashlib.sha256(b).hexdigest()
 doc=fitz.open(stream=b,filetype="pdf");state["pdf_pages"]=len(doc)
 seen={}
 for i,p in enumerate(doc):
  raw=p.get_text("text")
  # Publisher's original page layouts can reverse digits and slash; save exact literal.
  candidates=[]
  for m in re.finditer(r"(?<![0-9])(?:159\s*[-–—/]\s*([0-9]{1,2})|([0-9]{1,2})\s*[-–—/]\s*159)(?![0-9])",raw):
   z=int(m.group(1) or m.group(2))
   if 1<=z<=75:
    code=f"159-{z:02d}"
    candidates.append({"code":code,"literal":m.group(0),"start":m.start(),"around":raw[max(0,m.start()-45):m.end()+65].replace("\n"," ")})
    seen.setdefault(code,[]).append({"page_one_based":i+1,"literal":m.group(0)})
  if i in (14,16,17) or candidates:
   lines=[z.strip() for z in raw.splitlines() if z.strip()]
   entry={"page":i+1,"code_matches":candidates,"token_count":len(p.get_text("words"))}
   if i in (16,17):entry["page_lines"]=lines[:260]
   state["pages"].append(entry);save()
   print("THARA_PAGE_SOURCE "+json.dumps(entry,ensure_ascii=False,separators=(",",":"))[:24000],flush=True)
 state["codes"]=[{"publisher_unit_code":k,"publisher_source_occurrences":v} for k,v in sorted(seen.items())]
 state["status"]="COMPLETE_SOURCE_CODE_REVIEW";save()
except Exception as e:
 state["status"]="STOPPED_429" if "429" in str(e) else "STOPPED_ERROR"
 state["errors"].append(str(e)[:230])
finally:
 save();print("THARA_EXACT_SOURCE_RESULT "+json.dumps({"status":state["status"],"pdf_pages":state.get("pdf_pages"),"distinct_codes":len(state["codes"]),"codes":[x["publisher_unit_code"] for x in state["codes"]],"errors":state["errors"],"master_writes":0},ensure_ascii=False,separators=(",",":")))
if state["status"]!="COMPLETE_SOURCE_CODE_REVIEW":sys.exit(2)
