#!/usr/bin/env python3
"""Discover publicly listed individual Darco Prime unit-number + building on Yarmax portal.
Read-only public portal evidence, no private project IDs, no inference from marketing counts.
"""
import json,os,re,time
from pathlib import Path
from urllib.parse import urlsplit,urljoin
from urllib.robotparser import RobotFileParser
from scrapling.fetchers import Fetcher
from lxml import html as LX
ROOT="https://yarmax.estate"
HOST="yarmax.estate"
URL=ROOT+"/ar/developers/darco"
UA="SAE-DB-public-real-estate-unit-card-research/1.0"
OUT=Path(os.environ.get("RUNNER_TEMP","/tmp"))/"yarmax_darco_prj660_original_unit_links.json"
state={"schema":"SAE_PUBLIC_YARMAX_DARCO_PRIME_REAL_LISTED_PHYSICAL_UNIT_CARDS_V1",
       "status":"START","publisher_url":URL,"cards":[],"overview":{},"errors":[],"master_writes":0}
def save():OUT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def fetch(url):
 p=urlsplit(url)
 if p.scheme!="https" or p.hostname!=HOST or p.path not in ("/robots.txt","/ar/developers/darco"):raise ValueError("OFF_SOURCE")
 r=Fetcher.get(url,retries=0,timeout=35,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("HTTP_429_GLOBAL_STOP")
 if int(r.status)!=200:raise RuntimeError("HTTP_"+str(r.status))
 if urlsplit(str(r.url)).hostname!=HOST:raise ValueError("OFFSITE_REDIRECT")
 return r
try:
 rb=fetch(ROOT+"/robots.txt")
 rp=RobotFileParser();rp.parse(rb.body.decode("utf8","replace").splitlines())
 if not rp.can_fetch(UA,URL):raise RuntimeError("ROBOTS_DISALLOW")
 time.sleep(max(3,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
 r=fetch(URL);doc=LX.fromstring(r.body)
 s=set()
 for a in doc.xpath("//a[@href]"):
  url=urljoin(URL,a.get("href"))
  u=urlsplit(url)
  if u.hostname!=HOST or not u.path.startswith("/ar/developers/darco/"):continue
  text=" ".join(" ".join(a.itertext()).split())
  # Per publisher named physical apartment and building, not a model/category.
  match=re.search(r"الشقة\s+(\d{1,3})\s*·\s*المبنى\s+([AB]\d{2})",text)
  if not match:continue
  unit_number=match.group(1);building=match.group(2)
  if not re.search(r"داركو برايم",text):continue
  identity=building+"|"+unit_number
  if identity in s:continue
  s.add(identity)
  area_match=re.search(r"(\d+(?:\.\d+)?)\s*م²",text)
  price_match=re.search(r"(\d{1,3}(?:,\d{3})+)\s*ر\.س",text)
  beds=re.search(r"(\d+)\s*غرف",text)
  if "غرفة نوم واحدة" in text:bedrooms=1
  elif "غرفتا نوم" in text:bedrooms=2
  elif beds:bedrooms=int(beds.group(1))
  else:bedrooms=None
  state["cards"].append({"source_listing_url":url,"source_portal":URL,
         "original_publisher_card_text":text[:580],
         "original_displayed_unit_number":unit_number,"original_displayed_building":building,
         "area_sqm_displayed":float(area_match.group(1)) if area_match else None,
         "bedrooms_displayed":bedrooms,
         "source_published_asking_price_sar":int(price_match.group(1).replace(",","")) if price_match else None,
         "asking_basis":"THIRD_PARTY_PUBLISHED_ADVERTISED_NOT_CONFIRMED_LIVE",
         "developer_source_verified":False,
         "availability":"THIRD_PARTY_PENDING_CONFIRMATION",
         "original_source_identity":identity})
 state["overview"]={"links_total":len(doc.xpath('//a[@href]')),"unique_itemized_unit_cards":len(state["cards"]),"unique_buildings":sorted(set(x["original_displayed_building"] for x in state["cards"]))}
 state["status"]="COMPLETE_SOURCE_CARDS"
except Exception as e:
 state["status"]="STOPPED_429" if "HTTP_429_GLOBAL_STOP" in str(e) else "STOPPED_ERROR"
 state["errors"].append(type(e).__name__+": "+str(e)[:220])
finally:
 save()
 print("YARMAX_SOURCE_AUDIT "+json.dumps({"status":state["status"],"overview":state["overview"],"errors":state["errors"]},ensure_ascii=False),flush=True)
 for i in range(0,len(state["cards"]),10):
  print("YARMAX_ORIGINAL_PUBLIC_CARDS "+json.dumps(state["cards"][i:i+10],ensure_ascii=False,separators=(",",":")),flush=True)
if state["status"]!="COMPLETE_SOURCE_CARDS":raise SystemExit(2)
