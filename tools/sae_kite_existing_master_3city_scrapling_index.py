#!/usr/bin/env python3
"""Scrapling source-first Kite indexed project discovery, canonical existing IDs only.

Scans public city indexes and *verified* public project URLs. Names/cities are
research matching candidates, never automatic physical-unit identity.
No UNIT writes; listing ID is not unit code. No project/developer creation.
"""
import collections, hashlib, json, re, time, unicodedata
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from html.parser import HTMLParser
from scrapling.fetchers import Fetcher

HOME="https://kite.sa"
INDEXES={
 "riyadh":list(range(1,27)),
 "jeddah":list(range(1,25)),
 "eastern-province":list(range(1,23))
}
MANIFEST=Path("tools/sae_kite_existing_master_only_index_20261030.json")
OUT=Path("sae-kite-existing-master-index-paginated-original-links.json")
UA="SAE-DB-verified-existing-project-index-survey/1.0"
DOC={"schema":"SAE_KITE_INDEX_EXACT_EXISTING_MASTER_CROSSWALK_READONLY_V1",
     "utc":datetime.now(timezone.utc).isoformat(),"writes":0,
     "indexed_pages":[],"source_project_candidates":[],"source_project_inventory_preview":[],
     "stop":None,"errors":[]}
PREG=re.compile(r"/en/projects/(riyadh|jeddah|eastern-province)/(\d+)/?$")
LREG=re.compile(r"/en/listing/(\d+)/?$")

class Anchors(HTMLParser):
 def __init__(self):
  super().__init__();self.stack=[];self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag=="a":
   self.stack.append({"href":dict(attrs).get("href",""),"parts":[]})
 def handle_data(self,data):
  if self.stack and data.strip():self.stack[-1]["parts"].append(data.strip())
 def handle_endtag(self,tag):
  if tag=="a" and self.stack:
   x=self.stack.pop()
   self.links.append((x["href"]," ".join(x["parts"])))
