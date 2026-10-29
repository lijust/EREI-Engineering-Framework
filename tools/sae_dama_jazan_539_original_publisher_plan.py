#!/usr/bin/env python3
"""Original Al Omar Dama Jazan publisher brochure: discover ONLY literal plotted unique villa IDs, source-only."""
import json,hashlib,re,urllib.request,urllib.robotparser
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit
import fitz
URL="https://alomarinvestment.com/wp-content/uploads/2025/10/Dama-Jazan-final-8oct2.pdf"
UA="SAE-DB-Dama-Jazan-original-plot-evidence/1.0"
OUT=Path("sae-dama-jazan-firstparty-source-pdf-page-diagnostics.json")
TMP=Path("dama-jazan-source-temp.pdf")
report={"schema":"SAE_DAMA_JAZAN_EXISTING_PRJ_000333_OFFICIAL_BROCHURE_PLOTTED_VILLAS_AUDIT_V1","canonical_project_id":"PRJ-000333","publisher_source_url":URL,"utc":datetime.now(timezone.utc).isoformat(),"sheet_writes":0,"pages":[]}
try:
 u=urlsplit(URL)
 req=urllib.request.Request(u.scheme+"://"+u.netloc+"/robots.txt",headers={"User-Agent":UA})
 with urllib.request.urlopen(req,timeout=18) as f:
  if f.status!=200:raise RuntimeError("ROBOTS_NOT_200")
  buf=f.read(180001)
  if len(buf)>180000:raise RuntimeError("ROBOTS_LIMIT")
 r=urllib.robotparser.RobotFileParser()
 r.parse(buf.decode("utf-8","replace").splitlines())
 if not r.can_fetch(UA,URL):raise RuntimeError("ROBOTS_DENY")
 size=0;sha=hashlib.sha256()
 with urllib.request.urlopen(urllib.request.Request(URL,headers={"User-Agent":UA}),timeout=100) as f:
  if f.status in (403,429):raise RuntimeError("SOURCE_ACCESS_STOP_"+str(f.status))
  if f.status!=200:raise RuntimeError("PDF_NOT_200_"+str(f.status))
  with TMP.open("wb") as g:
   while True:
    c=f.read(1048576)
    if not c:break
    size+=len(c)
    if size>95000000:raise RuntimeError("PDF_EXCEEDS_95MB")
    sha.update(c);g.write(c)
 with fitz.open(TMP) as doc:
  report.update(pdf_bytes=size,sha256=sha.hexdigest(),page_count=len(doc))
  for i,page in enumerate(doc):
   words=page.get_text("words")
   nums=[(str(w[4]),round(w[0],1),round(w[1],1)) for w in words if re.fullmatch(r"[A-Za-z]?[0-9]{1,4}(?:[-/][0-9]{1,4})?",str(w[4]))]
   report["pages"].append({"page":i+1,"word_count":len(words),"num_tokens":len(nums),"unique_number_like":len(set(z[0] for z in nums)),"source_number_positions":nums[:120],"preview":page.get_text().replace("\n"," ")[:500]})
  top=sorted(report["pages"],key=lambda x:x["unique_number_like"],reverse=True)[:20]
  print("DAMA_PDF_SCAN",json.dumps({"pages":len(doc),"bytes":size,"top":[{"page":x["page"],"unique":x["unique_number_like"],"words":x["word_count"],"preview":x["preview"][:150]} for x in top]},ensure_ascii=False),flush=True)
except Exception as e:report["stop_or_error"]=type(e).__name__+":"+str(e)[:200];print("DAMA_PDF_STOP",report["stop_or_error"],flush=True)
finally:
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 TMP.unlink(missing_ok=True)
