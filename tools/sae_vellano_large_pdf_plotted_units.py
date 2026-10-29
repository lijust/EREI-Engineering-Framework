#!/usr/bin/env python3
"""Official Vellano heavy brochure page-label source inspection, read-only."""
import urllib.request,urllib.robotparser,json,hashlib,re
from pathlib import Path
from datetime import datetime,timezone
import fitz
URL="https://koohejidevelopment.sa/wp-content/uploads/2025/11/Vellano-Brochure-2025.pdf"
UA="SAE-DB-Vellano-public-heavy-brochure-plot-study/1.0"
OUT=Path("sae-vellano-heavy-brochure-publisher-plot-evidence.json")
PDF=Path("vellano_original_source_temp.pdf")
R={"schema":"SAE_KOOHEJI_VELLANO_ORIGINAL_HEAVY_PUBLIC_BROCHURE_V1","existing_canonical":"PRJ-001215",
   "url":URL,"utc":datetime.now(timezone.utc).isoformat(),"master_writes":0,"pages":[]}
try:
 rp=urllib.robotparser.RobotFileParser()
 with urllib.request.urlopen(urllib.request.Request("https://koohejidevelopment.sa/robots.txt",headers={"User-Agent":UA}),timeout=20) as f:
  if f.status!=200:raise RuntimeError("ROBOTS_NOT_200")
  rp.parse(f.read(180000).decode("utf8","replace").splitlines())
 if not rp.can_fetch(UA,URL):raise RuntimeError("ROBOTS_DENY_PDF")
 size=0;h=hashlib.sha256()
 with urllib.request.urlopen(urllib.request.Request(URL,headers={"User-Agent":UA}),timeout=100) as f:
  if f.status in (403,429):raise RuntimeError("SOURCE_ACCESS_STOP_"+str(f.status))
  if f.status!=200:raise RuntimeError("PDF_NOT_200")
  with PDF.open("wb") as o:
   while True:
    chunk=f.read(1024*1024)
    if not chunk:break
    size+=len(chunk)
    if size>180000000:raise RuntimeError("PDF_LIMIT_180MB")
    h.update(chunk);o.write(chunk)
 R["source_bytes"]=size;R["sha256"]=h.hexdigest()
 with fitz.open(PDF) as doc:
  R["pages_count"]=len(doc)
  for i,p in enumerate(doc):
   words=p.get_text("words")
   numeric=[{"word":str(w[4]),"x":round(w[0],1),"y":round(w[1],1)} for w in words if re.fullmatch(r"[A-Z]?\d{1,4}(?:[-/]\d{1,4})?",str(w[4]))]
   unique={x["word"] for x in numeric}
   R["pages"].append({"page":i+1,"words":len(words),"numeric_total":len(numeric),"numeric_unique":len(unique),
                     "numeric_samples":numeric[:75],"title":p.get_text().replace("\n"," ")[:900]})
 scores=sorted(R["pages"],key=lambda x:x["numeric_unique"],reverse=True)[:25]
 print("SAE_VELLANO_HEAVY_BROCHURE",json.dumps({"bytes":size,"pages":len(R["pages"]),
  "top":[{"page":x["page"],"numeric_unique":x["numeric_unique"],"words":x["words"],"preview":x["title"][:160]} for x in scores]},ensure_ascii=False),flush=True)
except Exception as e:
 R["error"]=type(e).__name__+":"+str(e)[:200]
 print("SAE_VELLANO_HEAVY_ERROR",R["error"],flush=True)
finally:
 OUT.write_text(json.dumps(R,ensure_ascii=False,indent=2)+"\n")
 PDF.unlink(missing_ok=True)
