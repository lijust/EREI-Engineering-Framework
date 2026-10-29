#!/usr/bin/env python3
"""Read-only: official Wakan 043/045 public brochure link annotations and
individual plot/siteplan original identity. No synthetic units from totals.
Public official direct GDrive PDFs only; stop on access/robots errors.
"""
import urllib.request, urllib.error, urllib.robotparser, json, hashlib, re, time
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit
import fitz

UA="SAE-DB-original-Wakan-project-public-plan/1.0"
SEEDS=[
 {"project":"PRJ-000820","name":"وكن 043","original_official":"https://wakan.sa/EstateProjects",
  "public_brochure":"https://drive.google.com/file/d/1vLL7yikiwWuaDU9hOZi1I1MvcrVQx5Ic/view?usp=drive_link",
  "drive_id":"1vLL7yikiwWuaDU9hOZi1I1MvcrVQx5Ic"},
 {"project":"PRJ-000825","name":"وكن 045","original_official":"https://wakan.sa/EstateProjects",
  "public_brochure":"https://drive.google.com/file/d/18wsIvR86myjvL-6PCqG479hbAfLJnKHH/view?usp=drive_link",
  "drive_id":"18wsIvR86myjvL-6PCqG479hbAfLJnKHH"}
]
O=Path("sae-wakan-043-045-firstparty-brochure-links.json")
data={"schema":"SAE_WAKAN_EXISTING_043_045_ORIGINAL_PUBLIC_GDRIVE_LINKED_BROCHURE_DEEP_SCAN",
      "utc":datetime.now(timezone.utc).isoformat(),"production_writes":0,"sources":[]}

def robots(url):
 u=urlsplit(url)
 if u.scheme!="https" or u.hostname not in ("drive.google.com","docs.google.com"):
  raise RuntimeError("HOST_NOT_OFFICIAL_PUBLIC_GDRIVE")
 robotsurl=u.scheme+"://"+u.netloc+"/robots.txt"
 with urllib.request.urlopen(urllib.request.Request(robotsurl,headers={"User-Agent":UA}),timeout=20) as f:
  if f.status!=200:raise RuntimeError("ROBOTS_STATUS_"+str(f.status))
  txt=f.read(200000).decode("utf8","replace")
 rp=urllib.robotparser.RobotFileParser()
 rp.parse(txt.splitlines())
 if not rp.can_fetch(UA,url):raise RuntimeError("ROBOTS_DISALLOW")
 return True

def check_url(url):
 u=urlsplit(url)
 if u.scheme!="https" or u.hostname not in ("drive.google.com","docs.google.com"):
  raise RuntimeError("UNEXPECTED_HOST")
 return True

def download(seed, item):
 # Only the original officially linked PUBLIC Drive file and its public
 # standard download endpoint, no credentials or auth bypass.
 original=seed["public_brochure"]
 direct="https://drive.google.com/uc?export=download&id="+seed["drive_id"]
 for url in (direct,original):
  try:
   robots(url)
   req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/pdf,*/*"})
   with urllib.request.urlopen(req,timeout=48) as f:
    if f.status in (403,429):raise RuntimeError("ORIGIN_HTTP_"+str(f.status))
    final=f.url;check_url(final)
    raw=f.read(35000001)
    ct=f.headers.get("content-type","")
   item["download_trials"].append({"mode":"standard_public","status":200,
      "final_domain":urlsplit(final).hostname,"mime":ct,"bytes":len(raw),
      "sha256":hashlib.sha256(raw).hexdigest()})
   if len(raw)>35000000:raise RuntimeError("FILE_TOO_LARGE")
   if raw.startswith(b"%PDF"):return raw
   if b"<html" in raw[:300].lower():
    item["download_trials"][-1]["reason"]="GOOGLE_DRIVE_HTML_PREVIEW_NOT_PDF"
  except urllib.error.HTTPError as exc:
   item["download_trials"].append({"url":url,"status":exc.code,"failure":"HTTPError"})
   if exc.code in (403,429):raise RuntimeError("STOP_ACCESS_"+str(exc.code))
  except Exception as exc:
   item["download_trials"].append({"url":url,"failure":type(exc).__name__+":"+str(exc)[:100]})
   if "ROBOTS" in str(exc) or "STOP_ACCESS" in str(exc):break
 return None

def inspect_pdf(pdf_bytes, item):
 doc=fitz.open(stream=pdf_bytes,filetype="pdf")
 item["pages"]=len(doc);item["source_pdf_sha256"]=hashlib.sha256(pdf_bytes).hexdigest()
 item["total_link_annotations"]=0
 item["link_references"]=[]
 item["page_stats"]=[]
 for i,page in enumerate(doc):
  links=page.get_links();item["total_link_annotations"]+=len(links)
  for link in links[:200]:
   rawuri=link.get("uri")
   item["link_references"].append({"page_zero_based":i,"uri":rawuri,
      "internal_page":link.get("page"),"kind":link.get("kind"),
      "bbox":str(link.get("from"))[:95]})
  words=[(w[4],*[round(q,1) for q in w[:4]]) for w in page.get_text("words",sort=True)]
  numwords=[w for w in words if re.fullmatch(r"(?:(?:[A-Z]{1,2}[-/]?)?\d{2,4}(?:[-/]\d{1,3})?)",w[0],re.I)]
  item["page_stats"].append({"page":i,"text_chars":len(page.get_text("text")),
    "numeric_candidates":len(numwords),"sample":numwords[:25],
    "link_count":len(links),"image_count":len(page.get_images(full=False))})
 doc.close()
 item["top_candidate_pages"]=sorted(item["page_stats"],key=lambda v:v["numeric_candidates"],reverse=True)[:12]
 item["status"]="PDF_INSPECTED_LINKS_AND_NUMBERED_WORDS_READONLY"

for seed in SEEDS:
 item={**seed,"status":"STARTED","download_trials":[],"errors":[]}
 data["sources"].append(item)
 try:
  raw=download(seed,item)
  if raw is not None:inspect_pdf(raw,item)
  else:item["status"]="PUBLIC_DIRECT_PDF_NOT_DOWNLOADED"
 except Exception as exc:
  item["status"]="FAIL_CLOSED_SOURCE_ACCESS"
  item["errors"].append(type(exc).__name__+":"+str(exc)[:220])
 O.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("SAE_WAKAN_PDF_SOURCE",json.dumps({"project":item["project"],"status":item["status"],
   "download_trials":item["download_trials"],"pages":item.get("pages"),
   "annotations":item.get("total_link_annotations"),"first_links":item.get("link_references",[])[:25],
   "top_pages":item.get("top_candidate_pages",[])[:5],
   "errors":item["errors"]},ensure_ascii=False)[:12000],flush=True)
 if item.get("errors") and "429" in " ".join(item["errors"]):break
 time.sleep(2)
