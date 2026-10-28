#!/usr/bin/env python3
"""Public first-party Kooheji Lavira brochure source table extraction, no DB private IDs."""
import json,os,time,hashlib,re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
import fitz
HOST="koohejidevelopment.sa"
ROOT="https://"+HOST
URLS={
 "bareh":ROOT+"/wp-content/uploads/2025/06/Kooheji-Development_Lavira-Bareh-.pdf",
 "thuraya":ROOT+"/wp-content/uploads/2025/06/Kooheji-Development_Lavira-Thuraya-.pdf"
}
UA="SAE-public-Kooheji-original-villa-unit-research/1.0"
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"lavira_publisher_pdf_source_tables.json"
state={"schema":"LAVIRA_KOOHEJI_FIRSTPARTY_PDF_ITEMIZED_UNIT_TABLES_V1","status":"START",
       "source_brochures":[],"rows":[],"pages_with_unit_tables":[],"errors":[],"master_writes":0,"private_project_ids":False}
def save():OUT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def fetch(url):
 p=urlsplit(url)
 if p.scheme!="https" or p.hostname!=HOST:raise ValueError("BAD_HOST")
 x=Fetcher.get(url,retries=0,timeout=80,follow_redirects="safe",headers={"User-Agent":UA})
 if int(x.status)==429:raise RuntimeError("GLOBAL_STOP_429")
 if int(x.status)!=200:raise RuntimeError("HTTP_"+str(x.status))
 if urlsplit(str(x.url)).hostname!=HOST:raise ValueError("OFF_SOURCE_REDIRECT")
 return x
try:
 robot=fetch(ROOT+"/robots.txt")
 rp=RobotFileParser();rp.parse(robot.body.decode("utf8","replace").splitlines())
 for name,url in URLS.items():
  if not rp.can_fetch(UA,url):
   state["source_brochures"].append({"key":name,"url":url,"status":"ROBOTS_DISALLOW"});continue
  time.sleep(max(3,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
  res=fetch(url)
  b=res.body
  if not b.startswith(b"%PDF") or len(b)>65_000_000:raise RuntimeError("NOT_PDF_OR_TOO_BIG_"+name)
  doc=fitz.open(stream=b,filetype="pdf")
  book={"key":name,"url":url,"pages":len(doc),"sha256":hashlib.sha256(b).hexdigest(),
        "size_bytes":len(b),"pages_with_unit_label":[]}
  for page_idx,page in enumerate(doc):
   t=page.get_text("text")
   labels=bool(re.search("رقم الوحدة|الوحدات|unit no|unit number",t,re.I))
   if not labels:continue
   book["pages_with_unit_label"].append(page_idx+1)
   # record exact original publisher text lines around physical table
   lines=[v.strip() for v in t.splitlines() if v.strip()]
   for batch_start in range(0,len(lines),35):
    print("ORIGINAL_PDF_NUMBERED_UNIT_PAGE_LINES "+json.dumps({"source":name,"page":page_idx+1,"start":batch_start,"lines":lines[batch_start:batch_start+35]},ensure_ascii=False,separators=(",",":")),flush=True)
   # All labels explicitly present on the publisher drawing, never generated from a declared 264-unit total.
   block="61" if name=="bareh" else "47"
   source_matches={}
   for match in re.finditer(r"(?<![\\w])(?:("+block+r")[-\\s]([0-9]{2})|([0-9]{2})[-\\s]("+block+r"))(?![\\w])",t):
    raw=match.group(0)
    n=int(match.group(2) or match.group(3))
    if not 1<=n<=99:continue
    k=block+"-"+str(n).zfill(2)
    source_matches.setdefault(k,set()).add(raw)
   stage=[{"publisher_block":block,"original_label_normalized":k,
           "original_text_variants":sorted(v),"source":name,"pdf_url":url,
           "publisher_page_number":page_idx+1,"source_page_sha256":hashlib.sha256(b).hexdigest(),
           "verification":"PUBLISHER_NUMBERED_SITE_PLAN_SOURCE_ONLY_NO_CURRENT_STATUS"} for k,v in source_matches.items()]
   stage.sort(key=lambda x:int(x["original_label_normalized"].split("-")[1]))
   state.setdefault("numbered_site_plan_unit_identifiers",[]).extend(stage)
   print("PDF_ORIGINAL_NUMBERED_PLOT_CODES "+json.dumps({"source":name,"page":page_idx+1,"codes":stage},ensure_ascii=False,separators=(",",":")),flush=True)
   tables=page.find_tables()
   matches=[]
   for table_no,table in enumerate(tables.tables):
    grid=table.extract()
    if len(grid)<2:continue
    for row_num,row in enumerate(grid):
     vals=[(z or "").strip() if isinstance(z,str) else str(z or "") for z in row]
     if not any(z for z in vals):continue
     state["rows"].append({"source":name,"pdf_url":url,"page_number":page_idx+1,"table_index":table_no,
                           "row_num":row_num,"original_cells":vals})
     matches.append(vals)
    print("PDF_TABLE_RAW_SHAPE "+json.dumps({"source":name,"page":page_idx+1,"table":table_no,"rows":len(grid),"columns":table.col_count,"first":grid[:5]},ensure_ascii=False)[:3500],flush=True)
   sample={"source":name,"page":page_idx+1,"text_line_count":len(lines),"tables":len(tables.tables),
           "matching_rows":len(matches),"text_sample":lines[:60]}
   state["pages_with_unit_tables"].append(sample)
   print("PDF_PAGE_SOURCE_DIAGNOSTIC "+json.dumps({k:sample[k] for k in ("source","page","text_line_count","tables","matching_rows")},ensure_ascii=False),flush=True)
   if not matches:
    print("PDF_PAGE_NO_TABLE_TEXT "+json.dumps(sample,ensure_ascii=False)[:3500],flush=True)
   save()
  state["source_brochures"].append(book)
  print("PDF_BROCHURE_COMPLETE "+json.dumps(book,ensure_ascii=False),flush=True)
  save()
 state["status"]="COMPLETE_FIRSTPARTY_PDF_SOURCE_ONLY"
except Exception as e:
 state["status"]="STOPPED_429" if "429" in str(e) else "STOPPED_ERROR"
 state["errors"].append(type(e).__name__+": "+str(e)[:300])
finally:
 state["total_raw_rows"]=len(state["rows"])
 save()
 print("PDF_SOURCE_RUN_RESULT "+json.dumps({k:state[k] for k in ("status","source_brochures","total_raw_rows","errors","master_writes")},ensure_ascii=False),flush=True)
 for i in range(0,len(state["rows"]),14):
  print("LAVIRA_UNIT_TABLE_SOURCE_ROWS "+json.dumps(state["rows"][i:i+14],ensure_ascii=False,separators=(",",":")),flush=True)
if state["status"]!="COMPLETE_FIRSTPARTY_PDF_SOURCE_ONLY":raise SystemExit(2)
