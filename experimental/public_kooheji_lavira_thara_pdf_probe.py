#!/usr/bin/env python3
"""Public source-only exact Lavira Al Thara official numbered unit PDF audit."""
import json,os,re,time,hashlib
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
import fitz
ROOT="https://koohejidevelopment.sa"
URL=ROOT+"/wp-content/uploads/2025/06/Kooheji-Development_Lavira-Thara-.pdf"
UA="SAE-public-kooheji-thara-firstparty/1.0"
OUT=Path(os.environ["RUNNER_TEMP"])/"kooheji_thara_original_unit_numbers.json"
state={"source":URL,"status":"START","pages":[],"codes":[],"errors":[],"master_writes":0}
def save():OUT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def get(url):
 if urlsplit(url).hostname!="koohejidevelopment.sa":raise ValueError("OFFSOURCE")
 r=Fetcher.get(url,retries=0,timeout=80,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("GLOBAL_STOP_429")
 if int(r.status)!=200:raise RuntimeError("HTTP_"+str(r.status))
 if urlsplit(str(r.url)).hostname!="koohejidevelopment.sa":raise ValueError("CROSSHOST")
 return r
try:
 rb=get(ROOT+"/robots.txt")
 p=RobotFileParser();p.parse(rb.body.decode("utf8","replace").splitlines())
 if not p.can_fetch(UA,URL):raise RuntimeError("ROBOTS_DISALLOW")
 time.sleep(max(3,float(p.crawl_delay(UA) or p.crawl_delay("*") or 0)))
 b=get(URL).body
 if not b.startswith(b"%PDF") or len(b)>60_000_000:raise ValueError("NOT_PDF")
 doc=fitz.open(stream=b,filetype="pdf")
 state["sha256"]=hashlib.sha256(b).hexdigest()
 state["page_count"]=len(doc)
 for i,page in enumerate(doc):
  t=page.get_text("text")
  if "رقم الوحدة" not in t:continue
  lines=[s.strip() for s in t.splitlines() if s.strip()]
  tokens=re.findall(r"(?<!\d)\d{1,2}[-]\d{1,2}(?!\d)",t)
  tokens=[a for a in tokens if re.fullmatch(r"[0-9]{1,2}-[0-9]{1,2}",a)]
  item={"page_number":i+1,"first80lines":lines[:80],"numbered_tokens":sorted(set(tokens)),"raw_tokens_count":len(tokens)}
  state["pages"].append(item)
  state["codes"].extend([{"publisher_raw_code":code,"pdf_page":i+1} for code in sorted(set(tokens))])
  print("THARA_SOURCE_PAGE "+json.dumps(item,ensure_ascii=False,separators=(",",":"))[:14000],flush=True)
 state["status"]="SOURCE_ONLY_COMPLETE"
except Exception as ex:
 state["status"]="STOPPED_429" if "429" in str(ex) else "STOPPED_ERROR"
 state["errors"].append(type(ex).__name__+": "+str(ex)[:220])
finally:
 save()
 print("THARA_SOURCE_SUMMARY "+json.dumps({"status":state["status"],"pages":len(state["pages"]),"tokens":len(state["codes"]),"sha256":state.get("sha256"),"errors":state["errors"],"master_writes":0},ensure_ascii=False),flush=True)
if state["status"]!="SOURCE_ONLY_COMPLETE":raise SystemExit(2)
