#!/usr/bin/env python3
"""SAE public first-party Fursan PDF siteplan discovery. No DB writes."""
import io,json,hashlib,re,urllib.request,urllib.robotparser
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageDraw
import fitz

DOCS=[
  {"project":"PRJ-001483","name":"بيوت الفرسان الدمام",
   "url":"https://alargan.com.sa/wp-content/uploads/2018/09/Fursan-Bruchore-2022.pdf",
   "developer_project_page":"https://alargan.com.sa/fursan/","marketing_total":623},
  {"project":"PRJ-001484","name":"الواحة الخضراء",
   "url":"https://alargan.com.sa/wp-content/uploads/2018/09/GreenOasis_Bruchore.pdf",
   "developer_project_page":"https://alargan.com.sa/green-oasis/","marketing_total":931}
]
UA="SAE-DB-original-public-PDF-study/1.0"
out={"schema":"SAE_FIRSTPARTY_ARGAN_TWO_OFFICIAL_BROCHURES_READ_ONLY",
     "captured_at_utc":datetime.now(timezone.utc).isoformat(),"source_only":True,
     "sheets_writes":0,"brochures":[]}
def allow(url):
    p=urllib.request.urlsplit(url)
    request=urllib.request.Request("https://"+p.hostname+"/robots.txt",headers={"User-Agent":UA})
    with urllib.request.urlopen(request,timeout=20) as r:
        if r.status!=200:return False,"ROBOTS_HTTP_"+str(r.status)
        content=r.read(200000).decode("utf-8","replace")
    rp=urllib.robotparser.RobotFileParser()
    rp.parse(content.splitlines())
    return rp.can_fetch(UA,url),"ROBOTS_CHECKED"

for doc in DOCS:
    record=dict(doc,word_counts=[],errors=[])
    try:
        permitted,rule=allow(doc["url"])
        record["robots"]={"allowed":permitted,"result":rule}
        if not permitted:raise RuntimeError("ROBOTS_DENIED")
        request=urllib.request.Request(doc["url"],headers={"User-Agent":UA})
        with urllib.request.urlopen(request,timeout=48) as response:
            record["status_code"]=response.status
            if response.status in (403,429):raise RuntimeError("STOP_ACCESS_"+str(response.status))
            data=response.read(40_000_000)
        if not data.startswith(b"%PDF"):raise RuntimeError("NOT_PDF")
        record["sha256"]=hashlib.sha256(data).hexdigest()
        record["pdf_bytes"]=len(data)
        pdf=fitz.open(stream=data,filetype="pdf")
        record["page_count"]=len(pdf)
        panels=[]
        for i,p in enumerate(pdf):
            text=p.get_text("text")
            words=p.get_text("words")
            labels=[str(w[4]).strip() for w in words if re.fullmatch(r"[0-9]{3,6}",str(w[4]).strip())]
            record["word_counts"].append({"page_zero_based":i,"number_words":len(labels),
                 "distinct_number_words":len(set(labels)),
                 "sample_codes":list(dict.fromkeys(labels))[:12],
                 "siteplan_context":bool(re.search(r"مخطط|masterplan|site.?plan|block|بلوك|lot|plot",text,re.I))})
            pix=p.get_pixmap(matrix=fitz.Matrix(.32,.32),alpha=False)
            im=Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            im.thumbnail((245,180))
            tile=Image.new("RGB",(260,205),"white")
            tile.paste(im,((260-im.width)//2,0))
            ImageDraw.Draw(tile).text((9,185),f"PDF page {i+1}; numeric={len(labels)}",fill=(10,10,10))
            panels.append(tile)
        cols=5
        target=Image.new("RGB",(260*cols,205*((len(panels)+cols-1)//cols)),"white")
        for i,p in enumerate(panels):target.paste(p,((i%cols)*260,(i//cols)*205))
        thumb="sae-argan-"+doc["project"]+"-contact.png"
        target.save(thumb,optimize=True)
        record["contact_image"]=thumb
        record["pages_with_more_than_12_digit_labels"]=[x["page_zero_based"] for x in record["word_counts"] if x["distinct_number_words"]>=12]
        pdf.close()
        record["conclusion"]="PDF_DOWNLOADED_NEEDS_PER_UNIT_SITEPLAN_IDENTITY_REVIEW"
    except Exception as e:
        record["errors"].append(type(e).__name__+":"+str(e)[:230])
        record["conclusion"]="STOP_UNAVAILABLE_OR_UNVERIFIED"
    out["brochures"].append(record)
    Path("sae-argan-fursan-green-oasis-public-brochures.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
    print(doc["project"],record["conclusion"],record.get("page_count"),record["errors"],flush=True)
