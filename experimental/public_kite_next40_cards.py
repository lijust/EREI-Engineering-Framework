#!/usr/bin/env python3
"""Robots-gated public Kite project-page itemized listing cards; source-only JSON, no database writes."""
from __future__ import annotations
import json,os,re,time,sys
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from lxml import html as lx
from scrapling.fetchers import Fetcher

UA="SAE-DB-public-real-estate-listing-research/1.0"
OUT=Path(os.environ["RUNNER_TEMP"])/"kite-next40-individual-offer-cards.json"
CATALOG=Path(__file__).with_name("public_kite_next40_urls.json")
state={"schema":"PUBLIC_KITE_INDIVIDUALLY_ITEMIZED_LISTINGS_V1","status":"STARTED",
       "sources":[],"source_cards":[],"errors":[],"private_db_access":False,"master_writes":0}
def save():OUT.write_text(json.dumps(state,ensure_ascii=False),encoding="utf-8")
def get(url):
 p=urlsplit(url)
 if p.scheme!="https" or p.hostname!="kite.sa" or p.username or p.password or p.port:
  raise ValueError("NON_KITE_URL")
 if not (p.path=="/robots.txt" or re.fullmatch(r"/en/projects/(?:riyadh|jeddah|eastern-province)/[0-9]+",p.path)):
  raise ValueError("NOT_PUBLIC_PROJECT_DETAIL")
 r=Fetcher.get(url,retries=1,timeout=30,follow_redirects="safe",
               headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("HTTP_429_GLOBAL_STOP")
 if urlsplit(str(r.url)).hostname!="kite.sa":raise ValueError("OFF_SOURCE_REDIRECT")
 return r
def parse_page(content,url):
 root=lx.fromstring(content)
 project=" ".join(" ".join(root.xpath("//h1[1]//text()")).split())
 records=[]
 for a in root.xpath('//a[starts-with(@href,"/en/listing/")]'):
  href=a.get("href") or ""
  if not re.fullmatch(r"/en/listing/[0-9]+",href):continue
  paras=[" ".join(" ".join(p.itertext()).split()) for p in a.xpath(".//p")]
  title=paras[0] if paras else ""
  specs=paras[1] if len(paras)>1 else ""
  price_nodes=a.xpath(".//span[contains(text(),'SAR')]/text()")
  asking=price_nodes[-1] if price_nodes else None
  asking_number=None
  if asking and re.search(r"\d",asking):
   v=re.sub(r"[^0-9.]","",asking)
   try:asking_number=float(v)
   except ValueError:pass
  code=None
  m=re.search(r" - وحدة ([^/]{2,90})$",title,re.I) or re.search(r"\s/\s([^/]{1,100})$",title)
  if m:code=m.group(1).strip()
  if code and (len(code)<1 or len(code)>95):code=None
  sale=("للبيع" in title or "for sale" in title.lower())
  rent=("للإيجار" in title or "للايجار" in title or "for rent" in title.lower())
  bb=re.search(r"(\d+)\s+Beds?",specs,re.I)
  bt=re.search(r"(\d+)\s+Baths?",specs,re.I)
  area=re.search(r"([\d,.]+)\s+sqm",specs,re.I)
  records.append({"publisher_listing_id":href.split("/")[-1],"listing_url":"https://kite.sa"+href,
       "publisher_project_url":url,"publisher_project_title":project,"published_title":title,
       "source_unit_code":code,"spec_text":specs,"beds":int(bb.group(1)) if bb else None,
       "baths":int(bt.group(1)) if bt else None,
       "area_sqm":float(area.group(1).replace(",","")) if area else None,
       "asking_price_sar":asking_number,"publisher_asking_text":asking,
       "offer_class":"SALE" if sale else "RENT" if rent else "UNKNOWN",
       "source_availability":"LISTED_KITE_SNAPSHOT_NOT_LIVE"})
 return project,records
try:
 urls=json.loads(CATALOG.read_text(encoding="utf-8"))["urls"]
 if not 1<=len(urls)<=40 or len(set(urls))!=len(urls):raise ValueError("INVALID_CATALOG")
 r=get("https://kite.sa/robots.txt")
 if int(r.status)!=200:raise RuntimeError("ROBOTS_HTTP_"+str(r.status))
 rp=RobotFileParser();rp.parse(r.body.decode("utf-8","replace").splitlines())
 delay=max(3.0,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0))
 seen=set()
 for url in urls:
  if not rp.can_fetch(UA,url):
   state["errors"].append({"url":url,"error":"ROBOTS_DISALLOW"})
   save()
   continue
  time.sleep(delay)
  response=get(url)
  if int(response.status)!=200:
   state["errors"].append({"url":url,"error":"HTTP_"+str(response.status)})
   save()
   continue
  title,items=parse_page(response.body,url)
  for item in items:
   identity=(url,item["publisher_listing_id"])
   if identity in seen:raise ValueError("DUPLICATE_LISTING_KEY")
   seen.add(identity)
  state["source_cards"].extend(items)
  source={"url":url,"publisher_project_title":title,"source_cards":len(items),
          "coded_cards":sum(x["source_unit_code"] is not None for x in items),
          "sale_cards":sum(x["offer_class"]=="SALE" for x in items)}
  state["sources"].append(source)
  save()
  print("PUBLISHER_PAGE "+json.dumps(source,ensure_ascii=False,separators=(",",":")))
 state["status"]="COMPLETE_SOURCE_CARDS"
except Exception as exc:
 state["status"]="STOPPED_429" if "HTTP_429_GLOBAL_STOP" in str(exc) else "STOPPED_ERROR"
 state["errors"].append({"error":type(exc).__name__+": "+str(exc)[:200]})
finally:
 save()
 for k in range(0,len(state["source_cards"]),10):
  print("SOURCE_CARDS_JSON "+json.dumps(state["source_cards"][k:k+10],ensure_ascii=False,separators=(",",":")))
 print("PROJECT_UNIT_CARDS_SUMMARY "+json.dumps({"status":state["status"],"projects":len(state["sources"]),
   "itemized_offers":len(state["source_cards"]),"coded_cards":sum(bool(x["source_unit_code"]) for x in state["source_cards"]),
   "errors":state["errors"]},ensure_ascii=False,separators=(",",":")))
