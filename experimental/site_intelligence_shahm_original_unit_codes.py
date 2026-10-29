#!/usr/bin/env python3
"""SAE official Shahm firstparty unit identity discovery, source-only.

Only previously public original developer project pages and firstparty compare.
Scrapling 0.5 + robust Arabic digit/decimal normalization. No guessed units.
JSON findings must be crosschecked against existing SAE Master project identity.
"""
import os,json,re,time
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit,urlunsplit
from urllib.robotparser import RobotFileParser
from collections import Counter
from bs4 import BeautifulSoup
from scrapling.fetchers import Fetcher
ROOT="https://shahm.re"
PATHS=["/compare","/projects/scarlet","/projects/sapphire",
       "/projects/veloria","/projects/variant","/projects/shahm-one","/projects/emerald"]
UA="SAE-DB-Firstparty-Shahm-Published-Unit-Source-Research/1.0"
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"shahm-source-intelligence-public-original-individual-codes.json"
d={"schema":"SAE_SHAHM_PUBLISHER_ACTUAL_UNIT_CODES_FIRSTPARTY_V1",
"source":"https://shahm.re","timestamp_utc":datetime.now(timezone.utc).isoformat(),
"pages":[],"errors":[],"status":"START","master_writes":0}
def save():OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def fetch(path):
 if path not in PATHS+["/robots.txt"]:raise ValueError("OFF_SCOPE")
 r=Fetcher.get(ROOT+path,retries=0,timeout=35,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("GLOBAL_429_STOP")
 if int(r.status)!=200 and not(path=="/robots.txt" and int(r.status)==404):
  raise RuntimeError("HTTP_"+str(r.status)+"_"+path)
 if urlsplit(str(r.url)).hostname not in ("shahm.re","www.shahm.re"):raise ValueError("OFF_PUBLISHER_REDIRECT")
 return r
def normalize(s):
 ar="٠١٢٣٤٥٦٧٨٩"
 return str(s).translate(str.maketrans(ar,"0123456789")).replace("٫",".").replace("٬","").replace("ـ","")
try:
 rb=fetch("/robots.txt")
 rp=RobotFileParser()
 if int(rb.status)==200:rp.parse(rb.body.decode("utf8","replace").splitlines())
 else:rp.parse([])
 delay=max(3,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0))
 for path in PATHS:
  url=ROOT+path
  if not rp.can_fetch(UA,url):raise RuntimeError("ROBOTS_DENY_"+path)
  time.sleep(delay)
  resp=fetch(path)
  html=resp.body.decode("utf8","replace")
  soup=BeautifulSoup(html,"lxml")
  for tag in soup(["script","style","noscript","form","svg"]):tag.decompose()
  text=" ".join(soup.get_text(" ",strip=True).split())
  clean=normalize(text)
  units=[]
  # Unit 01 – first floor, 114.75 m². Preserve exact code and floor as primary identity.
  pattern=re.compile(r"الوحدة\s*(\d{1,3})\s*[-–—]?\s*الدور\s*(الأول|الثاني|الثالث|الرابع|الأرضي|الملحق)\s*(\d+(?:\.\d+)?)\s*م\s*(?:²|2|مربع)",re.I)
  for hit in pattern.finditer(clean):
   n=int(hit.group(1))
   if n<1 or n>500:continue
   units.append({"original_number":hit.group(1),"floor_original":hit.group(2),
    "area_sqm":float(hit.group(3)),
    "evidence":text[max(0,hit.start()-50):hit.end()+40]})
  # Exact source text near code can be recovered if markup separated "م²".
  snippets=[]
  for hit in list(re.finditer(r"الوحدة\s*\d{1,3}",clean))[:100]:
   snippets.append(clean[max(0,hit.start()-65):hit.end()+115])
  seen=set();unique=[];dupes=[]
  for x in units:
   k=(x["original_number"],x["floor_original"],x["area_sqm"])
   if k in seen:dupes.append(x);continue
   seen.add(k);unique.append(x)
  h1=[x.get_text(" ",strip=True) for x in soup.select("h1")[:4]]
  pages={"url":url,"http":int(resp.status),"title":soup.title.get_text(" ",strip=True)[:150] if soup.title else None,
         "h1":h1,"bytes":len(resp.body),"unit_phrase_occurrences":len(re.findall(r"الوحدة\s*\d{1,3}",clean)),
         "original_identified_unit_rows":unique,"same_page_repeats":len(dupes),
         "samples":snippets[:35],"project_title_nearby":clean[:450]}
  d["pages"].append(pages);save()
  print("SHAHM_PAGE "+json.dumps({"path":path,"unit_phrase":pages["unit_phrase_occurrences"],
     "verified_rows":len(unique),"repeated":len(dupes),"h1":h1,"samples":snippets[:2]},ensure_ascii=False),flush=True)
 d["status"]="COMPLETE_PUBLIC_SOURCE_ONLY"
except Exception as ex:
 d["status"]="STOP_429" if "GLOBAL_429" in str(ex) else "STOP_SOURCE_ERROR"
 d["errors"].append(type(ex).__name__+": "+str(ex)[:320])
finally:
 save()
 print("FINAL "+json.dumps({"status":d["status"],"pages":len(d["pages"]),
   "unit_pattern_matches":sum(len(x["original_identified_unit_rows"]) for x in d["pages"]),"errors":d["errors"]},ensure_ascii=False))
if d["status"]!="COMPLETE_PUBLIC_SOURCE_ONLY":raise SystemExit(1)
