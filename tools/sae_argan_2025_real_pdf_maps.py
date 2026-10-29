#!/usr/bin/env python3
"""Read-only exact first-party 2025 Alargan PDF map audit.
Input URLs sourced from the public official project pages' download links,
not guessed. No private data. Never creates unit rows automatically.
"""
import hashlib,io,json,re,urllib.request,urllib.robotparser,urllib.parse
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageDraw
import fitz
DOCS=[
 {"project_id":"PRJ-001483","name":"Fursan Dammam 2025 V3",
  "url":"https://alargan.com.sa/wp-content/uploads/2025/09/%D8%A8%D8%B1%D9%88%D8%B4%D9%88%D8%B1%20%D9%85%D8%B4%D8%B1%D9%88%D8%B9%20%D8%A7%D9%84%D9%81%D8%B1%D8%B3%D8%A7%D9%86%20%20V3%20.pdf?_t=1757255115"},
 {"project_id":"PRJ-001487","name":"Suhool Jubail 2025 V3",
  "url":"https://alargan.com.sa/wp-content/uploads/2025/09/%D8%A8%D8%B1%D9%88%D8%B4%D9%88%D8%B1%20%D9%85%D8%B4%D8%B1%D9%88%D8%B9%20%D8%A7%D9%84%D8%B4%D9%87%D9%88%D9%84%20V3.pdf?_t=1757255152"},
 {"project_id":"PRJ-001484","name":"Green Oasis Riyadh Villas 2025",
  "url":"https://alargan.com.sa/wp-content/uploads/2025/09/%D8%A7%D9%84%D9%88%D8%A7%D8%AD%D8%A9%20%D8%A7%D9%84%D8%AE%D8%B6%D8%B1%D8%A7%D8%A1%20%D9%81%D9%84%D9%84.pdf?_t=1757255158"},
 {"project_id":"PRJ-001484","name":"Green Oasis Riyadh Apartments 2025",
  "url":"https://alargan.com.sa/wp-content/uploads/2025/09/%D8%A7%D9%84%D9%88%D8%A7%D8%AD%D8%A9%20%D8%A7%D9%84%D8%AE%D8%B6%D8%B1%D8%A7%D8%A1%20%D8%A7%D9%84%D8%B4%D9%82%D9%82%20Small.pdf?_t=1757255154"}
]
out={"schema":"SAE_ALARGAN_2025_4_ACTUAL_FIRSTPARTY_BROCHURES_PLOT_AUDIT_V1","captured_utc":datetime.now(timezone.utc).isoformat(),"source_only":True,"sheets_writes":0,"sources":[]}
UA="SAE-DB-public-siteplan-research/1.0"
def robots(url):
 p=urllib.parse.urlsplit(url)
 with urllib.request.urlopen(urllib.request.Request(f"{p.scheme}://{p.netloc}/robots.txt",headers={"User-Agent":UA}),timeout=20) as f:
  if f.status!=200:return False
  rp=urllib.robotparser.RobotFileParser()
  rp.parse(f.read(250000).decode("utf-8","replace").splitlines())
  return rp.can_fetch(UA,url)
for entry in DOCS:
 x=dict(entry);x["errors"]=[]
 try:
  if not robots(entry["url"]):raise RuntimeError("ROBOTS_DENIED_OR_UNVERIFIED")
  with urllib.request.urlopen(urllib.request.Request(entry["url"],headers={"User-Agent":UA}),timeout=75) as r:
   x["status"]=r.status
   if r.status in (403,429):raise RuntimeError("STOP_ACCESS_"+str(r.status))
   content=r.read(50000000)
  if not content.startswith(b"%PDF"):raise RuntimeError("NOT_PDF")
  x["bytes"]=len(content);x["sha256"]=hashlib.sha256(content).hexdigest()
  pdf=fitz.open(stream=content,filetype="pdf")
  x["pages"]=len(pdf)
  cards=[];scores=[]
  for ix,page in enumerate(pdf):
   words=page.get_text("words")
   numeric=[str(w[4]).strip() for w in words if re.fullmatch(r"\d{3,5}",str(w[4]).strip())]
   unique=list(dict.fromkeys(numeric))
   text=page.get_text("text")
   scores.append({"pdf_page_zero_based":ix,"numeric_original_labels_count":len(numeric),
                  "distinct_numeric":len(unique),"numeric_example":unique[:20],
                  "text_mentions_siteplan":bool(re.search(r"المخطط|مخطط عام|site.?plan|master.?plan|block|بلوك|رقم الفيلا|رقم القطعة",text,re.I)),
                  "selectable_text_characters":len(text)})
   scale=.3
   pix=page.get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False)
   im=Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB");im.thumbnail((260,192))
   tile=Image.new("RGB",(276,220),"white");tile.paste(im,((276-im.width)//2,0))
   ImageDraw.Draw(tile).text((8,198),f"PDF p{ix+1}, words={len(unique)}",fill=(5,5,5))
   cards.append(tile)
  x["page_evidence"]=scores
  x["most_numbered_pages"]=sorted(scores,key=lambda z:z["distinct_numeric"],reverse=True)[:8]
  cols=5
  sheet=Image.new("RGB",(cols*276,((len(cards)+cols-1)//cols)*220),"white")
  for ix,im in enumerate(cards):sheet.paste(im,((ix%cols)*276,(ix//cols)*220))
  tag=entry["project_id"]+("-villas" if "Villas" in entry["name"] else "-apartments" if "Apartments" in entry["name"] else "")
  path=f"sae-argan-real-{tag}-contact.png";sheet.save(path,optimize=True)
  x["contact_sheet"]=path
  for hit in x["most_numbered_pages"][:3]:
   ix=hit["pdf_page_zero_based"]
   pix=pdf[ix].get_pixmap(matrix=fitz.Matrix(2.2,2.2),alpha=False)
   pix.save(f"sae-argan-real-{tag}-page-{ix+1}.png")
  x["status_audit"]="PDF_SOURCE_VERIFIED_NUMBERED_PLOT_QUALIFICATION_PENDING"
  pdf.close()
 except Exception as ex:
  x["status_audit"]="STOP_SOURCE_UNAVAILABLE"
  x["errors"].append(type(ex).__name__+":"+str(ex)[:250])
 out["sources"].append(x)
 Path("sae-argan-2025-real-brochure-siteplan-audit.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
 print(entry["name"],x["status_audit"],"pages",x.get("pages"),"top",[(p["pdf_page_zero_based"]+1,p["distinct_numeric"]) for p in x.get("most_numbered_pages",[])[:3]],"errors",x["errors"],flush=True)
