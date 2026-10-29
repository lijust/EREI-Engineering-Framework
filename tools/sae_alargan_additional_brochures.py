#!/usr/bin/env python3
"""First-party Al Argan additional brochures: source-only visual masterplan discovery.
Preserve original PDF hash and page locations; never manufacture individual units
from announced totals or from unnumbered architectural shapes.
"""
import hashlib,io,json,re,urllib.request,urllib.robotparser
from pathlib import Path
from datetime import datetime,timezone
from PIL import Image,ImageOps,ImageDraw

DOCS=[
 {"project_id":"PRJ-001491","name":"Murjana Dammam","marketing_total":327,
  "url":"https://alargan.com.sa/wp-content/uploads/2024/11/Murjana_Brochure-1.pdf"},
 {"project_id":"PRJ-001488","name":"Shurouq Riyadh","marketing_total":334,
  "url":"https://alargan.com.sa/en/shurouq-bruchore-new-2022/"}
]
UA="SAE-public-brochure-research/1.0"
def allowed(url):
 p=urllib.request.Request("https://alargan.com.sa/robots.txt",headers={"User-Agent":UA})
 with urllib.request.urlopen(p,timeout=15) as r:
  if r.status!=200:return False
  words=r.read(200000).decode("utf-8","replace")
 rp=urllib.robotparser.RobotFileParser();rp.parse(words.splitlines())
 return rp.can_fetch(UA,url)
def main():
 import fitz
 result={"schema":"SAE_OTHER_ALARGAN_OFFICIAL_MASTERPLAN_CONTACT_SHEETS_SOURCE_ONLY",
         "created_utc":datetime.now(timezone.utc).isoformat(),
         "sheets_writes":0,"brochures":[]}
 for doc in DOCS:
  obs=dict(doc)
  try:
   if not allowed(doc["url"]):raise RuntimeError("ROBOTS_DENIED")
   request=urllib.request.Request(doc["url"],headers={"User-Agent":UA})
   with urllib.request.urlopen(request,timeout=40) as r:
    obs["http_status"]=r.status
    if r.status in (403,429):raise RuntimeError("STOP_ACCESS_CONTROL_"+str(r.status))
    raw=r.read(28000000)
   obs["sha256"]=hashlib.sha256(raw).hexdigest()
   obs["source_bytes"]=len(raw)
   if not raw.startswith(b"%PDF"):raise RuntimeError("NOT_PDF")
   pdf=fitz.open(stream=raw,filetype="pdf")
   obs["page_count"]=len(pdf)
   ims=[];counts=[]
   for idx,p in enumerate(pdf):
    words=p.get_text("words")
    numbers=[w[4] for w in words if re.fullmatch(r"\d{4}",w[4])]
    counts.append({"pdf_zero_based":idx,"4digit_words":len(numbers),
                   "distinct_4digit":len(set(numbers)),
                   "sample":numbers[:15]})
    pix=p.get_pixmap(matrix=fitz.Matrix(.3,.3),alpha=False)
    image=Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    image.thumbnail((280,210))
    canvas=Image.new("RGB",(300,247),"white")
    canvas.paste(image,((300-image.width)//2,18))
    ImageDraw.Draw(canvas).text((8,226),f"PDF index={idx} / printed may differ",fill=(0,0,0))
    ims.append(canvas)
   cols=5;rows=(len(ims)+cols-1)//cols
   panel=Image.new("RGB",(cols*300,rows*247),"white")
   for i,im in enumerate(ims):panel.paste(im,((i%cols)*300,(i//cols)*247))
   dest="sae-alargan-contact-"+doc["project_id"]+".png"
   panel.save(dest,optimize=True)
   obs["contact_sheet"]=dest
   obs["pages"]=counts
   obs["total_original_4digit_words"]=sum(v["4digit_words"] for v in counts)
   obs["result"]="SOURCE_EVIDENCE_NOT_IMPORTABLE_WITHOUT_EXACT_UNIT_REVIEW"
   pdf.close()
  except Exception as e:
   obs["error"]=str(e)[:180]
   obs["result"]="STOP_SOURCE_UNAVAILABLE_OR_DISALLOWED"
  result["brochures"].append(obs)
  Path("sae-alargan-additional-pdf-discovery.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
  print(doc["name"],obs["result"],obs.get("page_count"),obs.get("total_original_4digit_words"),flush=True)
if __name__=="__main__":main()
