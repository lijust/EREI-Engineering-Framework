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
  p26=pdf[26]
  drawings=p26.get_drawings()
  sample_colors={}
  known={"C1":[135.2,663.2],"C2":[135.2,680.8],"D1":[135.2,718.4],"D2":[135.2,735.0],"E1":[135.2,765.6],"E2":[135.2,782.0],"A1":[227.2,662.0],"A2":[227.2,680.0],"A3":[227.2,697.0],"B1":[227.2,719.0],"B2":[227.2,735.0],"B3":[227.2,753.0],"FACILITIES":[227.2,780.0]}
  pp=p26.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
  def sample(x,y):
   sx,sy=int(x*2),int(y*2)
   if sx<0 or sy<0 or sx>=pp.width or sy>=pp.height:return None
   i=(sy*pp.width+sx)*pp.n
   return "#"+bytes(pp.samples[i:i+3]).hex()
  for typ,(x,y) in known.items():
   sample_colors[typ]=sample(x,y)
  words=[w for w in p26.get_text("words") if re.fullmatch(r"[0-9]{1,4}",str(w[4]).strip()) and 1<=int(w[4])<=1270 and float(w[1])<800]
  report={"drawings":len(drawings),"fill_drawings":sum(1 for z in drawings if z.get("fill")),"reference_colors":sample_colors,"sample_words":[]}
  for w in words[:35]+words[-35:]:
   cx,cy=(w[0]+w[2])/2,(w[1]+w[3])/2
   f=[z for z in drawings if z.get("fill") and z.get("rect") and z["rect"].contains(fitz.Point(cx,cy))]
   report["sample_words"].append({"unit":w[4],"xy":[round(cx,1),round(cy,1)],"pixel":[sample(cx-3,cy),sample(cx+3,cy),sample(cx,cy+4)],"candidate_fills":[[list(round(k,3) for k in z["fill"]),str(z.get("rect"))[:110]] for z in f[-3:]]})
  print("REWAN_SITEPLAN_MODEL_DIAGNOSTIC "+json.dumps(report,separators=(",",":")))
 except Exception as diag_error:print("REWAN_MODEL_DIAGNOSTIC_ERROR "+str(diag_error)[:250])
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
 try:
  p26=pdf[26]
  pp=p26.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
  swatch_xy={"C1":[135.2,663.2],"C2":[135.2,680.8],"D1":[135.2,718.4],"D2":[135.2,735.0],"E1":[135.2,765.6],"E2":[135.2,782.0],"A1":[227.2,662.0],"A2":[227.2,680.0],"A3":[227.2,697.0],"B1":[227.2,719.0],"B2":[227.2,735.0],"B3":[227.2,753.0],"FACILITIES":[227.2,780.0]}
  def rgb_at(x,y):
   sx,sy=round(x*2),round(y*2)
   if sx<0 or sy<0 or sx>=pp.width or sy>=pp.height:return None
   j=(sy*pp.width+sx)*pp.n
   return tuple(pp.samples[j:j+3])
  palette={k:rgb_at(*xy) for k,xy in swatch_xy.items()}
  import math,collections
  cards=[]
  words=[w for w in p26.get_text("words") if re.fullmatch(r"[0-9]{1,4}",str(w[4]).strip()) and 1<=int(w[4])<=1270 and float(w[1])<800]
  for w in words:
   cx,cy=(w[0]+w[2])/2,(w[1]+w[3])/2
   samples=[(-3,0),(3,0),(-2.1,-2.3),(2.1,-2.3),(-2.1,2.3),(2.1,2.3),(0,-3.6),(0,3.6),(-4.5,0),(4.5,0)]
   good=[]
   for dx,dy in samples:
    px=rgb_at(cx+dx,cy+dy)
    if px is None:continue
    ranks=sorted((math.dist(px,color),key) for key,color in palette.items())
    if ranks[0][0]<=36:good.append(ranks[0])
   votes=collections.Counter(k for _,k in good)
   if votes:
    best,num=votes.most_common(1)[0]
    ds=sorted(d for d,k in good if k==best)
    second=max([v for k,v in votes.items() if k!=best] or [0])
    confidence="HIGH" if num>=4 and second<=1 and ds[len(ds)//2]<15 else ("MEDIUM" if num>=3 and num>second*2 and ds[len(ds)//2]<27 else "LOW")
    dist=round(ds[len(ds)//2],1)
   else:best="UNCLASSIFIED";num=0;second=0;dist=None;confidence="UNCLASSIFIED"
   cards.append({"publisher_plot_label":str(w[4]),"villa_type":best,"confidence":confidence,"vote_count":num,"runner_up_vote_count":second,"median_color_distance":dist})
  cards.sort(key=lambda x:int(x["publisher_plot_label"]))
  if len(cards)!=1270 or len(set(x["publisher_plot_label"] for x in cards))!=1270:raise ValueError("LABEL_COUNT_DID_NOT_MATCH_1270")
  grouped=dict(collections.Counter(c["villa_type"] for c in cards))
  conf=dict(collections.Counter(c["confidence"] for c in cards))
  print("REWAN_TYPE_CLASSIFICATION_SUMMARY "+json.dumps({"plot_labels":len(cards),"model_distribution":grouped,"confidence":conf,"non_villa_or_unclassified":[c for c in cards if c["villa_type"] in ("FACILITIES","UNCLASSIFIED")],"low_confidence_examples":[c for c in cards if c["confidence"]=="LOW"][:20]},separators=(",",":")))
  for i in range(0,len(cards),80):print("REWAN_TYPE_CARDS_CHUNK "+json.dumps(cards[i:i+80],separators=(",",":")))
 except Exception as exc:print("REWAN_TYPE_CLASSIFICATION_ERROR "+str(exc)[:270])
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
