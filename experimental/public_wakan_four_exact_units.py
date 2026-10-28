#!/usr/bin/env python3
"""Scrapling first-party individual Wakan units; original publisher codes, no private SAE project IDs."""
import os,re,time,json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from lxml import html as LX
from scrapling.fetchers import Fetcher
HOST="wakan.sa";UA="SAE-DB-public-original-individual-units/1.0"
URLS={"042":"https://wakan.sa/EstateProjects/Detail/30074","027":"https://wakan.sa/EstateProjects/Detail/10047","013":"https://wakan.sa/EstateProjects/Detail/42","017":"https://wakan.sa/EstateProjects/Detail/56"}
OUT=Path(os.environ["RUNNER_TEMP"])/"wakan_four_real_unit_cards.json"
data={"status":"STARTED","projects":[],"cards":[],"errors":[],"production_writes":0,"private_project_mapping":False}
def save():OUT.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
def text(el):return " ".join(" ".join(el.itertext()).split()) if el is not None else ""
def get(url):
 p=urlsplit(url)
 if p.scheme!="https" or p.hostname!=HOST or (p.path!="/robots.txt" and p.path not in [urlsplit(x).path for x in URLS.values()]):raise ValueError("OFF_SCOPE_HOST_PATH")
 r=Fetcher.get(url,retries=1,timeout=35,follow_redirects="safe",headers={"User-Agent":UA})
 if int(r.status)==429:raise RuntimeError("HTTP429_STOP_GLOBAL")
 if urlsplit(str(r.url)).hostname not in ("wakan.sa","www.wakan.sa"):raise ValueError("OFF_SOURCE_REDIRECT")
 return r
