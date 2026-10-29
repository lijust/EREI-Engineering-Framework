#!/usr/bin/env python3
"""Publisher PDFs: examine original *printed* individual inventory labels for
two existing Dar wa Emaar projects. Read only; counts never become units.
"""
import hashlib, io, json, re, urllib.request, urllib.robotparser
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import fitz

SEEDS=[
 {"pid":"PRJ-001463","name":"سرايا لازورد","project_url":"https://darwaemaar.com/project/saraya-lazurd-2/","pdf":"https://darwaemaar.com/wp-content/uploads/2025/09/Saraya-Lazurd-Brochure-Mobile-Version-Small-size.pdf","marketing":912},
 {"pid":"PRJ-001463","name":"سرايا لازورد full V2","project_url":"https://darwaemaar.com/project/saraya-lazurd-2/","pdf":"https://darwaemaar.com/wp-content/uploads/2025/08/Saraya-Lazurd-Brochure-V2-2.pdf","marketing":912},
 {"pid":"PRJ-001462","name":"النرجس هايتس","project_url":"https://darwaemaar.com/project/al-narjes-heights/","pdf":"https://darwaemaar.com/wp-content/uploads/2025/11/Alnarjis-Communities-Brochure-5.pdf","marketing":210}
]
UA="SAE-DB-original-brochure-plot-evidence/1.0"
OUT=Path("sae-darwa-lazurd-narjes-original-brochures-readonly.json")
D={"schema":"SAE_DARWA_EXISTING_PROJECTS_BROCHURE_WORD_MAP_PROBE_V1",
   "utc":datetime.now(timezone.utc).isoformat(),"master_writes":0,"sources":[]}
PLOT=re.compile(r"^(?:[A-Z]{0,3}[-/]?)?\d{2,5}(?:[-/][A-Z]?\d{1,4})?$",re.I)
def check(url):
 p=urlsplit(url)
 if p.scheme!="https" or p.hostname not in ("darwaemaar.com","www.darwaemaar.com"):
  raise ValueError("UNTRUSTED_HOST")
 req=urllib.request.Request("https://darwaemaar.com/robots.txt",headers={"User-Agent":UA})
 with urllib.request.urlopen(req,timeout=20) as r:
  if r.status!=200:raise RuntimeError("ROBOTS_HTTP_"+str(r.status))
  raw=r.read(150001)
 if len(raw)>150000:raise RuntimeError("ROBOTS_TOO_LARGE")
 rp=urllib.robotparser.RobotFileParser();rp.parse(raw.decode("utf8","replace").splitlines())
 return rp.can_fetch(UA,url)
def pdf_read(seed):
 item={**seed,"status":"STARTED","errors":[]}
 D["sources"].append(item)
 try:
  allowed=check(seed["pdf"])
  if not allowed:raise RuntimeError("ROBOTS_DISALLOW_PDF")
  with urllib.request.urlopen(urllib.request.Request(seed["pdf"],headers={"User-Agent":UA}),timeout=60) as r:
   item["http"]=r.status
   if r.status in (403,429):raise RuntimeError("STOP_HTTP_"+str(r.status))
   raw=r.read(60000001)
  if len(raw)>60000000 or not raw.startswith(b"%PDF"):raise RuntimeError("NOT_PUBLIC_PDF_OR_TOO_LARGE")
  item["sha256"]=hashlib.sha256(raw).hexdigest()
  item["bytes"]=len(raw)
  doc=fitz.open(stream=raw,filetype="pdf")
  item["pages"]=len(doc);item["page_metrics"]=[]
  for i,page in enumerate(doc):
   words=page.get_text("words",sort=False)
   labels=[{"code":str(w[4]).strip(".,:;"),"bbox":[round(z,2) for z in w[:4]]} for w in words
           if PLOT.fullmatch(str(w[4]).strip(".,:;"))]
   counts=Counter(x["code"] for x in labels)
   boxarea=page.rect.width*page.rect.height
   modechars=len(page.get_text("text"))
   item["page_metrics"].append({
    "page":i,"size":[round(page.rect.width),round(page.rect.height)],
    "text_chars":modechars,"image_count":len(page.get_images(full=False)),
    "candidate_code_word_count":len(labels),
    "unique_candidate_codes":len(counts),
    "labels":labels[:1800],
    "likely_siteplan":len(labels)>=75 and len(counts)>=70,
    "page_has_printed_plot_context":bool(re.search("مخطط|map|site plan|master plan|block|villa",page.get_text("text"),re.I))
   })
  item["top_label_pages"]=sorted([{"page":x["page"],"word_count":x["candidate_code_word_count"],
     "distinct":x["unique_candidate_codes"],"text_chars":x["text_chars"],
     "image_count":x["image_count"],"context":x["page_has_printed_plot_context"]}
     for x in item["page_metrics"]],key=lambda a:-a["distinct"])[:12]
  item["potential_original_plotted_pages"]=[x["page"] for x in item["page_metrics"] if x["likely_siteplan"]]
  item["status"]="PDF_TEXT_VECTOR_SURVEY_FINISHED_SOURCE_ONLY"
  doc.close()
 except Exception as exc:
  item["status"]="SOURCE_STOP_OR_UNVERIFIED"
  item["errors"].append(type(exc).__name__+":"+str(exc)[:250])
 OUT.write_text(json.dumps(D,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("SAE_DARWA_BROCHURE_SOURCE",json.dumps({
  "pid":item["pid"],"pdf":item["pdf"],"status":item["status"],
  "pages":item.get("pages"),"top":item.get("top_label_pages",[])[:7],
  "image_or_text_plans":item.get("potential_original_plotted_pages",[])[:16],
  "errors":item["errors"]},ensure_ascii=False),flush=True)
if __name__=="__main__":
 for s in SEEDS:
  pdf_read(s)
  if D["sources"][-1].get("errors") and "429" in " ".join(D["sources"][-1]["errors"]):
   break
