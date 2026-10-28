#!/usr/bin/env python3
"""First-party Vellano original brochure page contact sheet, read-only visual source review."""
import base64,hashlib,io,json,os,sys,time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
import fitz
from PIL import Image,ImageDraw
BASE="https://koohejidevelopment.sa"
URL=BASE+"/wp-content/uploads/2025/11/Vellano-Brochure-2025.pdf"
UA="SAE-DB-source-review/1.0"
status={"status":"START","source_url":URL,"bytes":0,"pdf_pages":0,"text_words":0,"error":None,"master_writes":0}
def get(url):
 r=Fetcher.get(url,retries=0,timeout=155,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("HTTP429_STOP")
 if int(r.status)!=200:raise RuntimeError("HTTP_"+str(r.status))
 if urlsplit(str(r.url)).hostname!="koohejidevelopment.sa":raise RuntimeError("OFF_SOURCE")
 return r.body
try:
 rob=get(BASE+"/robots.txt")
 rp=RobotFileParser();rp.parse(rob.decode("utf8","replace").splitlines())
 if not rp.can_fetch(UA,URL):raise RuntimeError("ROBOTS_DISALLOW")
 time.sleep(max(3.0,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
 b=get(URL)
 if not b.startswith(b"%PDF") or len(b)>130_000_000:raise RuntimeError("BAD_PDF")
 doc=fitz.open(stream=b,filetype="pdf")
 status["bytes"]=len(b);status["sha256"]=hashlib.sha256(b).hexdigest();status["pdf_pages"]=len(doc)
 cells=[]
 for i,p in enumerate(doc):
  status["text_words"]+=len(p.get_text("words"))
  sc=min(330/p.rect.width,230/p.rect.height)
  pix=p.get_pixmap(matrix=fitz.Matrix(sc,sc),alpha=False)
  im=Image.frombytes("RGB",(pix.width,pix.height),pix.samples)
  cells.append(im)
 cols=5;cw=338;ch=266
 rows=(len(cells)+cols-1)//cols
 canvas=Image.new("RGB",(cols*cw,rows*ch),(240,240,240))
 pen=ImageDraw.Draw(canvas)
 for i,im in enumerate(cells):
  x=(i%cols)*cw+4;y=(i//cols)*ch+21
  canvas.paste(im,(x,y));pen.text((x,y-17),"PDF PAGE "+str(i+1),fill=(0,0,0))
 f=io.BytesIO();canvas.save(f,format="JPEG",quality=52,optimize=True)
 img=f.getvalue()
 if len(img)>1_600_000:raise RuntimeError("CONTACT_TOO_LARGE")
 print("VELLANO_PDF_ALL_PAGES_JPEG_BASE64 "+base64.b64encode(img).decode("ascii"),flush=True)
 status["status"]="CONTACT_RENDER_COMPLETE";status["mosaic_bytes"]=len(img);status["dimensions"]=[canvas.width,canvas.height]
except Exception as e:
 status["status"]="STOPPED_429" if "429" in str(e) else "STOPPED_ERROR";status["error"]=str(e)[:250]
finally:
 print("VELLANO_PDF_CONTACT_RESULT "+json.dumps(status,separators=(",",":")),flush=True)
 Path(os.environ.get("RUNNER_TEMP","/tmp"),"vellano_visual_page_contact_status.json").write_text(json.dumps(status),encoding="utf-8")
if status["status"]!="CONTACT_RENDER_COMPLETE":sys.exit(2)
