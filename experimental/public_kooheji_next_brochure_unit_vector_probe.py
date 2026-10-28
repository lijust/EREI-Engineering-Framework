#!/usr/bin/env python3
"""Source-only first-party brochure vector probe: existing SAE projects, no private data."""
import json,os,hashlib,re,time,sys
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import requests,fitz
ROOT="https://koohejidevelopment.sa"
BOOKS=[
 ("vellano",ROOT+"/wp-content/uploads/2025/11/Vellano-Brochure-2025.pdf",130000000),
 ("belgravia",ROOT+"/wp-content/uploads/2025/06/Kooheji-Development_BELGRAVIA.pdf",85000000),
 ("lavira_thara",ROOT+"/wp-content/uploads/2025/06/Kooheji-Development_Lavira-Thara-.pdf",65000000),
]
UA="SAE-DB-Official-Source-Unit-Vector-Research/1.0"
out=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"sae_kooheji_next_firstparty_brochure_vector_probe.json"
state={"schema":"SAE_KOOHEJI_NEXT_BROCHURES_V1","books":[],"status":"STARTED","errors":[],"production_writes":0}
def save():out.write_text(json.dumps(state,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
s=requests.Session();s.headers["User-Agent"]=UA
try:
 rr=s.get(ROOT+"/robots.txt",timeout=30,allow_redirects=False)
 if rr.status_code==429:raise RuntimeError("HTTP_429_STOP")
 if rr.status_code!=200:raise RuntimeError("ROBOTS_ERROR_"+str(rr.status_code))
 rp=RobotFileParser();rp.parse(rr.text.splitlines())
 for key,url,cap in BOOKS:
  if not rp.can_fetch(UA,url):
   state["books"].append({"key":key,"status":"ROBOTS_DISALLOW"});save();continue
  time.sleep(max(3.,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
  book={"key":key,"url":url,"status":"STARTED","pages":[],"top_label_pages":[]}
  state["books"].append(book)
  with s.get(url,timeout=150,stream=True,allow_redirects=False) as resp:
   if resp.status_code==429:raise RuntimeError("HTTP_429_STOP")
   if resp.status_code!=200:raise RuntimeError("PDF_HTTP_"+key+"_"+str(resp.status_code))
   if urlsplit(resp.url).hostname!="koohejidevelopment.sa":raise RuntimeError("PDF_HOST_CHANGED")
   path=Path(os.environ.get("RUNNER_TEMP","/tmp"))/("source_"+key+".pdf")
   sha=hashlib.sha256();n=0
   with path.open("wb") as fo:
    for chunk in resp.iter_content(chunk_size=256*1024):
     if not chunk:continue
     fo.write(chunk);sha.update(chunk);n+=len(chunk)
     if n>cap:raise RuntimeError("PDF_EXCEEDS_BOUNDED_MAX_"+key)
  with path.open("rb") as fo:
   if fo.read(4)!=b"%PDF":raise RuntimeError("NOT_PDF_"+key)
  pdf=fitz.open(path)
  book.update({"bytes":n,"sha256":sha.hexdigest(),"pdf_pages":len(pdf)})
  for i,p in enumerate(pdf):
   words=p.get_text("words")
   numeric=[w for w in words if re.fullmatch(r"[1-9][0-9]{0,3}",str(w[4]).strip())]
   short=[w for w in numeric if 1<=int(w[4])<=1400]
   # Collect only source page facts, no synthetic apartment/plot numbers.
   hits=[w for w in short if 1<=int(w[4])<=1300]
   if len(hits)>=35:
    ids=[int(w[4]) for w in hits]
    pc={"pdf_page_zero_based":i,"numeric_token_count":len(hits),"unique_values":len(set(ids)),
      "min":min(ids),"max":max(ids),"first_exact_tokens":[str(w[4]) for w in hits[:25]],
      "last_exact_tokens":[str(w[4]) for w in hits[-20:]],"page_dimensions":[round(p.rect.width,1),round(p.rect.height,1)],
      "sample_labeled_positions":[{"code":str(w[4]),"rect_pt":[round(z,1) for z in w[:4]]} for w in hits[:12]]}
    book["pages"].append(pc)
   txt=p.get_text("text")
   lines=[q.strip() for q in txt.splitlines() if q.strip()]
   relevant=[(j,q) for j,q in enumerate(lines) if re.search(r'unit.?no|apartment.?no|villa.?no|رقم الوحدة|رقم الفيلا|رقم الشقة|رقم القطعة|floor plan|floor layout|site plan|masterplan|master plan|بلو[كك]|المخطط العام',q,re.I)]
   if relevant:
    book["top_label_pages"].append({"page":i,"hit_count":len(relevant),"selected_text_context":[{"line":j,"surrounding":lines[max(0,j-1):min(len(lines),j+3)]} for j,q in relevant[:4]]})
  book["status"]="COMPLETE_PDF_TEXT_VECTORS";save()
  print("BROCHURE_SOURCE_EXAMINED "+json.dumps({"key":key,"bytes":n,"pages":len(pdf),"dense_numeric_pages":len(book["pages"]),"most_dense":sorted(book["pages"],key=lambda x:-x["unique_values"])[:8],"context":book["top_label_pages"][:10]},ensure_ascii=False,separators=(",",":")),flush=True)
  pdf.close();path.unlink(missing_ok=True)
 state["status"]="COMPLETE_ALL_SOURCE_ONLY"
except Exception as e:
 state["status"]="STOPPED_429" if "429" in str(e) else "STOPPED_ERROR"
 state["errors"].append(str(e)[:340])
finally:
 save()
 print("BROCHURE_FINAL "+json.dumps({"status":state["status"],"books":[{"key":x["key"],"status":x.get("status"),"pages":x.get("pdf_pages"),"bytes":x.get("bytes"),"dense_pages":len(x.get("pages",[]))} for x in state["books"]],"errors":state["errors"],"master_writes":0},separators=(",",":")))
if state["status"]!="COMPLETE_ALL_SOURCE_ONLY":sys.exit(2)