try:
 robot=get("https://"+HOST+"/robots.txt")
 if int(robot.status) not in (200,404,410):raise RuntimeError("ROBOTS_HTTP_"+str(robot.status))
 rp=RobotFileParser()
 if int(robot.status)==200:rp.parse(robot.body.decode("utf-8","replace").splitlines())
 else:rp.allow_all=True
 seen=set()
 for key,url in URLS.items():
  if not rp.can_fetch(UA,url):raise RuntimeError("ROBOTS_DISALLOW_"+key)
  time.sleep(max(3.,float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0)))
  r=get(url)
  if int(r.status)!=200:raise RuntimeError("PAGE_HTTP_"+str(r.status))
  root=LX.fromstring(r.body.decode("utf-8","replace"))
  h=text(root.xpath("//h1")[0]) if root.xpath("//h1") else ""
  if not re.search(r"\bWAKAN\s+0?"+key+r"\b",h,re.I):raise RuntimeError("PROJECT_IDENTITY_FAILED_"+key+"_"+h[:60])
  project={"publisher_project_code":key,"title":h,"source_url":url,"real_cards":0,"building_counts":{},"statuses":{}}
  for building in root.xpath('//div[contains(concat(" ",normalize-space(@class)," ")," buld ")]'):
   heading=text(building.xpath(".//h3")[0]) if building.xpath(".//h3") else ""
   match=re.search(r"\bbuilding\s+(.+?)$",heading,re.I)
   building_name=match.group(1).strip() if match else None
   if not building_name:raise ValueError("SOURCE_BUILDING_HEADING_MISSING_"+key)
   for anchor in building.xpath('.//a[contains(concat(" ",normalize-space(@class)," ")," toggle ")]'):
    raw_code=" ".join(" ".join(anchor.xpath("./text()")).split()).strip()
    if not re.fullmatch(r"[A-Za-z0-9]{1,4}(?:/[A-Za-z0-9]{1,4})?",raw_code):raise ValueError("BAD_UNIT_CODE_"+key+"_"+raw_code[:30])
    pub_code=(building_name+" "+raw_code) if building_name in ("A","B","C","D","E") else raw_code
    identity=key+"|"+pub_code
    if identity in seen:raise ValueError("DUP_SOURCE_KEY_"+identity)
    seen.add(identity)
    sub=anchor.xpath('following-sibling::div[contains(concat(" ",normalize-space(@class)," ")," accordion-inner ")][1]')
    if len(sub)!=1:raise ValueError("ORIGINAL_CARD_BODY_MISSING_"+identity)
    body=sub[0]
    header=body.xpath('.//h4[contains(translate(normalize-space(.),"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"),"unit area")]')
    area_text=text(header[0]) if header else ""
    area_match=re.search(r"(?<!\d)(\d+(?:\.\d+)?)\s*(?:م|m\b)",area_text,re.I)
    if not area_match:raise ValueError("NO_INDIVIDUAL_AREA_"+identity+" "+area_text[:70])
    area=float(area_match.group(1))
    raw_status=text(anchor.xpath('./strong[last()]')[0]) if anchor.xpath('./strong') else "UNSPECIFIED"
    status={"sold":"PUBLISHER_SOLD","مباع":"PUBLISHER_SOLD","للايجار":"PUBLISHER_RENT","for rent":"PUBLISHER_RENT","for sell":"PUBLISHER_FOR_SALE"}.get(raw_status.strip().lower(),"PUBLISHER_STATUS_"+raw_status.strip().replace(" ","_"))
    price_nodes=anchor.xpath('./strong[contains(concat(" ",normalize-space(@class)," ")," myDIV ")]')
    visible_price=int(re.sub(r"[^0-9]","",text(price_nodes[0]))) if price_nodes else None
    if status!="PUBLISHER_FOR_SALE" and visible_price is not None:raise ValueError("SALE_PRICE_ON_NON_SALE_CARD_"+identity)
    attrs=[text(span) for span in body.xpath('.//span') if text(span)]
    floor=next((a.replace("Floor ","").strip() for a in attrs if re.match(r"^Floor\s",a,re.I)),None)
    beds=next((int(m.group(1)) for a in attrs if (m:=re.search(r"\b(?:Bedrooms?|غرف نوم)\s+(\d+)\b",a,re.I))),None)
    baths=next((int(m.group(1)) for a in attrs if (m:=re.search(r"\b(?:Bathrooms?|حمام)\s+(\d+)\b",a,re.I))),None)
    card={"publisher_project_code":key,"publisher_project_name":h,"source_url":url,
      "original_building_name":building_name,"original_unit_label":raw_code,"original_unit_code":pub_code,
      "area_sqm":area,"floor_original":floor,"bedrooms":beds,"bathrooms":baths,
      "publisher_status":status,"publisher_status_text":raw_status,
      "visible_sale_asking_price_sar":visible_price,"raw_features":attrs[:28]}
    data["cards"].append(card);project["real_cards"]+=1
    project["building_counts"][building_name]=project["building_counts"].get(building_name,0)+1
    project["statuses"][status]=project["statuses"].get(status,0)+1
  data["projects"].append(project);save()
  print("WAKAN_ORIGINAL_PROJECT "+json.dumps(project,ensure_ascii=False,separators=(",",":")))
 if len(data["cards"])<50:raise ValueError("INSUFFICIENT_EXACT_UNIT_CARDS")
 data["status"]="COMPLETE_SOURCE_CARDS"
except Exception as exc:
 data["status"]="STOPPED_429" if "HTTP429_STOP" in str(exc) else "STOPPED_ERROR"
 data["errors"].append({"error":type(exc).__name__+": "+str(exc)[:220]})
finally:
 save()
 print("WAKAN_ORIGINAL_SOURCE_SUMMARY "+json.dumps({"status":data["status"],"total_cards":len(data["cards"]),"projects":data["projects"],"errors":data["errors"]},ensure_ascii=False,separators=(",",":")))
 for i in range(0,len(data["cards"]),12):print("WAKAN_SOURCE_CARDS_JSON "+json.dumps(data["cards"][i:i+12],ensure_ascii=False,separators=(",",":")))
if data["status"]!="COMPLETE_SOURCE_CARDS":raise SystemExit(1)