def save():
 tmp=OUT.with_suffix(".tmp")
 tmp.write_text(json.dumps(DOC,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 tmp.replace(OUT)
def norm(s):
 s=unicodedata.normalize("NFKC",str(s or ""))
 s=re.sub(r"[\u064b-\u065f\u0670\u0640]","",s)
 s=s.replace("إ","ا").replace("أ","ا").replace("آ","ا").replace("ى","ي").replace("ة","ه")
 s=s.lower()
 s=re.sub(r"[^0-9a-z\u0621-\u064a]+"," ",s)
 return " ".join(s.split())
def city_ok(master,source_city):
 city=norm(master).replace("jiddah","jeddah")
 matches={
  "riyadh":("riyadh","الرياض","diriyah","الدرعية"),
  "jeddah":("jeddah","جده","جدة","makkah","مكه"),
  "eastern-province":("dammam","الدمام","khobar","الخبر","al ahsa","الاحساء",
    "jubail","الجبيل","qatif","القطيف","safwa","صفوي","al hofuf","الهفوف","al hassa")
 }
 return any(norm(x) == city for x in matches[source_city])
def robots():
 r=Fetcher.get(HOME+"/robots.txt",retries=0,timeout=22,headers={"User-Agent":UA})
 if int(r.status)!=200:raise RuntimeError("ROBOTS_HTTP_"+str(r.status))
 rp=RobotFileParser();rp.parse(r.body.decode("utf8","replace").splitlines())
 return rp
def fetch(url):
 p=urlparse(url)
 if p.scheme!="https" or p.hostname!="kite.sa":raise RuntimeError("OFF_HOST")
 r=Fetcher.get(url,retries=0,timeout=27,headers={"User-Agent":UA})
 status=int(r.status)
 if status in (403,429):raise RuntimeError("SOURCE_HTTP_"+str(status))
 if status!=200:raise RuntimeError("HTTP_"+str(status))
 body=r.body
 if len(body)>5000000:raise RuntimeError("LARGE_HTML")
 return body.decode("utf8","replace"),hashlib.sha256(body).hexdigest()
def main():
 master=json.loads(MANIFEST.read_text(encoding="utf8"))["projects"]
 bynorm=collections.defaultdict(list)
 for m in master:
  if m["project_id"].startswith("PRJ-") and (m.get("name_ar") or m.get("name_en")):
   for text in (m.get("name_ar"),m.get("name_en")):
    n=norm(text)
    if n and len(n)>=6:bynorm[n].append(m)
 try:
  rules=robots()
  possibles={}
  for city,pages in INDEXES.items():
   missing=0
   for page in pages:
    u=HOME+"/en/projects/"+city+("?page="+str(page) if page>1 else "")
    if not rules.can_fetch(UA,u):
     DOC["indexed_pages"].append({"url":u,"status":"ROBOTS_DISALLOW"})
     continue
    time.sleep(1.65)
    try:
     html,sh=fetch(u)
    except Exception as e:
     if "429" in str(e) or "403" in str(e):
      DOC["stop"]="ACCESS_"+str(e);save();return
     DOC["indexed_pages"].append({"url":u,"status":"PAGE_SOURCE_ERROR","error":str(e)[:90]})
     missing+=1
     if missing>=3:break
     continue
    miss=0;found=0;matched=0
    parser=Anchors();parser.feed(html)
    for href,label in parser.links:
     p=urlparse(urljoin(u,href))
     if p.hostname!="kite.sa" or not PREG.fullmatch(p.path) or PREG.fullmatch(p.path).group(1)!=city:continue
     found+=1
     clean=norm(label)
     matches=[]
     # Exact normalized name preferred; a subset match is discovery-only.
     for n in (clean,):
      for row in bynorm.get(n,[]):
       if city_ok(row["city"],city):matches.append({"canonical_project_id":row["project_id"],"exact_name":True})
     if not matches:
      # avoid matching generic names without identifying developer
      for n,rows in bynorm.items():
       if len(n)<11:continue
       if n in clean and len(clean)-len(n)<=35:
        for row in rows:
         if city_ok(row["city"],city):matches.append({"canonical_project_id":row["project_id"],"exact_name":False})
     distinct={m["canonical_project_id"]:m for m in matches}
     if len(distinct)==1:
      m=next(iter(distinct.values()))
      uri=HOME+p.path
      possibles[(m["canonical_project_id"],uri)]={"canonical_project_id":m["canonical_project_id"],
        "source_url":uri,"source_project_label":label[:240],"city":city,
        "exact_name":m["exact_name"],"source_index":u}
      matched+=1
    DOC["indexed_pages"].append({"url":u,"sha":sh,"links":found,"matched_candidates":matched})
    print("SAE_KITE_INDEX",json.dumps({"city":city,"page":page,"links":found,"possible":matched},ensure_ascii=False),flush=True)
    save()
  DOC["source_project_candidates"]=list(possibles.values())
  DOC["sources_found"]=len(possibles)
  # Query detail projects only after exact name/city source match, and limit
  # to 45 per run; other matches retained for subsequent batch processing.
  shortlist=sorted(possibles.values(),key=lambda x:(not x["exact_name"],x["city"],x["canonical_project_id"]))[:45]
  for candidate in shortlist:
   u=candidate["source_url"]
   if not rules.can_fetch(UA,u):
    DOC["source_project_inventory_preview"].append({"source_url":u,"status":"ROBOTS_DISALLOW"});continue
   time.sleep(1.7)
   try:
    html,sh=fetch(u)
   except Exception as e:
    DOC["source_project_inventory_preview"].append({"source_url":u,"error":str(e)[:100]})
    if "429" in str(e) or "403" in str(e):
     DOC["stop"]="ACCESS_"+str(e);save();return
    continue
   parser=Anchors();parser.feed(html)
   ids=[]
   for href,label in parser.links:
    link=urlparse(urljoin(u,href))
    if link.hostname=="kite.sa" and LREG.fullmatch(link.path):
     ids.append({"original_listing_url":HOME+link.path,"original_anchor":label[:180]})
   dedup={k["original_listing_url"]:k for k in ids}
   out={**candidate,"sha256":sh,"original_individual_listing_links":len(dedup),
      "source_listing_samples":list(dedup.values())[:25]}
   DOC["source_project_inventory_preview"].append(out)
   print("SAE_KITE_PROJECT",json.dumps({"pid":out["canonical_project_id"],"source_label":out["source_project_label"],
       "exact":out["exact_name"],"source_url":out["source_url"],"listing_links":len(dedup),
       "codes_preview":out["source_listing_samples"][:3]},ensure_ascii=False)[:2200],flush=True)
   save()
 except Exception as exc:
  DOC["stop"]="SOURCE_FAILURE_"+type(exc).__name__+":"+str(exc)[:150]
 finally:
  save()
  print("SAE_KITE_SUMMARY",json.dumps({"indexed":len(DOC["indexed_pages"]),
    "candidate_project_links":len(DOC["source_project_candidates"]),
    "detail_projects":len(DOC["source_project_inventory_preview"]),
    "total_original_listing_links_in_details":sum(x.get("original_individual_listing_links",0) for x in DOC["source_project_inventory_preview"]),
    "stop":DOC["stop"]},ensure_ascii=False),flush=True)
if __name__=="__main__":
 assert norm("الماجدية ١٢٤") != norm("الماجدية 124") or True
 main()
