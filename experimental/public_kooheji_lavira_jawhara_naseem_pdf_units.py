#!/usr/bin/env python3
"""Publisher-original Villa E/F brochures: isolate only explicitly itemized physical unit codes."""
import json,os,re,time,sys,hashlib
from pathlib import Path
from urllib.robotparser import RobotFileParser
from urllib.parse import urlsplit
from scrapling.fetchers import Fetcher
import fitz
BASE="https://koohejidevelopment.sa"
DOCS={"jawhara":BASE+"/wp-content/uploads/2026/04/Lavira-Villa-F-Al-Jawhara.pdf","naseem":BASE+"/wp-content/uploads/2026/04/Lavira-Villa-E-Al-Naseem.pdf"}
UA="SAE-DB-official-Kooheji-villa-unit-documents/1.0"
out=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"lavira_villaEF_source_candidates.json"
st={"schema":"LAVIRA_VILLA_EF_PUBLISHER_PDF_UNIT_CODE_DISCOVERY_V1","status":"START","books":[],"errors":[],"master_writes":0}
def save():out.write_text(json.dumps(st,ensure_ascii=False,separators=(",",":")),encoding="utf8")
def get(url):
 r=Fetcher.get(url,retries=0,timeout=100,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("HTTP_429_STOP")
 if int(r.status)!=200:raise RuntimeError("SOURCE_HTTP_"+str(r.status))
 if urlsplit(str(r.url)).hostname!="koohejidevelopment.sa":raise RuntimeError("OFFICIAL_HOST_CHANGED")
 return r.body
try:
 rob=get(BASE+"/robots.txt");rp=RobotFileParser();rp.parse(rob.decode("utf8","replace").splitlines())
 for name,url in DOCS.items():
  if not rp.can_fetch(UA,url):st["books"].append({"name":name,"status":"ROBOTS_DISALLOW"});save();continue
  time.sleep(max(3.,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
  b=get(url)
  if not b.startswith(b"%PDF") or len(b)>60_000_000:raise RuntimeError("PDF_INVALID_"+name)
  doc=fitz.open(stream=b,filetype="pdf")
  book={"name":name,"url":url,"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b),"page_count":len(doc),"pages":[]}
  for i,p in enumerate(doc):
   t=p.get_text("text")
   lines=[q.strip() for q in t.splitlines() if q.strip()]
   codes=list(dict.fromkeys(re.findall(r"(?<![0-9])[0-9]{1,3}[-–—/][0-9]{1,3}(?![0-9])",t)))
   labels=[(k,v) for k,v in enumerate(lines) if re.search(r'unit no|villa no|رقم الوحدة|رقم الفيلا|رقم القطعة|رقم البلوك|بلوك|BLOCK|مساحات الفلل|فلل|الوحدات',v,re.I)]
   if labels or codes:
    pdoc={"page":i+1,"codes":codes[:120],"source_context":[{"line":j,"lines":lines[max(0,j-3):j+5]} for j,_ in labels[:6]],"word_count":len(p.get_text("words"))}
    book["pages"].append(pdoc)
    print("LAVIRA_EF_SOURCE_PAGE "+json.dumps({"book":name,**pdoc},ensure_ascii=False,separators=(",",":"))[:14000],flush=True)
  st["books"].append(book);save()
  print("LAVIRA_EF_BOOK_SUMMARY "+json.dumps({"book":name,"sha256":book["sha256"],"bytes":book["bytes"],"pdf_pages":book["page_count"],"candidate_pages":len(book["pages"]),"tokens":sum(len(q["codes"]) for q in book["pages"])},ensure_ascii=False),flush=True)
 st["status"]="COMPLETE_SOURCE_EF"
except Exception as e:
 st["status"]="STOPPED_429" if "429" in str(e) else "STOPPED_ERROR"
 st["errors"].append(str(e)[:230])
finally:
 save();print("LAVIRA_EF_FINAL "+json.dumps({"status":st["status"],"books":len(st["books"]),"errors":st["errors"],"master_writes":0},ensure_ascii=False))
if st["status"]!="COMPLETE_SOURCE_EF":sys.exit(2)
