#!/usr/bin/env python3
"""First-party Al Argan Murooj brochure numbered-plot discovery; source-only."""
import hashlib,json,re,urllib.request,urllib.robotparser
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

URL="https://alargan.com.sa/wp-content/uploads/2024/11/Murooj_Brochure.pdf"
OUT=Path("sae-murooj-pdf-numerical-evidence.json")
UA="SAE-DB-public-source-review/1.0"
report={"schema":"SAE_FIRSTPARTY_MUROOJ_PDF_MAP_NUMBERED_PLOTS_SOURCE_ONLY",
        "source_url":URL,"project_id":"PRJ-001489",
        "project_name":"مروج","source_project_total":324,
        "generated_utc":datetime.now(timezone.utc).isoformat(),
        "production_writes":0,"pages":[]}
try:
    robots_url="https://alargan.com.sa/robots.txt"
    with urllib.request.urlopen(urllib.request.Request(robots_url,headers={"User-Agent":UA}),timeout=20) as res:
        if res.status!=200:raise RuntimeError("ROBOTS_NON_200_"+str(res.status))
        lines=res.read(100000).decode("utf-8","replace").splitlines()
    rp=urllib.robotparser.RobotFileParser();rp.parse(lines)
    report["robots_permitted"]=rp.can_fetch(UA,URL)
    if not report["robots_permitted"]:raise RuntimeError("ROBOTS_DENIED")
    with urllib.request.urlopen(urllib.request.Request(URL,headers={"User-Agent":UA}),timeout=40) as res:
        report["http_status"]=res.status
        if res.status in (403,429):raise RuntimeError("STOP_HTTP_"+str(res.status))
        b=res.read(30000000)
    report["source_size"]=len(b);report["source_sha256"]=hashlib.sha256(b).hexdigest()
    if not b.startswith(b"%PDF"):raise RuntimeError("NOT_PDF")
    import fitz
    doc=fitz.open(stream=b,filetype="pdf")
    report["pdf_pages"]=len(doc)
    plot=re.compile(r"^\d{3,5}$")
    for i,page in enumerate(doc):
        words=page.get_text("words",sort=True)
        candidates=[]
        for x in words:
            w=str(x[4]).strip()
            if plot.fullmatch(w):
                candidates.append({"label":w,"bbox_pt":[round(q,2) for q in x[:4]]})
        report["pages"].append({"page_zero_based":i,"numeric_labels":len(candidates),
            "distinct_numeric_labels":len(set(x["label"] for x in candidates)),
            "candidate_numbered_plot_words":candidates})
    best=sorted(report["pages"],key=lambda x:x["numeric_labels"],reverse=True)[:5]
    report["top_pages"]=[{"index":x["page_zero_based"],
                        "numeric_labels":x["numeric_labels"],
                        "distinct_labels":x["distinct_numeric_labels"]} for x in best]
    for ix in [23,24,25,26,27]:
        if ix >= len(doc):continue
        pix=doc[ix].get_pixmap(matrix=fitz.Matrix(2.8,2.8),alpha=False)
        pix.save("sae-murooj-map-page-"+str(ix+1)+".png")
    doc.close()
    report["status"]="SOURCE_NUMERIC_SITEPLAN_WORDS_NOT_YET_HUMAN_VERIFIED"
except Exception as e:
    report["status"]="HOLD_SOURCE_UNAVAILABLE_OR_NOT_ALLOWED"
    report["error"]=str(e)[:300]
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"status":report["status"],"pages":report.get("pdf_pages"),
                  "best":report.get("top_pages"),"error":report.get("error")},ensure_ascii=False))
