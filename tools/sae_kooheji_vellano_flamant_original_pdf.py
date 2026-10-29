#!/usr/bin/env python3
"""Two original publisher Vellano and Flamant brochure inspections: source-only, no guessing unit rows."""
import urllib.request,urllib.robotparser,hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone
import fitz
URLS=[("PRJ-001215","https://koohejidevelopment.sa/wp-content/uploads/2025/11/Vellano-Brochure-2025.pdf"),("PRJ-001213","https://koohejidevelopment.sa/wp-content/uploads/2025/06/Kooheji-Development_Flamant-.pdf")]
UA="SAE-DB-Kooheji-original-brochure-layout-study/1.0"
D={"schema":"SAE_VELLANO_FLAMANT_ORIGINAL_PUBLISHER_PDF_CODED_LAYOUT_STUDY","utc":datetime.now(timezone.utc).isoformat(),"master_writes":0,"pdfs":[]}
OUT=Path("sae-vellano-flamant-official-pdf-token-study.json")
def run():
 try:
  rp=urllib.robotparser.RobotFileParser()
  with urllib.request.urlopen(urllib.request.Request("https://koohejidevelopment.sa/robots.txt",headers={"User-Agent":UA}),timeout=18) as f:
   if f.status!=200:raise RuntimeError("ROBOTS_HTTP")
   rp.parse(f.read(180000).decode("utf8","replace").splitlines())
  if not all(rp.can_fetch(UA,url) for _,url in URLS):D["stop"]="ROBOTS_DISALLOW";return
  for pid,url in URLS:
   item={"project_id":pid,"url":url,"pages":[]};D["pdfs"].append(item)
   try:
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":UA}),timeout=55) as f:
     if f.status in (403,429):item["stop"]="ACCESS_"+str(f.status);break
     if f.status!=200:raise RuntimeError("PDF_NOT_200")
     b=f.read(65000001)
    if len(b)>65000000:raise RuntimeError("PDF_LIMIT_65MB")
    doc=fitz.open(stream=b,filetype="pdf")
    item.update(pdf_sha256=hashlib.sha256(b).hexdigest(),pdf_bytes=len(b),pdf_pages=len(doc))
    for i,page in enumerate(doc):
     words=page.get_text("words")
     numerics=[(str(w[4]),round(w[0],1),round(w[1],1)) for w in words if re.fullmatch(r"(?:[A-Za-z]{1,2}[-/]?)?\\d{1,4}(?:[-/]\\d{1,4})?",str(w[4]))]
     codes=sorted(set(x[0] for x in numerics))
     item["pages"].append({"page":i+1,"text_words":len(words),"unique_numeric_tokens":len(codes),"numeric_samples":numerics[:45],"text_preview":page.get_text().replace("\\n"," ")[:620]})
    top=sorted(item["pages"],key=lambda p:p["unique_numeric_tokens"],reverse=True)[:18]
    print("SAE_KOOHEJI_PDF",json.dumps({"pid":pid,"pages":len(doc),"size":len(b),"top_pages":[{"page":q["page"],"numbered_tokens":q["unique_numeric_tokens"],"text_words":q["text_words"],"preview":q["text_preview"][:120]} for q in top]},ensure_ascii=False),flush=True)
   except Exception as e:item["error"]=type(e).__name__+":"+str(e)[:130]
 except Exception as e:D["error"]=type(e).__name__+":"+str(e)[:220]
 finally:OUT.write_text(json.dumps(D,ensure_ascii=False,indent=2)+"\n")
if __name__=="__main__":run()
