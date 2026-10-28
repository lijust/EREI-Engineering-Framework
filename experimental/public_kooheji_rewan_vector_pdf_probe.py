#!/usr/bin/env python3
"""Read-only examination of publisher vector PDF for individually numbered plots.

All candidate numbers are research-only until manual spatial/visual confirmation;
does not create invented unit rows and does not include SAE private project IDs.
"""
import json,os,re,sys,time,base64
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import requests
import fitz

URL="https://koohejidevelopment.sa/wp-content/uploads/2025/06/Kooheji-Development_Rewan-Al-Ruba-.pdf"
UA="SAE-DB-public-brochure-research/1.0"
out=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"rewan_masterplan_vector_unit_provenance.json"
doc={"schema":"SAE_DB_KOOHEJI_REWAN_VECTOR_PDF_RESEARCH_V1","source_url":URL,"status":"STARTED","pages":[],"candidate_plot_codes":[],"confirmed_physical_units":0,"master_writes":0,"errors":[]}
def save():
 out.write_text(json.dumps(doc,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
try:
 s=requests.Session();s.headers.update({"User-Agent":UA})
 robots_url="https://koohejidevelopment.sa/robots.txt"
 rr=s.get(robots_url,timeout=30,allow_redirects=False)
 if rr.status_code==429:raise RuntimeError("HTTP_429_STOP")
 if rr.status_code!=200:raise RuntimeError("ROBOTS_NOT_VERIFIABLE_"+str(rr.status_code))
 rp=RobotFileParser();rp.parse(rr.text.splitlines())
 if not rp.can_fetch(UA,URL):raise RuntimeError("ROBOTS_DISALLOW")
 time.sleep(max(3.0,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
 resp=s.get(URL,timeout=100,allow_redirects=False,stream=True)
 if resp.status_code==429:raise RuntimeError("HTTP_429_STOP")
 if resp.status_code!=200:raise RuntimeError("SOURCE_HTTP_"+str(resp.status_code))
 if urlparse(resp.url).hostname!="koohejidevelopment.sa":raise RuntimeError("SOURCE_HOST_CHANGED")
 b=bytearray()
 for chunk in resp.iter_content(chunk_size=262144):
  b.extend(chunk)
  if len(b)>38_000_000:raise RuntimeError("PDF_TOO_LARGE")
 if not b.startswith(b"%PDF"):raise RuntimeError("NOT_A_PDF")
 pdf=fitz.open(stream=bytes(b),filetype="pdf")
 doc["pdf_bytes"]=len(b);doc["pdf_pages"]=len(pdf)
 try:
  page=pdf[26]
  pix=page.get_pixmap(matrix=fitz.Matrix(1.25,1.25),alpha=False)
  packed=pix.tobytes("jpeg",jpg_quality=58)
  print("REWAN_SITEPLAN_PAGE27_JPEG_BASE64 "+base64.b64encode(packed).decode("ascii"))
 except Exception as image_exc:
  print("REWAN_SITEPLAN_IMAGE_ERROR "+str(image_exc)[:250])
 for i,page in enumerate(pdf):
  words=page.get_text("words")
  codes=[]
  for w in words:
   text=str(w[4]).strip()
   if re.fullmatch(r"[0-9]{1,4}",text):
    n=int(text)
    if 1<=n<=1300:codes.append({"code":text,"x":round(w[0],1),"y":round(w[1],1),"x2":round(w[2],1),"y2":round(w[3],1)})
  if len(codes)>=45:
   doc["pages"].append({"page_zero_based":i,"page_size":[round(page.rect.width,2),round(page.rect.height,2)],"number_token_count":len(codes),"unique_numbers":len(set(x["code"] for x in codes)),"numbers":codes})
  elif len(codes)>=8:
   doc["pages"].append({"page_zero_based":i,"number_token_count":len(codes),"unique_numbers":len(set(x["code"] for x in codes))})
  save()
 doc["status"]="COMPLETE_VECTOR_INVENTORY_PROBE"
except Exception as e:
 doc["status"]="STOPPED" if "429" in str(e) else "SOURCE_PROBE_ERROR"
 doc["errors"].append(str(e)[:240])
finally:
 save()
 print("REWAN_VECTOR_RESULT "+json.dumps({"status":doc["status"],"pdf_pages":doc.get("pdf_pages"),"pdf_bytes":doc.get("pdf_bytes"),"candidate_pages":[{k:v for k,v in p.items() if k!="numbers"} for p in doc["pages"] if p.get("number_token_count",0)>=45],"error":doc["errors"],"confirmed_new_physical_units":0,"master_writes":0},separators=(",",":")))
if doc["status"]=="COMPLETE_VECTOR_INVENTORY_PROBE":
 for p in doc["pages"]:
  if p.get("page_zero_based")==26 and "numbers" in p:
   raw=p["numbers"]
   nset={int(x["code"]) for x in raw}
   missing=[n for n in range(1,1301) if n not in nset]
   print("REWAN_P26_NUMBER_VALIDATION "+json.dumps({"min":min(nset),"max":max(nset),"unique":len(nset),"missing_1_to_1300":missing,"duplicate_tokens":len(raw)-len(nset),"page_width":p["page_size"][0],"page_height":p["page_size"][1],"x_range":[min(x["x"] for x in raw),max(x["x2"] for x in raw)],"y_range":[min(x["y"] for x in raw),max(x["y2"] for x in raw)]},separators=(",",":")))
   for i in range(0,len(raw),65):
    print("REWAN_P26_VECTOR_ROWS "+json.dumps(raw[i:i+65],separators=(",",":")))
if doc["status"]!="COMPLETE_VECTOR_INVENTORY_PROBE":sys.exit(2)
