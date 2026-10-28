#!/usr/bin/env python3
"""Source-only Alsoliman elite development PDF vector plot label census; no synthetic units."""
import json,re,os,time,hashlib,sys,collections
from pathlib import Path
from urllib.robotparser import RobotFileParser
from urllib.parse import urlsplit
from scrapling.fetchers import Fetcher
import fitz
ROOT="https://www.alsoliman.com.sa"
URL=ROOT+"/storage/settings/01JMESN52DT967KR97KSXEZZJR.pdf"
UA="SAE-DB-Original-Saudi-Unit-Vector-Siteplans/1.0"
out=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"alsoliman_elite_firstparty_vector_numeric_source_probe.json"
state={"schema":"SAE_ALSOLIMAN_ELITE_ORIGINAL_PLAN_VECTOR_NUMBER_AUDIT_V1","source_url":URL,"status":"START","pdf_pages":[],"errors":[],"master_writes":0}
def save():out.write_text(json.dumps(state,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
def fetch(url,limit):
 r=Fetcher.get(url,retries=0,timeout=115,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("STOP_HTTP429")
 if int(r.status)!=200:raise RuntimeError("SOURCE_HTTP_"+str(r.status))
 if urlsplit(str(r.url)).hostname not in ("alsoliman.com.sa","www.alsoliman.com.sa"):raise RuntimeError("UNTRUSTED_REDIRECT")
 if len(r.body)>limit:raise RuntimeError("SOURCE_TOO_BIG")
 return r.body
try:
 rob=fetch(ROOT+"/robots.txt",500000)
 rp=RobotFileParser();rp.parse(rob.decode("utf8","replace").splitlines())
 if not rp.can_fetch(UA,URL):raise RuntimeError("ROBOTS_DISALLOW")
 time.sleep(max(3.,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
 b=fetch(URL,55000000)
 if not b.startswith(b"%PDF"):raise RuntimeError("NOT_PDF")
 state["pdf_bytes"]=len(b);state["pdf_sha256"]=hashlib.sha256(b).hexdigest()
 pdf=fitz.open(stream=b,filetype="pdf");state["pdf_page_count"]=len(pdf)
 for i,p in enumerate(pdf):
  words=p.get_text("words")
  tokens=[w for w in words if re.fullmatch(r"[1-9][0-9]{0,3}",str(w[4]).strip()) and int(w[4])<=3000]
  uniq=len(set(str(x[4]) for x in tokens))
  pageinfo={"page_one_based":i+1,"word_count":len(words),"numeric_token_count":len(tokens),"unique_numeric_tokens":uniq,
     "page_width":round(p.rect.width,1),"page_height":round(p.rect.height,1),"number_samples":[str(w[4]) for w in tokens[:22]]}
  if uniq>50:
   pageinfo["original_vector_number_labels"]=[{"literal":str(w[4]),"bbox_pt":[round(t,2) for t in w[:4]]} for w in tokens]
  state["pdf_pages"].append(pageinfo);save()
  if uniq>=60:print("ALSOLIMAN_ELITE_DENSE_SOURCE_PAGE "+json.dumps({k:v for k,v in pageinfo.items() if k!="original_vector_number_labels"},ensure_ascii=False,separators=(",",":")),flush=True)
 state["status"]="COMPLETE_FIRSTPARTY_PDF_AUDIT"
except Exception as e:
 state["status"]="STOPPED_429" if "429" in str(e) else "STOPPED_SOURCE_ERROR";state["errors"].append(str(e)[:260])
finally:
 save()
 print("ALSOLIMAN_ELITE_PDF_RESULT "+json.dumps({"status":state["status"],"pdf_pages":state.get("pdf_page_count"),"size":state.get("pdf_bytes"),"max_unique_numeric_tokens":max([x["unique_numeric_tokens"] for x in state["pdf_pages"]] or [0]),"top_pages":sorted([{k:v for k,v in x.items() if k!="original_vector_number_labels"} for x in state["pdf_pages"]],key=lambda x:-x["unique_numeric_tokens"])[:8],"errors":state["errors"],"master_writes":0},ensure_ascii=False,separators=(",",":")),flush=True)
if state["status"]!="COMPLETE_FIRSTPARTY_PDF_AUDIT":sys.exit(2)
