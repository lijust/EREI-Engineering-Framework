#!/usr/bin/env python3
"""One original publisher Belgravia PDF inspection: source-only, no guessing unit rows."""
import urllib.request,urllib.robotparser,hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone
import fitz
URL="https://koohejidevelopment.sa/wp-content/uploads/2026/04/Belgravia_Brochure_Eng.pdf"
UA="SAE-DB-Kooheji-original-brochure-layout-study/1.0"
D={"schema":"SAE_BELGRAVIA_ORIGINAL_PUBLISHER_PDF_CODED_PLOT_STUDY","project_id":"PRJ-001212","url":URL,"utc":datetime.now(timezone.utc).isoformat(),"master_writes":0,"pages":[]}
OUT=Path("sae-belgravia-original-pdf-page-token-study.json")
def run():
 try:
  rp=urllib.robotparser.RobotFileParser()
  with urllib.request.urlopen(urllib.request.Request("https://koohejidevelopment.sa/robots.txt",headers={"User-Agent":UA}),timeout=18) as f:
   if f.status!=200:raise RuntimeError("ROBOTS_HTTP")
   rp.parse(f.read(180000).decode("utf8","replace").splitlines())
  if not rp.can_fetch(UA,URL):D["stop"]="ROBOTS_DISALLOW";return
  with urllib.request.urlopen(urllib.request.Request(URL,headers={"User-Agent":UA}),timeout=50) as f:
   if f.status in (403,429):D["stop"]="SOURCE_ACCESS_"+str(f.status);return
   if f.status!=200:raise RuntimeError("PDF_NOT_200")
   b=f.read(55000001)
  if len(b)>55000000:raise RuntimeError("PDF_LIMIT_55MB")
  doc=fitz.open(stream=b,filetype="pdf")
  D.update(pdf_sha256=hashlib.sha256(b).hexdigest(),pdf_bytes=len(b),pdf_pages=len(doc))
  for i,page in enumerate(doc):
   words=page.get_text("words")
   numerics=[(str(w[4]),round(w[0],1),round(w[1],1)) for w in words if re.fullmatch(r"(?:[A-Za-z]{1,2}[-/]?)?\d{1,4}(?:[-/]\d{1,4})?",str(w[4]))]
   codes=sorted(set(x[0] for x in numerics))
   D["pages"].append({"page":i+1,"text_words":len(words),"unique_numeric_tokens":len(codes),"numeric_samples":numerics[:45],"text_preview":page.get_text().replace("\n"," ")[:950]})
  print("BELGRAVIA_PDF",json.dumps({"source_sha256":D["pdf_sha256"],"pages":len(doc),"page_scores":[{"page":p["page"],"unique_tokens":p["unique_numeric_tokens"],"words":p["text_words"],"preview":p["text_preview"][:140]} for p in D["pages"]]},ensure_ascii=False),flush=True)
 except Exception as e:D["error"]=type(e).__name__+":"+str(e)[:220]
 finally:OUT.write_text(json.dumps(D,ensure_ascii=False,indent=2)+"\n")
if __name__=="__main__":run()
